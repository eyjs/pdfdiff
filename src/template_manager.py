# src/template_manager.py (v4.0 최종 - 템플릿 매칭 앵커 지원)

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json
import os
import fitz  # PyMuPDF
from PIL import Image, ImageTk

class TemplateManager:
    def __init__(self, root):
        self.root = root
        self.root.title("1단계: 템플릿 관리 (v4.0 - 템플릿 매칭)")
        self.root.geometry("1200x850")

        self.pdf_doc, self.current_page, self.rois = None, 0, {}
        self.templates = self.load_all_templates()
        self.zoom_factor = 1.0
        self.start_x, self.start_y, self.current_rect = 0, 0, None
        self.mode = "roi"  # 'roi' 또는 'anchor' 모드

        self.setup_ui()
        self.root.bind("<Configure>", lambda e: self.display_page() if self.pdf_doc else None, add="+")

    def setup_ui(self):
        top_frame = ttk.Frame(self.root, padding=5); top_frame.pack(side=tk.TOP, fill=tk.X)
        ttk.Button(top_frame, text="새 PDF 열기", command=self.open_pdf).pack(side=tk.LEFT, padx=5)

        self.nav_controls_frame = ttk.Frame(top_frame)
        self.prev_btn = ttk.Button(self.nav_controls_frame, text="◀ 이전", command=self.prev_page); self.prev_btn.pack(side=tk.LEFT)
        self.page_label = ttk.Label(self.nav_controls_frame, text="페이지: 0/0", width=15, anchor="center"); self.page_label.pack(side=tk.LEFT, padx=5)
        self.next_btn = ttk.Button(self.nav_controls_frame, text="다음 ▶", command=self.next_page); self.next_btn.pack(side=tk.LEFT)
        self.zoom_in_btn = ttk.Button(self.nav_controls_frame, text="확대 (+)", command=lambda: self.zoom(1.2)); self.zoom_in_btn.pack(side=tk.LEFT, padx=(20, 5))
        self.zoom_out_btn = ttk.Button(self.nav_controls_frame, text="축소 (-)", command=lambda: self.zoom(0.8)); self.zoom_out_btn.pack(side=tk.LEFT)

        ttk.Button(top_frame, text="템플릿 삭제", command=self.delete_template).pack(side=tk.RIGHT, padx=5)
        ttk.Button(top_frame, text="템플릿 저장", command=self.save_template).pack(side=tk.RIGHT)
        ttk.Button(top_frame, text="템플릿 불러오기", command=self.load_template_from_list).pack(side=tk.RIGHT, padx=5)

        main_frame = ttk.Frame(self.root, padding=(10, 0, 10, 10)); main_frame.pack(fill=tk.BOTH, expand=True)
        canvas_frame = ttk.Frame(main_frame); canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas_frame.grid_rowconfigure(0, weight=1); canvas_frame.grid_columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(canvas_frame, bg='lightgrey')
        self.v_scroll = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.h_scroll = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)
        self.canvas.grid(row=0, column=0, sticky="nsew"); self.v_scroll.grid(row=0, column=1, sticky="ns"); self.h_scroll.grid(row=1, column=0, sticky="ew")
        self.canvas.bind("<Button-1>", self.start_drag); self.canvas.bind("<B1-Motion>", self.drag_motion); self.canvas.bind("<ButtonRelease-1>", self.end_drag)

        roi_frame = ttk.LabelFrame(main_frame, text="ROI 목록", padding=5); roi_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5)
        self.roi_listbox = tk.Listbox(roi_frame, width=35); self.roi_listbox.pack(fill=tk.BOTH, expand=True)
        self.roi_listbox.bind("<<ListboxSelect>>", self.on_roi_select)

        self.anchor_btn = ttk.Button(roi_frame, text="기준 영역(앵커) 설정", command=self.set_anchor_mode, state=tk.DISABLED)
        self.anchor_btn.pack(fill=tk.X, pady=5)
        ttk.Button(roi_frame, text="선택 영역 삭제", command=self.delete_roi).pack(fill=tk.X)

        self.update_nav_controls_state()

    def get_display_matrix(self):
        if not self.pdf_doc or self.canvas.winfo_width() < 10: return fitz.Matrix(1, 1), 0, 0
        page = self.pdf_doc[self.current_page]
        fit_scale = min(self.canvas.winfo_width() / page.rect.width, self.canvas.winfo_height() / page.rect.height)
        mat = fitz.Matrix(fit_scale * self.zoom_factor, fit_scale * self.zoom_factor)
        img_w, img_h = page.rect.width * mat.a, page.rect.height * mat.d
        offset_x = (self.canvas.winfo_width() - img_w) / 2 if img_w < self.canvas.winfo_width() else 0
        offset_y = (self.canvas.winfo_height() - img_h) / 2 if img_h < self.canvas.winfo_height() else 0
        return mat, offset_x, offset_y

    def screen_to_pdf_coords(self, x, y):
        mat, ox, oy = self.get_display_matrix(); return (fitz.Point(x - ox, y - oy) * ~mat).x, (fitz.Point(x - ox, y - oy) * ~mat).y
    def pdf_to_screen_coords(self, pdf_x, pdf_y):
        mat, ox, oy = self.get_display_matrix(); return (fitz.Point(pdf_x, pdf_y) * mat).x + ox, (fitz.Point(pdf_x, pdf_y) * mat).y + oy

    def open_pdf(self, path=None, rois_to_load=None):
        if not path: path = filedialog.askopenfilename(title="템플릿으로 사용할 원본 PDF 열기", filetypes=[("PDF Files", "*.pdf")])
        if not path: return
        try:
            self.pdf_doc = fitz.open(path); self.current_page = 0; self.zoom_factor = 1.0
            self.rois = rois_to_load if rois_to_load is not None else {}
            self.nav_controls_frame.pack(side=tk.LEFT, padx=10)
            self.display_page()
        except Exception as e: messagebox.showerror("오류", f"PDF 파일을 여는 데 실패했습니다:\n{e}")

    def display_page(self):
        if not self.pdf_doc: return
        page = self.pdf_doc[self.current_page]
        mat, ox, oy = self.get_display_matrix()
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.tk_image = ImageTk.PhotoImage(img)
        self.canvas.delete("all"); self.canvas.config(scrollregion=(0, 0, img.width, img.height))
        self.canvas.create_image(max(0, ox), max(0, oy), anchor=tk.NW, image=self.tk_image)
        self.draw_rois_on_canvas()
        self.page_label.config(text=f"페이지: {self.current_page + 1}/{len(self.pdf_doc)}")
        self.update_roi_listbox()
        self.update_nav_controls_state()

    def draw_rois_on_canvas(self):
        for name, data in self.rois.items():
            if data['page'] == self.current_page:
                # ROI 그리기
                x0, y0 = self.pdf_to_screen_coords(data['coords'][0], data['coords'][1])
                x1, y1 = self.pdf_to_screen_coords(data['coords'][2], data['coords'][3])
                color = 'blue' if data['method'] == 'ocr' else 'red'
                self.canvas.create_rectangle(x0, y0, x1, y1, outline=color, width=2, tags=(name, "roi"))
                self.canvas.create_text(x0, y0 - 5, text=name, anchor=tk.SW, fill=color, tags=(name, "roi"))
                # 앵커 그리기
                if 'anchor_coords' in data:
                    ax0, ay0 = self.pdf_to_screen_coords(data['anchor_coords'][0], data['anchor_coords'][1])
                    ax1, ay1 = self.pdf_to_screen_coords(data['anchor_coords'][2], data['anchor_coords'][3])
                    self.canvas.create_rectangle(ax0, ay0, ax1, ay1, outline="purple", width=2, dash=(5, 3), tags=(name, "anchor"))

    def set_anchor_mode(self):
        sel = self.roi_listbox.curselection()
        if not sel: return
        self.mode = "anchor"
        messagebox.showinfo("기준 영역 설정", "선택된 ROI의 위치를 찾기 위한 기준 영역(앵커)을 드래그하세요.\n(ROI를 포함하는 주변의 고유한 텍스트나 표를 선택)")

    def configure_roi(self, x1, y1, x2, y2):
        if self.mode == "anchor":
            sel = self.roi_listbox.curselection()
            if not sel: return
            roi_name = self.roi_listbox.get(sel[0]).split(" ")[0]
            px0, py0 = self.screen_to_pdf_coords(min(x1, x2), min(y1, y2))
            px1, py1 = self.screen_to_pdf_coords(max(x1, x2), max(y1, y2))
            self.rois[roi_name]['anchor_coords'] = [px0, py0, px1, py1]
            self.canvas.delete(self.current_rect); self.current_rect = None
            self.display_page() # 앵커 표시를 위해 다시 그림
            self.mode = "roi" # 모드 초기화
            return

        # 기본 ROI 설정 다이얼로그
        dialog = tk.Toplevel(self.root); dialog.title("ROI 설정"); dialog.transient(self.root); dialog.grab_set()
        name_var = tk.StringVar(); method_var = tk.StringVar(value="ocr"); threshold_var = tk.IntVar(value=500)
        ttk.Label(dialog, text="영역 이름:").pack(padx=10, pady=5); name_entry = ttk.Entry(dialog, textvariable=name_var); name_entry.pack(padx=10); name_entry.focus_set()
        ttk.Label(dialog, text="검증 방법:").pack(padx=10, pady=5); ttk.Radiobutton(dialog, text="OCR (텍스트)", variable=method_var, value="ocr").pack(anchor=tk.W, padx=20); ttk.Radiobutton(dialog, text="Contour (도형/서명)", variable=method_var, value="contour").pack(anchor=tk.W, padx=20)
        ttk.Label(dialog, text="민감도 (Contour용):").pack(padx=10, pady=5); ttk.Scale(dialog, from_=10, to=5000, variable=threshold_var, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10)
        def save_roi():
            name = name_var.get().strip()
            if not name or name in self.rois: messagebox.showwarning("경고", "이름을 입력하거나 중복되지 않는 이름을 사용하세요.", parent=dialog); return
            px0, py0 = self.screen_to_pdf_coords(min(x1, x2), min(y1, y2)); px1, py1 = self.screen_to_pdf_coords(max(x1, x2), max(y1, y2))
            thresh = len(name) if method_var.get() == 'ocr' else threshold_var.get()
            self.rois[name] = {'page': self.current_page, 'coords': [px0, py0, px1, py1], 'method': method_var.get(), 'threshold': thresh}
            self.canvas.delete(self.current_rect); self.current_rect = None; self.draw_rois_on_canvas(); self.update_roi_listbox(); dialog.destroy()
        def on_cancel(): self.canvas.delete(self.current_rect); self.current_rect = None; dialog.destroy()
        ttk.Button(dialog, text="저장", command=save_roi).pack(side=tk.LEFT, padx=10, pady=10); ttk.Button(dialog, text="취소", command=on_cancel).pack(side=tk.RIGHT, padx=10, pady=10)
        dialog.protocol("WM_DELETE_WINDOW", on_cancel)

    # (이하 템플릿 CRUD 및 기타 헬퍼 함수는 이전 버전과 동일)
    def save_template(self):
        if not self.rois or not self.pdf_doc: messagebox.showwarning("경고", "PDF를 열고 ROI를 하나 이상 지정해야 합니다."); return
        template_name = simpledialog.askstring("템플릿 저장", "저장할 템플릿의 이름을 입력하세요:", initialvalue=os.path.splitext(os.path.basename(self.pdf_doc.name))[0])
        if not template_name: return
        self.templates[template_name] = {'original_pdf_path': self.pdf_doc.name, 'rois': self.rois}
        try:
            with open("templates.json", 'w', encoding='utf-8') as f: json.dump(self.templates, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("성공", f"템플릿 '{template_name}'이(가) templates.json에 저장되었습니다.")
        except Exception as e: messagebox.showerror("오류", f"템플릿 저장 실패: {e}")
    def load_all_templates(self):
        try:
            if os.path.exists("templates.json"):
                with open("templates.json", 'r', encoding='utf-8') as f: return json.load(f)
        except Exception as e: messagebox.showwarning("경고", f"templates.json 파일을 불러오는 데 실패했습니다:\n{e}")
        return {}
    def load_template_from_list(self):
        self.templates = self.load_all_templates()
        if not self.templates: messagebox.showinfo("안내", "저장된 템플릿이 없습니다."); return
        dialog = tk.Toplevel(self.root); dialog.title("템플릿 불러오기"); dialog.transient(self.root); dialog.grab_set()
        listbox = tk.Listbox(dialog, width=50); listbox.pack(padx=10, pady=10)
        for name in self.templates.keys(): listbox.insert(tk.END, name)
        def on_load():
            selection = listbox.curselection();
            if not selection: return
            name = listbox.get(selection[0]); template = self.templates[name]
            self.open_pdf(path=template['original_pdf_path'], rois_to_load=template['rois']); dialog.destroy()
        ttk.Button(dialog, text="불러오기", command=on_load).pack(pady=5)
    def delete_template(self):
        self.templates = self.load_all_templates()
        if not self.templates: messagebox.showinfo("안내", "저장된 템플릿이 없습니다."); return
        dialog = tk.Toplevel(self.root); dialog.title("템플릿 삭제"); dialog.transient(self.root); dialog.grab_set()
        listbox = tk.Listbox(dialog, width=50); listbox.pack(padx=10, pady=10)
        for name in self.templates.keys(): listbox.insert(tk.END, name)
        def on_delete():
            selection = listbox.curselection();
            if not selection: return
            name = listbox.get(selection[0])
            if messagebox.askyesno("확인", f"'{name}' 템플릿을 정말 삭제하시겠습니까?"):
                del self.templates[name]
                try:
                    with open("templates.json", 'w', encoding='utf-8') as f: json.dump(self.templates, f, ensure_ascii=False, indent=2)
                    messagebox.showinfo("성공", f"템플릿 '{name}'이(가) 삭제되었습니다."); dialog.destroy()
                except Exception as e: messagebox.showerror("오류", f"템플릿 파일 저장 실패: {e}")
        ttk.Button(dialog, text="삭제", command=on_delete).pack(pady=5)
    def zoom(self, factor):
        if self.pdf_doc: self.zoom_factor *= factor; self.display_page()
    def update_roi_listbox(self):
        self.roi_listbox.delete(0, tk.END); [self.roi_listbox.insert(tk.END, f"{n} (P.{d['page']+1}, {d['method']})") for n, d in sorted(self.rois.items())]
        self.on_roi_select(None)
    def on_roi_select(self, event):
        self.anchor_btn.config(state=tk.NORMAL if self.roi_listbox.curselection() else tk.DISABLED)
    def delete_roi(self):
        s = self.roi_listbox.curselection();
        if s: name = self.roi_listbox.get(s[0]).split(" ")[0]; del self.rois[name]; self.update_roi_listbox(); self.display_page()
    def prev_page(self):
        if self.pdf_doc and self.current_page > 0: self.current_page -= 1; self.display_page()
    def next_page(self):
        if self.pdf_doc and self.current_page < len(self.pdf_doc) - 1: self.current_page += 1; self.display_page()
    def start_drag(self, e):
        x, y = self.canvas.canvasx(e.x), self.canvas.canvasy(e.y)
        if self.pdf_doc: self.start_x, self.start_y = x, y; color = "purple" if self.mode == 'anchor' else "green"; self.current_rect = self.canvas.create_rectangle(x, y, x, y, outline=color, width=2, dash=(4, 4))
    def drag_motion(self, e):
        x, y = self.canvas.canvasx(e.x), self.canvas.canvasy(e.y)
        if self.current_rect: self.canvas.coords(self.current_rect, self.start_x, self.start_y, x, y)
    def end_drag(self, e):
        if not self.current_rect: return
        x1, y1, x2, y2 = self.canvas.coords(self.current_rect)
        if abs(x1 - x2) < 5 or abs(y1 - y2) < 5: self.canvas.delete(self.current_rect); self.current_rect = None; return
        self.configure_roi(x1, y1, x2, y2)
    def update_nav_controls_state(self):
        state = tk.NORMAL if self.pdf_doc else tk.DISABLED
        for btn in [self.prev_btn, self.next_btn, self.zoom_in_btn, self.zoom_out_btn]: btn.config(state=state)
        if self.pdf_doc:
            self.prev_btn.config(state=tk.DISABLED if self.current_page == 0 else tk.NORMAL)
            self.next_btn.config(state=tk.DISABLED if self.current_page == len(self.pdf_doc) - 1 else tk.NORMAL)

def main():
    root = tk.Tk(); app = TemplateManager(root); root.mainloop()
if __name__ == "__main__": main()