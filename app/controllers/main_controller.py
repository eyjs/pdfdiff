import tkinter as tk

# Infrastructure
from infrastructure.repositories.json_template_repository import JsonTemplateRepository
from infrastructure.services.vision_service import VisionService

# Domain
from domain.services.template_service import TemplateService
from domain.repositories.template_repository import TemplateRepository # Interface for type hinting

# Application
from app.controllers.template_controller import TemplateController

# Presentation
from app.gui.template_editor_window import TemplateEditorWindow

class MainController:
    def __init__(self, root):
        self.root = root

    def open_template_editor(self):
        """
        템플릿 편집기 창을 생성하고 실행합니다.
        의존성 주입(DI)이 이 메서드 내에서 이루어집니다.
        """
        editor_window = tk.Toplevel(self.root)

        # 1. Infrastructure Layer 객체 생성
        json_repository = JsonTemplateRepository()
        vision_service = VisionService()

        # 2. Domain Layer 객체 생성
        template_service = TemplateService(
            template_repository=json_repository,
            vision_service=vision_service
        )

        # 3. Application & Presentation Layer 객체 생성
        controller = TemplateController(view=None, template_service=template_service)
        view = TemplateEditorWindow(editor_window, controller)
        controller.view = view

    def open_validation_tool(self):
        """
        검증 도구 창을 생성하고 실행합니다. (현재는 플레이스홀더)
        """
        # 향후 검증 도구 관련 MVC 구성요소들이 이곳에서 조립됩니다.
        print("검증 도구 실행 기능은 아직 구현되지 않았습니다.")
        info_window = tk.Toplevel(self.root)
        info_window.title("알림")
        info_window.geometry("300x100")
        label = tk.Label(info_window, text="검증 도구 기능은 현재 개발 중입니다.")
        label.pack(pady=20, padx=20)
