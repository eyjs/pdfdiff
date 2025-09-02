# src/template_editor.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import fitz  # PyMuPDF
import os
import json

class ROIEditorDialog(simpledialog.Dialog):
    """ROI 정보와 앵커를 한 번에 설정하는 커스텀 다이얼로그"""

    def __init__(self, parent, title, roi_data=None):
        self.roi_data = roi_data if roi_data else {}
        super().__init__(parent, title)

    def body(self, master):
        ttk.Label(master, text="이름:").grid(row=0, sticky=tk.W, padx=5, pady=5)
        self.name_entry = ttk.Entry(master, width=30)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)
        self.name_entry.insert(0, self.roi_data.get("name", ""))

        ttk.Label(master, text="검증 방식:").grid(row=1, sticky=tk.W, padx=5, pady=5)
        self.method_var = tk.StringVar(value=self.roi_data.get("method", "contour"))
        self.method_combo = ttk.Combobox(master, textvariable=self.method_var, values=["contour", "ocr"], state="readonly")
        self.method_combo.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(master, text="임계값:").grid(row=2, sticky=tk.W, padx=5, pady=5)
        self.threshold_entry = ttk.Entry(master, width=10)
        self.threshold_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        self.threshold_entry.insert(0, self.roi_data.get("threshold", 500))

        # --- 앵커 기능 UI ---
        self.anchor_coords = self.roi_data.get("anchor_coords")
        anchor_frame = ttk.Frame(master)
        anchor_frame.grid(row=3, columnspan=2, pady=10)

        self.anchor_btn = ttk.Button(anchor_frame, text="앵커 지정/변경", command=self.set_anchor_mode)
        self.anchor_btn.pack(side=tk.LEFT, padx=5)

        self.anchor_status_label = ttk.Label(anchor_frame, text=self._get_anchor_status_text(), foreground="blue")
        self.anchor_status_label.pack(side=tk.LEFT)

        return self.name_entry

    def _get_anchor_status_text(self):
        if self.anchor_coords:
            coords_text = ", ".join(map(lambda x: str(int(x)), self.anchor_coords))
            return f"앵커 지정됨: ({coords_text})"
        return "앵커 미지정"

    def set_anchor_mode(self):
        self.withdraw()
        anchor_coords = self.master.enter_anchor_mode()
        if anchor_coords:
            self.anchor_coords = anchor_coords
            self.anchor_status_label.config(text=self._get_anchor_status_text())
        self.deiconify()
        self.lift()

    def apply(self):
        try:
            name = self.name_entry.get().strip()
            if not name:
                messagebox.showerror("오류", "ROI 이름은 필수입니다.", parent=self)
                self.result = None
                return

            self.result = {
                "name": name,
                "method": self.method_var.get(),
                "threshold": int(self.threshold_entry.get()),
                "anchor_coords": self.anchor_coords
            }
        except ValueError:
            messagebox.showerror("오류", "임계값은 숫자여야 합니다.", parent=self)
            self.result = None

class TemplateEditor:
    def __init__(self, root, template_name, template_data, on_save_callback):
        self.root = root
        self.root.title(f"템플릿 편집기: {template_name}")
        self.root.geometry("1200x900")

        self.template_name = template_name
        self.pdf_path = template_data.get("original_pdf_path")
        self.rois = template_data.get("rois", {})
        self.on_save_callback = on_save_callback

        self.pdf_doc = None
        self.current_page_num = 0
        self.photo_image = None
        self.start_x = self.start_y = None
        self.rect = None

        self.is_anchor_mode = False
        self._anchor_coords_result = None

        self.setup_ui()
        if self.pdf_path:
            self.load_pdf(self.pdf_path)

    def setup_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_panel = ttk.Frame(main_frame, width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        nav_frame = ttk.Frame(left_panel)
        nav_frame.pack(fill=tk.X, pady=5)
        self.prev_btn = ttk.Button(nav_frame, text="◀ 이전", command=self.prev_page, state=tk.DISABLED)
        self.prev_btn.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.page_label = ttk.Label(nav_frame, text="0 / 0", anchor=tk.CENTER)
        self.page_label.pack(side=tk.LEFT, padx=10)
        self.next_btn = ttk.Button(nav_frame, text="다음 ▶", command=self.next_page, state=tk.DISABLED)
        self.next_btn.pack(side=tk.LEFT, expand=True, fill=tk.X)

        list_frame = ttk.LabelFrame(left_panel, text="ROI 목록 (더블클릭으로 수정)")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.roi_listbox = tk.Listbox(list_frame)
        self.roi_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.roi_listbox.bind("<Double-1>", self.edit_selected_roi)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.roi_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.roi_listbox.config(yscrollcommand=scrollbar.set)

        btn_frame = ttk.Frame(left_panel)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="선택 항목 삭제", command=self.delete_selected_roi).pack(fill=tk.X)

        ttk.Button(left_panel, text="템플릿 저장 후 닫기", command=self.save_template).pack(fill=tk.X, pady=10)

        self.canvas = tk.Canvas(main_frame, bg="lightgray")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.root.bind("<Configure>", lambda e: self.render_current_page())

    def load_pdf(self, pdf_path):
        try:
            self.pdf_doc = fitz.open(pdf_path)
            self.render_current_page()
        except Exception as e:
            messagebox.showerror("오류", f"PDF 파일을 여는 데 실패했습니다:\n{e}", parent=self.root)
            self.root.destroy()

    def render_current_page(self):
        if not self.pdf_doc: return
        self.update_navigation()
        page = self.pdf_doc[self.current_page_num]

        self.root.after(1, self._render_page_image, page)

    def _render_page_image(self, page):
        canvas_w, canvas_h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if canvas_w < 10 or canvas_h < 10: return

        zoom = min(canvas_w / page.rect.width, canvas_h / page.rect.height)
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.photo_image = ImageTk.PhotoImage(image=img)

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_image)
        self.draw_rois()

    def draw_rois(self):
        self.roi_listbox.delete(0, tk.END)
        if not self.pdf_doc: return

        page = self.pdf_doc[self.current_page_num]
        zoom = min(self.canvas.winfo_width() / page.rect.width, self.canvas.winfo_height() / page.rect.height)

        for name in sorted(self.rois.keys()):
            roi = self.rois[name]
            if roi.get("page") == self.current_page_num:
                display_name = f"{name} (A)" if roi.get("anchor_coords") else name
                self.roi_listbox.insert(tk.END, display_name)

                coords = roi["coords"]
                color = "blue" if roi.get("method") == "ocr" else "red"
                self.canvas.create_rectangle(coords[0]*zoom, coords[1]*zoom, coords[2]*zoom, coords[3]*zoom, outline=color, width=2)
                self.canvas.create_text(coords[0]*zoom, coords[1]*zoom - 5, text=name, fill=color, anchor="sw")

                if roi.get("anchor_coords"):
                    acoords = roi["anchor_coords"]
                    self.canvas.create_rectangle(acoords[0]*zoom, acoords[1]*zoom, acoords[2]*zoom, acoords[3]*zoom, outline="cyan", width=2, dash=(4, 4))

    def on_press(self, event):
        self.start_x, self.start_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        if self.rect: self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="green", width=2, dash=(4,4))

    def on_drag(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))

    def on_release(self, event):
        if not self.rect or not self.pdf_doc: return

        page = self.pdf_doc[self.current_page_num]
        zoom = min(self.canvas.winfo_width() / page.rect.width, self.canvas.winfo_height() / page.rect.height)
        coords = [c / zoom for c in self.canvas.coords(self.rect)]

        if self.is_anchor_mode:
            self._anchor_coords_result = coords
            self.is_anchor_mode = False
            self.root.quit()
        else:
            self.canvas.delete(self.rect); self.rect = None
            dialog = ROIEditorDialog(self.root, title="신규 ROI 설정")
            if dialog.result:
                roi_data = dialog.result; roi_name = roi_data.pop("name")

                new_roi_info = {"page": self.current_page_num, "coords": coords, **roi_data}

                if not new_roi_info.get("anchor_coords"):
                    # anchor_coords가 None이면 키 자체를 삭제
                    new_roi_info.pop("anchor_coords", None)

                self.rois[roi_name] = new_roi_info
                self.render_current_page()

    def enter_anchor_mode(self):
        self.is_anchor_mode = True; self._anchor_coords_result = None

        info_window = tk.Toplevel(self.root)
        info_window.title("앵커 지정"); info_window.geometry("350x100")
        label = ttk.Label(info_window, text="\n기준점으로 사용할 앵커 영역을 드래그하세요.\n완료 후 이 창은 자동으로 닫힙니다.", justify=tk.CENTER)
        label.pack(pady=10); info_window.transient(self.root); info_window.grab_set()

        self.canvas.config(cursor="cross")
        self.root.mainloop() # 사용자가 앵커를 그릴 때까지 여기서 대기

        self.canvas.config(cursor=""); info_window.destroy()
        if self.rect: self.canvas.delete(self.rect); self.rect = None
        return self._anchor_coords_result

    def edit_selected_roi(self, event=None):
        selected_indices = self.roi_listbox.curselection()
        if not selected_indices: return

        selected_display_name = self.roi_listbox.get(selected_indices[0])
        original_name = selected_display_name.replace(" (A)", "")

        if original_name in self.rois:
            roi_data = self.rois[original_name].copy()
            roi_data["name"] = original_name

            dialog = ROIEditorDialog(self.root, title="ROI 수정", roi_data=roi_data)

            if dialog.result:
                new_data = dialog.result; new_name = new_data.pop("name")

                # 원본 ROI 데이터는 유지하고, 변경된 내용만 업데이트
                roi_to_update = self.rois.get(original_name, {})
                roi_to_update.update(new_data)

                # anchor_coords가 None이면 키 삭제
                if not roi_to_update.get("anchor_coords"):
                    roi_to_update.pop("anchor_coords", None)

                # 이름이 변경된 경우 처리
                if original_name != new_name:
                    del self.rois[original_name]

                self.rois[new_name] = roi_to_update
                self.render_current_page()

    def delete_selected_roi(self):
        selected_indices = self.roi_listbox.curselection()
        if not selected_indices: return

        selected_display_name = self.roi_listbox.get(selected_indices[0])
        original_name = selected_display_name.replace(" (A)", "")

        if messagebox.askyesno("확인", f"'{original_name}' ROI를 정말 삭제하시겠습니까?", parent=self.root):
            del self.rois[original_name]
            self.render_current_page()

    def save_template(self):
        self.on_save_callback(self.template_name, self.rois)
        self.root.destroy()

    def prev_page(self):
        if self.current_page_num > 0:
            self.current_page_num -= 1; self.render_current_page()

    def next_page(self):
        if self.pdf_doc and self.current_page_num < self.pdf_doc.page_count - 1:
            self.current_page_num += 1; self.render_current_page()

    def update_navigation(self):
        if self.pdf_doc:
            self.page_label.config(text=f"{self.current_page_num + 1} / {self.pdf_doc.page_count}")
            self.prev_btn.config(state=tk.NORMAL if self.current_page_num > 0 else tk.DISABLED)
            self.next_btn.config(state=tk.NORMAL if self.current_page_num < self.pdf_doc.page_count - 1 else tk.DISABLED)

if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()
    pdf_path = filedialog.askopenfilename(title="템플릿 PDF 선택")
    if pdf_path:
        test_data = {"original_pdf_path": pdf_path, "rois": {}}
        def save_callback(name, rois):
            print(f"--- 템플릿 '{name}' 저장 ---")
            print(json.dumps(rois, indent=2, ensure_ascii=False))

        editor_root = tk.Toplevel(root)
        app = TemplateEditor(editor_root, "테스트 템플릿", test_data, save_callback)
        root.mainloop()