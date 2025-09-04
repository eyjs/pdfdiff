import tkinter as tk
from tkinter import ttk

class MainWindow:
    """
    애플리케이션의 메인 메뉴 UI를 담당하는 클래스.
    역할:
    - '템플릿 편집기'와 '검증 도구'를 실행하는 버튼을 사용자에게 제공.
    - 사용자의 버튼 클릭 이벤트를 MainController에 전달.
    """
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        self.root.title("PDF 검증 시스템 v3.0")

        # 창을 화면 중앙에 위치시키기
        window_width = 400
        window_height = 250
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width / 2)
        center_y = int(screen_height/2 - window_height / 2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        self.root.resizable(False, False)

        self._setup_ui()

    def _setup_ui(self):
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(expand=True, fill=tk.BOTH)

        style = ttk.Style()
        style.configure("TButton", font=("Helvetica", 12), padding=10)

        title_label = ttk.Label(
            main_frame,
            text="PDF 문서 검증 자동화",
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=(0, 20))

        template_button = ttk.Button(
            main_frame,
            text="템플릿 생성 및 편집",
            command=self.controller.open_template_editor,
            style="TButton"
        )
        template_button.pack(fill=tk.X, pady=5)

        validator_button = ttk.Button(
            main_frame,
            text="검증 도구 실행",
            command=self.controller.open_validation_tool,
            style="TButton",
            state=tk.NORMAL # 버튼 활성화
        )
        validator_button.pack(fill=tk.X, pady=5)

