import fitz
import cv2
import numpy as np
import re
from skimage.metrics import structural_similarity as ssim
import logging

from domain.services.ocr_service import OcrService

# 로깅 설정: 문제 발생 시 원인 파악을 용이하게 함
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ValidationVisionService:
    """
    원본 문서와 기입된 문서의 ROI를 비교하여 기입 여부를 검증하는 통합 이미지 처리 서비스.
    강력한 좌표 보정 파이프라인을 내장하여 스캔/복사로 인한 레이아웃 변형에 대응합니다.
    """
    def __init__(self, ocr_service: OcrService, config=None):
        """서비스 초기화 시, 내부에 필요한 비전 컴포넌트를 생성합니다."""
        self.config = config or {}
        self.ocr_service = ocr_service
        # 좌표 보정을 위한 내부 FeatureMatcher 초기화
        self.feature_matcher = self._FeatureMatcher()

    def validate_roi(self, original_doc, filled_doc, field_name, roi_info):
        """
        단일 ROI의 기입 여부를 검증합니다.

        파이프라인:
        1. 원본/사본의 전체 페이지 이미지 렌더링
        2. 페이지 간의 기하학적 변형을 계산하여 ROI 좌표 보정 (전역 보정 + 앵커 기반 지역 보정)
        3. 보정된 좌표를 이용해 최종 ROI 이미지 추출
        4. 지정된 방법(OCR, Contour, SSIM 등)으로 기입 여부 검증
        """
        page_num = roi_info.get("page", 0)
        coords = roi_info.get("coords")
        method = roi_info.get("method", "ocr")
        threshold = roi_info.get("threshold", 3)
        anchor_coords = roi_info.get("anchor_coords")

        result = {
            "field_name": field_name, "page": page_num, "coords": coords,
            "corrected_coords": None, "status": "OK", "message": ""
        }
        if not coords:
            result["status"] = "ERROR"
            result["message"] = "ROI coordinates not found"
            return result

        try:
            # 고해상도 렌더링 (300DPI 수준)으로 정확도 향상
            render_scale = 3.0

            # --- 1. 전체 페이지 이미지 준비 (그레이스케일로 변환하여 처리 속도 향상) ---
            original_page_img = self._get_full_page_image(original_doc[page_num], render_scale, grayscale=True)
            filled_page_img = self._get_full_page_image(filled_doc[page_num], render_scale, grayscale=True)

            # --- 2. 좌표 보정 파이프라인 실행 ---
            corrected_coords_scaled = self._correct_roi_position(
                original_page_img, filled_page_img, coords, anchor_coords, render_scale, field_name
            )

            # 최종 사용된 좌표를 원본 스케일로 변환하여 결과에 저장
            final_coords_original_scale = [c / render_scale for c in corrected_coords_scaled]
            result["corrected_coords"] = final_coords_original_scale

            # --- 3. 최종 ROI 이미지 추출 (검증을 위해 컬러 이미지 사용) ---
            original_roi_color = self._extract_roi_from_pdf(original_doc, page_num, coords, render_scale)
            filled_roi_color = self._extract_roi_from_pdf(filled_doc, page_num, final_coords_original_scale, render_scale)

            # 크기 맞춤: 원본 ROI를 보정된 좌표로 추출된 채워진 ROI의 크기에 맞게 리사이즈합니다.
            # 이렇게 하면 좌표 보정으로 인해 발생할 수 있는 미세한 크기/비율 왜곡을 원본에 동일하게 적용하여 비교 정확도를 높입니다.
            h, w, _ = filled_roi_color.shape
            original_roi_resized = cv2.resize(original_roi_color, (w, h))

            # --- 추가: 테두리 노이즈 제거를 위한 ROI 침식(Erosion) ---
            border_to_crop = 4  # 각 가장자리에서 잘라낼 픽셀 수
            if h > border_to_crop * 2 and w > border_to_crop * 2:
                original_roi_for_validation = original_roi_resized[border_to_crop:h-border_to_crop, border_to_crop:w-border_to_crop]
                filled_roi_for_validation = filled_roi_color[border_to_crop:h-border_to_crop, border_to_crop:w-border_to_crop]
            else:
                # ROI가 너무 작으면 크롭하지 않음
                original_roi_for_validation = original_roi_resized
                filled_roi_for_validation = filled_roi_color

            # --- 4. 검증 로직 분기 ---
            if method == "ocr":
                # OCR은 전체 영역을 봐야 하므로 크롭되지 않은 원본 이미지를 사용합니다.
                self._validate_with_ocr(result, original_roi_resized, filled_roi_color, threshold, roi_info)
            elif method == "pixel_count":
                self._validate_with_pixel_count(result, original_roi_for_validation, filled_roi_for_validation, threshold)
            elif method == "contour":
                self._validate_with_contour(result, original_roi_for_validation, filled_roi_for_validation, threshold)
            elif method == "ssim":
                self._validate_with_ssim(result, original_roi_for_validation, filled_roi_for_validation, threshold)
            else:
                result["status"] = "ERROR"
                result["message"] = f"Unknown validation method: {method}"

        except Exception as e:
            result["status"] = "ERROR"
            result["message"] = f"Validation error: {e}"
            logging.error(f"Error validating field '{field_name}': {e}", exc_info=True)

        return result

    def _correct_roi_position(self, original_img, filled_img, coords, anchor_coords, scale, field_name):
        """좌표 보정 파이프라인: 전역 보정 (Feature Matching) + 지역 보정 (Anchor Template Matching)"""

        # --- 1단계: 전역 보정 (Global Correction) ---
        H, matches_count = self.feature_matcher.estimate_transformation(original_img, filled_img)

        if H is None:
            logging.warning(f"전역 변환 행렬 추정 실패 (매칭점: {matches_count}개). 원본 좌표를 사용합니다.")
            return [c * scale for c in coords] # 보정 실패 시 원본 좌표 반환

        # 원본 좌표를 스케일링하고 변환 행렬 적용
        scaled_coords = [c * scale for c in coords]

        x1, y1, x2, y2 = scaled_coords
        points = np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]], dtype=np.float32).reshape(-1, 1, 2)
        transformed_points = cv2.perspectiveTransform(points, H)

        x_coords, y_coords = transformed_points[:, 0, 0], transformed_points[:, 0, 1]
        globally_corrected_coords = [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]

        # --- 2단계: 앵커 기반 지역 보정 (Local Correction) ---
        if anchor_coords:
            try:
                scaled_anchor_coords = [c * scale for c in anchor_coords]
                anchor_template = self._extract_roi_from_image(original_img, scaled_anchor_coords, grayscale=True)

                # 템플릿 매칭으로 앵커의 새 위치 찾기
                res = cv2.matchTemplate(filled_img, anchor_template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)

                if max_val > 0.7: # 매칭 신뢰도 임계값
                    # 앵커의 원래 중심과 새로 찾은 중심 간의 오차 계산
                    orig_anchor_cx = (scaled_anchor_coords[0] + scaled_anchor_coords[2]) / 2

                    # 전역 변환된 앵커의 예상 위치
                    transformed_anchor_points = cv2.perspectiveTransform(np.array([[[orig_anchor_cx, (scaled_anchor_coords[1] + scaled_anchor_coords[3]) / 2]]], dtype=np.float32), H)
                    expected_anchor_cx, expected_anchor_cy = transformed_anchor_points[0, 0, 0], transformed_anchor_points[0, 0, 1]

                    # 템플릿 매칭으로 찾은 실제 앵커 위치
                    found_anchor_cx = max_loc[0] + anchor_template.shape[1] / 2
                    found_anchor_cy = max_loc[1] + anchor_template.shape[0] / 2

                    # 지역 보정 오프셋
                    local_offset_x = found_anchor_cx - expected_anchor_cx
                    local_offset_y = found_anchor_cy - expected_anchor_cy

                    # 최종 좌표에 지역 오프셋 적용
                    final_coords = [c + (local_offset_x if i % 2 == 0 else local_offset_y) for i, c in enumerate(globally_corrected_coords)]
                    logging.info(f"'{field_name}' 앵커 기반 미세 조정 적용: dx={local_offset_x:.2f}, dy={local_offset_y:.2f}")
                    return final_coords
                else:
                    logging.warning(f"'{field_name}' 앵커 매칭 신뢰도 낮음 ({max_val:.2f}). 전역 보정 결과만 사용.")
            except Exception as e:
                logging.warning(f"앵커 기반 지역 보정 중 오류 발생: {e}")

        return globally_corrected_coords

    # --- 검증 헬퍼 메서드들 (구체화된 로직) ---
    def _validate_with_pixel_count(self, result, original_roi, filled_roi, threshold):
        # 1. Binarize both images using Otsu's method for robustness
        gray_original = cv2.cvtColor(original_roi, cv2.COLOR_BGR2GRAY)
        gray_filled = cv2.cvtColor(filled_roi, cv2.COLOR_BGR2GRAY)
        _, thresh_original = cv2.threshold(gray_original, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        _, thresh_filled = cv2.threshold(gray_filled, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # 2. Create an "exclusion zone" by dilating the original checkbox border.
        # This accounts for scanning distortions (thicker lines, warping).
        # A 5x5 kernel allows for ~2-3 pixels of distortion tolerance.
        kernel = np.ones((5, 5), np.uint8)
        exclusion_zone = cv2.dilate(thresh_original, kernel, iterations=1)

        # 3. Subtract the exclusion zone from the filled image.
        # This leaves only pixels that are "new" and not part of the original (distorted) border.
        new_content_mask = cv2.bitwise_and(thresh_filled, cv2.bitwise_not(exclusion_zone))

        # 4. Count the remaining pixels. This is our actual change.
        change_in_pixels = np.count_nonzero(new_content_mask)

        # --- DEBUG IMAGE SAVING ---
        try:
            import os
            output_dir = "output/debug"
            os.makedirs(output_dir, exist_ok=True)
            field_name = result["field_name"]
            cv2.imwrite(os.path.join(output_dir, f"{field_name}_pc_1_original_binary.png"), thresh_original)
            cv2.imwrite(os.path.join(output_dir, f"{field_name}_pc_2_filled_binary.png"), thresh_filled)
            cv2.imwrite(os.path.join(output_dir, f"{field_name}_pc_3_exclusion_zone.png"), exclusion_zone)
            cv2.imwrite(os.path.join(output_dir, f"{field_name}_pc_4_new_content.png"), new_content_mask)
        except Exception as e:
            logging.warning(f"Failed to save debug images for {field_name}: {e}")
        # --- END DEBUG ---

        # 5. Compare the count of new pixels with the threshold.
        if change_in_pixels < threshold:
            result["status"] = "DEFICIENT"
            result["message"] = f"New pixel count insufficient ({change_in_pixels}, threshold: {threshold})"
        else:
            result["message"] = f"New pixel count OK ({change_in_pixels})"

    def _validate_with_ocr(self, result, original_roi, filled_roi, threshold, roi_info):
        # OCR은 컬러 이미지보다 회색조 이미지에서 더 잘 동작합니다.
        gray_filled = cv2.cvtColor(filled_roi, cv2.COLOR_BGR2GRAY)

        # ROI의 개별 설정을 가져와 OCR 실행
        # 전처리(이진화 등)는 각 OCR 서비스 구현체에 위임합니다.
        ocr_config = roi_info.get('ocr_config', {})
        if ocr_config is None: ocr_config = {}
        ocr_config['field_name'] = result.get('field_name')
        clean_text = self.ocr_service.recognize_text(gray_filled, config=ocr_config)

        # --- DEBUG IMAGE SAVING (OCR 전용) ---
        try:
            import os
            output_dir = "output/debug"
            os.makedirs(output_dir, exist_ok=True)
            field_name = result["field_name"]
            # OCR 서비스에 들어가는 회색조 이미지를 저장하여 디버깅에 사용
            cv2.imwrite(os.path.join(output_dir, f"{field_name}_ocr_input_gray.png"), gray_filled)
        except Exception as e:
            logging.warning(f"Failed to save OCR debug images for {field_name}: {e}")
        # --- END DEBUG ---

        if len(clean_text) < threshold:
            result["status"] = "DEFICIENT"
            result["message"] = f"OCR insufficient ({len(clean_text)} chars, threshold: {threshold})"
        else:
            result["message"] = f"OCR OK: '{clean_text}'"

    def _validate_with_contour(self, result, original_roi, filled_roi, threshold):
        # ROI 경계에서 발생하는 미세한 정렬 오류를 제거하기 위해 양쪽 이미지 모두 크롭
        # filled_roi는 이미 original_roi와 동일한 크기로 리사이즈되었음
        h, w, _ = original_roi.shape
        border = 3 # 크롭할 픽셀 수
        if h > border * 2 and w > border * 2:
            original_roi = original_roi[border:h-border, border:w-border]
            filled_roi = filled_roi[border:h-border, border:w-border]

        diff_img = cv2.absdiff(cv2.cvtColor(original_roi, cv2.COLOR_BGR2GRAY), cv2.cvtColor(filled_roi, cv2.COLOR_BGR2GRAY))

        # 미세한 렌더링 노이즈를 제거하기 위해 부드러운 블러 적용
        blur_img = cv2.GaussianBlur(diff_img, (7, 7), 0)

        # 임계값을 높여(20->35) 사소한 노이즈가 증폭되는 것을 방지
        _, thresh = cv2.threshold(blur_img, 35, 255, cv2.THRESH_BINARY)
        
        kernel = np.ones((3,3), np.uint8)
        # MORPH_OPEN을 사용하여 미세한 노이즈(가는 선 등) 제거
        thresh_morphed = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
        contours, _ = cv2.findContours(thresh_morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        total_area = sum(cv2.contourArea(c) for c in contours if cv2.contourArea(c) > 10)

        # --- DEBUG IMAGE SAVING ---
        try:
            import os
            output_dir = "output/debug"
            os.makedirs(output_dir, exist_ok=True)
            field_name = result["field_name"]
            cv2.imwrite(os.path.join(output_dir, f"{field_name}_1_original.png"), original_roi)
            cv2.imwrite(os.path.join(output_dir, f"{field_name}_2_filled.png"), filled_roi)
            cv2.imwrite(os.path.join(output_dir, f"{field_name}_3_diff.png"), diff_img)
            cv2.imwrite(os.path.join(output_dir, f"{field_name}_4_thresh.png"), thresh)
            cv2.imwrite(os.path.join(output_dir, f"{field_name}_5_morphed.png"), thresh_morphed)
        except Exception as e:
            logging.warning(f"Failed to save debug images for {field_name}: {e}")
        # --- END DEBUG ---

        if total_area < threshold:
            result["status"] = "DEFICIENT"
            result["message"] = f"Contour area insufficient ({total_area:.0f}, threshold: {threshold})"
        else:
            result["message"] = f"Contour OK (Total Area: {total_area:.0f})"

    def _validate_with_ssim(self, result, original_roi, filled_roi, threshold):
        gray_original = cv2.cvtColor(original_roi, cv2.COLOR_BGR2GRAY)
        gray_filled = cv2.cvtColor(filled_roi, cv2.COLOR_BGR2GRAY)

        # Otsu's Binarization to automatically find the optimal threshold
        _, thresh_original = cv2.threshold(gray_original, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        _, thresh_filled = cv2.threshold(gray_filled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Calculate pixel difference percentage
        diff_img = cv2.absdiff(thresh_original, thresh_filled)
        non_zero_count = np.count_nonzero(diff_img)
        total_pixels = diff_img.size
        change_percentage = (non_zero_count / total_pixels) * 100 if total_pixels > 0 else 0

        # --- DEBUG IMAGE SAVING ---
        try:
            import os
            output_dir = "output/debug"
            os.makedirs(output_dir, exist_ok=True)
            field_name = result["field_name"]
            cv2.imwrite(os.path.join(output_dir, f"{field_name}_ssim_1_original_otsu.png"), thresh_original)
            cv2.imwrite(os.path.join(output_dir, f"{field_name}_ssim_2_filled_otsu.png"), thresh_filled)
            cv2.imwrite(os.path.join(output_dir, f"{field_name}_ssim_3_pixel_diff.png"), diff_img)
        except Exception as e:
            logging.warning(f"Failed to save debug images for {field_name}: {e}")
        # --- END DEBUG ---

        # 'threshold' is the minimum percentage of pixels that must change
        if change_percentage < threshold:
            result["status"] = "DEFICIENT"
            result["message"] = f"Pixel change insufficient ({change_percentage:.2f}%, threshold: {threshold}%)"
        else:
            result["message"] = f"Pixel change OK ({change_percentage:.2f}%)"

    # --- 이미지 처리 헬퍼 메서드들 ---
    def _get_full_page_image(self, page, scale=2.0, grayscale=True):
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if grayscale:
            return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    def _extract_roi_from_pdf(self, pdf_doc, page_num, coords, scale=2.0):
        page = pdf_doc[page_num]
        rect = fitz.Rect(coords)
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat, clip=rect, alpha=False)
        img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        return cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR) if pix.n == 4 else cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

    def _extract_roi_from_image(self, image, coords, grayscale=False):
        x1, y1, x2, y2 = [int(c) for c in coords]
        h, w = image.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        roi = image[y1:y2, x1:x2]
        if grayscale:
            return roi if len(roi.shape) == 2 else cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        return roi if len(roi.shape) == 3 else cv2.cvtColor(roi, cv2.COLOR_GRAY2BGR)

    # --- 좌표 보정을 위한 중첩 클래스 ---
    class _FeatureMatcher:
        """
        특징점 매칭을 통해 이미지 간의 기하학적 변환(Homography)을 추정하는 클래스.
        """
        def __init__(self):
            self.detector = cv2.AKAZE_create()
            self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING)

        def estimate_transformation(self, img1, img2):
            kp1, desc1 = self.detector.detectAndCompute(img1, None)
            kp2, desc2 = self.detector.detectAndCompute(img2, None)

            if desc1 is None or desc2 is None or len(desc1) < 2 or len(desc2) < 2:
                return None, 0

            raw_matches = self.matcher.knnMatch(desc1, desc2, k=2)
            good_matches = [m for m, n in raw_matches if m.distance < 0.75 * n.distance]

            if len(good_matches) > 10:
                src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                H, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
                return H, len(good_matches)

            return None, len(good_matches)
