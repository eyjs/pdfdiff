import fitz # PyMuPDF
from PIL import Image

class ValidationService:
    def __init__(self, document_repository, vision_service):
        self.doc_repo = document_repository
        self.vision = vision_service

    def validate_document(self, template, target_pdf_path, progress_callback=None):
        original_doc = self.doc_repo.load_pdf(template['original_pdf_path'])
        target_doc = self.doc_repo.load_pdf(target_pdf_path)

        results = []
        rois = template['rois']
        total = len(rois)

        for i, (field_name, roi_info) in enumerate(rois.items()):
            if progress_callback:
                progress_callback(f"'{field_name}' 검증 중...", i + 1, total)

            # 복잡한 이미지 처리와 분석은 Infrastructure의 VisionService에 위임
            result = self.vision.validate_roi(original_doc, target_doc, field_name, roi_info)
            results.append(result)

        return results

    def create_annotated_pdf(self, original_pdf_path, target_pdf_path, validation_results):
        target_doc = self.doc_repo.load_pdf(target_pdf_path)
        print(f"DEBUG: create_annotated_pdf - target_doc num_pages: {target_doc.page_count}") # 추가
        for result in validation_results:
            if result["status"] != "OK":
                page_num = result["page"]
                print(f"DEBUG: create_annotated_pdf - Processing page_num: {page_num} for field: {result['field_name']}") # 추가
                
                # result["corrected_coords"] 사용
                if "corrected_coords" in result and result["corrected_coords"] is not None:
                    coords_to_use = result["corrected_coords"]
                else:
                    # 보정된 좌표가 없으면 원래 coords 사용 (fallback)
                    coords_to_use = result["coords"]

                # page_num이 유효한지 확인
                if page_num < 0 or page_num >= target_doc.page_count:
                    print(f"ERROR: create_annotated_pdf - Invalid page_num: {page_num}. target_doc has {target_doc.page_count} pages.")
                    continue # 다음 결과로 넘어감

                # coords_to_use 유효성 검사 및 로그 추가
                print(f"DEBUG: create_annotated_pdf - coords_to_use: {coords_to_use}")
                if not (len(coords_to_use) == 4 and coords_to_use[0] < coords_to_use[2] and coords_to_use[1] < coords_to_use[3]):
                    print(f"ERROR: create_annotated_pdf - Invalid coordinates for fitz.Rect: {coords_to_use}. Skipping annotation.")
                    continue

                # 페이지 객체 유효성 확인 및 rect 값 로그 추가
                page = target_doc[page_num]
                print(f"DEBUG: create_annotated_pdf - Retrieved page object: {page}") # 추가
                rect = fitz.Rect(coords_to_use)
                print(f"DEBUG: create_annotated_pdf - Created rect: {rect}") # 추가
                
                color = (1, 1, 0) # 노란색
                highlight = page.add_highlight_annot(rect)
                highlight.set_colors({"stroke": color})
                highlight.update()

        return target_doc.tobytes()

    # --- Viewer Helper Methods ---
    def load_docs_for_viewer(self, original_path, annotated_bytes):
        original_doc = self.doc_repo.load_pdf(original_path)
        annotated_doc = self.doc_repo.load_pdf_from_bytes(annotated_bytes)
        return original_doc, annotated_doc

    def render_page_to_image(self, doc, page_num, size):
        w, h = size
        page = doc[page_num]

        zoom = min(w / page.rect.width, h / page.rect.height) * 0.95
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

