import tkinter as tk
from tkinter import messagebox
import logging

# Infrastructure Layer - 외부 기술 및 데이터 구현체
from infrastructure.repositories.json_template_repository import JsonTemplateRepository
from infrastructure.services.anchor_finding_service import AnchorFindingService
from infrastructure.repositories.fitz_document_repository import FitzDocumentRepository

# Domain Layer - 핵심 비즈니스 로직 및 규칙
from domain.services.template_service import TemplateService
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
        self.anchor_finding_service = None

        try:
            # 공유 리소스(리포지토리, 서비스)를 애플리케이션 시작 시 한 번만 생성합니다.
            self.template_repository = JsonTemplateRepository()
            self.anchor_finding_service = AnchorFindingService()
            
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
        if not self.template_repository: return

        editor_window = tk.Toplevel(self.root)
        editor_window.transient(self.root)
        editor_window.grab_set()

        # --- 의존성 주입 (생성된 공유 객체 사용) ---
        template_service = TemplateService(
            template_repository=self.template_repository,
            anchor_finding_service=self.anchor_finding_service
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
        if not self.template_repository:
            messagebox.showwarning("Warning", "애플리케이션이 아직 준비되지 않았습니다.")
            return

        validator_window = tk.Toplevel(self.root)
        validator_window.transient(self.root)
        validator_window.grab_set()

        # --- 의존성 주입 (ValidationController에 책임 위임) ---
        doc_repo = FitzDocumentRepository()
        template_service = TemplateService(self.template_repository, self.anchor_finding_service)

        # ValidationController가 View와 핵심 서비스를 받아 자체적으로 검증 흐름을 관리
        controller = ValidationController(
            view=None, 
            doc_repo=doc_repo,
            template_service=template_service
        )
        view = ValidationWindow(validator_window, controller)
        controller.view = view
        controller.initialize_view()