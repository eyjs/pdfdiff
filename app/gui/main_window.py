"""
Main Window
메인 애플리케이션 윈도우 (통합 런처)
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sys
from pathlib import Path

from app.controllers.template_controller import TemplateController
from app.controllers.validation_controller import ValidationController
from infrastructure.config.settings import settings
from shared.constants import APPLICATION_NAME, VERSION


class MainWindow:
    """메인 윈도우 - 통합 런처"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.setup_window()
        self.setup_ui()
        self.center_window()

        # 컨트롤러 인스턴스 (지연 로드)
        self._template_controller = None
        self._validation_controller = None

    def setup_window(self):
        """윈도우 기본 설정"""
        self.root.title(f"{APPLICATION_NAME} v{VERSION}")
        self.root.geometry(f"{settings.ui.window_width}x{settings.ui.window_height}")
        self.root.minsize(settings.ui.min_window_width, settings.ui.min_window_height)

        # 윈도우 아이콘 설정 (옵션)
        try:
            icon_path = Path("resources") / "icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except:
            pass

        # 종료 이벤트 처리
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        """UI 구성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 제목 섹션
        self.create_title_section(main_frame)

        # 메뉴 섹션
        self.create_menu_section(main_frame)

        # 정보 섹션
        self.create_info_section(main_frame)

    def create_title_section(self, parent):
        """제목 섹션 생성"""
        title_frame = ttk.Frame(parent)
        title_frame.pack(pady=(0, 30))

        # 메인 타이틀
        title_label = ttk.Label(
            title_frame,
            text="보험서류 검증 시스템",
            font=('Arial', 24, 'bold')
        )
        title_label.pack()

        # 버전 정보
        version_label = ttk.Label(
            title_frame,
            text=f"Version {VERSION}",
            font=('Arial', 12)
        )
        version_label.pack(pady=(5, 0))

        # 구분선
        separator = ttk.Separator(parent, orient='horizontal')
        separator.pack(fill=tk.X, pady=(20, 30))

    def create_menu_section(self, parent):
        """메뉴 섹션 생성"""
        menu_frame = ttk.Frame(parent)
        menu_frame.pack(fill=tk.BOTH, expand=True)

        # 1단계: 템플릿 관리
        step1_frame = ttk.LabelFrame(menu_frame, text="1단계: 템플릿 관리", padding="15")
        step1_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(
            step1_frame,
            text="PDF 문서에서 검증할 영역(ROI)을 설정하고 템플릿을 생성합니다.",
            font=('Arial', 10)
        ).pack(anchor=tk.W, pady=(0, 10))

        template_btn = ttk.Button(
            step1_frame,
            text="📝 템플릿 생성 및 편집",
            command=self.open_template_manager,
            style="Accent.TButton"
        )
        template_btn.pack(fill=tk.X)

        # 2단계: 서류 검증
        step2_frame = ttk.LabelFrame(menu_frame, text="2단계: 서류 검증", padding="15")
        step2_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(
            step2_frame,
            text="생성된 템플릿을 사용하여 PDF 서류의 작성 완료 여부를 자동으로 검증합니다.",
            font=('Arial', 10)
        ).pack(anchor=tk.W, pady=(0, 10))

        validation_btn = ttk.Button(
            step2_frame,
            text="🔍 서류 검증 실행",
            command=self.open_validation_tool,
            style="Accent.TButton"
        )
        validation_btn.pack(fill=tk.X)

        # 부가 기능
        extra_frame = ttk.LabelFrame(menu_frame, text="부가 기능", padding="15")
        extra_frame.pack(fill=tk.X)

        # 설정 버튼
        settings_btn = ttk.Button(
            extra_frame,
            text="⚙️ 설정",
            command=self.open_settings
        )
        settings_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 도움말 버튼
        help_btn = ttk.Button(
            extra_frame,
            text="❓ 도움말",
            command=self.show_help
        )
        help_btn.pack(side=tk.LEFT)

        # 정보 버튼
        info_btn = ttk.Button(
            extra_frame,
            text="ℹ️ 정보",
            command=self.show_about
        )
        info_btn.pack(side=tk.RIGHT)

    def create_info_section(self, parent):
        """정보 섹션 생성"""
        info_frame = ttk.Frame(parent)
        info_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(30, 0))

        # 구분선
        separator = ttk.Separator(info_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=(0, 10))

        # 시스템 상태
        status_frame = ttk.Frame(info_frame)
        status_frame.pack(fill=tk.X)

        # Tesseract 상태
        tesseract_status = "✅ OCR 엔진 준비됨" if settings.tesseract.is_configured() else "❌ OCR 엔진 미설정"
        ttk.Label(status_frame, text=tesseract_status, font=('Arial', 9)).pack(side=tk.LEFT)

        # 저작권
        ttk.Label(
            status_frame,
            text="© 2025 PDF Validator System",
            font=('Arial', 9)
        ).pack(side=tk.RIGHT)

    def center_window(self):
        """윈도우를 화면 중앙에 배치"""
        self.root.update_idletasks()

        # 현재 윈도우 크기
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()

        # 화면 크기
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # 중앙 위치 계산
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        # 윈도우 위치 설정
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    @property
    def template_controller(self) -> TemplateController:
        """템플릿 컨트롤러 (지연 로드)"""
        if self._template_controller is None:
            self._template_controller = TemplateController()
        return self._template_controller

    @property
    def validation_controller(self) -> ValidationController:
        """검증 컨트롤러 (지연 로드)"""
        if self._validation_controller is None:
            self._validation_controller = ValidationController()
        return self._validation_controller

    def open_template_manager(self):
        """템플릿 관리자 열기"""
        try:
            self.root.withdraw()  # 메인 윈도우 숨기기
            self.template_controller.show_template_manager(
                parent=self.root,
                on_close=self.on_child_window_close
            )
        except Exception as e:
            self.on_child_window_close()
            messagebox.showerror("오류", f"템플릿 관리자를 열 수 없습니다:\n{str(e)}")

    def open_validation_tool(self):
        """검증 도구 열기"""
        try:
            self.root.withdraw()  # 메인 윈도우 숨기기
            self.validation_controller.show_validation_tool(
                parent=self.root,
                on_close=self.on_child_window_close
            )
        except Exception as e:
            self.on_child_window_close()
            messagebox.showerror("오류", f"검증 도구를 열 수 없습니다:\n{str(e)}")

    def open_settings(self):
        """설정 창 열기"""
        try:
            self.show_settings_dialog()
        except Exception as e:
            messagebox.showerror("오류", f"설정을 열 수 없습니다:\n{str(e)}")

    def show_settings_dialog(self):
        """설정 다이얼로그 표시"""
        dialog = tk.Toplevel(self.root)
        dialog.title("설정")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()

        # 중앙 배치
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 500) // 2
        y = (dialog.winfo_screenheight() - 400) // 2
        dialog.geometry(f"500x400+{x}+{y}")

        # 설정 내용
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 일반 설정 탭
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="일반")

        ttk.Label(general_frame, text="UI 설정", font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        ttk.Checkbutton(general_frame, text="창 크기 기억하기").pack(anchor=tk.W, padx=20)
        ttk.Checkbutton(general_frame, text="디버그 모드").pack(anchor=tk.W, padx=20)

        # OCR 설정 탭
        ocr_frame = ttk.Frame(notebook)
        notebook.add(ocr_frame, text="OCR")

        ttk.Label(ocr_frame, text="Tesseract 설정", font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(10, 5))

        # OCR 상태 표시
        status_text = "✅ 정상 설정됨" if settings.tesseract.is_configured() else "❌ 설정 필요"
        ttk.Label(ocr_frame, text=f"상태: {status_text}").pack(anchor=tk.W, padx=20, pady=5)

        if settings.tesseract.executable_path:
            ttk.Label(ocr_frame, text=f"실행 파일: {settings.tesseract.executable_path}").pack(anchor=tk.W, padx=20)

        if settings.tesseract.tessdata_path:
            ttk.Label(ocr_frame, text=f"언어팩: {settings.tesseract.tessdata_path}").pack(anchor=tk.W, padx=20)

        # 버튼 프레임
        button_frame = ttk.Frame(dialog)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="닫기", command=dialog.destroy).pack(side=tk.RIGHT)

    def show_help(self):
        """도움말 표시"""
        help_text = """
PDF 검증 시스템 사용법

1단계: 템플릿 생성
- 원본 PDF를 열어 검증할 영역(ROI)을 지정합니다
- 드래그로 영역을 선택하고 검증 방식을 설정합니다
- 템플릿을 저장합니다

2단계: 서류 검증
- 저장된 템플릿을 선택합니다
- 검증할 PDF 파일 또는 폴더를 선택합니다
- 검증을 실행하면 자동으로 결과가 생성됩니다

검증 방식:
- OCR: 텍스트 내용을 확인합니다
- Contour: 그림이나 서명 등을 확인합니다

문의사항이 있으시면 개발팀에 연락주세요.
        """

        messagebox.showinfo("도움말", help_text.strip())

    def show_about(self):
        """정보 창 표시"""
        about_text = f"""
{APPLICATION_NAME} v{VERSION}

PDF 문서 자동 검증 시스템

주요 기능:
• 템플릿 기반 ROI 검증
• OCR 및 컨퓨터 비전 검증
• 일괄 처리 지원
• 상세한 디버깅 정보

기술 스택:
• Python + Tkinter (UI)
• PyMuPDF (PDF 처리)
• OpenCV (컴퓨터 비전)
• Tesseract (OCR)

© 2025 All Rights Reserved
        """

        messagebox.showinfo("정보", about_text.strip())

    def on_child_window_close(self):
        """자식 윈도우 닫힘 이벤트 처리"""
        self.root.deiconify()  # 메인 윈도우 다시 표시
        self.root.lift()  # 메인 윈도우를 최상단으로
        self.root.focus_force()  # 메인 윈도우에 포커스

    def on_closing(self):
        """애플리케이션 종료 처리"""
        try:
            # 설정 저장
            if settings.ui.remember_window_size:
                settings.ui.window_width = self.root.winfo_width()
                settings.ui.window_height = self.root.winfo_height()
                settings.save()

            # 리소스 정리
            if self._template_controller:
                self._template_controller.cleanup()

            if self._validation_controller:
                self._validation_controller.cleanup()

        except Exception as e:
            print(f"종료 처리 중 오류: {e}")
        finally:
            self.root.quit()
            self.root.destroy()
