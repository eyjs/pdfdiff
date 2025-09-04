from tkinter import filedialog
import os
import datetime

class ValidationController:
    """
    ValidationWindow(View)와 ValidationService(Domain)를 연결하는 컨트롤러.
    사용자 입력을 받아 서비스에 처리를 요청하고, 그 결과를 뷰에 전달합니다.
    """
    def __init__(self, view, validation_service, template_service):
        self.view = view
        self.validation_service = validation_service
        self.template_service = template_service

        # UI/비즈니스 로직 상태를 관리하는 변수
        self.mode = "파일"  # 기본 모드는 '파일'
        self.selected_template = None
        self.target_path = None

        # '파일' 모드에서 사용될 PDF 뷰어 관련 상태 변수
        self.original_doc = None
        self.annotated_doc = None
        self.current_page_num = 0

        # __init__에서는 View의 위젯에 직접 접근하는 코드를 실행하지 않습니다.
        # View가 완전히 생성된 후에 initialize_view()가 호출됩니다.

    def initialize_view(self):
        """View가 완전히 생성되고 준비된 후 MainController에 의해 호출됩니다."""
        self.load_templates()

    def load_templates(self):
        """템플릿 목록을 불러와 View의 콤보박스를 채웁니다."""
        try:
            names = self.template_service.get_all_template_names()
            self.view.template_combo['values'] = names
            if names:
                self.view.template_combo.current(0)
                self.on_template_selected()
        except Exception as e:
            self.view.log(f"템플릿 로드 오류: {e}")

    def on_template_selected(self, event=None):
        """사용자가 템플릿 콤보박스에서 항목을 선택했을 때 호출됩니다."""
        name = self.view.template_var.get()
        if not name: return
        try:
            self.selected_template = self.template_service.load_template(name)
            self._update_ui_state()
        except Exception as e:
            self.view.log(f"'{name}' 템플릿 로드 실패: {e}")

    def switch_mode(self, mode):
        """'파일'/'폴더' 검증 모드를 전환합니다."""
        self.mode = mode
        self.target_path = None
        self.view.update_path("")
        self._update_ui_state()

    def browse_target(self):
        """검증할 파일 또는 폴더를 선택하는 대화상자를 엽니다."""
        path = None
        if self.mode == "파일":
            path = filedialog.askopenfilename(title="PDF 파일 선택", filetypes=[("PDF files", "*.pdf")])
        else:
            path = filedialog.askdirectory(title="PDF 폴더 선택")

        if path:
            self.target_path = path
            self.view.update_path(path)
        self._update_ui_state()

    def _update_ui_state(self):
        """현재 상태(템플릿, 대상 경로)에 따라 UI(버튼 등)를 업데이트합니다."""
        is_ready = self.selected_template and self.target_path
        self.view.update_button_state(is_ready)

    def run_validation(self):
        """'검사 실행' 버튼 클릭 시 호출되며, 모드에 따라 적절한 검증을 시작합니다."""
        self.view.clear_log()
        self.view.log(f"'{self.view.template_var.get()}' 템플릿으로 검증을 시작합니다.")

        if self.mode == "파일":
            self._run_single_file_validation()
        else:
            self._run_folder_validation()

    def _run_single_file_validation(self):
        """단일 파일 검증을 수행합니다."""
        try:
            # 1. Service에 문서 검증을 요청하고 결과를 받습니다.
            results = self.validation_service.validate_document(
                self.selected_template,
                self.target_path,
                progress_callback=self._progress_callback
            )
            self.view.log("="*50 + "\n상세 검증 결과:")
            self._log_results(results)

            # 2. Service를 통해 결과 PDF(주석 추가)를 메모리에 생성합니다.
            annotated_pdf_bytes = self.validation_service.create_annotated_pdf(self.target_path, results)

            # 3. Service를 통해 뷰어에 표시할 문서들을 로드합니다.
            self.original_doc, self.annotated_doc = self.validation_service.load_docs_for_viewer(
                self.selected_template['original_pdf_path'], annotated_pdf_bytes
            )
            self.current_page_num = 0
            self.render_docs() # 뷰어 렌더링 시작

        except Exception as e:
            self.view.log(f"🔥 검증 중 심각한 오류 발생: {e}")

    def _run_folder_validation(self):
        """폴더 내 모든 PDF 파일에 대한 일괄 검증을 수행합니다."""
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
                # 각 파일에 대해 검증 수행
                results = self.validation_service.validate_document(self.selected_template, filepath)
                deficient_count = sum(1 for r in results if r['status'] != 'OK')

                if deficient_count > 0:
                    fail += 1
                    self.view.log(f"  -> ❌ 미흡 ({deficient_count}개 항목).")
                    # 미흡한 경우에만 결과 PDF를 파일로 저장
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
        """Service에서 진행 상황을 View에 전달하기 위한 콜백 함수입니다."""
        self.view.log(message)
        self.view.update_progress(current, total)

    def _log_results(self, results):
        """검증 결과 리스트를 로그 창에 보기 좋게 출력합니다."""
        for result in results:
            icon = "✅" if result['status'] == 'OK' else "❌"
            self.view.log(f"  {icon} [{result['field_name']}]: {result['message']}")

    # --- PDF Viewer Control Methods ---
    def render_docs(self):
        """뷰어에 현재 페이지의 원본/결과 이미지를 렌더링합니다."""
        if not self.original_doc or not self.annotated_doc:
            return

        # View(Canvas)의 현재 크기를 가져옴
        w, h = self.view.left_canvas.winfo_width(), self.view.left_canvas.winfo_height()
        if w < 10 or h < 10: # 창이 완전히 그려지기 전이면 잠시 대기
            self.view.root.after(50, self.render_docs)
            return

        # Service에 페이지 이미지 렌더링을 요청
        original_img = self.validation_service.render_page_to_image(self.original_doc, self.current_page_num, (w,h))
        annotated_img = self.validation_service.render_page_to_image(self.annotated_doc, self.current_page_num, (w,h))

        # 렌더링된 이미지를 View에 전달하여 화면 업데이트
        self.view.update_viewer(original_img, annotated_img, self.current_page_num, len(self.original_doc))

    def prev_page(self):
        """'이전 페이지' 버튼 클릭 시 호출됩니다."""
        if self.current_page_num > 0:
            self.current_page_num -= 1
            self.render_docs()

    def next_page(self):
        """'다음 페이지' 버튼 클릭 시 호출됩니다."""
        if self.original_doc and self.current_page_num < len(self.original_doc) - 1:
            self.current_page_num += 1
            self.render_docs()

