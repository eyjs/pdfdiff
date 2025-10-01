import tkinter as tk
import os
from tkinter import ttk, scrolledtext, messagebox
from PIL import Image, ImageTk

class ValidationWindow:
    """
    검증 도구의 사용자 인터페이스(View)를 담당하는 클래스.
    """
    def __init__(self, root, controller, main_controller):
        self.root = root
        self.controller = controller
        self.main_controller = main_controller
        self.root.title("2단계: 문서 검증 도구")

        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        width = min(1600, int(screen_width * 0.9))
        height = min(1000, int(screen_height * 0.9))
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(1200, 800)

        self.left_photo = None
        self.right_photo = None

        # OCR 엔진 선택을 위한 변수
        self.ocr_engine_var = tk.StringVar(value='Tesseract')

        self._setup_ui()

    def _with_unfocus(self, func):
        def wrapper(*args, **kwargs):
            if func:
                func(*args, **kwargs)
            self.root.focus_set()
        return wrapper

    def _setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.rowconfigure(2, weight=1)
        main_frame.columnconfigure(0, weight=1)

        # --- 1. Control Frame ---
        control_frame = ttk.LabelFrame(main_frame, text="검증 설정", padding="5")
        control_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=2)
        control_frame.columnconfigure(1, weight=1)

        ttk.Label(control_frame, text="검사 방식:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.mode_var = tk.StringVar(value="파일")
        mode_frame = ttk.Frame(control_frame)
        mode_frame.grid(row=0, column=1, columnspan=3, sticky=tk.W)
        ttk.Radiobutton(mode_frame, text="파일 기준 검사", variable=self.mode_var, value="파일", command=self._with_unfocus(self._on_mode_switch)).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="폴더 기준 검사", variable=self.mode_var, value="폴더", command=self._with_unfocus(self._on_mode_switch)).pack(side=tk.LEFT, padx=5)

        ttk.Label(control_frame, text="템플릿 선택:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.template_var = tk.StringVar()
        self.template_combo = ttk.Combobox(control_frame, textvariable=self.template_var, state="readonly", width=40)
        self.template_combo.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        self.template_combo.bind('<<ComboboxSelected>>', self._with_unfocus(self.controller.on_template_selected))

        template_btn_frame = ttk.Frame(control_frame)
        template_btn_frame.grid(row=1, column=2, sticky=tk.W)
        ttk.Button(template_btn_frame, text="새로고침", command=self._with_unfocus(self.controller.load_templates)).pack(side=tk.LEFT, padx=5)
        ttk.Button(template_btn_frame, text="템플릿 관리", command=self._with_unfocus(self.main_controller.open_template_editor)).pack(side=tk.LEFT)

        # OCR 엔진 선택 드롭다운 추가
        ttk.Label(control_frame, text="OCR 엔진:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.ocr_combobox = ttk.Combobox(
            control_frame,
            textvariable=self.ocr_engine_var,
            values=['Tesseract', 'EasyOCR', 'Clova'],
            state='readonly'
        )
        self.ocr_combobox.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=2)

        self.target_label = ttk.Label(control_frame, text="검사 대상 파일:")
        self.target_label.grid(row=3, column=0, sticky=tk.W, pady=2)
        self.path_var = tk.StringVar()
        ttk.Entry(control_frame, textvariable=self.path_var, state="readonly").grid(row=3, column=1, sticky=tk.EW, padx=5, pady=2)
        self.browse_btn = ttk.Button(control_frame, text="파일 찾기", command=self._with_unfocus(self.controller.browse_target))
        self.browse_btn.grid(row=3, column=2, padx=5, pady=2)

        # --- 2. Action Frame ---
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=1, column=0, pady=5)

        self.validate_btn = ttk.Button(action_frame, text="검사 실행", command=self._with_unfocus(self.controller.run_validation), state=tk.DISABLED)
        self.validate_btn.pack(side=tk.LEFT, padx=10)

        self.save_btn = ttk.Button(action_frame, text="결과 PDF 저장", command=self._with_unfocus(self.controller.save_result_pdf), state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT, padx=10)

        # --- 3. Main Content Frame (Viewer + Log) ---
        content_pane = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        content_pane.grid(row=2, column=0, sticky="nsew")

        # --- 3a. Viewer Frame ---
        self.viewer_frame = ttk.Frame(content_pane)
        self.viewer_frame.rowconfigure(1, weight=1) # Canvas row should expand
        self.viewer_frame.columnconfigure(0, weight=1)
        content_pane.add(self.viewer_frame, weight=3)

        # Navigation controls at the top
        nav_frame = ttk.Frame(self.viewer_frame)
        nav_frame.grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.prev_page_btn = ttk.Button(nav_frame, text="◀ 이전", command=self._with_unfocus(self.controller.prev_page), state=tk.DISABLED)
        self.prev_page_btn.pack(side=tk.LEFT)
        self.page_label = ttk.Label(nav_frame, text="페이지: 0/0")
        self.page_label.pack(side=tk.LEFT, padx=10)
        self.next_page_btn = ttk.Button(nav_frame, text="다음 ▶", command=self._with_unfocus(self.controller.next_page), state=tk.DISABLED)
        self.next_page_btn.pack(side=tk.LEFT)
        ttk.Button(nav_frame, text="-", command=self._with_unfocus(self._zoom_out), width=2).pack(side=tk.LEFT, padx=(10, 2))
        ttk.Button(nav_frame, text="+", command=self._with_unfocus(self._zoom_in), width=2).pack(side=tk.LEFT)

        # PDF Canvases below the navigation
        viewer_pane = ttk.PanedWindow(self.viewer_frame, orient=tk.HORIZONTAL)
        viewer_pane.grid(row=1, column=0, sticky="nsew")

        left_frame = ttk.LabelFrame(viewer_pane, text="원본 템플릿", padding=5)
        self.left_canvas, self.left_v_scroll, self.left_h_scroll = self._create_scrolled_canvas(left_frame)
        viewer_pane.add(left_frame, weight=1)

        right_frame = ttk.LabelFrame(viewer_pane, text="검증된 문서 (주석)", padding=5)
        self.right_canvas, self.right_v_scroll, self.right_h_scroll = self._create_scrolled_canvas(right_frame)
        viewer_pane.add(right_frame, weight=1)

        # --- 3b. Log Frame ---
        log_panel = ttk.LabelFrame(content_pane, text="진행 상황 로그", padding=5)
        log_panel.rowconfigure(0, weight=1)
        log_panel.columnconfigure(0, weight=1)
        content_pane.add(log_panel, weight=1)

        self.log_text = scrolledtext.ScrolledText(log_panel, font=('Consolas', 9), state=tk.DISABLED, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        log_scrollbar = ttk.Scrollbar(log_panel, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text['yscrollcommand'] = log_scrollbar.set

        self.progress_bar = ttk.Progressbar(log_panel, mode='determinate')
        self.progress_bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5,0))

    def _create_scrolled_canvas(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        canvas = tk.Canvas(frame, bg="lightgrey")
        canvas.grid(row=0, column=0, sticky="nsew")

        v_scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self._on_vscroll)
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=self._on_hscroll)
        h_scroll.grid(row=1, column=0, sticky="ew")

        canvas.bind("<Control-MouseWheel>", self._on_zoom)

        # Mouse Wheel Scrolling
        canvas.bind("<MouseWheel>", self._on_mouse_wheel)  # For Windows & MacOS
        canvas.bind("<Button-4>", self._on_mouse_wheel)    # For Linux scroll up
        canvas.bind("<Button-5>", self._on_mouse_wheel)    # For Linux scroll down

        # Panning with Middle Mouse Button
        canvas.bind("<ButtonPress-2>", self._start_pan)
        canvas.bind("<B2-Motion>", self._do_pan)
        canvas.bind("<ButtonRelease-2>", self._end_pan)

        return canvas, v_scroll, h_scroll

    def _on_mouse_wheel(self, event):
        # Cross-platform mouse wheel scrolling
        if event.num == 5 or event.delta < 0:
            dy = -40 # Scroll down
        elif event.num == 4 or event.delta > 0:
            dy = 40 # Scroll up
        else:
            dy = 0

        if dy != 0:
            self.controller.scroll_by(0, dy)

    def _start_pan(self, event):
        self.root.config(cursor="hand2")
        self.controller.start_pan(event)

    def _do_pan(self, event):
        self.controller.do_pan(event)

    def _end_pan(self, event):
        self.root.config(cursor="") # Reset to default
        self.controller.end_pan(event)

    def _on_mode_switch(self):
        mode = self.mode_var.get()
        self.controller.switch_mode(mode)
        if mode == "파일":
            self.target_label.config(text="검사 대상 파일:")
            self.browse_btn.config(text="파일 찾기")
            self.viewer_frame.grid()
            self.save_btn.pack(side=tk.LEFT, padx=10)
        else:
            self.target_label.config(text="검사 대상 폴더:")
            self.browse_btn.config(text="폴더 찾기")
            self.viewer_frame.grid_remove()
            self.save_btn.pack_forget()

    def _on_zoom(self, event):
        factor = 1.1 if event.delta > 0 else 1 / 1.1
        self.controller.handle_zoom(factor, event.x, event.y)

    def _zoom_in(self):
        x = self.left_canvas.winfo_width() / 2
        y = self.left_canvas.winfo_height() / 2
        self.controller.handle_zoom(1.2, x, y)

    def _zoom_out(self):
        x = self.left_canvas.winfo_width() / 2
        y = self.left_canvas.winfo_height() / 2
        self.controller.handle_zoom(1 / 1.2, x, y)

    def _on_vscroll(self, *args):
        if args[0] == 'moveto':
            self.controller.set_pan(None, float(args[1]))

    def _on_hscroll(self, *args):
        if args[0] == 'moveto':
            self.controller.set_pan(float(args[1]), None)

    # --- 아래는 Controller가 View를 제어하기 위해 호출하는 메서드들 ---

    def update_path(self, path):
        self.path_var.set(path)

    def update_button_state(self, is_ready):
        self.validate_btn.config(state=tk.NORMAL if is_ready else tk.DISABLED)

    def update_save_button_state(self, is_ready):
        self.save_btn.config(state=tk.NORMAL if is_ready else tk.DISABLED)

    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state=tk.DISABLED)

    def update_progress(self, value, maximum):
        self.progress_bar['maximum'] = maximum
        self.progress_bar['value'] = value

    def _draw_rois(self, rois_on_page):
        for name, data in rois_on_page.items():
            screen_coords = data.get('screen_coords')
            if not screen_coords:
                continue
            x0, y0, x1, y1 = screen_coords
            color = 'blue'
            self.left_canvas.create_rectangle(x0, y0, x1, y1, outline=color, width=2, tags=name)
            self.left_canvas.create_text(x0, y0 - 5, text=name, anchor=tk.SW, fill=color, tags=name)

    def _update_scrollbars(self, pan_x, pan_y, total_width, total_height):
        canvas_w = self.left_canvas.winfo_width()
        canvas_h = self.left_canvas.winfo_height()

        for h_scroll, v_scroll in [(self.left_h_scroll, self.left_v_scroll), (self.right_h_scroll, self.right_v_scroll)]:
            if total_width > canvas_w:
                first_x = -pan_x / total_width
                last_x = (-pan_x + canvas_w) / total_width
                h_scroll.set(first_x, last_x)
                h_scroll.grid()
            else:
                h_scroll.grid_remove()

            if total_height > canvas_h:
                first_y = -pan_y / total_height
                last_y = (-pan_y + canvas_h) / total_height
                v_scroll.set(first_y, last_y)
                v_scroll.grid()
            else:
                v_scroll.grid_remove()

    def update_viewer(self, original_img, annotated_img, rois_on_page, page_num, total_pages, pan_x, pan_y, total_width, total_height):
        # print(f"DEBUG: update_viewer called with page_num={page_num}, total_pages={total_pages}")
        if original_img:
            self.left_photo = ImageTk.PhotoImage(original_img)
            self.left_canvas.delete("all")
            self.left_canvas.create_image(pan_x, pan_y, anchor=tk.NW, image=self.left_photo)
            self._draw_rois(rois_on_page)

        if annotated_img:
            self.right_photo = ImageTk.PhotoImage(annotated_img)
            self.right_canvas.delete("all")
            self.right_canvas.create_image(pan_x, pan_y, anchor=tk.NW, image=self.right_photo)

        self.page_label.config(text=f"페이지: {page_num + 1}/{total_pages}")
        self.prev_page_btn.config(state=tk.NORMAL if page_num > 0 else tk.DISABLED)
        self.next_page_btn.config(state=tk.NORMAL if page_num < total_pages - 1 else tk.DISABLED)

        # print(f"DEBUG: page_label text set to: {self.page_label.cget('text')}")
        # print(f"DEBUG: prev_page_btn state set to: {self.prev_page_btn.cget('state')}")
        # print(f"DEBUG: next_page_btn state set to: {self.next_page_btn.cget('state')}")

        self._update_scrollbars(pan_x, pan_y, total_width, total_height)

    def _on_mode_switch(self):
        mode = self.mode_var.get()
        self.controller.switch_mode(mode)
        if mode == "파일":
            self.target_label.config(text="검사 대상 파일:")
            self.browse_btn.config(text="파일 찾기")
            self.viewer_frame.grid()
            self.save_btn.pack(side=tk.LEFT, padx=10)
        else:
            self.target_label.config(text="검사 대상 폴더:")
            self.browse_btn.config(text="폴더 찾기")
            self.viewer_frame.grid_remove()
            self.save_btn.pack_forget()

    def _on_zoom(self, event):
        factor = 1.1 if event.delta > 0 else 1 / 1.1
        self.controller.handle_zoom(factor, event.x, event.y)

    def _zoom_in(self):
        x = self.left_canvas.winfo_width() / 2
        y = self.left_canvas.winfo_height() / 2
        self.controller.handle_zoom(1.2, x, y)

    def _zoom_out(self):
        x = self.left_canvas.winfo_width() / 2
        y = self.left_canvas.winfo_height() / 2
        self.controller.handle_zoom(1 / 1.2, x, y)

    def update_path(self, path):
        self.path_var.set(path)

    def update_button_state(self, is_ready):
        self.validate_btn.config(state=tk.NORMAL if is_ready else tk.DISABLED)

    def update_save_button_state(self, is_ready):
        self.save_btn.config(state=tk.NORMAL if is_ready else tk.DISABLED)

    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state=tk.DISABLED)

    def update_progress(self, value, maximum):
        self.progress_bar['maximum'] = maximum
        self.progress_bar['value'] = value

    def _draw_rois(self, rois_on_page):
        for name, data in rois_on_page.items():
            screen_coords = data.get('screen_coords')
            if not screen_coords:
                continue
            x0, y0, x1, y1 = screen_coords
            color = 'blue'
            self.left_canvas.create_rectangle(x0, y0, x1, y1, outline=color, width=2, tags=name)
            self.left_canvas.create_text(x0, y0 - 5, text=name, anchor=tk.SW, fill=color, tags=name)