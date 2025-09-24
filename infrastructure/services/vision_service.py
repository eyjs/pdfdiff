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
        print("Finding best anchor using Sliding Window...")
        candidates = self._generate_anchor_candidates(pdf_doc, page_num, roi_coords)
        if not candidates:
            return None

        print(f"Evaluated {len(candidates)} anchor candidates.")
        # 점수가 가장 높은 후보를 선택
        candidates.sort(key=lambda x: x['score'], reverse=True)
        best_candidate = candidates[0]

        print(f"[Anchor Selected] Position: {best_candidate['label']}, Score: {best_candidate['score']:.2f}")
        return best_candidate['coords']

    def _generate_anchor_candidates(self, pdf_doc, page_num, roi):
        page = pdf_doc[page_num]
        page_width, page_height = page.rect.width, page.rect.height
        x0, y0, x1, y1 = roi

        # 슬라이딩 윈도우 파라미터 정의
        search_margin = 150  # ROI에서 얼마나 멀리까지 탐색할지
        win_w, win_h = 120, 40 # 앵커 후보 창 크기
        step = 30            # 몇 픽셀씩 이동하며 탐색할지

        # 4방향 (상, 하, 좌, 우) 탐색 영역 정의
        search_areas = {
            "top": (x0 - win_w, y0 - search_margin - win_h, x1 + win_w, y0 - 5),
            "bottom": (x0 - win_w, y1 + 5, x1 + win_w, y1 + search_margin + win_h),
            "left": (x0 - search_margin - win_w, y0 - win_h, x0 - 5, y1 + win_h),
            "right": (x1 + 5, y0 - win_h, x1 + search_margin + win_w, y1 + win_h),
        }

        results = []
        for label, area in search_areas.items():
            area_x0, area_y0, area_x1, area_y1 = area
            
            # 페이지 경계 내에서 탐색
            area_x0, area_y0 = max(0, area_x0), max(0, area_y0)
            area_x1, area_y1 = min(page_width, area_x1), min(page_height, area_y1)

            # 정의된 step으로 슬라이딩 윈도우 탐색
            for y in range(int(area_y0), int(area_y1 - win_h), step):
                for x in range(int(area_x0), int(area_x1 - win_w), step):
                    coords = [x, y, x + win_w, y + win_h]
                    try:
                        img = self._extract_pdf_region(page, coords)
                        if img is None or img.size == 0:
                            continue

                        score = self._evaluate_anchor_quality(img)
                        # 점수가 0 이상인 유의미한 후보만 추가
                        if score > 0:
                            results.append({'label': label, 'coords': coords, 'score': score})
                    except Exception:
                        continue # 에러 발생 시 해당 후보는 건너뜀
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
        total_score = (harris_score * 1.0) + (feature_quality_score * 2.5) + (edge_density_score * 0.5)
        return total_score