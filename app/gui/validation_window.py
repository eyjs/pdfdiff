import tkinter as tk
from tkinter import ttk, scrolledtext
from PIL import Image, ImageTk

class ValidationWindow:
    """
    검증 도구의 사용자 인터페이스(View)를 담당하는 클래스.
    역할:
    - UI 위젯(버튼, 캔버스, 로그 창 등)을 생성하고 배치.
    - Controller로부터 받은 데이터(이미지, 로그 메시지)를 화면에 표시.
    - 사용자 입력(버튼 클릭, 콤보박스 선택 등)을 감지하여 Controller에 전달.
    """
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        self.root.title("2단계: 문서 검증 도구 (Clean Architecture)")

        # 창 크기 및 화면 중앙 위치 설정
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        width = min(1600, int(screen_width * 0.9))
        height = min(1000, int(screen_height * 0.9))
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(1200, 800)

        # UI 상태를 저장하는 변수 (Tkinter PhotoImage 객체 등)
        self.left_photo = None
        self.right_photo = None

        self._setup_ui()
        self.controller.load_templates() # View가 준비되면 컨트롤러에게 템플릿 로드를 요청

    def _setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.rowconfigure(2, weight=1)
        main_frame.columnconfigure(0, weight=1)

        # --- 1. Control Frame: 설정 영역 ---
        control_frame = ttk.LabelFrame(main_frame, text="검증 설정", padding="10")
        control_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        control_frame.columnconfigure(1, weight=1)

        # 검사 방식 선택 (파일/폴더)
        ttk.Label(control_frame, text="검사 방식:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.mode_var = tk.StringVar(value="파일")
        mode_frame = ttk.Frame(control_frame)
        mode_frame.grid(row=0, column=1, columnspan=2, sticky=tk.W)
        ttk.Radiobutton(mode_frame, text="파일 기준 검사", variable=self.mode_var, value="파일", command=self._on_mode_switch).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="폴더 기준 검사", variable=self.mode_var, value="폴더", command=self._on_mode_switch).pack(side=tk.LEFT, padx=5)

        # 템플릿 선택
        ttk.Label(control_frame, text="템플릿 선택:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.template_var = tk.StringVar()
        self.template_combo = ttk.Combobox(control_frame, textvariable=self.template_var, state="readonly", width=40)
        self.template_combo.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        self.template_combo.bind('<<ComboboxSelected>>', lambda e: self.controller.on_template_selected())
        ttk.Button(control_frame, text="새로고침", command=self.controller.load_templates).grid(row=1, column=2, padx=5, pady=5)

        # 검사 대상 경로 선택
        self.target_label = ttk.Label(control_frame, text="검사 대상 파일:")
        self.target_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        self.path_var = tk.StringVar()
        ttk.Entry(control_frame, textvariable=self.path_var, state="readonly").grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        self.browse_btn = ttk.Button(control_frame, text="파일 찾기", command=self.controller.browse_target)
        self.browse_btn.grid(row=2, column=2, padx=5, pady=5)

        # --- 2. Action Frame: 실행 버튼 ---
        self.validate_btn = ttk.Button(main_frame, text="검사 실행", command=self.controller.run_validation, state=tk.DISABLED)
        self.validate_btn.grid(row=1, column=0, pady=10)

        # --- 3. Viewer Frame: PDF 비교 뷰어 ---
        self.viewer_frame = ttk.Frame(main_frame)
        self.viewer_frame.grid(row=2, column=0, sticky="nsew")
        self.viewer_frame.rowconfigure(0, weight=1)
        self.viewer_frame.columnconfigure(0, weight=1)

        viewer_pane = ttk.PanedWindow(self.viewer_frame, orient=tk.HORIZONTAL)
        viewer_pane.grid(row=0, column=0, sticky="nsew")

        left_viewer = ttk.LabelFrame(viewer_pane, text="원본 템플릿", padding=5)
        self.left_canvas = tk.Canvas(left_viewer, bg="lightgrey")
        self.left_canvas.pack(fill=tk.BOTH, expand=True)
        viewer_pane.add(left_viewer, weight=1)

        right_viewer = ttk.LabelFrame(viewer_pane, text="검증된 문서 (주석)", padding=5)
        self.right_canvas = tk.Canvas(right_viewer, bg="lightgrey")
        self.right_canvas.pack(fill=tk.BOTH, expand=True)
        viewer_pane.add(right_viewer, weight=1)

        # 뷰어 페이지 네비게이션
        nav_frame = ttk.Frame(self.viewer_frame)
        nav_frame.grid(row=1, column=0, sticky="ew", pady=5)
        self.prev_page_btn = ttk.Button(nav_frame, text="◀ 이전", command=self.controller.prev_page, state=tk.DISABLED)
        self.prev_page_btn.pack(side=tk.LEFT)
        self.page_label = ttk.Label(nav_frame, text="페이지: 0/0")
        self.page_label.pack(side=tk.LEFT, padx=10)
        self.next_page_btn = ttk.Button(nav_frame, text="다음 ▶", command=self.controller.next_page, state=tk.DISABLED)
        self.next_page_btn.pack(side=tk.LEFT)

        # --- 4. Log Frame: 진행 상황 로그 ---
        log_frame = ttk.LabelFrame(main_frame, text="진행 상황 로그", padding=5, height=150)
        log_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=5)
        log_frame.pack_propagate(False) # 프레임 크기가 내용물에 따라 변하지 않도록 고정
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(0, 3))
        self.progress_bar = ttk.Progressbar(log_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X)

    def _on_mode_switch(self):
        """사용자가 '파일/폴더' 모드를 변경했을 때 호출되는 이벤트 핸들러."""
        mode = self.mode_var.get()
        self.controller.switch_mode(mode) # 컨트롤러에 모드 변경을 알림
        # 모드에 따라 UI 텍스트 변경
        if mode == "파일":
            self.target_label.config(text="검사 대상 파일:")
            self.browse_btn.config(text="파일 찾기")
            self.viewer_frame.grid() # 파일 모드에서는 뷰어 보이기
        else: # 폴더 모드
            self.target_label.config(text="검사 대상 폴더:")
            self.browse_btn.config(text="폴더 찾기")
            self.viewer_frame.grid_remove() # 폴더 모드에서는 뷰어 숨기기

    # --- 아래는 Controller가 View를 제어하기 위해 호출하는 메서드들 ---

    def update_path(self, path):
        """선택된 파일/폴더 경로를 화면에 업데이트합니다."""
        self.path_var.set(path)

    def update_button_state(self, is_ready):
        """'검사 실행' 버튼의 활성화/비활성화 상태를 업데이트합니다."""
        self.validate_btn.config(state=tk.NORMAL if is_ready else tk.DISABLED)

    def log(self, message):
        """로그 창에 메시지를 추가합니다."""
        # Tkinter는 다른 스레드에서 UI를 직접 업데이트할 수 없으므로,
        # after를 사용하여 메인 스레드에서 실행되도록 예약할 수 있습니다.
        # 여기서는 Controller가 메인 스레드에서 호출되므로 직접 업데이트합니다.
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END) # 스크롤을 항상 맨 아래로 이동
        self.root.update_idletasks() # UI 즉시 갱신

    def clear_log(self):
        """로그 창의 모든 내용을 지웁니다."""
        self.log_text.delete('1.0', tk.END)

    def update_progress(self, value, maximum):
        """진행 상태 바를 업데이트합니다."""
        self.progress_bar['maximum'] = maximum
        self.progress_bar['value'] = value

    def update_viewer(self, original_img, annotated_img, page_num, total_pages):
        """원본/결과 PDF 이미지를 뷰어 캔버스에 업데이트합니다."""
        if original_img:
            self.left_photo = ImageTk.PhotoImage(original_img)
            self.left_canvas.delete("all")
            self.left_canvas.create_image(0, 0, anchor=tk.NW, image=self.left_photo)

        if annotated_img:
            self.right_photo = ImageTk.PhotoImage(annotated_img)
            self.right_canvas.delete("all")
            self.right_canvas.create_image(0, 0, anchor=tk.NW, image=self.right_photo)

        # 네비게이션 UI 업데이트
        self.page_label.config(text=f"페이지: {page_num + 1}/{total_pages}")
        self.prev_page_btn.config(state=tk.NORMAL if page_num > 0 else tk.DISABLED)
        self.next_page_btn.config(state=tk.NORMAL if page_num < total_pages - 1 else tk.DISABLED)

