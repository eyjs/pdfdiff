import tkinter as tk

# Infrastructure Layer - 외부 기술 및 데이터 구현체
from infrastructure.repositories.json_template_repository import JsonTemplateRepository
from infrastructure.services.vision_service import VisionService
from infrastructure.repositories.file_document_repository import FileDocumentRepository
from infrastructure.services.validation_vision_service import ValidationVisionService

# Domain Layer - 핵심 비즈니스 로직 및 규칙
from domain.services.template_service import TemplateService
from domain.services.validation_service import ValidationService

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

    def open_template_editor(self):
        """
        '템플릿 생성 및 편집' 기능을 위한 새로운 창을 열고,
        해당 기능에 필요한 모든 객체를 생성하여 주입(Dependency Injection)합니다.
        """
        # 1. 새 Toplevel 창 생성
        editor_window = tk.Toplevel(self.root)

        # --- 의존성 주입 (Template Editor에 필요한 객체들 조립) ---
        # 2. Infrastructure Layer 객체 생성 (외부 기술 구현체)
        json_repository = JsonTemplateRepository()
        vision_service = VisionService()

        # 3. Domain Layer 객체 생성 (핵심 비즈니스 로직)
        template_service = TemplateService(
            template_repository=json_repository,
            vision_service=vision_service
        )

        # 4. Application & Presentation Layer 객체 생성
        controller = TemplateController(view=None, template_service=template_service)
        view = TemplateEditorWindow(editor_window, controller)

        # 5. View와 Controller를 상호 연결
        controller.view = view

        # 6. View가 완전히 준비된 후, Controller의 View 관련 초기화 로직 실행
        controller.initialize_view()

    def open_validation_tool(self):
        """
        '검증 도구 실행' 기능을 위한 새로운 창을 열고,
        해당 기능에 필요한 모든 객체를 생성하여 주입합니다.
        """
        # 1. 새 Toplevel 창 생성
        validator_window = tk.Toplevel(self.root)

        # --- 의존성 주입 (Validation Tool에 필요한 객체들 조립) ---
        # 2. Infrastructure Layer 객체 생성
        doc_repo = FileDocumentRepository()
        validation_vision_service = ValidationVisionService()
        template_repo = JsonTemplateRepository()

        # 3. Domain Layer 객체 생성
        template_service = TemplateService(template_repo, vision_service=None)
        validation_service = ValidationService(doc_repo, validation_vision_service)

        # 4. Application & Presentation Layer 객체 생성
        controller = ValidationController(
            view=None,
            validation_service=validation_service,
            template_service=template_service
        )
        view = ValidationWindow(validator_window, controller)

        # 5. View와 Controller를 상호 연결
        controller.view = view

        # 6. View가 완전히 준비된 후, Controller의 View 관련 초기화 로직 실행
        controller.initialize_view()

