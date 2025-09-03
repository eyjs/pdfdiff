import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json, os, fitz
from PIL import Image, ImageTk

import cv2
import numpy as np

class TemplateManager:
    def __init__(self, root):
        self.root = root
        self.root.title("템플릿 관리자 (체크박스/Contour 강화)")
        self.root.geometry("1200x850")

        self.pdf_doc, self.current_page, self.rois = None, 0, {}
        self.templates = self.load_all_templates()
        self.current_pdf_path = None
        self.start_x, self.start_y, self.current_rect = 0, 0, None

        self.setup_ui()
        self.root.bind("<Configure>", lambda e: self.display_page() if self.pdf_doc else None)

    # ---------------- UI ----------------
    def setup_ui(self):
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        ttk.Button(top_frame, text="새 PDF 열기", command=self.open_pdf).pack(side=tk.LEFT, padx=5)

        nav_frame = ttk.Frame(top_frame)
        ttk.Button(nav_frame, text="◀ 이전", command=self.prev_page).pack(side=tk.LEFT)
        self.page_label = ttk.Label(nav_frame, text="페이지: 0/0", width=15, anchor="center")
        self.page_label.pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="다음 ▶", command=self.next_page).pack(side=tk.LEFT)
        nav_frame.pack(side=tk.LEFT, padx=10)

        ttk.Button(top_frame, text="템플릿 삭제", command=self.delete_template).pack(side=tk.RIGHT, padx=5)
        ttk.Button(top_frame, text="템플릿 저장", command=self.save_template).pack(side=tk.RIGHT)
        ttk.Button(top_frame, text="템플릿 불러오기", command=self.load_template_from_list).pack(side=tk.RIGHT, padx=5)

        main_frame = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(main_frame, bg='lightgrey', cursor="plus")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self.end_drag)

        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=5)

        roi_frame = ttk.LabelFrame(right_panel, text="ROI 목록 (더블클릭 삭제)", padding=5)
        roi_frame.pack(fill=tk.BOTH, expand=True)
        self.roi_listbox = tk.Listbox(roi_frame, width=40)
        self.roi_listbox.pack(fill=tk.BOTH, expand=True)
        self.roi_listbox.bind("<Double-1>", self.delete_selected_roi)

    # ---------------- 좌표 변환 ----------------
    def get_display_matrix(self):
        if not self.pdf_doc or self.canvas.winfo_width() < 10:
            return fitz.Matrix(1, 1)
        page = self.pdf_doc[self.current_page]
        zoom = min(self.canvas.winfo_width() / page.rect.width, self.canvas.winfo_height() / page.rect.height)
        return fitz.Matrix(zoom, zoom)

    def screen_to_pdf_coords(self, x1, y1, x2, y2):
        mat = self.get_display_matrix()
        p1 = fitz.Point(min(x1, x2), min(y1, y2)) * ~mat
        p2 = fitz.Point(max(x1, x2), max(y1, y2)) * ~mat
        return [p1.x, p1.y, p2.x, p2.y]

    def pdf_to_screen_coords(self, coords):
        mat = self.get_display_matrix()
        p1 = fitz.Point(coords[0], coords[1]) * mat
        p2 = fitz.Point(coords[2], coords[3]) * mat
        return p1.x, p1.y, p2.x, p2.y

    # ---------------- ROI 드래그 ----------------
    def start_drag(self, e):
        if not self.pdf_doc: return
        self.start_x, self.start_y = self.canvas.canvasx(e.x), self.canvas.canvasy(e.y)
        self.current_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="purple", width=2, dash=(4, 4)
        )

    def drag_motion(self, e):
        if self.current_rect:
            self.canvas.coords(
                self.current_rect,
                self.start_x, self.start_y,
                self.canvas.canvasx(e.x), self.canvas.canvasy(e.y)
            )

    def end_drag(self, e):
        if not self.current_rect: return
        x1, y1, x2, y2 = self.canvas.coords(self.current_rect)
        self.canvas.delete(self.current_rect)
        self.current_rect = None
        if abs(x1 - x2) < 5 or abs(y1 - y2) < 5: return

        roi_coords = self.screen_to_pdf_coords(x1, y1, x2, y2)
        anchor_coords = self.generate_label_anchor(roi_coords)
        self.get_roi_info_and_save(roi_coords, anchor_coords)

    # ---------------- 앵커 ----------------
    def generate_label_anchor(self, roi_coords):
        left, top, right, bottom = roi_coords
        label_width = min(100, left)
        return [max(0, left - label_width), top - 5, left - 5, bottom + 5]

    # ---------------- ROI 저장 ----------------
    def get_roi_info_and_save(self, roi_coords, anchor_coords):
        dialog = tk.Toplevel(self.root)
        dialog.title("ROI 정보 입력")
        dialog.transient(self.root); dialog.grab_set()

        name_var = tk.StringVar()
        method_var = tk.StringVar(value="ocr")
        threshold_var = tk.IntVar(value=3)

        ttk.Label(dialog, text="이름:").pack(padx=10, pady=5)
        name_entry = ttk.Entry(dialog, textvariable=name_var)
        name_entry.pack(padx=10); name_entry.focus_set()

        ttk.Label(dialog, text="검증 방식:").pack(padx=10, pady=5)
        ttk.Radiobutton(dialog, text="OCR (텍스트)", variable=method_var, value="ocr").pack(anchor=tk.W, padx=20)
        ttk.Radiobutton(dialog, text="Contour (체크박스/서명)", variable=method_var, value="contour").pack(anchor=tk.W, padx=20)

        ttk.Label(dialog, text="임계값:").pack(padx=10, pady=5)
        ttk.Entry(dialog, textvariable=threshold_var, width=10).pack(padx=10)

        def on_save():
            name = name_var.get().strip()
            if not name or name in self.rois:
                messagebox.showerror("오류", "이름이 비어있거나 중복됨.", parent=dialog)
                return
            self.rois[name] = {
                'page': self.current_page,
                'coords': roi_coords,
                'anchor_coords': anchor_coords,
                'method': method_var.get(),
                'threshold': threshold_var.get()
            }
            self.display_page()
            dialog.destroy()

        ttk.Button(dialog, text="저장", command=on_save).pack(pady=10)

    # ---------------- 체크박스 검출 ----------------
    def detect_checkbox(self, image, threshold=0.2):
        """
        체크박스 검출: aspect_ratio ≈ 1 && 일정 면적 이상 && 채움률(fill ratio) 조건
        threshold = 채움률 기준 (0 ~ 1)
        """
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        results = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w < 10 or h < 10:  # 너무 작은 노이즈 제외
                continue

            aspect_ratio = w / float(h)
            if 0.8 < aspect_ratio < 1.2:  # 정사각형
                box_area = w * h
                filled = cv2.countNonZero(th[y:y+h, x:x+w])
                fill_ratio = filled / float(box_area)

                if fill_ratio > threshold:  # 일정 이상 채워짐
                    results.append({"x": x, "y": y, "w": w, "h": h, "fill_ratio": fill_ratio})

        return results

    # ---------------- PDF 표시 ----------------
    def open_pdf(self, path=None, rois_to_load=None):
        if not path:
            path = filedialog.askopenfilename(title="템플릿 PDF 열기", filetypes=[("PDF Files", "*.pdf")])
        if not path: return
        try:
            if self.pdf_doc: self.pdf_doc.close()
            self.pdf_doc = fitz.open(path)
            self.current_pdf_path = path
            self.current_page = 0
            self.rois = rois_to_load if rois_to_load else {}
            self.display_page()
        except Exception as e:
            messagebox.showerror("오류", f"PDF 열기 실패:\n{e}", parent=self.root)

    def display_page(self):
        if not self.pdf_doc: return
        page = self.pdf_doc[self.current_page]
        mat = self.get_display_matrix()
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.tk_image = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.draw_rois_on_canvas()
        self.page_label.config(text=f"페이지: {self.current_page + 1}/{len(self.pdf_doc)}")
        self.update_roi_listbox()

    def draw_rois_on_canvas(self):
        for name, data in self.rois.items():
            if data.get('page') == self.current_page:
                x0, y0, x1, y1 = self.pdf_to_screen_coords(data['coords'])
                color = 'blue' if data.get('method') == 'ocr' else 'red'
                self.canvas.create_rectangle(x0, y0, x1, y1, outline=color, width=2, tags=name)
                self.canvas.create_text(x0, y0 - 5, text=name, anchor=tk.SW, fill=color, tags=name)

    # ---------------- 기타 ----------------
    def update_roi_listbox(self):
        self.roi_listbox.delete(0, tk.END)
        for name, data in sorted(self.rois.items()):
            if data.get('page') == self.current_page:
                self.roi_listbox.insert(tk.END, name)

    def delete_selected_roi(self, event=None):
        sel = self.roi_listbox.curselection()
        if not sel: return
        roi_name = self.roi_listbox.get(sel[0])
        if messagebox.askyesno("삭제 확인", f"'{roi_name}' 삭제?", parent=self.root):
            del self.rois[roi_name]; self.display_page()

    def prev_page(self):
        if self.pdf_doc and self.current_page > 0:
            self.current_page -= 1; self.display_page()

    def next_page(self):
        if self.pdf_doc and self.current_page < len(self.pdf_doc) - 1:
            self.current_page += 1; self.display_page()

    def save_template(self):
        if not self.rois or not self.current_pdf_path:
            messagebox.showwarning("경고", "PDF와 ROI 필요", parent=self.root); return
        default_name = os.path.splitext(os.path.basename(self.current_pdf_path))[0]
        template_name = simpledialog.askstring("템플릿 저장", "템플릿 이름 입력:", parent=self.root, initialvalue=default_name)
        if not template_name: return
        self.templates[template_name] = {'original_pdf_path': self.current_pdf_path, 'rois': self.rois}
        try:
            with open("templates.json", 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("성공", f"'{template_name}' 저장 완료", parent=self.root)
        except Exception as e:
            messagebox.showerror("오류", f"저장 실패: {e}", parent=self.root)

    def load_all_templates(self):
        if os.path.exists("templates.json"):
            try:
                with open("templates.json", 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: return {}
        return {}

    def load_template_from_list(self):
        self.templates = self.load_all_templates()
        if not self.templates:
            messagebox.showinfo("안내", "저장된 템플릿 없음", parent=self.root); return
        dialog = tk.Toplevel(self.root); dialog.title("템플릿 불러오기"); dialog.transient(self.root); dialog.grab_set()
        listbox = tk.Listbox(dialog, width=50, height=15); listbox.pack(padx=10, pady=10)
        for name in sorted(self.templates.keys()): listbox.insert(tk.END, name)
        def on_load():
            sel = listbox.curselection()
            if not sel: return
            name = listbox.get(sel[0]); template = self.templates[name]
            self.open_pdf(path=template['original_pdf_path'], rois_to_load=template['rois'])
            dialog.destroy()
        ttk.Button(dialog, text="불러오기", command=on_load).pack(pady=5)

    def delete_template(self):
        pass

def main():
    root = tk.Tk()
    app = TemplateManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()
