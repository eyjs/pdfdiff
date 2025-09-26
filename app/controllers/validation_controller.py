from tkinter import filedialog, messagebox
import os
import datetime
import logging

import fitz
from PIL import Image
from shared.exceptions import DocumentCorruptedError

# Infrastructure Layer - OCR 서비스 및 검증 서비스
from infrastructure.services.validation_vision_service import ValidationVisionService
from infrastructure.services.tesseract_ocr_service import TesseractOcrService

# EasyOCR 통합 서비스
try:
    from infrastructure.services.easyocr_service import EasyOCRService
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    logging.warning("EasyOCR 서비스를 가져올 수 없습니다. 'EasyOCR' 또는 '비교 모드'를 선택하면 Tesseract로 대체됩니다.")

# Domain Layer
from domain.services.validation_service import ValidationService

class ValidationController:
    """
    ValidationWindow(View)와 ValidationService(Domain)를 연결하는 컨트롤러.
    검증 실행에 필요한 모든 서비스를 동적으로 생성하고 전체 흐름을 관장합니다.
    """
    def __init__(self, view, doc_repo, template_service):
        self.view = view
        self.doc_repo = doc_repo
        self.template_service = template_service

        # UI/비즈니스 로직 상태
        self.mode = "파일"
        self.selected_template = None
        self.target_path = None
        self.target_filename = None
        self.last_results = []

        # 뷰어 관련 상태
        self.original_doc = None
        self.annotated_doc = None
        self.current_page_num = 0
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.is_panning = False
        self.pan_start_x = 0
        self.pan_start_y = 0

    def initialize_view(self):
        self.load_templates()

    def _create_ocr_service(self, engine_name: str):
        """사용자 선택에 따라 OCR 서비스를 동적으로 생성합니다."""
        
        tesseract_service = TesseractOcrService()

        if engine_name == 'Tesseract':
            logging.info("Tesseract 단독 서비스로 초기화합니다.")
            return tesseract_service
        
        if EASYOCR_AVAILABLE:
            if engine_name == 'EasyOCR':
                logging.info("EasyOCR 단독 서비스 초기화 중...")
                try:
                    return EasyOCRService()
                except Exception as e:
                    logging.error(f"EasyOCR 초기화 실패: {e}. Tesseract로 대체합니다.")
                    messagebox.showwarning("EasyOCR 실패", "EasyOCR 초기화에 실패했습니다. Tesseract 엔진으로 대체하여 실행합니다.")
                    return tesseract_service
        
        if engine_name != 'Tesseract':
            logging.warning(f"'{engine_name}'은(는) 유효한 OCR 엔진이 아니거나 EasyOCR을 사용할 수 없습니다. Tesseract를 사용합니다.")
            if not EASYOCR_AVAILABLE:
                 messagebox.showwarning("EasyOCR 없음", "EasyOCR이 설치되지 않았습니다. Tesseract 엔진으로 실행합니다.")
        return tesseract_service

    def run_validation(self):
        self.view.clear_log()
        self.view.log(f"'{self.view.template_var.get()}' 템플릿으로 검증을 시작합니다.")

        # 1. UI에서 선택된 OCR 엔진 이름 가져오기
        selected_engine = self.view.ocr_engine_var.get()
        self.view.log(f"선택된 OCR 엔진: {selected_engine}")

        # 2. 선택된 이름에 맞는 서비스 동적 생성
        try:
            ocr_service = self._create_ocr_service(selected_engine)
            vision_service = ValidationVisionService(ocr_service=ocr_service)
            validation_service = ValidationService(self.doc_repo, vision_service)
        except Exception as e:
            self.view.log(f"🔥 서비스 초기화 중 심각한 오류 발생: {e}")
            messagebox.showerror("오류", f"서비스를 초기화하는 중 오류가 발생했습니다: {e}")
            return

        # 3. 검증 모드에 따라 실행
        if self.mode == "파일":
            self._run_single_file_validation(validation_service)
        else:
            self._run_folder_validation(validation_service)

    def _run_single_file_validation(self, validation_service):
        try:
            self.last_results = validation_service.validate_document(
                self.selected_template,
                self.target_path,
                progress_callback=self._progress_callback
            )
            self.target_filename = os.path.basename(self.target_path)
            self.view.log("="*50 + "\n상세 검증 결과:")
            self._log_results(self.last_results)

            annotated_pdf_bytes = validation_service.create_annotated_pdf(
                self.selected_template['original_pdf_path'],
                self.target_path,
                self.last_results
            )

            if self.original_doc: self.original_doc.close()
            if self.annotated_doc: self.annotated_doc.close()

            self.original_doc, self.annotated_doc = validation_service.load_docs_for_viewer(
                self.selected_template['original_pdf_path'], annotated_pdf_bytes
            )

            if not self.original_doc or len(self.original_doc) == 0:
                messagebox.showerror("PDF 로드 오류", "원본 PDF 파일을 로드할 수 없거나 페이지가 없습니다. 템플릿 설정을 확인해주세요.")
                self.view.update_save_button_state(False)
                return

            self.current_page_num = 0
            page = self.original_doc[self.current_page_num]
            zoom_x = self.view.left_canvas.winfo_width() / page.rect.width
            zoom_y = self.view.left_canvas.winfo_height() / page.rect.height
            self.zoom = min(zoom_x, zoom_y) * 0.98
            self.pan_x, self.pan_y = 0, 0

            self.render_docs()
            self.view.update_save_button_state(True)

        except DocumentCorruptedError as e:
            messagebox.showerror("PDF 로드 실패", f"PDF 파일을 로드하는 중 오류가 발생했습니다: {e}")
            self.view.update_save_button_state(False)
        except Exception as e:
            self.view.log(f"🔥 검증 중 심각한 오류 발생: {e}")
            messagebox.showerror("오류", f"검증 중 오류가 발생했습니다: {e}")
            self.view.update_save_button_state(False)

    def _run_folder_validation(self, validation_service):
        pdf_files = [f for f in os.listdir(self.target_path) if f.lower().endswith('.pdf')]
        if not pdf_files:
            self.view.log("폴더에 검증할 PDF 파일이 없습니다.")
            return

        template_name = self.view.template_var.get()
        base_output_dir = os.path.join("output", template_name)
        pass_dir = os.path.join(base_output_dir, "pass")
        fail_dir = os.path.join(base_output_dir, "fail")
        os.makedirs(pass_dir, exist_ok=True)
        os.makedirs(fail_dir, exist_ok=True)

        self.view.log(f"결과는 '{os.path.abspath(base_output_dir)}' 폴더에 저장됩니다.")

        success_count, fail_count = 0, 0
        total = len(pdf_files)

        for i, filename in enumerate(pdf_files):
            filepath = os.path.join(self.target_path, filename)
            self.view.update_progress(i + 1, total)
            self.view.log(f"[{i+1}/{total}] '{filename}' 검증 중...")

            try:
                results = validation_service.validate_document(self.selected_template, filepath)
                is_pass = all(r['status'] == 'OK' for r in results)

                annotated_pdf_bytes = validation_service.create_annotated_pdf(self.selected_template['original_pdf_path'], filepath, results)

                if is_pass:
                    success_count += 1
                    self.view.log("  -> ✅ 통과.")
                    output_path = os.path.join(pass_dir, filename)
                else:
                    fail_count += 1
                    deficient_count = sum(1 for r in results if r['status'] != 'OK')
                    self.view.log(f"  -> ❌ 미흡 ({deficient_count}개 항목).")
                    output_path = os.path.join(fail_dir, filename)

                with open(output_path, "wb") as f:
                    f.write(annotated_pdf_bytes)

            except Exception as e:
                fail_count += 1
                self.view.log(f"  -> 🔥 오류 발생: {e}")

        self.view.log("="*50 + f"\n일괄 검증 완료! (성공: {success_count}, 실패/오류: {fail_count})")

    # --- 이하 기존 메서드들 (load_templates, on_template_selected 등) ---
    def load_templates(self):
        try:
            names = self.template_service.get_all_template_names()
            self.view.template_combo['values'] = names
            if names:
                self.view.template_combo.current(0)
                self.on_template_selected()
        except Exception as e:
            self.view.log(f"템플릿 로드 오류: {e}")

    def on_template_selected(self, event=None):
        name = self.view.template_var.get()
        if not name: return
        try:
            self.selected_template = self.template_service.load_template(name)
            self._update_ui_state()
        except Exception as e:
            self.view.log(f"'{name}' 템플릿 로드 실패: {e}")

    def switch_mode(self, mode):
        self.mode = mode
        self.target_path = None
        self.view.update_path("")
        self._update_ui_state()
        self.view.update_save_button_state(False)

    def browse_target(self):
        path = None
        if self.mode == "파일":
            path = filedialog.askopenfilename(title="PDF 파일 선택", filetypes=[("PDF files", "*.pdf")])
        else:
            path = filedialog.askdirectory(title="PDF 폴더 선택")

        if path:
            self.target_path = path
            self.view.update_path(path)
            self.view.update_save_button_state(False)
        self._update_ui_state()

    def _update_ui_state(self):
        is_ready = self.selected_template and self.target_path
        self.view.update_button_state(is_ready)

    def save_result_pdf(self):
        if not self.annotated_doc or not self.last_results:
            messagebox.showwarning("저장 오류", "먼저 검증을 실행해야 합니다.")
            return
        try:
            is_pass = all(r['status'] == 'OK' for r in self.last_results)
            status_folder = "pass" if is_pass else "fail"
            template_name = self.view.template_var.get()
            output_path = os.path.join("output", template_name, status_folder)
            os.makedirs(output_path, exist_ok=True)
            output_filepath = os.path.join(output_path, self.target_filename)
            self.annotated_doc.save(output_filepath)
            messagebox.showinfo("저장 완료", f"결과가 다음 파일로 저장되었습니다:\n{os.path.abspath(output_filepath)}")
        except Exception as e:
            messagebox.showerror("저장 실패", f"결과를 저장하는 중 오류가 발생했습니다:\n{e}")

    def _progress_callback(self, message, current, total):
        self.view.log(message)
        self.view.update_progress(current, total)

    def _log_results(self, results):
        for result in results:
            icon = "✅" if result['status'] == 'OK' else "❌"
            self.view.log(f"  {icon} [{result['field_name']}]: {result['message']}")

    # --- PDF Viewer Control Methods ---
    def _get_display_matrix(self):
        if not self.original_doc:
            return fitz.Matrix(1, 1)
        return fitz.Matrix(self.zoom, self.zoom)

    def _pdf_to_screen_coords(self, pdf_coords, mat):
        p1 = fitz.Point(pdf_coords[0], pdf_coords[1]) * mat
        p2 = fitz.Point(pdf_coords[2], pdf_coords[3]) * mat
        screen_x0 = p1.x + self.pan_x
        screen_y0 = p1.y + self.pan_y
        screen_x1 = p2.x + self.pan_x
        screen_y1 = p2.y + self.pan_y
        return screen_x0, screen_y0, screen_x1, screen_y1

    def render_docs(self):
        if not self.original_doc or not self.annotated_doc:
            return

        w, h = self.view.left_canvas.winfo_width(), self.view.left_canvas.winfo_height()
        if w < 10 or h < 10:
            self.view.root.after(50, self.render_docs)
            return

        mat = self._get_display_matrix()

        original_pix = self.original_doc[self.current_page_num].get_pixmap(matrix=mat, alpha=False)
        annotated_pix = self.annotated_doc[self.current_page_num].get_pixmap(matrix=mat, alpha=False)

        original_img = Image.frombytes("RGB", [original_pix.width, original_pix.height], original_pix.samples)
        annotated_img = Image.frombytes("RGB", [annotated_pix.width, annotated_pix.height], annotated_pix.samples)

        rois_on_page = {
            name: {**roi, 'screen_coords': self._pdf_to_screen_coords(roi['coords'], mat)}
            for name, roi in self.selected_template['rois'].items()
            if roi['page'] == self.current_page_num
        }

        page = self.original_doc[self.current_page_num]
        total_width = page.rect.width * self.zoom
        total_height = page.rect.height * self.zoom

        self.view.update_viewer(
            original_img, annotated_img, rois_on_page,
            self.current_page_num, len(self.original_doc),
            self.pan_x, self.pan_y, total_width, total_height
        )

    def handle_zoom(self, factor, x, y):
        if not self.original_doc: return
        img_x, img_y = x - self.pan_x, y - self.pan_y
        pdf_p = fitz.Point(img_x, img_y) * ~fitz.Matrix(self.zoom, self.zoom)
        self.zoom *= factor
        self.zoom = max(0.1, min(self.zoom, 5.0))
        new_img_p = pdf_p * fitz.Matrix(self.zoom, self.zoom)
        self.pan_x += img_x - new_img_p.x
        self.pan_y += img_y - new_img_p.y
        self.render_docs()

    def start_pan(self, event):
        self.is_panning = True
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def do_pan(self, event):
        if self.is_panning:
            dx = event.x - self.pan_start_x
            dy = event.y - self.pan_start_y
            self.pan_x += dx
            self.pan_y += dy
            self.pan_start_x = event.x
            self.pan_start_y = event.y
            self.render_docs()

    def end_pan(self, event):
        self.is_panning = False

    def set_pan(self, x_offset, y_offset):
        if not self.original_doc: return
        page = self.original_doc[self.current_page_num]
        total_width = page.rect.width * self.zoom
        total_height = page.rect.height * self.zoom
        canvas_width = self.view.left_canvas.winfo_width()
        canvas_height = self.view.left_canvas.winfo_height()
        if x_offset is not None:
            self.pan_x = -x_offset * (total_width - canvas_width)
        if y_offset is not None:
            self.pan_y = -y_offset * (total_height - canvas_height)
        self.render_docs()

    def prev_page(self):
        if self.original_doc and self.current_page_num > 0:
            self.current_page_num -= 1
            self.render_docs()

    def next_page(self):
        if self.original_doc and self.current_page_num < len(self.original_doc) - 1:
            self.current_page_num += 1
            self.render_docs()