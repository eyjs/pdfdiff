import tkinter as tk
from tkinter import ttk, messagebox
from shared.settings import settings

class MainWindow:
    """
    애플리케이션의 메인 메뉴 UI를 담당하는 클래스.
    역할:
    - '템플릿 편집기'와 '검증 도구'를 실행하는 버튼을 사용자에게 제공.
    - API 키 설정을 관리하는 UI 제공.
    - 사용자의 버튼 클릭 이벤트를 MainController에 전달.
    """
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        self.root.title("PDF 검증 시스템 v1.0")

        # 창을 화면 중앙에 위치시키기
        window_width = 400
        window_height = 350  # 높이 증가
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width / 2)
        center_y = int(screen_height/2 - window_height / 2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        self.root.resizable(False, False)

        # API 키 저장을 위한 변수
        self.clova_api_key = tk.StringVar(value=settings.clova.secret_key)

        self._setup_ui()

    def _save_api_keys(self):
        """UI에 입력된 API 키를 설정에 저장합니다."""
        settings.clova.secret_key = self.clova_api_key.get()
        try:
            settings.save()
            messagebox.showinfo("저장 완료", "API 키가 성공적으로 저장되었습니다.")
        except Exception as e:
            messagebox.showerror("저장 실패", f"API 키를 저장하는 중 오류가 발생했습니다:\n{e}")

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
        title_label.pack(pady=(0, 15))

        # --- 메인 기능 버튼 ---
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
            state=tk.NORMAL
        )
        validator_button.pack(fill=tk.X, pady=5)

        # --- API 키 설정 ---
        api_settings_frame = ttk.LabelFrame(main_frame, text="API 키 설정", padding=10)
        api_settings_frame.pack(fill=tk.X, pady=(15, 5), expand=True)

        clova_label = ttk.Label(api_settings_frame, text="Clova Secret Key:")
        clova_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        clova_entry = ttk.Entry(api_settings_frame, textvariable=self.clova_api_key, width=30)
        clova_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

        save_button = ttk.Button(
            api_settings_frame,
            text="저장",
            command=self._save_api_keys
        )
        save_button.grid(row=1, column=0, columnspan=2, pady=(10, 0))

        api_settings_frame.columnconfigure(1, weight=1)
