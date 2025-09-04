# document_layout_detector.py - 프린터/스캔 변형 감지 및 보정

import cv2
import numpy as np
import fitz
from typing import Tuple, List, Optional

class DocumentLayoutDetector:
    """프린터/스캔 과정의 여백, 스케일, 크롭 변화를 감지하고 보정"""
    
    def __init__(self):
        self.debug = True
        
    def detect_layout_changes(self, original_pdf_page, scanned_pdf_page) -> dict:
        """원본과 스캔본 간의 레이아웃 변화 종합 분석"""
        
        # 1. 이미지 추출
        orig_img = self._page_to_image(original_pdf_page, scale=1.5)
        scan_img = self._page_to_image(scanned_pdf_page, scale=1.5)
        
        # 2. 문서 컨텐츠 영역 감지
        orig_content_box = self._find_content_bounding_box(orig_img)
        scan_content_box = self._find_content_bounding_box(scan_img)
        
        # 3. 여백 변화 계산
        margin_changes = self._calculate_margin_changes(orig_content_box, scan_content_box, 
                                                       orig_img.shape, scan_img.shape)
        
        # 4. 스케일 변화 감지
        scale_changes = self._detect_scale_changes(orig_content_box, scan_content_box)
        
        # 5. 회전 감지
        rotation_angle = self._detect_rotation_advanced(scan_img)
        
        return {
            "margin_offset": margin_changes,
            "scale_factor": scale_changes,
            "rotation_angle": rotation_angle,
            "original_content_box": orig_content_box,
            "scanned_content_box": scan_content_box
        }
    
    def _page_to_image(self, page, scale=1.5):
        """PDF 페이지를 고품질 이미지로 변환"""
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    
    def _find_content_bounding_box(self, img):
        """문서의 실제 컨텐츠 영역 찾기 (여백 제외)"""
        
        # 1. 적응형 이진화로 텍스트 영역 강조
        binary = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY_INV, 11, 2)
        
        # 2. 모폴로지 연산으로 텍스트 연결
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(binary, kernel, iterations=2)
        
        # 3. 컨투어 찾기
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
            
        # 4. 모든 컨텐츠를 포함하는 바운딩 박스
        all_contours = np.vstack(contours)
        x, y, w, h = cv2.boundingRect(all_contours)
        
        if self.debug:
            print(f"[컨텐츠 영역] 감지: ({x}, {y}, {x+w}, {y+h}) 크기: {w}×{h}")
        
        return [x, y, x + w, y + h]
    
    def _calculate_margin_changes(self, orig_box, scan_box, orig_shape, scan_shape):
        """여백 변화 계산"""
        if not orig_box or not scan_box:
            return {"left": 0, "top": 0, "right": 0, "bottom": 0}
        
        # 원본과 스캔본의 여백 비교
        orig_margins = {
            "left": orig_box[0],
            "top": orig_box[1], 
            "right": orig_shape[1] - orig_box[2],
            "bottom": orig_shape[0] - orig_box[3]
        }
        
        scan_margins = {
            "left": scan_box[0],
            "top": scan_box[1],
            "right": scan_shape[1] - scan_box[2], 
            "bottom": scan_shape[0] - scan_box[3]
        }
        
        margin_diff = {
            "left": scan_margins["left"] - orig_margins["left"],
            "top": scan_margins["top"] - orig_margins["top"],
            "right": scan_margins["right"] - orig_margins["right"],
            "bottom": scan_margins["bottom"] - orig_margins["bottom"]
        }
        
        if self.debug:
            print(f"[여백 변화] 좌:{margin_diff['left']:.1f} 상:{margin_diff['top']:.1f} "
                  f"우:{margin_diff['right']:.1f} 하:{margin_diff['bottom']:.1f}")
        
        return margin_diff
    
    def _detect_scale_changes(self, orig_box, scan_box):
        """스케일 변화 감지 (용지 크기 변환, DPI 변화 등)"""
        if not orig_box or not scan_box:
            return {"x": 1.0, "y": 1.0}
        
        orig_width = orig_box[2] - orig_box[0]
        orig_height = orig_box[3] - orig_box[1]
        scan_width = scan_box[2] - scan_box[0]
        scan_height = scan_box[3] - scan_box[1]
        
        scale_x = scan_width / orig_width if orig_width > 0 else 1.0
        scale_y = scan_height / orig_height if orig_height > 0 else 1.0
        
        if self.debug:
            print(f"[스케일 변화] X: {scale_x:.3f} ({orig_width:.0f}→{scan_width:.0f}) "
                  f"Y: {scale_y:.3f} ({orig_height:.0f}→{scan_height:.0f})")
        
        return {"x": scale_x, "y": scale_y}
    
    def _detect_rotation_advanced(self, img):
        """고급 회전 감지 (문서 경계선 기반)"""
        
        # 1. Canny 엣지 감지
        edges = cv2.Canny(img, 50, 150)
        
        # 2. 확률적 허프 변환으로 긴 직선들 찾기
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, 
                               minLineLength=img.shape[1]//4, maxLineGap=20)
        
        if lines is None:
            return 0.0
        
        # 3. 수평/수직에 가까운 선분들만 필터링
        horizontal_angles = []
        vertical_angles = []
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            
            # 수평선 (-15° ~ +15°)
            if -15 <= angle <= 15:
                horizontal_angles.append(angle)
            # 수직선 (75° ~ 105°)
            elif 75 <= abs(angle) <= 105:
                vertical_angles.append(90 - abs(angle))
        
        # 4. 가장 일관된 각도 선택
        all_angles = horizontal_angles + vertical_angles
        if all_angles:
            median_angle = np.median(all_angles)
            if self.debug:
                print(f"[회전 감지] {len(all_angles)}개 선분 분석, 중간값: {median_angle:.2f}도")
            return median_angle
        
        return 0.0
    
    def apply_layout_correction(self, roi_coords, layout_changes):
        """감지된 레이아웃 변화를 ROI 좌표에 적용"""
        
        margin = layout_changes["margin_offset"]
        scale = layout_changes["scale_factor"] 
        rotation = layout_changes["rotation_angle"]
        
        # 1. 여백 오프셋 적용
        corrected_coords = [
            roi_coords[0] + margin["left"],
            roi_coords[1] + margin["top"],
            roi_coords[2] + margin["left"], 
            roi_coords[3] + margin["top"]
        ]
        
        # 2. 스케일 변화 적용
        if scale["x"] != 1.0 or scale["y"] != 1.0:
            corrected_coords = [
                corrected_coords[0] * scale["x"],
                corrected_coords[1] * scale["y"],
                corrected_coords[2] * scale["x"],
                corrected_coords[3] * scale["y"]
            ]
        
        # 3. 회전 보정 (중심점 기준)
        if abs(rotation) > 1.0:
            # 회전 변환 행렬 적용 (추후 구현)
            pass
        
        if self.debug:
            print(f"[좌표 보정] {roi_coords} → {corrected_coords}")
            print(f"   여백오프셋: ({margin['left']:.1f}, {margin['top']:.1f})")
            print(f"   스케일: ({scale['x']:.3f}, {scale['y']:.3f})")
            print(f"   회전: {rotation:.2f}도")
        
        return corrected_coords

# 사용 예시
def test_layout_detection():
    """레이아웃 감지 테스트"""
    detector = DocumentLayoutDetector()
    
    # 실제 사용 시 PDF 페이지 객체 전달
    # layout_changes = detector.detect_layout_changes(original_page, scanned_page)
    # corrected_coords = detector.apply_layout_correction(roi_coords, layout_changes)
    
    print("✅ DocumentLayoutDetector 클래스 준비 완료")
    print("📌 pdf_validator_gui.py에 통합하여 사용하세요")

if __name__ == "__main__":
    test_layout_detection()
