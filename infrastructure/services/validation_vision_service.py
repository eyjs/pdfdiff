import fitz
import cv2
import numpy as np
import pytesseract
import re
from skimage.metrics import structural_similarity as ssim


# 이 클래스는 레거시 pdf_validator_gui.py에 있던 DocumentLayoutDetector와
# _validate_single_roi 함수의 모든 이미지 처리 로직을 포함해야 합니다.
# 아래 코드는 그 구조를 잡아놓은 것이며, 실제 로직을 채워넣어야 합니다.

class ValidationVisionService:
    def __init__(self):
        # Tesseract 설정 등 필요한 초기화를 수행합니다.
        # 예: self.setup_tesseract()
        self.layout_detector = self._DocumentLayoutDetector()
        self.detectors = [cv2.AKAZE_create(), cv2.ORB_create(nfeatures=2000)]


    def validate_roi(self, original_doc, filled_doc, field_name, roi_info):
        # 이 메서드는 레거시 `_validate_single_roi` 함수의 로직을 그대로 가져와 구현합니다.
        # 아래는 해당 함수의 구조를 따라 재구성한 코드입니다.

        page_num = roi_info.get("page", 0)
        coords = roi_info.get("coords")
        method = roi_info.get("method", "ocr")
        threshold = roi_info.get("threshold", 3)
        anchor_coords = roi_info.get("anchor_coords")

        result = {"field_name": field_name, "page": page_num, "coords": coords, "status": "OK", "message": ""}
        if not coords:
            result["status"] = "ERROR"
            result["message"] = "ROI coordinates not found"
            return result

        try:
            render_scale = 2.0  # TODO: DPI 기반으로 변경 고려
            original_roi_img = self._extract_roi_image(original_doc, page_num, coords, render_scale)

            # 1. 레이아웃 오프셋 감지
            original_page_img = self._get_full_page_image(original_doc[page_num], render_scale)
            filled_page_img = self._get_full_page_image(filled_doc[page_num], render_scale)
            layout_offset = self.layout_detector.detect_layout_offset(original_page_img, filled_page_img)

            # 2. 1차 좌표 보정
            new_coords = self._apply_layout_correction(coords, layout_offset)

            # 3. 앵커 기반 미세 조정
            if anchor_coords:
                anchor_img = self._extract_roi_image(original_doc, page_num, anchor_coords, render_scale, grayscale=True)
                # ... (앵커 찾는 로직: _find_anchor_template_matching, _find_anchor_affine_robust)
                # ... (찾은 앵커를 기반으로 new_coords 미세 조정)
                pass # Placeholder for anchor logic

            # 4. 최종 ROI 이미지 추출 및 검증
            filled_roi = self._extract_roi_image(filled_doc, page_num, new_coords, render_scale)

            # 크기 맞춤
            h, w, _ = original_roi_img.shape
            filled_roi_resized = cv2.resize(filled_roi, (w, h))

            # 검증 로직 분기
            if method == "contour":
                # ... (Contour 검증 로직)
                result["message"] = "Contour validation logic needs to be implemented."
            elif method == "ocr":
                # ... (OCR 검증 로직)
                ocr_img = cv2.cvtColor(filled_roi_resized, cv2.COLOR_RGB2GRAY)
                raw_text = pytesseract.image_to_string(ocr_img, lang='kor+eng')
                clean_text = re.sub(r'[\s\W_]+', '', raw_text)
                if len(clean_text) < threshold:
                    result["status"] = "DEFICIENT"
                    result["message"] = f"OCR insufficient ({len(clean_text)} chars)"
                else:
                    result["message"] = f"OCR OK: '{clean_text[:20]}...'"

            result["coords"] = new_coords # 최종 사용된 좌표 업데이트

        except Exception as e:
            result["status"] = "ERROR"
            result["message"] = f"Validation error: {e}"

        return result

    # --- 아래는 _validate_single_roi가 사용하던 Helper 메서드들 ---
    # --- 이 메서드들은 레거시 pdf_validator_gui.py에서 복사해와야 합니다. ---

    def _extract_roi_image(self, pdf_doc, page_num, coords, scale=2.0, grayscale=False):
        # ... (Implementation from legacy code) ...
        page = pdf_doc[page_num]; rect = fitz.Rect(coords); mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat, clip=rect, alpha=False)
        img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if grayscale: return cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        return cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB) if pix.n == 4 else img_array

    def _get_full_page_image(self, page, scale=2.0):
        # ... (Implementation from legacy code) ...
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    def _apply_layout_correction(self, coords, layout_offset):
        # ... (Implementation from legacy code) ...
        offset_x = layout_offset.get("offset_x", 0)
        offset_y = layout_offset.get("offset_y", 0)
        scale_x = layout_offset.get("scale_x", 1.0)
        scale_y = layout_offset.get("scale_y", 1.0)
        return [
            coords[0] * scale_x + offset_x, coords[1] * scale_y + offset_y,
            coords[2] * scale_x + offset_x, coords[3] * scale_y + offset_y
        ]

    # --- Nested Class for Layout Detection ---
    class _DocumentLayoutDetector:
        def detect_layout_offset(self, original_img, scanned_img):
            # ... (Implementation from legacy code) ...
            return {"offset_x": 0, "offset_y": 0, "scale_x": 1.0, "scale_y": 1.0, "rotation": 0}

