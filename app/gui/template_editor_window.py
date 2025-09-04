# 파일 경로: app/gui/template_editor_window.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk

# Presentation Layer (View)
# 역할: 사용자에게 화면을 보여주고, 사용자 입력을 Controller에 전달하는 역할만 수행합니다.
#      비즈니스 로직이나 데이터 처리 코드는 포함하지 않습니다.

class TemplateEditorWindow:
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller

        self.root.title("Template Editor (Clean Architecture)")
        self.root.geometry("1200x850")

        # UI 상태 변수
        self.tk_image = None
        self.start_x = 0
        self.start_y = 0
        self.current_rect = None

        self._setup_ui()
        self.root.bind("<Configure>", lambda e: self.controller.on_window_resize())

    def _setup_ui(self):
        # --- Top Frame ---
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(top_frame, text="PDF불러오기", command=self.controller.open_pdf_file).pack(side=tk.LEFT, padx=5)

        nav_frame = ttk.Frame(top_frame)
        ttk.Button(nav_frame, text="◀ 이전", command=self.controller.prev_page).pack(side=tk.LEFT)
        self.page_label = ttk.Label(nav_frame, text="Page: 0/0", width=15, anchor="center")
        self.page_label.pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="다음 ▶", command=self.controller.next_page).pack(side=tk.LEFT)
        nav_frame.pack(side=tk.LEFT, padx=10)

        ttk.Button(top_frame, text="템플릿 삭제", command=self.controller.delete_template).pack(side=tk.RIGHT, padx=5)
        ttk.Button(top_frame, text="템플릿 저장", command=self.controller.save_template).pack(side=tk.RIGHT)
        ttk.Button(top_frame, text="템플릿 불러오기", command=self.controller.load_template).pack(side=tk.RIGHT, padx=5)

        # --- Main Frame ---
        main_frame = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(main_frame, bg='lightgrey', cursor="plus")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.bind("<ButtonPress-1>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self._end_drag)

        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=5)

        roi_frame = ttk.LabelFrame(right_panel, text="ROI List (Double-click to delete)", padding=5)
        roi_frame.pack(fill=tk.BOTH, expand=True)
        self.roi_listbox = tk.Listbox(roi_frame, width=40)
        self.roi_listbox.pack(fill=tk.BOTH, expand=True)
        self.roi_listbox.bind("<Double-1>", lambda e: self.controller.delete_selected_roi())

    # --- Event Handlers (Calls Controller) ---
    def _start_drag(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.current_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="purple", width=2, dash=(4, 4)
        )

    def _drag_motion(self, event):
        if self.current_rect:
            self.canvas.coords(
                self.current_rect, self.start_x, self.start_y,
                self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            )

    def _end_drag(self, event):
        if not self.current_rect:
            return

        x1, y1, x2, y2 = self.canvas.coords(self.current_rect)
        self.canvas.delete(self.current_rect)
        self.current_rect = None

        if abs(x1 - x2) < 5 or abs(y1 - y2) < 5:
            return

        # UI는 좌표만 전달, 처리는 Controller가 담당
        self.controller.add_roi(x1, y1, x2, y2)

    # --- UI Update Methods (Called by Controller) ---
    def update_page_display(self, page_image, page_num, total_pages, rois_on_page):
        if page_image:
            self.tk_image = ImageTk.PhotoImage(page_image)
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
            self._draw_rois(rois_on_page)

        self.page_label.config(text=f"Page: {page_num + 1}/{total_pages}")
        self.update_roi_listbox(rois_on_page)

    def update_roi_listbox(self, rois_on_page):
        self.roi_listbox.delete(0, tk.END)
        for name in sorted(rois_on_page.keys()):
            self.roi_listbox.insert(tk.END, name)

    def get_selected_roi_name(self):
        selection = self.roi_listbox.curselection()
        return self.roi_listbox.get(selection[0]) if selection else None

    def _draw_rois(self, rois_on_page):
        for name, data in rois_on_page.items():
            screen_coords = data.get('screen_coords')
            if not screen_coords:
                continue

            x0, y0, x1, y1 = screen_coords
            color = 'blue' if data.get('method') == "ocr" else 'red'
            self.canvas.create_rectangle(x0, y0, x1, y1, outline=color, width=2, tags=name)
            self.canvas.create_text(x0, y0 - 5, text=name, anchor=tk.SW, fill=color, tags=name)

            anchor_screen_coords = data.get('anchor_screen_coords')
            if anchor_screen_coords:
                ax0, ay0, ax1, ay1 = anchor_screen_coords
                self.canvas.create_rectangle(ax0, ay0, ax1, ay1, outline="cyan", width=2, dash=(5, 3), tags=name)
                self.canvas.create_line(
                    (x0 + x1) / 2, (y0 + y1) / 2,
                    (ax0 + ax1) / 2, (ay0 + ay1) / 2,
                    fill="yellow", dash=(2, 2), tags=name
                )

    def get_roi_creation_info(self):
        """ROI 생성에 필요한 정보를 담은 대화상자를 띄웁니다."""
        dialog = tk.Toplevel(self.root)
        dialog.title("ROI Info")
        dialog.transient(self.root)
        dialog.grab_set()

        result = {}

        name_var = tk.StringVar()
        method_var = tk.StringVar(value="ocr")
        threshold_var = tk.IntVar(value=3)

        def update_threshold(*_):
            threshold_var.set(3 if method_var.get() == "ocr" else 100)
        method_var.trace('w', update_threshold)

        ttk.Label(dialog, text="Name:").pack(padx=10, pady=5)
        name_entry = ttk.Entry(dialog, textvariable=name_var)
        name_entry.pack(padx=10)
        name_entry.focus_set()

        ttk.Label(dialog, text="검증 타입:").pack(padx=10, pady=5)
        ttk.Radiobutton(dialog, text="OCR", variable=method_var, value="ocr").pack(anchor=tk.W, padx=20)
        ttk.Radiobutton(dialog, text="Contour", variable=method_var, value="contour").pack(anchor=tk.W, padx=20)

        ttk.Label(dialog, text="Threshold:").pack(padx=10, pady=5)
        ttk.Entry(dialog, textvariable=threshold_var, width=10).pack(padx=10)

        def on_save():
            result['name'] = name_var.get().strip()
            result['method'] = method_var.get()
            result['threshold'] = threshold_var.get()
            dialog.destroy()

        ttk.Button(dialog, text="Save", command=on_save).pack(pady=10)

        self.root.wait_window(dialog)
        return result

    # --- Utility methods for the view ---
    def ask_yes_no(self, title, message):
        return messagebox.askyesno(title, message, parent=self.root)

    def show_info(self, title, message):
        messagebox.showinfo(title, message, parent=self.root)

    def show_warning(self, title, message):
        messagebox.showwarning(title, message, parent=self.root)

    def show_error(self, title, message):
        messagebox.showerror(title, message, parent=self.root)

    def ask_string(self, title, prompt, initial_value=None):
        return simpledialog.askstring(title, prompt, parent=self.root, initialvalue=initial_value)

    def ask_open_filename(self):
        return filedialog.askopenfilename(
            title="Open Template PDF",
            filetypes=[("PDF Files", "*.pdf")]
        )

    def ask_load_template(self, template_names):
        if not template_names:
            self.show_info("Info", "No saved templates found.")
            return None

        dialog = tk.Toplevel(self.root)
        dialog.title("Load Template")
        dialog.transient(self.root)
        dialog.grab_set()

        selected_name = None

        listbox = tk.Listbox(dialog, width=50, height=15)
        listbox.pack(padx=10, pady=10)
        for name in sorted(template_names):
            listbox.insert(tk.END, name)

        def on_load():
            nonlocal selected_name
            selection = listbox.curselection()
            if selection:
                selected_name = listbox.get(selection[0])
            dialog.destroy()

        ttk.Button(dialog, text="Load", command=on_load).pack(pady=5)
        self.root.wait_window(dialog)
        return selected_name