# 파일 경로: infrastructure/services/vision_service.py
import cv2
import numpy as np
import fitz

# Infrastructure Layer (Service Implementation)
# 역할: 외부 기술/라이브러리(OpenCV, PyMuPDF 등)를 직접 사용하여
#       Domain Service가 요청한 작업을 실제로 수행합니다.
#       이곳의 코드는 특정 라이브러리에 강하게 의존합니다.

class VisionService:
    def find_best_anchor(self, pdf_doc, page_num, roi_coords):
        """OpenCV를 사용하여 최적의 앵커 영역을 탐색합니다."""
        candidates = self._generate_anchor_candidates(pdf_doc, page_num, roi_coords)
        if not candidates:
            return None

        # 점수가 가장 높은 후보를 선택
        candidates.sort(key=lambda x: x['score'], reverse=True)
        best_candidate = candidates[0]

        print(f"[Anchor Selected] Position: {best_candidate['label']}, Score: {best_candidate['score']:.2f}")
        return best_candidate['coords']

    def _generate_anchor_candidates(self, pdf_doc, page_num, roi):
        page = pdf_doc[page_num]
        page_width, page_height = page.rect.width, page.rect.height
        x0, y0, x1, y1 = roi

        # ROI 주변의 4방향에 대한 앵커 후보 영역 정의
        offsets = {
            "left":   [max(0, x0 - 120), y0 - 10, x0 - 5, y1 + 10],
            "right":  [x1 + 5, y0 - 10, min(page_width, x1 + 120), y1 + 10],
            "top":    [x0 - 10, max(0, y0 - 60), x1 + 10, y0 - 5],
            "bottom": [x0 - 10, y1 + 5, x1 + 10, min(page_height, y1 + 60)]
        }

        results = []
        for label, coords in offsets.items():
            try:
                # 후보 영역 이미지 추출
                img = self._extract_pdf_region(page, coords)
                if img is None or img.size == 0:
                    continue

                # 이미지 품질 평가
                score = self._evaluate_anchor_quality(img)
                results.append({'label': label, 'coords': coords, 'score': score})
            except Exception as e:
                print(f"Error evaluating anchor candidate {label}: {e}")
                continue
        return results

    def _extract_pdf_region(self, page, coords, scale=2.0):
        """PyMuPDF를 사용해 PDF의 특정 영역을 이미지로 추출합니다."""
        rect = fitz.Rect(coords)
        if rect.is_empty:
            return None

        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat, clip=rect, alpha=False)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    def _evaluate_anchor_quality(self, img):
        """OpenCV를 사용하여 앵커 후보 이미지의 품질 점수를 계산합니다."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 1. Harris Corner Detection: 코너가 많을수록 좋음
        harris_corners = cv2.cornerHarris(gray, 2, 3, 0.04)
        harris_score = np.sum(harris_corners > 0.01 * harris_corners.max())

        # 2. AKAZE Feature Detection: 특징점이 많고 품질이 좋을수록 좋음
        akaze = cv2.AKAZE_create()
        kp = akaze.detect(gray, None)
        feature_quality_score = 0
        if kp:
            feature_quality_score = len(kp) + int(sum(p.response for p in kp))

        # 3. Canny Edge Detection: 엣지(선)가 많을수록 좋음
        edges = cv2.Canny(gray, 100, 200)
        edge_density_score = int(np.sum(edges) / 255)

        # 각 점수에 가중치를 부여하여 최종 점수 계산
        total_score = (harris_score * 2.0) + (feature_quality_score * 1.5) + (edge_density_score * 1.0)
        return total_score