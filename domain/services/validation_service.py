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

    def create_annotated_pdf(self, target_pdf_path, validation_results):
        target_doc = self.doc_repo.load_pdf(target_pdf_path)
        for result in validation_results:
            if result["status"] != "OK":
                page = target_doc[result["page"]]
                rect = fitz.Rect(result["coords"])
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

