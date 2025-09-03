# src/template_manager.py (v9.0 - 자동 ROI 생성 최종본)

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json
import os
import fitz  # PyMuPDF
from PIL import Image, ImageTk

class TemplateManager:
    def __init__(self, root):
        self.root = root
        self.root.title("템플릿 관리자 (v10.0 - 라벨 기반 앵커 시스템)")
        self.root.geometry("1200x850")

        self.pdf_doc, self.current_page, self.rois = None, 0, {}
        self.templates = self.load_all_templates()
        self.current_pdf_path = None
        self.start_x, self.start_y, self.current_rect = 0, 0, None

        self.setup_ui()
        self.root.bind("<Configure>", lambda e: self.display_page() if self.pdf_doc else None)

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

        roi_frame = ttk.LabelFrame(right_panel, text="ROI 목록 (더블클릭으로 삭제)", padding=5)
        roi_frame.pack(fill=tk.BOTH, expand=True)
        self.roi_listbox = tk.Listbox(roi_frame, width=40)
        self.roi_listbox.pack(fill=tk.BOTH, expand=True)
        self.roi_listbox.bind("<Double-1>", self.delete_selected_roi)

        status_frame = ttk.LabelFrame(right_panel, text="개선된 사용법", padding=5)
        status_frame.pack(fill=tk.X, pady=(5,0))
        ttk.Label(status_frame, text="1. PDF 위에서 검증할 영역(ROI)을 드래그하세요.\n2. 자동으로 좌측 라벨을 앵커로 설정합니다.\n3. 앵커 품질이 낮으면 대안을 제시합니다.", justify=tk.LEFT).pack(anchor=tk.W)


    def get_display_matrix(self):
        if not self.pdf_doc or self.canvas.winfo_width() < 10: return fitz.Matrix(1, 1)
        page = self.pdf_doc[self.current_page]
        zoom = min(self.canvas.winfo_width() / page.rect.width, self.canvas.winfo_height() / page.rect.height)
        return fitz.Matrix(zoom, zoom)

    def screen_to_pdf_coords(self, x1, y1, x2, y2):
        mat = self.get_display_matrix()
        p1 = fitz.Point(min(x1, x2), min(y1, y2)) * ~mat; p2 = fitz.Point(max(x1, x2), max(y1, y2)) * ~mat
        return [p1.x, p1.y, p2.x, p2.y]

    def pdf_to_screen_coords(self, coords):
        mat = self.get_display_matrix()
        p1 = fitz.Point(coords[0], coords[1]) * mat; p2 = fitz.Point(coords[2], coords[3]) * mat
        return p1.x, p1.y, p2.x, p2.y

    def start_drag(self, e):
        if not self.pdf_doc: return
        self.start_x, self.start_y = self.canvas.canvasx(e.x), self.canvas.canvasy(e.y)
        self.current_rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="purple", width=2, dash=(4, 4))

    def drag_motion(self, e):
        if self.current_rect: self.canvas.coords(self.current_rect, self.start_x, self.start_y, self.canvas.canvasx(e.x), self.canvas.canvasy(e.y))

    def end_drag(self, e):
        if not self.current_rect: return
        x1, y1, x2, y2 = self.canvas.coords(self.current_rect)
        self.canvas.delete(self.current_rect); self.current_rect = None
        if abs(x1 - x2) < 5 or abs(y1 - y2) < 5: return

        # --- 개선된 로직: 라벨 기반 앵커 시스템 ---
        # 1. 드래그한 영역을 ROI로 설정
        roi_coords = self.screen_to_pdf_coords(x1, y1, x2, y2)
        
        # 2. ROI 좌측의 라벨 영역을 앵커로 자동 생성
        anchor_coords = self.generate_label_anchor(roi_coords)
        
        # 3. 앵커 품질 검사 및 대안 제시
        anchor_quality = self.check_anchor_quality(anchor_coords)
        if anchor_quality < 10:  # 키포인트 10개 미만
            # 대안 앵커 제시
            alternative_anchors = self.suggest_alternative_anchors(roi_coords)
            if alternative_anchors:
                anchor_coords = self.select_best_anchor(alternative_anchors)
                
        # 4. 정보 입력창 호출
        self.get_roi_info_and_save(roi_coords, anchor_coords)
    
    def generate_label_anchor(self, roi_coords):
        """ROI 좌측 라벨 영역을 앵커로 자동 생성"""
        roi_left, roi_top, roi_right, roi_bottom = roi_coords
        
        # ROI 좌측 100px 영역을 라벨 앵커로 설정
        label_width = min(100, roi_left)  # 페이지 경계 고려
        
        anchor_coords = [
            max(0, roi_left - label_width),  # 페이지 경계 제한
            roi_top - 5,    # ROI보다 약간 위에서 시작
            roi_left - 5,   # ROI 직전까지
            roi_bottom + 5  # ROI보다 약간 아래까지
        ]
        
        return anchor_coords
    
    def check_anchor_quality(self, anchor_coords):
        """앵커 영역의 특징점 품질 검사"""
        if not self.pdf_doc:
            return 0
            
        try:
            # 앵커 영역 이미지 추출
            page = self.pdf_doc[self.current_page]
            rect = fitz.Rect(anchor_coords)
            mat = fitz.Matrix(2.0, 2.0)  # 고해상도로 추출
            pix = page.get_pixmap(matrix=mat, clip=rect, alpha=False)
            
            import cv2
            import numpy as np
            
            img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # AKAZE로 키포인트 검출
            detector = cv2.AKAZE_create()
            kp, des = detector.detectAndCompute(gray, None)
            
            keypoint_count = len(kp) if kp else 0
            print(f"[앵커 품질] 키포인트: {keypoint_count}개")
            
            return keypoint_count
            
        except Exception as e:
            print(f"[앵커 품질] 검사 실패: {e}")
            return 0
    
    def suggest_alternative_anchors(self, roi_coords):
        """ROI 주변의 대안 앵커 후보들 제시"""
        alternatives = []
        
        # 1. 상단 영역 (헤더/제목)
        page_width = self.pdf_doc[self.current_page].rect.width
        header_anchor = [0, 0, page_width, roi_coords[1] - 20]
        
        # 2. 하단 영역 (푸터)
        page_height = self.pdf_doc[self.current_page].rect.height
        footer_anchor = [0, roi_coords[3] + 20, page_width, page_height]
        
        # 3. 우측 영역
        right_anchor = [
            roi_coords[2] + 10,
            roi_coords[1] - 10,
            min(roi_coords[2] + 120, page_width),
            roi_coords[3] + 10
        ]
        
        # 4. 확장된 좌측 영역
        extended_left_anchor = [
            max(0, roi_coords[0] - 200),
            roi_coords[1] - 20,
            roi_coords[0] - 5,
            roi_coords[3] + 20
        ]
        
        candidates = [
            {"name": "헤더 영역", "coords": header_anchor},
            {"name": "확장 좌측", "coords": extended_left_anchor},
            {"name": "우측 영역", "coords": right_anchor},
            {"name": "푸터 영역", "coords": footer_anchor}
        ]
        
        # 각 후보의 품질 평가
        for candidate in candidates:
            quality = self.check_anchor_quality(candidate["coords"])
            candidate["quality"] = quality
            print(f"[대안 앵커] {candidate['name']}: {quality}개 키포인트")
        
        # 품질 순으로 정렬
        return sorted(candidates, key=lambda x: x["quality"], reverse=True)
    
    def select_best_anchor(self, alternatives):
        """최고 품질의 앵커 선택"""
        if alternatives and alternatives[0]["quality"] > 5:
            best = alternatives[0]
            print(f"[최적 앵커] '{best['name']}' 선택 ({best['quality']}개 키포인트)")
            return best["coords"]
        return None

    def get_roi_info_and_save(self, roi_coords, anchor_coords):
        dialog = tk.Toplevel(self.root); dialog.title("ROI 정보 입력"); dialog.transient(self.root); dialog.grab_set()
        name_var = tk.StringVar(); method_var = tk.StringVar(value="ocr"); threshold_var = tk.IntVar(value=3)

        def update_threshold(*args):
            """검증 방식에 따라 기본 임계값 자동 설정"""
            if method_var.get() == "ocr":
                threshold_var.set(3)  # OCR: 3글자 이상
            else:  # contour
                threshold_var.set(100)  # Contour: 100픽셀 이상

        method_var.trace('w', update_threshold)

        ttk.Label(dialog, text="이름:").pack(padx=10, pady=5)
        name_entry = ttk.Entry(dialog, textvariable=name_var); name_entry.pack(padx=10); name_entry.focus_set()

        ttk.Label(dialog, text="검증 방식:").pack(padx=10, pady=5)
        ttk.Radiobutton(dialog, text="OCR (텍스트 - 기본 3글자)", variable=method_var, value="ocr").pack(anchor=tk.W, padx=20)
        ttk.Radiobutton(dialog, text="Contour (도형/서명 - 기본 100픽셀)", variable=method_var, value="contour").pack(anchor=tk.W, padx=20)

        ttk.Label(dialog, text="임계값:").pack(padx=10, pady=5)
        threshold_frame = ttk.Frame(dialog)
        threshold_frame.pack(padx=10)
        threshold_entry = ttk.Entry(threshold_frame, textvariable=threshold_var, width=10)
        threshold_entry.pack(side=tk.LEFT)
        self.threshold_info = ttk.Label(threshold_frame, text="(OCR: 글자 수, Contour: 픽셀 면적)", font=('Arial', 8))
        self.threshold_info.pack(side=tk.LEFT, padx=5)

        def on_save():
            name = name_var.get().strip()
            if not name or name in self.rois:
                messagebox.showerror("오류", "이름을 입력하거나 중복되지 않는 이름을 사용하세요.", parent=dialog); return

            self.rois[name] = {'page': self.current_page, 'coords': roi_coords, 'anchor_coords': anchor_coords, 'method': method_var.get(), 'threshold': threshold_var.get()}
            self.display_page(); dialog.destroy()

        ttk.Button(dialog, text="저장", command=on_save).pack(pady=10)

    def open_pdf(self, path=None, rois_to_load=None):
        if not path: path = filedialog.askopenfilename(title="템플릿 PDF 열기", filetypes=[("PDF Files", "*.pdf")])
        if not path: return
        try:
            if self.pdf_doc: self.pdf_doc.close()
            self.pdf_doc = fitz.open(path); self.current_pdf_path = path; self.current_page = 0
            self.rois = rois_to_load if rois_to_load is not None else {}; self.display_page()
        except Exception as e: messagebox.showerror("오류", f"PDF 열기 실패:\n{e}", parent=self.root)

    def display_page(self):
        if not self.pdf_doc: return
        page = self.pdf_doc[self.current_page]
        mat = self.get_display_matrix()
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples); self.tk_image = ImageTk.PhotoImage(img)
        self.canvas.delete("all"); self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
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

                if 'anchor_coords' in data:
                    ax0, ay0, ax1, ay1 = self.pdf_to_screen_coords(data['anchor_coords'])
                    self.canvas.create_rectangle(ax0, ay0, ax1, ay1, outline="cyan", width=2, dash=(5, 3), tags=name)
                    # ROI와 앵커를 연결하는 중심선
                    self.canvas.create_line((x0+x1)/2, (y0+y1)/2, (ax0+ax1)/2, (ay0+ay1)/2, fill="yellow", dash=(2,2), tags=name)

    def update_roi_listbox(self):
        self.roi_listbox.delete(0, tk.END)
        for name, data in sorted(self.rois.items()):
            if data.get('page') == self.current_page: self.roi_listbox.insert(tk.END, name)

    def delete_selected_roi(self, event=None):
        sel = self.roi_listbox.curselection()
        if not sel: return
        roi_name = self.roi_listbox.get(sel[0])
        if messagebox.askyesno("삭제 확인", f"'{roi_name}' 영역을 삭제하시겠습니까?", parent=self.root):
            del self.rois[roi_name]; self.display_page()

    def prev_page(self):
        if self.pdf_doc and self.current_page > 0: self.current_page -= 1; self.display_page()

    def next_page(self):
        if self.pdf_doc and self.current_page < len(self.pdf_doc) - 1: self.current_page += 1; self.display_page()

    def save_template(self):
        if not self.rois or not self.current_pdf_path:
            messagebox.showwarning("경고", "PDF를 열고 ROI를 하나 이상 지정해야 합니다.", parent=self.root); return
        default_name = os.path.splitext(os.path.basename(self.current_pdf_path))[0]
        template_name = simpledialog.askstring("템플릿 저장", "저장할 템플릿의 이름을 입력하세요:", parent=self.root, initialvalue=default_name)
        if not template_name: return
        self.templates[template_name] = {'original_pdf_path': self.current_pdf_path, 'rois': self.rois}
        try:
            with open("templates.json", 'w', encoding='utf-8') as f: json.dump(self.templates, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("성공", f"템플릿 '{template_name}'이(가) 저장되었습니다.", parent=self.root)
        except Exception as e: messagebox.showerror("오류", f"템플릿 저장 실패: {e}", parent=self.root)

    def load_all_templates(self):
        try:
            if os.path.exists("templates.json"):
                with open("templates.json", 'r', encoding='utf-8') as f: return json.load(f)
        except Exception as e: messagebox.showwarning("경고", f"templates.json 로딩 실패:\n{e}", parent=self.root)
        return {}

    def load_template_from_list(self):
        self.templates = self.load_all_templates()
        if not self.templates: messagebox.showinfo("안내", "저장된 템플릿이 없습니다.", parent=self.root); return
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
        # ... (이하 삭제 로직)
        pass

def main():
    root = tk.Tk()
    app = TemplateManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()