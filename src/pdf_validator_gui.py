# src/pdf_validator_gui.py (v17.0 - 전처리 강화 및 폴백)

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import os
import fitz  # PyMuPDF
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import pytesseract
import sys
from PIL import Image, ImageTk
import re
import datetime
import time

# 레이아웃 감지 시스템 추가
class DocumentLayoutDetector:
    """프린터/스캔 과정의 여백, 스케일, 크롭 변화를 감지하고 보정"""

    def __init__(self):
        self.debug = True

    def find_content_bounding_box(self, img):
        """문서의 실제 컨텐츠 영역 찾기 (프로젝션 프로파일 기반)"""
        # 1. 이진화
        # 배경이 흰색(255)이고 내용이 검은색(0)이라고 가정
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img

        # 적응형 이진화로 그림자 등 음영 제거
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY_INV, 11, 2)

        # 2. 노이즈 제거 (선택적이지만 권장)
        kernel = np.ones((3,3),np.uint8)
        morphed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        # 3. 프로젝션 프로파일 계산
        # 수직 프로젝션 (x축 따라 합산) -> y좌표 찾기
        vertical_projection = np.sum(morphed, axis=1)
        # 수평 프로젝션 (y축 따라 합산) -> x좌표 찾기
        horizontal_projection = np.sum(morphed, axis=0)

        # 4. 내용이 있는 시작/끝 지점 찾기
        # 0이 아닌 값을 가진 첫번째/마지막 인덱스
        y_coords = np.where(vertical_projection > 0)[0]
        x_coords = np.where(horizontal_projection > 0)[0]

        if len(x_coords) == 0 or len(y_coords) == 0:
            # 내용이 전혀 없으면 전체 이미지 영역 반환
            if self.debug:
                print(f"[컨텐츠 영역] 감지 실패, 전체 페이지 사용")
            return [0, 0, img.shape[1], img.shape[0]]

        y_min, y_max = y_coords[0], y_coords[-1]
        x_min, x_max = x_coords[0], x_coords[-1]

        # 5. 여백 추가 (너무 타이트하게 자르지 않도록)
        padding = 10
        x_min = max(0, x_min - padding)
        y_min = max(0, y_min - padding)
        x_max = min(img.shape[1], x_max + padding)
        y_max = min(img.shape[0], y_max + padding)

        if self.debug:
            w, h = x_max - x_min, y_max - y_min
            print(f"[컨텐츠 영역] 감지: ({x_min}, {y_min}, {x_max}, {y_max}) 크기: {w}×{h}")

        return [x_min, y_min, x_max, y_max]

    def detect_document_rotation(self, img):
        """문서 기울기 자동 감지 (Hough 변환 이용)"""
        edges = cv2.Canny(img, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=200)

        if lines is not None:
            angles = []
            # lines의 각 원소를 안전하게 처리
            for line in lines[:30]:  # 상위 30개 선분 분석
                if len(line) >= 2:  # 안전 검사 추가
                    rho, theta = line[0], line[1]
                    angle = np.degrees(theta) - 90
                    if -45 < angle < 45:  # 수평/수직 선분만 고려
                        angles.append(angle)

            if angles:
                median_angle = np.median(angles)
                if self.debug:
                    print(f"[회전 감지] 기울기: {median_angle:.2f}도 ({len(angles)}개 선분 분석)")
                return median_angle

        if self.debug:
            print(f"[회전 감지] 선분 검출 실패, 회전 없음으로 가정")
        return 0

    def detect_layout_offset(self, original_img, scanned_img):
        """원본과 스캔본 간의 레이아웃 오프셋 감지 (회전 보정 포함)"""
        # 1. 회전 각도 감지
        rotation_angle = self.detect_document_rotation(scanned_img)

        # 2. 회전 보정 적용 (1도 이상 기울어진 경우)
        if abs(rotation_angle) > 1.0:
            center = (scanned_img.shape[1]//2, scanned_img.shape[0]//2)
            M_rotation = cv2.getRotationMatrix2D(center, rotation_angle, 1.0)
            scanned_img_rotated = cv2.warpAffine(scanned_img, M_rotation,
                                                (scanned_img.shape[1], scanned_img.shape[0]))
            if self.debug:
                print(f"[회전 보정] {rotation_angle:.2f}도 회전 보정 적용")
        else:
            scanned_img_rotated = scanned_img

        # 3. 컨텐츠 영역 감지
        orig_box = self.find_content_bounding_box(original_img)
        scan_box = self.find_content_bounding_box(scanned_img_rotated)

        if not orig_box or not scan_box:
            if self.debug:
                print(f"[레이아웃 감지] 컨텐츠 영역 감지 실패, 기본값 사용")
            return {"offset_x": 0, "offset_y": 0, "scale_x": 1.0, "scale_y": 1.0, "rotation": 0}

        # 4. 오프셋 계산 (컨텐츠 시작점 기준)
        offset_x = scan_box[0] - orig_box[0]
        offset_y = scan_box[1] - orig_box[1]

        # 5. 스케일 계산 (컨텐츠 크기 기준)
        orig_width = orig_box[2] - orig_box[0]
        orig_height = orig_box[3] - orig_box[1]
        scan_width = scan_box[2] - scan_box[0]
        scan_height = scan_box[3] - scan_box[1]

        scale_x = scan_width / orig_width if orig_width > 0 else 1.0
        scale_y = scan_height / orig_height if orig_height > 0 else 1.0

        # 6. 스케일 변화 분석
        scale_change_x = abs(scale_x - 1.0) * 100
        scale_change_y = abs(scale_y - 1.0) * 100

        if self.debug:
            print(f"[레이아웃 감지] 오프셋:({offset_x:.1f}, {offset_y:.1f}) 스케일:({scale_x:.3f}, {scale_y:.3f})")
            print(f"[스케일 분석] X축:{scale_change_x:.1f}% Y축:{scale_change_y:.1f}% 변화 감지")

            # 프린터/스캔 설정 추정
            if scale_change_x > 5 or scale_change_y > 5:
                if scale_x < 0.95 or scale_y < 0.95:
                    print(f"[변형 분석] A4↔Letter 용지 변환으로 추정 (축소: {min(scale_x, scale_y):.1%})")
                elif scale_x > 1.05 or scale_y > 1.05:
                    print(f"[변형 분석] 고해상도 스캔으로 추정 (확대: {max(scale_x, scale_y):.1%})")

            if abs(offset_x) > 20 or abs(offset_y) > 20:
                print(f"[변형 분석] 프린터 마진/자동크롭으로 추정 (오프셋: {abs(offset_x) + abs(offset_y):.0f}px)")

        return {
            "offset_x": offset_x,
            "offset_y": offset_y,
            "scale_x": scale_x,
            "scale_y": scale_y,
            "rotation": rotation_angle
        }

def setup_tesseract():
    """배포(frozen) 및 개발 환경 모두에서 Tesseract 경로를 안정적으로 설정합니다."""
    # PyInstaller로 생성된 실행파일인지 확인
    if getattr(sys, 'frozen', False):
        # EXE 파일과 같은 폴더에서 vendor 찾기 (외부 배치)
        application_path = os.path.dirname(sys.executable)
    else:
        # 일반 Python 스크립트 실행 환경
        # __file__은 현재 스크립트(pdf_validator_gui.py)의 경로
        # os.path.dirname()으로 스크립트가 있는 폴더(src)를 얻음
        # '..'을 통해 상위 폴더(프로젝트 루트)로 이동
        application_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Tesseract 실행 파일 경로 조합
    tesseract_cmd_path = os.path.join(application_path, 'vendor', 'tesseract', 'tesseract.exe')
    tessdata_dir = os.path.join(application_path, 'vendor', 'tesseract', 'tessdata')

    # 경로 존재 여부 확인 및 설정
    if os.path.exists(tesseract_cmd_path) and os.path.exists(tessdata_dir):
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd_path
        os.environ['TESSDATA_PREFIX'] = tessdata_dir
        return True
    else:
        # 디버깅용 로그 (배포 시는 비활성화)
        # print(f"🔥 Tesseract 경로 설정 실패. 다음 경로를 확인하세요:")
        # print(f"  - 실행 파일: {tesseract_cmd_path} (존재: {os.path.exists(tesseract_cmd_path)})")
        # print(f"  - 데이터 폴더: {tessdata_dir} (존재: {os.path.exists(tessdata_dir)})")
        return False

TESSERACT_CONFIGURED = setup_tesseract()

class PDFValidator:
    """PDF 검증 엔진 (v17.0)"""
    def __init__(self, template_data):
        self.template_data = template_data
        self.original_pdf_path = template_data["original_pdf_path"]
        self.rois = template_data["rois"]
        self.detectors = [cv2.AKAZE_create(), cv2.ORB_create(nfeatures=2000), cv2.SIFT_create(nfeatures=1000)]
        self.validation_results = []

        # 레이아웃 감지 시스템 추가
        self.layout_detector = DocumentLayoutDetector()

    def _preprocess_for_features(self, img):
        """앵커 특징점 검출을 위한 전용 전처리 (흑백화 및 대비 극대화)"""
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        else:
            gray = img.copy()
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 3)
        return thresh

    def _get_full_page_image(self, page, scale=2.0):
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    def _extract_roi_image(self, pdf_doc, page_num, coords, scale=2.0, grayscale=False):
        page = pdf_doc[page_num]; rect = fitz.Rect(coords); mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat, clip=rect, alpha=False)
        img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if grayscale: return cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        return cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB) if pix.n == 4 else img_array

    def _find_anchor_affine_robust(self, page_img_gray, anchor_img_gray):
        """특징점 기반의 안정적인 아핀 변환을 찾습니다."""
        anchor_processed = self._preprocess_for_features(anchor_img_gray)
        page_processed = self._preprocess_for_features(page_img_gray)

        best_affine_matrix, best_match_count = None, 0
        for detector in self.detectors:
            try:
                kp_anchor, des_anchor = detector.detectAndCompute(anchor_processed, None)
                kp_page, des_page = detector.detectAndCompute(page_processed, None)
                if des_anchor is None or des_page is None or len(des_anchor) < 4: continue

                matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
                matches = matcher.knnMatch(des_anchor, des_page, k=2)

                good_matches = []
                for pair in matches:
                    if len(pair) == 2:
                        m, n = pair
                        if m.distance < 0.75 * n.distance:
                            good_matches.append(m)

                if len(good_matches) >= 10:
                    src_pts = np.float32([kp_anchor[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                    dst_pts = np.float32([kp_page[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

                    # 아핀 변환 계산
                    affine_matrix, mask = cv2.estimateAffine2D(src_pts, dst_pts, method=cv2.RANSAC, ransacReprojThreshold=5.0)

                    if affine_matrix is not None:
                        inlier_count = np.sum(mask)
                        if inlier_count > best_match_count:
                            best_affine_matrix, best_match_count = affine_matrix, inlier_count
            except cv2.error:
                continue
        return best_affine_matrix

    def _find_anchor_template_matching(self, page_img_gray, anchor_img_gray):
        result = cv2.matchTemplate(page_img_gray, anchor_img_gray, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val > 0.55: # 임계값 하향 조정 (0.6 -> 0.55)
            return max_loc

    def _enhanced_handwriting_ocr(self, image):
        """손글씨 특화 OCR: 다양한 전처리 + 다중 시도"""
        import cv2
        import numpy as np
        import pytesseract
        import re

        results = []

        # 1. 기본 OCR (기존 방식)
        try:
            raw_text = pytesseract.image_to_string(image, lang='kor+eng')
            clean_text = re.sub(r'[\s\W_]+', '', raw_text)
            results.append({
                'method': '기본',
                'raw_text': raw_text,
                'clean_text': clean_text
            })
        except Exception as e:
            results.append({'method': '기본', 'raw_text': '', 'clean_text': '', 'error': str(e)})

        # 2. 손글씨용 전처리 1: 대비 강화 + 이진화
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image

            # 대비 강화
            clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(4,4))
            enhanced = clahe.apply(gray)

            # 적응적 이진화
            binary = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

            # 모포로지 연산으로 노이즈 제거
            kernel = np.ones((2,2), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

            raw_text = pytesseract.image_to_string(cleaned, lang='kor+eng')
            clean_text = re.sub(r'[\s\W_]+', '', raw_text)
            results.append({
                'method': '대비강화',
                'raw_text': raw_text,
                'clean_text': clean_text
            })
        except Exception as e:
            results.append({'method': '대비강화', 'raw_text': '', 'clean_text': '', 'error': str(e)})

        # 3. 손글씨용 전처리 2: 팬팔링 + 고해상도 변환
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image

            # 3배 확대
            height, width = gray.shape
            upscaled = cv2.resize(gray, (width*3, height*3), interpolation=cv2.INTER_CUBIC)

            # 가우시안 블러로 노이즈 제거
            blurred = cv2.GaussianBlur(upscaled, (3, 3), 0)

            # 오츠 이진화
            _, otsu_binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # 닫힌 모포로지
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            final = cv2.morphologyEx(otsu_binary, cv2.MORPH_CLOSE, kernel)

            raw_text = pytesseract.image_to_string(final, lang='kor+eng')
            clean_text = re.sub(r'[\s\W_]+', '', raw_text)
            results.append({
                'method': '고해상도',
                'raw_text': raw_text,
                'clean_text': clean_text
            })
        except Exception as e:
            results.append({'method': '고해상도', 'raw_text': '', 'clean_text': '', 'error': str(e)})

        # 4. 손글씨용 전처리 3: 비노매틱 필터
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image

            # 비선형 필터링
            bilat = cv2.bilateralFilter(gray, 9, 75, 75)

            # 니벤 또는 브랙-팔 이진화
            _, binary = cv2.threshold(bilat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # 열기 연산으로 끊어진 선분 연결
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

            raw_text = pytesseract.image_to_string(opened, lang='kor+eng')
            clean_text = re.sub(r'[\s\W_]+', '', raw_text)
            results.append({
                'method': '비노매틱',
                'raw_text': raw_text,
                'clean_text': clean_text
            })
        except Exception as e:
            results.append({'method': '비노매틱', 'raw_text': '', 'clean_text': '', 'error': str(e)})

        # 5. 손글씨용 PSM 모드 시도
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image

            # PSM 6: 단일 균일 텍스트 블록
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789가-히ㄱ-ㅣㆍ-ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
            raw_text = pytesseract.image_to_string(gray, lang='kor+eng', config=custom_config)
            clean_text = re.sub(r'[\s\W_]+', '', raw_text)
            results.append({
                'method': 'PSM6+문자제한',
                'raw_text': raw_text,
                'clean_text': clean_text
            })
        except Exception as e:
            results.append({'method': 'PSM6+문자제한', 'raw_text': '', 'clean_text': '', 'error': str(e)})

        # 6. 손글씨용 PSM 8 모드
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image

            # 4배 확대 + 가우시안 블러
            height, width = gray.shape
            upscaled = cv2.resize(gray, (width*4, height*4), interpolation=cv2.INTER_CUBIC)
            blurred = cv2.GaussianBlur(upscaled, (5, 5), 0)

            # PSM 8: 단일 단어
            custom_config = r'--oem 3 --psm 8'
            raw_text = pytesseract.image_to_string(blurred, lang='kor+eng', config=custom_config)
            clean_text = re.sub(r'[\s\W_]+', '', raw_text)
            results.append({
                'method': 'PSM8+4배확대',
                'raw_text': raw_text,
                'clean_text': clean_text
            })
        except Exception as e:
            results.append({'method': 'PSM8+4배확대', 'raw_text': '', 'clean_text': '', 'error': str(e)})

        # 7. 손글씨용 극단 전처리: 엣지 강화 + 비니어 필터
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image

            # 6배 확대 (극대 해상도)
            height, width = gray.shape
            mega_upscaled = cv2.resize(gray, (width*6, height*6), interpolation=cv2.INTER_LANCZOS4)

            # 비니어 필터로 노이즈 제거 후 엣지 보존
            bilateral = cv2.bilateralFilter(mega_upscaled, 15, 80, 80)

            # 엣지 강화 커널
            edge_kernel = np.array([[-1,-1,-1], [-1,8,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(bilateral, -1, edge_kernel)

            # 오츠 + 모포로지 조합
            _, thresh = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            final = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

            # PSM 6 + 문자 제한
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789가-히ㄱ-ㅣ쎍-ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
            raw_text = pytesseract.image_to_string(final, lang='kor+eng', config=custom_config)
            clean_text = re.sub(r'[\s\W_]+', '', raw_text)
            results.append({
                'method': '극대강화',
                'raw_text': raw_text,
                'clean_text': clean_text
            })
        except Exception as e:
            results.append({'method': '극대강화', 'raw_text': '', 'clean_text': '', 'error': str(e)})

        # 결과 로깅
        print(f"[손글씨 OCR] {len(results)}개 방법 시도 결과:")
        for r in results:
            char_count = len(r['clean_text'])
            error_msg = f" (오류: {r.get('error', '')})" if 'error' in r else ""
            print(f"   {r['method']}: {char_count}자{error_msg}")

        return results

    def _apply_layout_correction(self, coords, layout_offset):
        """레이아웃 오프셋을 ROI 좌표에 적용"""
        if not layout_offset:
            return coords

        offset_x = layout_offset.get("offset_x", 0)
        offset_y = layout_offset.get("offset_y", 0)
        scale_x = layout_offset.get("scale_x", 1.0)
        scale_y = layout_offset.get("scale_y", 1.0)

        # 스케일 적용 후 오프셋 적용
        corrected_coords = [
            coords[0] * scale_x + offset_x,
            coords[1] * scale_y + offset_y,
            coords[2] * scale_x + offset_x,
            coords[3] * scale_y + offset_y
        ]

        print(f"[레이아웃 보정] 원본좌표: {coords} → 보정좌표: {corrected_coords}")
        return corrected_coords

    def _validate_single_roi(self, original_doc, filled_doc, field_name, roi_info):
        print(f"DEBUG: Validating '{field_name}' with roi_info: {roi_info}")  # 디버깅 로그 추가
        page_num = roi_info.get("page", 0); coords = roi_info.get("coords")
        method = roi_info.get("method", "ocr"); threshold = roi_info.get("threshold", 500)
        anchor_coords = roi_info.get("anchor_coords")
        result = {"field_name": field_name, "page": page_num, "coords": coords, "status": "OK", "message": ""}
        if not coords: result["status"] = "ERROR"; result["message"] = "ROI 좌표 없음"; return result

        try:
            render_scale = 2.0
            original_roi_img = self._extract_roi_image(original_doc, page_num, coords, render_scale)
            if original_roi_img.size == 0: result["status"] = "ERROR"; result["message"] = "빈 원본 ROI"; return result

            # 1단계: 레이아웃 오프셋 감지 (전체 페이지 기반)
            print(f"[{field_name}] 1단계: 레이아웃 오프셋 감지 시작")
            original_page_img = self._get_full_page_image(original_doc[page_num], render_scale)
            filled_page_img = self._get_full_page_image(filled_doc[page_num], render_scale)

            layout_offset = self.layout_detector.detect_layout_offset(original_page_img, filled_page_img)

            # 안전장치: 유의미한 차이가 있을 때만 보정 적용
            offset_threshold = 5  # 5픽셀 이상 이동
            scale_threshold = 0.02  # 2% 이상 크기 변화

            if abs(layout_offset['offset_x']) > offset_threshold or \
               abs(layout_offset['offset_y']) > offset_threshold or \
               abs(layout_offset['scale_x'] - 1.0) > scale_threshold or \
               abs(layout_offset['scale_y'] - 1.0) > scale_threshold:

                result['message'] += f"[레이아웃보정:오프셋({layout_offset['offset_x']:.1f},{layout_offset['offset_y']:.1f})] "
                layout_corrected_coords = self._apply_layout_correction(coords, layout_offset)
            else:
                result['message'] += "[레이아웃차이없음] "
                layout_corrected_coords = coords # 원본 좌표 사용

            # 2단계: 앵커 기반 미세 조정 (선택적)
            new_coords = layout_corrected_coords
            if anchor_coords:
                print(f"[{field_name}] 2단계: 앵커 기반 미세조정 시작")
                anchor_img = self._extract_roi_image(original_doc, page_num, anchor_coords, render_scale, grayscale=True)

                if anchor_img.size == 0:
                    result["message"] += "[앵커이미지오류→레이아웃보정만사용] "
                    print(f"[{field_name}] 앵커 이미지 추출 실패, 레이아웃 보정 결과만 사용")
                else:
                    # 앵커도 레이아웃 보정 적용
                    layout_corrected_anchor_coords = self._apply_layout_correction(anchor_coords, layout_offset)

                    # 1순위: 템플릿 매칭 시도
                    top_left = self._find_anchor_template_matching(filled_page_img, anchor_img)
                    if top_left:
                        scale_factor = render_scale
                        anchor_w = (layout_corrected_anchor_coords[2] - layout_corrected_anchor_coords[0]) * scale_factor
                        anchor_h = (layout_corrected_anchor_coords[3] - layout_corrected_anchor_coords[1]) * scale_factor

                        found_center_x = top_left[0] + anchor_w / 2
                        found_center_y = top_left[1] + anchor_h / 2

                        orig_anchor_center_x = (layout_corrected_anchor_coords[0] + layout_corrected_anchor_coords[2]) * scale_factor / 2
                        orig_anchor_center_y = (layout_corrected_anchor_coords[1] + layout_corrected_anchor_coords[3]) * scale_factor / 2

                        dx = (found_center_x - orig_anchor_center_x) / scale_factor
                        dy = (found_center_y - orig_anchor_center_y) / scale_factor

                        if abs(dx) > 4.0 or abs(dy) > 4.0: # 임계값 상향 (2.0 -> 4.0)
                            new_coords = [layout_corrected_coords[0] + dx, layout_corrected_coords[1] + dy,
                                        layout_corrected_coords[2] + dx, layout_corrected_coords[3] + dy]
                            result['message'] += "[T미세조정] "
                            print(f"[{field_name}] 템플릿 매칭 미세조정 성공 (이동량: dx={dx:.2f}, dy={dy:.2f})")
                        else:
                            result['message'] += "[T변화미미] "
                            print(f"[{field_name}] 템플릿 매칭 변화량 미미 (dx={dx:.2f}, dy={dy:.2f}), 보정 무시")
                    else:
                        # 2순위: 아핀 변환 시도
                        affine_matrix = self._find_anchor_affine_robust(filled_page_img, anchor_img)
                        if affine_matrix is not None:
                            roi_pts = np.float32([[layout_corrected_coords[0], layout_corrected_coords[1]],
                                               [layout_corrected_coords[2], layout_corrected_coords[1]],
                                               [layout_corrected_coords[2], layout_corrected_coords[3]],
                                               [layout_corrected_coords[0], layout_corrected_coords[3]]]).reshape(-1,1,2)

                            # 아핀 변환 적용
                            transformed_pts = cv2.transform(roi_pts * render_scale, affine_matrix)

                            if transformed_pts is not None:
                                x_coords, y_coords = transformed_pts[:, 0, 0], transformed_pts[:, 0, 1]
                                anchor_corrected_coords = [c / render_scale for c in [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]]

                                page_rect = filled_doc[page_num].rect
                                if anchor_corrected_coords[0] > page_rect.width or anchor_corrected_coords[1] > page_rect.height:
                                    result['message'] += "[A결과오류] "
                                    print(f"[{field_name}] 아핀 변환 결과가 페이지를 벗어남, 보정 무시")
                                else:
                                    coord_diff = np.sum(np.abs(np.array(anchor_corrected_coords) - np.array(layout_corrected_coords)))
                                    if coord_diff > 3.0:
                                        new_coords = anchor_corrected_coords
                                        result['message'] += "[A미세조정] "
                                        print(f"[{field_name}] 아핀 변환 미세조정 성공 (변화량: {coord_diff:.2f})")
                                    else:
                                        result['message'] += "[A변화미미] "
                                        print(f"[{field_name}] 아핀 변환 변화량 미미 ({coord_diff:.2f}), 보정 무시")
                        else:
                            result['message'] += "[앵커실패→레이아웃보정만사용] "
                            print(f"[{field_name}] 앵커 매칭 실패, 레이아웃 보정 결과만 사용")
            else:
                result['message'] += "[앵커없음→레이아웃보정만사용] "
                print(f"[{field_name}] 앵커 정보 없음, 레이아웃 보정만 사용")

            # 3단계: 보정된 좌표로 ROI 검증 수행
            print(f"[{field_name}] 3단계: ROI 검증 수행 (최종좌표: {new_coords})")
            page_bounds = filled_doc[page_num].rect
            print(f"[{field_name}] 페이지 크기: {page_bounds}, 검증할 좌표: {new_coords}")
            filled_roi = self._extract_roi_image(filled_doc, page_num, new_coords, render_scale)
            if filled_roi.size == 0: result["status"] = "ERROR"; result["message"] += "채워진 ROI 없음"; return result

            h, w, _ = original_roi_img.shape
            filled_roi_resized = cv2.resize(filled_roi, (w, h))
            original_gray = cv2.cvtColor(original_roi_img, cv2.COLOR_RGB2GRAY)
            filled_gray = cv2.cvtColor(filled_roi_resized, cv2.COLOR_RGB2GRAY)

            # if ssim(original_gray, filled_gray, data_range=255) > 0.95:
            #     result["status"] = "DEFICIENT"
            #     result["message"] += "내용 없음(SSIM)"
            #     return result

            if method == "contour":
                # 블러 처리를 비활성화하여 미세한 선도 감지하도록 함
                # blurred_original = cv2.GaussianBlur(original_gray, (5, 5), 0)
                # blurred_filled = cv2.GaussianBlur(filled_gray, (5, 5), 0)
                diff = cv2.absdiff(original_gray, filled_gray)
                
                _, binary = cv2.threshold(diff, 20, 255, cv2.THRESH_BINARY)

                contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # --- 상세 디버깅 로그 추가 ---
                if not contours:
                    print(f"  [{field_name}] Contour 검출 결과: 컨투어 없음")
                    significant_contours = []
                else:
                    all_areas = [cv2.contourArea(c) for c in contours]
                    print(f"  [{field_name}] Contour 검출 결과: 총 {len(all_areas)}개, 면적리스트: {[f'{a:.0f}' for a in all_areas]}")
                    print(f"  [{field_name}] 사용자 설정 임계값: {threshold}")
                    significant_contours = [c for c in contours if cv2.contourArea(c) > threshold]
                    print(f"  [{field_name}] 임계값 통과 컨투어: {len(significant_contours)}개")
                # --- 디버깅 로그 끝 ---

                if significant_contours:
                    # 의미있는 컨투어가 존재하면 통과
                    result["status"] = "OK"
                    result["message"] += f"Contour통과(유효 컨투어 {len(significant_contours)}개 발견)"
                else:
                    # 그렇지 않으면 미흡
                    result["status"] = "DEFICIENT"
                    result["message"] += f"Contour미흡(유효 컨투어 없음)"
            elif method == "ocr":
                ocr_img = cv2.adaptiveThreshold(
                    cv2.cvtColor(filled_roi, cv2.COLOR_RGB2GRAY),
                    255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY,
                    11,
                    2
                )
                raw_text = pytesseract.image_to_string(ocr_img, lang='kor+eng')
                clean_text = re.sub(r'[\s\W_]+', '', raw_text)
                if len(clean_text) < threshold:
                    result["status"] = "DEFICIENT"
                    result["message"] += f"OCR미흡({len(clean_text)}자)"
                else:
                    result["message"] += f"OCR통과: '{clean_text[:20]}'"

        except Exception as e:
            result["status"] = "ERROR"
            result["message"] = f"검증 오류: {str(e)}"

        # 최종적으로 사용된 좌표를 결과에 반영
        result["coords"] = new_coords
        return result

    def validate_pdf(self, filled_pdf_path, progress_callback=None):
        self.validation_results = []
        original_doc = fitz.open(self.original_pdf_path)
        filled_doc = fitz.open(filled_pdf_path)

        for i, (field_name, roi_info) in enumerate(self.rois.items()):
            if progress_callback:
                progress_callback(f"'{field_name}' 검증 중...", i, len(self.rois))
            result = self._validate_single_roi(original_doc, filled_doc, field_name, roi_info)
            self.validation_results.append(result)

        original_doc.close()
        filled_doc.close()
        return self.validation_results

    def create_annotated_pdf(self, filled_pdf_path, output_path):
        pdf_doc = fitz.open(filled_pdf_path)

        for result in self.validation_results:
            if result["status"] != "OK":
                page = pdf_doc[result["page"]]
                rect = fitz.Rect(result["coords"])
                color = (1, 1, 0) if result["status"] == "ERROR" else (1, 0.8, 0)
                highlight = page.add_highlight_annot(rect)
                highlight.set_colors({"stroke": color})
                highlight.update()

        pdf_doc.save(output_path, garbage=4, deflate=True, clean=True)
        pdf_doc.close()

class PDFValidatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("2단계: ROI 검증 도구 (v18.0 - 레이아웃 감지 통합)")

        # 화면 크기에 맞춰 창 크기 설정
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = min(1600, int(screen_width * 0.9))  # 화면의 90% 또는 최대 1600px
        window_height = min(1000, int(screen_height * 0.9))  # 화면의 90% 또는 최대 1000px

        # 창을 화면 중앙에 위치
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # 창 크기 조절 가능하도록 설정
        self.root.minsize(1200, 800)

        self.templates = {}
        self.selected_template = None
        self.target_path = ""
        self.validator = None

        self.original_pdf_doc = None
        self.annotated_pdf_doc = None
        self.current_page_num = 0
        self.total_pages = 0

        self.left_photo = None
        self.right_photo = None

        self.setup_ui()
        self.load_templates()

    def check_tesseract(self):
        if not TESSERACT_CONFIGURED:
            self.log("🔥 경고: Tesseract OCR 엔진을 찾을 수 없습니다.")
            return False
        self.log(f"✅ Tesseract OCR 엔진 사용: {pytesseract.pytesseract.tesseract_cmd}")
        return True

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Grid 레이아웃으로 변경
        main_frame.rowconfigure(2, weight=1) # 뷰어 프레임이 세로 공간을 모두 차지하도록 설정
        main_frame.columnconfigure(0, weight=1)

        control_frame = ttk.LabelFrame(main_frame, text="검증 설정", padding="10")
        control_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        self.mode_var = tk.StringVar(value="폴더")
        ttk.Label(control_frame, text="검사 방식 선택:").grid(row=0, column=0, sticky=tk.W, pady=5)
        mode_frame = ttk.Frame(control_frame)
        mode_frame.grid(row=0, column=1, columnspan=2, sticky=tk.W)
        ttk.Radiobutton(mode_frame, text="파일 기준 검사", variable=self.mode_var, value="파일", command=self.switch_mode).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="폴더 기준 검사", variable=self.mode_var, value="폴더", command=self.switch_mode).pack(side=tk.LEFT, padx=5)

        ttk.Label(control_frame, text="템플릿 선택:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.template_var = tk.StringVar()
        self.template_combo = ttk.Combobox(control_frame, textvariable=self.template_var, state="readonly", width=40)
        self.template_combo.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        self.template_combo.bind('<<ComboboxSelected>>', self.on_template_selected)
        ttk.Button(control_frame, text="새로고침", command=self.load_templates).grid(row=1, column=2, padx=5, pady=5)

        self.target_label = ttk.Label(control_frame, text="검사 대상 폴더:")
        self.target_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(control_frame, textvariable=self.path_var, state="readonly", width=40)
        self.path_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        self.browse_btn = ttk.Button(control_frame, text="폴더 찾기", command=self.browse_target)
        self.browse_btn.grid(row=2, column=2, padx=5, pady=5)
        control_frame.columnconfigure(1, weight=1)

        self.validate_btn = ttk.Button(main_frame, text="검사 실행", command=self.run_validation, state=tk.DISABLED)
        self.validate_btn.grid(row=1, column=0, pady=10)

        self.viewer_frame = ttk.Frame(main_frame)
        self.viewer_frame.grid(row=2, column=0, sticky="nsew") # 뷰어 프레임이 남는 공간을 모두 차지
        self.viewer_frame.rowconfigure(0, weight=1)
        self.viewer_frame.columnconfigure(0, weight=1)

        viewer_pane = ttk.PanedWindow(self.viewer_frame, orient=tk.HORIZONTAL)
        viewer_pane.grid(row=0, column=0, sticky="nsew")

        left_viewer_frame = ttk.LabelFrame(viewer_pane, text="원본 템플릿", padding="5")
        viewer_pane.add(left_viewer_frame, weight=1)
        left_viewer_frame.rowconfigure(0, weight=1)
        left_viewer_frame.columnconfigure(0, weight=1)

        self.left_canvas = tk.Canvas(left_viewer_frame, bg="white")
        self.left_canvas.grid(row=0, column=0, sticky="nsew")

        left_v_scroll = ttk.Scrollbar(left_viewer_frame, orient="vertical", command=self.left_canvas.yview)
        left_v_scroll.grid(row=0, column=1, sticky="ns")
        left_h_scroll = ttk.Scrollbar(left_viewer_frame, orient="horizontal", command=self.left_canvas.xview)
        left_h_scroll.grid(row=1, column=0, sticky="ew")
        self.left_canvas.configure(yscrollcommand=left_v_scroll.set, xscrollcommand=left_h_scroll.set)

        right_viewer_frame = ttk.LabelFrame(viewer_pane, text="검증된 문서 (주석)", padding="5")
        viewer_pane.add(right_viewer_frame, weight=1)
        right_viewer_frame.rowconfigure(0, weight=1)
        right_viewer_frame.columnconfigure(0, weight=1)

        self.right_canvas = tk.Canvas(right_viewer_frame, bg="white")
        self.right_canvas.grid(row=0, column=0, sticky="nsew")

        right_v_scroll = ttk.Scrollbar(right_viewer_frame, orient="vertical", command=self.right_canvas.yview)
        right_v_scroll.grid(row=0, column=1, sticky="ns")
        right_h_scroll = ttk.Scrollbar(right_viewer_frame, orient="horizontal", command=self.right_canvas.xview)
        right_h_scroll.grid(row=1, column=0, sticky="ew")
        self.right_canvas.configure(yscrollcommand=right_v_scroll.set, xscrollcommand=right_h_scroll.set)

        nav_frame = ttk.Frame(self.viewer_frame)
        nav_frame.grid(row=1, column=0, sticky="ew", pady=5)
        self.prev_page_btn = ttk.Button(nav_frame, text="◀ 이전", command=self.prev_page, state=tk.DISABLED)
        self.prev_page_btn.pack(side=tk.LEFT)
        self.page_label = ttk.Label(nav_frame, text="페이지: 0/0")
        self.page_label.pack(side=tk.LEFT, padx=10)
        self.next_page_btn = ttk.Button(nav_frame, text="다음 ▶", command=self.next_page, state=tk.DISABLED)
        self.next_page_btn.pack(side=tk.LEFT)
        self.save_file_btn = ttk.Button(nav_frame, text="결과 저장", command=self.save_single_file_result, state=tk.DISABLED)
        self.save_file_btn.pack(side=tk.RIGHT, padx=10)

        log_frame = ttk.LabelFrame(main_frame, text="진행 상황 로그", padding="5")
        log_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=5)
        main_frame.rowconfigure(3, weight=0) # 로그 프레임은 추가 공간을 차지하지 않음

        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.progress_bar = ttk.Progressbar(log_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(3, 0))

        self.switch_mode()

    def update_validate_button_state(self):
        state = tk.NORMAL if self.selected_template and self.target_path else tk.DISABLED
        self.validate_btn.config(state=state)

    def switch_mode(self):
        mode = self.mode_var.get()
        self.path_var.set("")
        self.target_path = ""

        if mode == "파일":
            self.target_label.config(text="검사 대상 파일:")
            self.browse_btn.config(text="파일 찾기")
            self.viewer_frame.grid(row=2, column=0, sticky="nsew") # 뷰어 다시 표시
            self.save_file_btn.config(state=tk.DISABLED)
        else:
            self.target_label.config(text="검사 대상 폴더:")
            self.browse_btn.config(text="폴더 찾기")
            self.viewer_frame.grid_remove() # 뷰어 숨기기

        self.update_validate_button_state()

    def browse_target(self):
        mode = self.mode_var.get()

        if mode == "파일":
            path = filedialog.askopenfilename(title="PDF 파일 선택", filetypes=[("PDF files", "*.pdf")])
        else:
            path = filedialog.askdirectory(title="PDF 폴더 선택")

        if path:
            self.target_path = path
            self.path_var.set(path)
            self.log(f"대상 선택: {path}")
            self.update_validate_button_state()

    def run_validation(self):
        if not self.check_tesseract():
            messagebox.showerror("OCR 엔진 오류", "Tesseract OCR 엔진을 찾을 수 없습니다. 로그를 확인하세요.")
            return

        if self.mode_var.get() == "파일":
            self.run_file_validation()
        else:
            self.run_folder_validation()

    def log(self, message):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def log_results(self, results):
        for result in results:
            icon = "✅" if result['status'] == 'OK' else "❌"
            self.log(f"  {icon} [{result['field_name']}]: {result['message']}")

    def run_file_validation(self):
        self.validate_btn.config(state=tk.DISABLED)
        self.save_file_btn.config(state=tk.DISABLED)
        self.log_text.delete('1.0', tk.END)
        self.log(f"파일 검증 시작: {os.path.basename(self.target_path)}")

        self.validator = PDFValidator(self.selected_template)
        self.progress_bar['maximum'] = len(self.validator.rois)

        def progress_update(msg, current, total):
            self.log(msg)
            if current >= 0:
                self.progress_bar['value'] = current + 1

        try:
            results = self.validator.validate_pdf(self.target_path, progress_update)
            self.log("="*50 + "\n상세 검증 결과:")
            self.log_results(results)

            deficient = sum(1 for r in results if r['status'] != 'OK')
            temp_dir = "output"
            os.makedirs(temp_dir, exist_ok=True)
            temp_annot_path = os.path.join(temp_dir, f"temp_review_{int(time.time())}.pdf")
            self.validator.create_annotated_pdf(self.target_path, temp_annot_path)

            self.log("="*50)
            self.log(f"요약: {"❌ 검증 미흡" if deficient > 0 else "✅ 검증 통과"} ({deficient}개 항목 미흡)")
            self.log("="*50)

            self.load_docs_for_viewer(self.selected_template['original_pdf_path'], temp_annot_path)

        except Exception as e:
            self.log(f"🔥 치명적 오류 발생: {e}")
            messagebox.showerror("오류", f"검증 중 오류:\n{e}")
        finally:
            self.validate_btn.config(state=tk.NORMAL)
            self.save_file_btn.config(state=tk.NORMAL)

    def run_folder_validation(self):
        self.validate_btn.config(state=tk.DISABLED)
        template_name = self.template_var.get()

        pdf_files = [f for f in os.listdir(self.target_path) if f.lower().endswith('.pdf')]
        if not pdf_files:
            messagebox.showinfo("완료", "폴더에 PDF 파일이 없습니다.")
            self.validate_btn.config(state=tk.NORMAL)
            return

        output_dir = os.path.join("output", re.sub(r'[\\/*?:"<>|]', "", template_name))
        os.makedirs(output_dir, exist_ok=True)

        self.log_text.delete('1.0', tk.END)
        self.log(f"'{template_name}' 템플릿으로 일괄 검증을 시작합니다. (총 {len(pdf_files)}개)")
        self.progress_bar['maximum'] = len(pdf_files)

        validator = PDFValidator(self.selected_template)
        success_count, fail_count = 0, 0

        for i, filename in enumerate(pdf_files):
            filepath = os.path.join(self.target_path, filename)
            self.log(f"[{i+1}/{len(pdf_files)}] '{filename}' 검증 중...")
            self.progress_bar['value'] = i + 1

            try:
                results = validator.validate_pdf(filepath)
                deficient_count = sum(1 for r in results if r['status'] != 'OK')

                if deficient_count > 0:
                    fail_count += 1
                    self.log(f"  -> ❌ 미흡 ({deficient_count}개 항목). 주석 PDF를 저장합니다.")
                    out_name = f"review_{os.path.splitext(filename)[0]}.pdf"
                    out_path = os.path.join(output_dir, out_name)
                    validator.create_annotated_pdf(filepath, out_path)
                else:
                    success_count += 1
                    self.log("  -> ✅ 통과.")

            except Exception as e:
                fail_count += 1
                self.log(f"  -> 🔥 오류 발생: {e}")

        summary = f"검증 완료! (성공: {success_count}, 실패/오류: {fail_count})"
        self.log("="*50)
        self.log(summary)
        self.log(f"미흡 파일은 '{os.path.abspath(output_dir)}' 폴더에 저장되었습니다.")
        messagebox.showinfo("완료", summary)
        self.validate_btn.config(state=tk.NORMAL)

    def save_single_file_result(self):
        if not self.validator or not self.target_path:
            messagebox.showwarning("경고", "먼저 파일 검사를 실행해야 합니다.")
            return

        template_name = self.template_var.get()
        output_dir = os.path.join("output", re.sub(r'[\\/*?:"<>|]', "", template_name))
        os.makedirs(output_dir, exist_ok=True)

        base_name = os.path.splitext(os.path.basename(self.target_path))[0]
        default_filename = f"review_{base_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        save_path = filedialog.asksaveasfilename(
            title="주석 PDF 결과 저장",
            initialdir=output_dir,
            initialfile=default_filename,
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")]
        )

        if save_path:
            try:
                self.validator.create_annotated_pdf(self.target_path, save_path)
                messagebox.showinfo("성공", f"결과 파일이 저장되었습니다:\n{save_path}")
                self.log(f"결과 파일 저장됨: {save_path}")
            except Exception as e:
                messagebox.showerror("오류", f"파일 저장 중 오류 발생:\n{e}")
                self.log(f"🔥 파일 저장 오류: {e}")

    def load_docs_for_viewer(self, original_path, annotated_path):
        try:
            if self.original_pdf_doc:
                self.original_pdf_doc.close()
            if self.annotated_pdf_doc:
                self.annotated_pdf_doc.close()

            self.original_pdf_doc = fitz.open(original_path)
            self.annotated_pdf_doc = fitz.open(annotated_path)
            self.total_pages = self.original_pdf_doc.page_count
            self.current_page_num = 0
            self.root.after(10, self.display_dual_pages)
        except Exception as e:
            self.log(f"PDF 뷰어 로딩 실패: {e}")

    def display_dual_pages(self):
        if not self.original_pdf_doc or not self.root.winfo_viewable():
            return

        # 좌역 캔버스 크기 업데이트 대기
        self.root.update_idletasks()

        # 원본 또는 변경 난 원본을 재사용 안하고 새로 찾기 위해 바로 로딩
        page_orig = self.original_pdf_doc[self.current_page_num]
        img_orig = self.render_page_to_image(page_orig, self.left_canvas)
        if img_orig:
            self.left_photo = img_orig
            self.left_canvas.delete("all")

            # 이미지를 중앙에 배치
            canvas_width = self.left_canvas.winfo_width()
            canvas_height = self.left_canvas.winfo_height()
            img_width = img_orig.width()
            img_height = img_orig.height()

            x = max(0, (canvas_width - img_width) // 2)
            y = max(0, (canvas_height - img_height) // 2)

            self.left_canvas.create_image(x, y, anchor=tk.NW, image=self.left_photo)

            # 스크롤 영역 설정
            self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))

            # ROI 드로잉
            self.draw_rois_on_viewer(self.left_canvas, page_orig, x, y)

        # 우측 캔버스 (검증된 문서)
        if self.annotated_pdf_doc and self.current_page_num < self.annotated_pdf_doc.page_count:
            page_annot = self.annotated_pdf_doc[self.current_page_num]
            img_annot = self.render_page_to_image(page_annot, self.right_canvas)
            if img_annot:
                self.right_photo = img_annot
                self.right_canvas.delete("all")

                # 이미지를 중앙에 배치
                canvas_width = self.right_canvas.winfo_width()
                canvas_height = self.right_canvas.winfo_height()
                img_width = img_annot.width()
                img_height = img_annot.height()

                x = max(0, (canvas_width - img_width) // 2)
                y = max(0, (canvas_height - img_height) // 2)

                self.right_canvas.create_image(x, y, anchor=tk.NW, image=self.right_photo)

                # 스크롤 영역 설정
                self.right_canvas.configure(scrollregion=self.right_canvas.bbox("all"))

        self.update_navigation_buttons()

    def draw_rois_on_viewer(self, canvas, page, offset_x=0, offset_y=0):
        if not self.selected_template:
            return

        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        if canvas_width < 50 or canvas_height < 50:
            return

        # 줄 배율 계산 (렌더링과 동일)
        page_rect = page.rect
        zoom_x = canvas_width / page_rect.width
        zoom_y = canvas_height / page_rect.height
        zoom = min(zoom_x, zoom_y) * 1.2

        max_zoom = 4.0
        zoom = min(zoom, max_zoom)

        mat = fitz.Matrix(zoom, zoom)

        for field_name, roi_info in self.selected_template['rois'].items():
            if roi_info['page'] == self.current_page_num:
                rect = fitz.Rect(roi_info['coords']) * mat
                color = "blue" if roi_info['method'] == 'ocr' else 'red'

                # 오프셋 적용
                x0, y0, x1, y1 = rect.x0 + offset_x, rect.y0 + offset_y, rect.x1 + offset_x, rect.y1 + offset_y

                canvas.create_rectangle(x0, y0, x1, y1, outline=color, width=2, dash=(4, 4))
                canvas.create_text(x0, y0 - 5, text=field_name, fill=color, anchor="sw")

    def render_page_to_image(self, page, canvas):
        """PDF 페이지를 캔버스에 맞는 이미지로 렌더링 (고해상도)"""
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if w < 50 or h < 50:  # 최소 크기 보장
            return None

        # 더 큰 화면에 맞춰 고해상도 렌더링
        page_rect = page.rect
        zoom_x = w / page_rect.width
        zoom_y = h / page_rect.height
        zoom = min(zoom_x, zoom_y) * 1.2  # 20% 더 크게 렌더링

        # 최대 해상도 제한 (성능 고려)
        max_zoom = 4.0
        zoom = min(zoom, max_zoom)

        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        try:
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            return ImageTk.PhotoImage(image=img)
        except Exception as e:
            print(f"이미지 렌더링 오류: {e}")
            return None

    def update_navigation_buttons(self):
        self.page_label.config(text=f"페이지: {self.current_page_num + 1}/{self.total_pages}")
        self.prev_page_btn.config(state=tk.NORMAL if self.current_page_num > 0 else tk.DISABLED)
        self.next_page_btn.config(state=tk.NORMAL if self.total_pages > 0 and self.current_page_num < self.total_pages - 1 else tk.DISABLED)

    def prev_page(self):
        if self.current_page_num > 0:
            self.current_page_num -= 1
            self.display_dual_pages()

    def next_page(self):
        if self.current_page_num < self.total_pages - 1:
            self.current_page_num += 1
            self.display_dual_pages()

    def load_templates(self):
        try:
            if os.path.exists("templates.json"):
                with open('templates.json', 'r', encoding='utf-8') as f:
                    self.templates = json.load(f)
                self.template_combo['values'] = list(self.templates.keys())
                if self.templates:
                    self.template_combo.current(0)
                    self.on_template_selected()
            else:
                self.templates = {}
                self.template_combo['values'] = []
        except Exception as e:
            self.log(f"템플릿 로드 오류: {str(e)}")

    def on_template_selected(self, event=None):
        template_name = self.template_var.get()
        if template_name in self.templates:
            self.selected_template = self.templates[template_name]
            self.update_validate_button_state()

def main():
    root = tk.Tk()
    app = PDFValidatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
