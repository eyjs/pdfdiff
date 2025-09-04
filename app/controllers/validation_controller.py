"""
Validation Controller
검증 컨트롤러
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, Callable, List
import threading
from pathlib import Path

from domain.services.validation_service import ValidationService
from domain.services.template_service import TemplateService
from domain.entities.document import Document
from infrastructure.repositories.json_template_repository import JsonTemplateRepository
from infrastructure.repositories.file_document_repository import FileDocumentRepository
from shared.exceptions import *
from shared.utils import TimeUtils


class ValidationController:
    """검증 컨트롤러"""

    def __init__(self):
        # 의존성 주입
        self.template_repository = JsonTemplateRepository()
        self.document_repository = FileDocumentRepository()
        self.template_service = TemplateService(self.template_repository)
        self.validation_service = ValidationService()

        # UI 참조
        self.current_window = None
        self.progress_bar = None
        self.log_text = None
        self.status_label = None

        # UI 컨트롤 변수
        self.selected_template = None
        self.target_path = ""
        self.validation_mode = tk.StringVar(value="folder")

        # 검증 상태
        self.is_validating = False
        self.current_thread = None

    def show_validation_tool(self, parent: tk.Tk, on_close: Optional[Callable] = None):
        """검증 도구 창 표시"""
        try:
            # 기존 창이 있으면 포커스만 이동
            if self.current_window and self.current_window.winfo_exists():
                self.current_window.lift()
                self.current_window.focus_force()
                return

            # 새 창 생성
            self.current_window = tk.Toplevel(parent)
            self.current_window.title("PDF 검증 도구")
            self.current_window.geometry("1000x700")

            # 창 닫힘 이벤트 처리
            def on_window_close():
                self.cleanup()
                if on_close:
                    on_close()

            self.current_window.protocol("WM_DELETE_WINDOW", on_window_close)

            # 검증 도구 UI 로드
            self._load_validation_tool_ui()

        except Exception as e:
            raise ValidationException(f"검증 도구 실행 실패: {str(e)}")

    def _load_validation_tool_ui(self):
        """검증 도구 UI 로드"""
        try:
            main_frame = tk.Frame(self.current_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # 제목
            title_label = tk.Label(
                main_frame,
                text="PDF 서류 검증 도구",
                font=('Arial', 16, 'bold')
            )
            title_label.pack(pady=(0, 20))

            # 설정 섹션
            self._create_settings_section(main_frame)

            # 제어 섹션
            self._create_control_section(main_frame)

            # 진행률 섹션
            self._create_progress_section(main_frame)

            # 로그 섹션
            self._create_log_section(main_frame)

            # 상태바
            self._create_status_bar(main_frame)

        except Exception as e:
            raise ValidationException(f"UI 로드 실패: {str(e)}")

    def _create_settings_section(self, parent):
        """설정 섹션 생성"""
        settings_frame = tk.LabelFrame(parent, text="검증 설정", font=('Arial', 12))
        settings_frame.pack(fill=tk.X, pady=(0, 10))

        # 검사 방식 선택
        mode_frame = tk.Frame(settings_frame)
        mode_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(mode_frame, text="검사 방식:", font=('Arial', 10)).pack(side=tk.LEFT)

        tk.Radiobutton(
            mode_frame,
            text="파일 기준 검사",
            variable=self.validation_mode,
            value="file",
            command=self._on_mode_changed
        ).pack(side=tk.LEFT, padx=(10, 5))

        tk.Radiobutton(
            mode_frame,
            text="폴더 기준 검사",
            variable=self.validation_mode,
            value="folder",
            command=self._on_mode_changed
        ).pack(side=tk.LEFT, padx=(0, 5))

        # 템플릿 선택
        template_frame = tk.Frame(settings_frame)
        template_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(template_frame, text="템플릿 선택:", font=('Arial', 10)).pack(side=tk.LEFT)

        self.template_combo = ttk.Combobox(template_frame, state="readonly", width=30)
        self.template_combo.pack(side=tk.LEFT, padx=(10, 5))
        self.template_combo.bind('<<ComboboxSelected>>', self._on_template_selected)

        tk.Button(
            template_frame,
            text="새로고침",
            command=self._refresh_templates
        ).pack(side=tk.LEFT, padx=5)

        # 대상 경로 선택
        self.path_frame = tk.Frame(settings_frame)
        self.path_frame.pack(fill=tk.X, padx=10, pady=5)

        self.path_label = tk.Label(self.path_frame, text="검사 대상 폴더:", font=('Arial', 10))
        self.path_label.pack(side=tk.LEFT)

        self.path_entry = tk.Entry(self.path_frame, state="readonly", width=40)
        self.path_entry.pack(side=tk.LEFT, padx=(10, 5), fill=tk.X, expand=True)

        self.browse_btn = tk.Button(
            self.path_frame,
            text="폴더 찾기",
            command=self._browse_target
        )
        self.browse_btn.pack(side=tk.LEFT, padx=5)

        # 초기 설정
        self._refresh_templates()
        self._on_mode_changed()

    def _create_control_section(self, parent):
        """제어 섹션 생성"""
        control_frame = tk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        self.validate_btn = tk.Button(
            control_frame,
            text="검증 시작",
            command=self._start_validation,
            font=('Arial', 12, 'bold'),
            bg='#4CAF50',
            fg='white',
            padx=30,
            pady=10
        )
        self.validate_btn.pack(side=tk.LEFT)

        self.stop_btn = tk.Button(
            control_frame,
            text="검증 중단",
            command=self._stop_validation,
            font=('Arial', 12),
            bg='#f44336',
            fg='white',
            padx=30,
            pady=10,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=(10, 0))

        self.clear_btn = tk.Button(
            control_frame,
            text="로그 지우기",
            command=self._clear_log,
            font=('Arial', 10),
            padx=20,
            pady=8
        )
        self.clear_btn.pack(side=tk.RIGHT)

    def _create_progress_section(self, parent):
        """진행률 섹션 생성"""
        progress_frame = tk.LabelFrame(parent, text="진행 상황", font=('Arial', 12))
        progress_frame.pack(fill=tk.X, pady=(0, 10))

        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, padx=10, pady=10)

        self.progress_label = tk.Label(
            progress_frame,
            text="대기 중",
            font=('Arial', 10)
        )
        self.progress_label.pack(pady=(0, 5))

    def _create_log_section(self, parent):
        """로그 섹션 생성"""
        log_frame = tk.LabelFrame(parent, text="검증 로그", font=('Arial', 12))
        log_frame.pack(fill=tk.BOTH, expand=True)

        # 스크롤 가능한 텍스트 위젯
        text_frame = tk.Frame(log_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log_text = tk.Text(
            text_frame,
            height=15,
            font=('Consolas', 10),
            wrap=tk.WORD
        )

        scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=scrollbar.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_status_bar(self, parent):
        """상태바 생성"""
        self.status_label = tk.Label(
            parent,
            text="검증 도구가 준비되었습니다.",
            font=('Arial', 10),
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))

    def _on_mode_changed(self):
        """검사 방식 변경 이벤트"""
        mode = self.validation_mode.get()

        if mode == "file":
            self.path_label.config(text="검사 대상 파일:")
            self.browse_btn.config(text="파일 찾기")
        else:
            self.path_label.config(text="검사 대상 폴더:")
            self.browse_btn.config(text="폴더 찾기")

        self.target_path = ""
        self.path_entry.config(state="normal")
        self.path_entry.delete(0, tk.END)
        self.path_entry.config(state="readonly")

        self._update_validate_button_state()

    def _on_template_selected(self, event=None):
        """템플릿 선택 이벤트"""
        template_name = self.template_combo.get()
        if template_name:
            self.selected_template = self.template_service.get_template(template_name)
            self._update_validate_button_state()
            self._log(f"템플릿 선택: {template_name}")

    def _refresh_templates(self):
        """템플릿 목록 새로고침"""
        try:
            template_names = self.template_service.get_template_names()
            self.template_combo['values'] = template_names

            if template_names and not self.template_combo.get():
                self.template_combo.current(0)
                self._on_template_selected()

        except Exception as e:
            self._log(f"템플릿 목록 로드 실패: {str(e)}")

    def _browse_target(self):
        """대상 경로 선택"""
        mode = self.validation_mode.get()

        if mode == "file":
            path = filedialog.askopenfilename(
                title="PDF 파일 선택",
                filetypes=[("PDF files", "*.pdf")]
            )
        else:
            path = filedialog.askdirectory(title="PDF 폴더 선택")

        if path:
            self.target_path = path
            self.path_entry.config(state="normal")
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)
            self.path_entry.config(state="readonly")

            self._log(f"대상 선택: {path}")
            self._update_validate_button_state()

    def _update_validate_button_state(self):
        """검증 버튼 상태 업데이트"""
        can_validate = (
            self.selected_template is not None and
            bool(self.target_path) and
            not self.is_validating
        )

        self.validate_btn.config(state=tk.NORMAL if can_validate else tk.DISABLED)

    def _start_validation(self):
        """검증 시작"""
        if self.is_validating:
            return

        try:
            self.is_validating = True
            self._update_ui_for_validation_start()

            # 백그라운드 스레드에서 검증 실행
            self.current_thread = threading.Thread(
                target=self._run_validation_thread,
                daemon=True
            )
            self.current_thread.start()

        except Exception as e:
            self.is_validating = False
            self._update_ui_for_validation_end()
            messagebox.showerror("오류", f"검증 시작 실패: {str(e)}")

    def _stop_validation(self):
        """검증 중단"""
        if self.is_validating:
            self.is_validating = False
            self._log("검증 중단 요청됨...")

    def _run_validation_thread(self):
        """검증 스레드 실행"""
        try:
            mode = self.validation_mode.get()

            if mode == "file":
                self._validate_single_file()
            else:
                self._validate_folder()

        except Exception as e:
            self._log(f"검증 오류: {str(e)}")
        finally:
            # UI 업데이트는 메인 스레드에서
            self.current_window.after(0, self._update_ui_for_validation_end)

    def _validate_single_file(self):
        """단일 파일 검증"""
        self._log(f"파일 검증 시작: {Path(self.target_path).name}")

        # 문서 로드
        document = self.document_repository.load_document(self.target_path)
        if not document:
            self._log("❌ 문서 로드 실패")
            return

        # 검증 실행
        result = self.validation_service.validate_document(document, self.selected_template)

        # 결과 출력
        self._log("=" * 50)
        self._log(f"검증 완료: {result.get_summary()['success_rate']:.1f}% 성공")

        for roi_result in result.roi_results:
            status_icon = "✅" if roi_result.is_success else "❌"
            self._log(f"{status_icon} {roi_result.roi_name}: {roi_result.message}")

    def _validate_folder(self):
        """폴더 일괄 검증"""
        self._log(f"폴더 검증 시작: {self.target_path}")

        # PDF 파일 찾기
        pdf_files = self.document_repository.find_pdf_files(self.target_path)
        if not pdf_files:
            self._log("❌ PDF 파일을 찾을 수 없습니다")
            return

        self._log(f"총 {len(pdf_files)}개 PDF 파일 발견")

        # 진행률 설정
        self.current_window.after(0, lambda: self.progress_bar.config(maximum=len(pdf_files)))

        success_count = 0
        fail_count = 0

        for i, pdf_path in enumerate(pdf_files):
            if not self.is_validating:
                self._log("검증이 중단되었습니다")
                break

            filename = Path(pdf_path).name
            self._log(f"[{i+1}/{len(pdf_files)}] {filename} 검증 중...")

            try:
                # 문서 로드
                document = self.document_repository.load_document(pdf_path)
                if not document:
                    self._log(f"  ❌ {filename}: 문서 로드 실패")
                    fail_count += 1
                    continue

                # 검증 실행
                result = self.validation_service.validate_document(document, self.selected_template)

                if result.is_overall_success:
                    self._log(f"  ✅ {filename}: 검증 통과")
                    success_count += 1
                else:
                    self._log(f"  ❌ {filename}: {result.failure_count}개 항목 미흡")
                    fail_count += 1

            except Exception as e:
                self._log(f"  🔥 {filename}: 오류 - {str(e)}")
                fail_count += 1

            # 진행률 업데이트
            self.current_window.after(0, lambda: self.progress_bar.config(value=i+1))

        # 최종 결과
        self._log("=" * 50)
        self._log(f"일괄 검증 완료: 성공 {success_count}개, 실패 {fail_count}개")

    def _update_ui_for_validation_start(self):
        """검증 시작 시 UI 업데이트"""
        self.validate_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress_bar.config(value=0)
        self.progress_label.config(text="검증 진행 중...")
        self.status_label.config(text="검증 중...")

    def _update_ui_for_validation_end(self):
        """검증 완료 시 UI 업데이트"""
        self.is_validating = False
        self.validate_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress_label.config(text="검증 완료")
        self.status_label.config(text="검증이 완료되었습니다.")
        self._update_validate_button_state()

    def _clear_log(self):
        """로그 지우기"""
        self.log_text.delete('1.0', tk.END)

    def _log(self, message: str):
        """로그 메시지 추가"""
        if self.log_text:
            timestamp = TimeUtils.get_timestamp_filename()
            log_message = f"[{timestamp}] {message}\n"

            # 메인 스레드에서 실행되도록 보장
            if threading.current_thread() != threading.main_thread():
                self.current_window.after(0, lambda: self._add_log_message(log_message))
            else:
                self._add_log_message(log_message)

    def _add_log_message(self, message: str):
        """로그 메시지 추가 (메인 스레드에서 실행)"""
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        self.current_window.update_idletasks()

    def cleanup(self):
        """리소스 정리"""
        # 진행 중인 검증 중단
        self.is_validating = False

        # 스레드 종료 대기
        if self.current_thread and self.current_thread.is_alive():
            self.current_thread.join(timeout=1.0)

        # 윈도우 정리
        if self.current_window and self.current_window.winfo_exists():
            self.current_window.destroy()
        self.current_window = None
