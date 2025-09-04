from tkinter import filedialog
import os
import datetime

class ValidationController:
    def __init__(self, view, validation_service, template_service):
        self.view = view
        self.validation_service = validation_service
        self.template_service = template_service

        # 상태 변수
        self.mode = "파일"
        self.selected_template = None
        self.target_path = None

        # 파일 모드 뷰어 상태
        self.original_doc = None
        self.annotated_doc = None
        self.current_page_num = 0

        self.load_templates()

    def load_templates(self):
        try:
            names = self.template_service.get_all_template_names()
            self.view.template_combo['values'] = names
            if names:
                self.view.template_combo.current(0)
                self.on_template_selected()
        except Exception as e:
            self.view.log(f"템플릿 로드 오류: {e}")

    def on_template_selected(self):
        name = self.view.template_var.get()
        self.selected_template = self.template_service.load_template(name)
        self._update_ui_state()

    def switch_mode(self, mode):
        self.mode = mode
        self.target_path = None
        self.view.update_path("")
        self._update_ui_state()

    def browse_target(self):
        if self.mode == "파일":
            path = filedialog.askopenfilename(title="PDF 파일 선택", filetypes=[("PDF files", "*.pdf")])
        else:
            path = filedialog.askdirectory(title="PDF 폴더 선택")

        if path:
            self.target_path = path
            self.view.update_path(path)
        self._update_ui_state()

    def _update_ui_state(self):
        is_ready = self.selected_template and self.target_path
        self.view.update_button_state(is_ready)

    def run_validation(self):
        self.view.clear_log()
        self.view.log(f"'{self.view.template_var.get()}' 템플릿으로 검증을 시작합니다.")

        if self.mode == "파일":
            self._run_single_file_validation()
        else:
            self._run_folder_validation()

    def _run_single_file_validation(self):
        try:
            results = self.validation_service.validate_document(
                self.selected_template,
                self.target_path,
                progress_callback=self._progress_callback
            )
            self.view.log("="*50 + "\n상세 검증 결과:")
            self._log_results(results)

            # 결과 PDF 생성 및 뷰어에 로드
            annotated_pdf_bytes = self.validation_service.create_annotated_pdf(self.target_path, results)
            self.original_doc, self.annotated_doc = self.validation_service.load_docs_for_viewer(
                self.selected_template['original_pdf_path'], annotated_pdf_bytes
            )
            self.current_page_num = 0
            self.render_docs()

        except Exception as e:
            self.view.log(f"🔥 검증 중 심각한 오류 발생: {e}")

    def _run_folder_validation(self):
        pdf_files = [f for f in os.listdir(self.target_path) if f.lower().endswith('.pdf')]
        if not pdf_files:
            self.view.log("폴더에 검증할 PDF 파일이 없습니다.")
            return

        output_dir = os.path.join("output", self.view.template_var.get())
        os.makedirs(output_dir, exist_ok=True)
        self.view.log(f"결과는 '{os.path.abspath(output_dir)}' 폴더에 저장됩니다.")

        success, fail = 0, 0
        total = len(pdf_files)

        for i, filename in enumerate(pdf_files):
            filepath = os.path.join(self.target_path, filename)
            self.view.update_progress(i + 1, total)
            self.view.log(f"[{i+1}/{total}] '{filename}' 검증 중...")

            try:
                results = self.validation_service.validate_document(self.selected_template, filepath)
                deficient_count = sum(1 for r in results if r['status'] != 'OK')

                if deficient_count > 0:
                    fail += 1
                    self.view.log(f"  -> ❌ 미흡 ({deficient_count}개 항목).")
                    annotated_pdf_bytes = self.validation_service.create_annotated_pdf(filepath, results)
                    out_name = f"review_{os.path.splitext(filename)[0]}_{datetime.datetime.now().strftime('%H%M%S')}.pdf"
                    with open(os.path.join(output_dir, out_name), "wb") as f:
                        f.write(annotated_pdf_bytes)
                else:
                    success += 1
                    self.view.log("  -> ✅ 통과.")
            except Exception as e:
                fail += 1
                self.view.log(f"  -> 🔥 오류 발생: {e}")

        self.view.log("="*50 + f"\n일괄 검증 완료! (성공: {success}, 실패/오류: {fail})")

    def _progress_callback(self, message, current, total):
        self.view.log(message)
        self.view.update_progress(current, total)

    def _log_results(self, results):
        for result in results:
            icon = "✅" if result['status'] == 'OK' else "❌"
            self.view.log(f"  {icon} [{result['field_name']}]: {result['message']}")

    # --- Viewer Control ---
    def render_docs(self):
        if not self.original_doc or not self.annotated_doc:
            return

        w, h = self.view.left_canvas.winfo_width(), self.view.left_canvas.winfo_height()
        if w < 10 or h < 10: # 창이 완전히 그려지기 전이면 잠시 대기
            self.view.root.after(50, self.render_docs)
            return

        original_img = self.validation_service.render_page_to_image(self.original_doc, self.current_page_num, (w,h))
        annotated_img = self.validation_service.render_page_to_image(self.annotated_doc, self.current_page_num, (w,h))

        self.view.update_viewer(original_img, annotated_img, self.current_page_num, len(self.original_doc))

    def prev_page(self):
        if self.current_page_num > 0:
            self.current_page_num -= 1
            self.render_docs()

    def next_page(self):
        if self.original_doc and self.current_page_num < len(self.original_doc) - 1:
            self.current_page_num += 1
            self.render_docs()

