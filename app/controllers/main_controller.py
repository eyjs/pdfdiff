import tkinter as tk
from tkinter import messagebox

# Infrastructure Layer - 외부 기술 및 데이터 구현체
from infrastructure.repositories.json_template_repository import JsonTemplateRepository
from infrastructure.services.vision_service import VisionService
from infrastructure.repositories.fitz_document_repository import FitzDocumentRepository
from infrastructure.services.validation_vision_service import ValidationVisionService
from infrastructure.services.tesseract_ocr_service import TesseractOcrService # OCR 서비스 구현체 추가

# Domain Layer - 핵심 비즈니스 로직 및 규칙
from domain.services.template_service import TemplateService
from domain.services.validation_service import ValidationService
from shared.exceptions import DataIntegrityError

# Application Layer - 이 파일 자신
from app.controllers.template_controller import TemplateController
from app.controllers.validation_controller import ValidationController

# Presentation Layer - 사용자 인터페이스
from app.gui.template_editor_window import TemplateEditorWindow
from app.gui.validation_window import ValidationWindow

class MainController:
    """
    애플리케이션의 최상위 컨트롤러.
    메인 윈도우의 이벤트를 받아 각 기능 모듈을 초기화하고 실행하는 역할을 담당.
    """
    def __init__(self, root):
        self.root = root
        self.template_repository = None
        self.vision_service = None
        self.ocr_service = None # OCR 서비스 멤버 변수 추가

        try:
            # 공유 리소스(리포지토리, 서비스)를 애플리케이션 시작 시 한 번만 생성합니다.
            self.template_repository = JsonTemplateRepository()
            self.vision_service = VisionService()
            self.ocr_service = TesseractOcrService() # Tesseract OCR 서비스 생성
        except DataIntegrityError as e:
            messagebox.showerror(
                "Application Start Error",
                f"Failed to load template data, the application will now close.Details: {e}"
            )
            self.root.destroy()

    def open_template_editor(self):
        """
        '템플릿 생성 및 편집' 기능을 위한 새로운 창을 열고,
        해당 기능에 필요한 모든 객체를 생성하여 주입(Dependency Injection)합니다.
        """
        if not self.template_repository: return # 초기화 실패 시 실행 방지

        editor_window = tk.Toplevel(self.root)
        editor_window.transient(self.root)
        editor_window.grab_set()

        # --- 의존성 주입 (생성된 공유 객체 사용) ---
        template_service = TemplateService(
            template_repository=self.template_repository,
            vision_service=self.vision_service
        )
        controller = TemplateController(view=None, template_service=template_service)
        view = TemplateEditorWindow(editor_window, controller)
        controller.view = view
        controller.initialize_view()

    def open_validation_tool(self):
        """
        '검증 도구 실행' 기능을 위한 새로운 창을 열고,
        해당 기능에 필요한 모든 객체를 생성하여 주입합니다.
        """
        if not self.template_repository: return # 초기화 실패 시 실행 방지

        validator_window = tk.Toplevel(self.root)
        validator_window.transient(self.root)
        validator_window.grab_set()

        # --- 의존성 주입 (생성된 공유 객체 사용) ---
        doc_repo = FitzDocumentRepository()
        # ValidationVisionService 생성 시, OCR 서비스 주입
        validation_vision_service = ValidationVisionService(ocr_service=self.ocr_service)

        template_service = TemplateService(self.template_repository, self.vision_service)
        validation_service = ValidationService(doc_repo, validation_vision_service)

        controller = ValidationController(
            view=None,
            validation_service=validation_service,
            template_service=template_service
        )
        view = ValidationWindow(validator_window, controller)
        controller.view = view
        controller.initialize_view()

