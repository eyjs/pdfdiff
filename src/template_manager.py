import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json, os, fitz
from PIL import Image, ImageTk
import cv2, numpy as np

class TemplateManager:
    def __init__(self, root):
        self.root = root
        self.root.title("템플릿 관리자 (v11.0 - 고도화 앵커 시스템)")
        self.root.geometry("1200x850")

        self.pdf_doc, self.current_page, self.rois = None, 0, {}
        self.templates = self.load_all_templates()
        self.current_pdf_path = None
        self.start_x, self.start_y, self.current_rect = 0, 0, None

        self.setup_ui()
        self.root.bind("<Configure>", lambda e: self.display_page() if self.pdf_doc else None)

    # ---------------- UI ----------------
    def setup_ui(self):
        top_frame = ttk.Frame(self.root, padding=10); top_frame.pack(side=tk.TOP, fill=tk.X)
        ttk.Button(top_frame, text="새 PDF 열기", command=self.open_pdf).pack(side=tk.LEFT, padx=5)

        nav_frame = ttk.Frame(top_frame)
        ttk.Button(nav_frame, text="◀ 이전", command=self.prev_page).pack(side=tk.LEFT)
        self.page_label = ttk.Label(nav_frame, text="페이지: 0/0", width=15, anchor="center"); self.page_label.pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="다음 ▶", command=self.next_page).pack(side=tk.LEFT)
        nav_frame.pack(side=tk.LEFT, padx=10)

        ttk.Button(top_frame, text="템플릿 삭제", command=self.delete_template).pack(side=tk.RIGHT, padx=5)
        ttk.Button(top_frame, text="템플릿 저장", command=self.save_template).pack(side=tk.RIGHT)
        ttk.Button(top_frame, text="템플릿 불러오기", command=self.load_template_from_list).pack(side=tk.RIGHT, padx=5)

        main_frame = ttk.Frame(self.root, padding=(10, 0, 10, 10)); main_frame.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(main_frame, bg='lightgrey', cursor="plus"); self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self.end_drag)

        right_panel = ttk.Frame(main_frame); right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=5)
        roi_frame = ttk.LabelFrame(right_panel, text="ROI 목록 (더블클릭으로 삭제)", padding=5); roi_frame.pack(fill=tk.BOTH, expand=True)
        self.roi_listbox = tk.Listbox(roi_frame, width=40); self.roi_listbox.pack(fill=tk.BOTH, expand=True)
        self.roi_listbox.bind("<Double-1>", self.delete_selected_roi)

        status_frame = ttk.LabelFrame(right_panel, text="사용법", padding=5); status_frame.pack(fill=tk.X, pady=(5,0))
        ttk.Label(status_frame, text="1. PDF 위에서 검증 영역을 드래그하세요.\n2. 자동 앵커가 ROI 주변에서 탐색됩니다.\n3. 품질 점수 기반 최적 앵커가 선택됩니다.", justify=tk.LEFT).pack(anchor=tk.W)

    # ---------------- 좌표 변환 ----------------
    def get_display_matrix(self):
        if not self.pdf_doc or self.canvas.winfo_width() < 10: return fitz.Matrix(1, 1)
        page = self.pdf_doc[self.current_page]
        zoom = min(self.canvas.winfo_width()/page.rect.width, self.canvas.winfo_height()/page.rect.height)
        return fitz.Matrix(zoom, zoom)

    def screen_to_pdf_coords(self, x1,y1,x2,y2):
        mat = self.get_display_matrix()
        p1 = fitz.Point(min(x1,x2), min(y1,y2)) * ~mat
        p2 = fitz.Point(max(x1,x2), max(y1,y2)) * ~mat
        return [p1.x,p1.y,p2.x,p2.y]

    def pdf_to_screen_coords(self, coords):
        mat = self.get_display_matrix()
        p1 = fitz.Point(coords[0], coords[1]) * mat
        p2 = fitz.Point(coords[2], coords[3]) * mat
        return p1.x, p1.y, p2.x, p2.y

    # ---------------- ROI 드래그 ----------------
    def start_drag(self,e):
        if not self.pdf_doc: return
        self.start_x, self.start_y = self.canvas.canvasx(e.x), self.canvas.canvasy(e.y)
        self.current_rect = self.canvas.create_rectangle(self.start_x,self.start_y,self.start_x,self.start_y, outline="purple", width=2, dash=(4,4))

    def drag_motion(self,e):
        if self.current_rect: self.canvas.coords(self.current_rect,self.start_x,self.start_y,self.canvas.canvasx(e.x),self.canvas.canvasy(e.y))

    def end_drag(self,e):
        if not self.current_rect: return
        x1,y1,x2,y2 = self.canvas.coords(self.current_rect)
        self.canvas.delete(self.current_rect); self.current_rect = None
        if abs(x1-x2)<5 or abs(y1-y2)<5: return

        roi_coords = self.screen_to_pdf_coords(x1,y1,x2,y2)

        # 앵커 탐색
        anchor_coords = self.select_best_anchor(roi_coords)
        if not anchor_coords:
            messagebox.showwarning("경고","앵커 후보를 찾을 수 없습니다.", parent=self.root)
            return

        self.get_roi_info_and_save(roi_coords, anchor_coords)

    # ---------------- 앵커 시스템 ----------------
    def extract_region(self, coords, scale=2.0):
        page = self.pdf_doc[self.current_page]
        rect = fitz.Rect(coords)
        pix = page.get_pixmap(matrix=fitz.Matrix(scale,scale), clip=rect, alpha=False)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    def evaluate_anchor_region(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # 특징점 (AKAZE + SIFT)
        kp1 = cv2.AKAZE_create().detect(gray, None)
        kp2 = cv2.SIFT_create().detect(gray, None)
        # 엣지 밀도
        edges = cv2.Canny(gray,100,200); edge_density = edges.mean()
        return len(kp1)+len(kp2)+int(edge_density/10)

    def generate_anchor_candidates(self, roi):
        page = self.pdf_doc[self.current_page]; pw, ph = page.rect.width, page.rect.height
        x0,y0,x1,y1 = roi
        offsets = {
            "left":[max(0,x0-120), y0-10, x0-5, y1+10],
            "right":[x1+5, y0-10, min(pw,x1+120), y1+10],
            "top":[x0-10, max(0,y0-60), x1+10, y0-5],
            "bottom":[x0-10, y1+5, x1+10, min(ph,y1+60)]
        }
        results=[]
        for label,coords in offsets.items():
            try:
                img=self.extract_region(coords)
                score=self.evaluate_anchor_region(img)
                results.append((label,coords,score))
                print(f"[앵커 후보] {label}: {score}")
            except: continue
        return results

    def select_best_anchor(self, roi):
        candidates=self.generate_anchor_candidates(roi)
        if not candidates: return None
        candidates.sort(key=lambda x:x[2], reverse=True)
        best=candidates[0]
        print(f"[선택된 앵커] {best[0]} ({best[2]}점)")
        return best[1]

    # ---------------- ROI 저장 ----------------
    def get_roi_info_and_save(self, roi_coords, anchor_coords):
        dialog = tk.Toplevel(self.root); dialog.title("ROI 정보 입력"); dialog.transient(self.root); dialog.grab_set()
        name_var=tk.StringVar(); method_var=tk.StringVar(value="ocr"); threshold_var=tk.IntVar(value=3)

        def update_threshold(*_):
            threshold_var.set(3 if method_var.get()=="ocr" else 100)
        method_var.trace('w', update_threshold)

        ttk.Label(dialog, text="이름:").pack(padx=10,pady=5)
        name_entry=ttk.Entry(dialog,textvariable=name_var); name_entry.pack(padx=10); name_entry.focus_set()
        ttk.Label(dialog, text="검증 방식:").pack(padx=10,pady=5)
        ttk.Radiobutton(dialog,text="OCR",variable=method_var,value="ocr").pack(anchor=tk.W,padx=20)
        ttk.Radiobutton(dialog,text="Contour",variable=method_var,value="contour").pack(anchor=tk.W,padx=20)

        ttk.Label(dialog, text="임계값:").pack(padx=10,pady=5)
        ttk.Entry(dialog,textvariable=threshold_var,width=10).pack(padx=10)

        def on_save():
            name=name_var.get().strip()
            if not name or name in self.rois:
                messagebox.showerror("오류","이름을 입력하거나 중복되지 않는 이름을 사용하세요.",parent=dialog); return
            self.rois[name]={'page':self.current_page,'coords':roi_coords,'anchor_coords':anchor_coords,'method':method_var.get(),'threshold':threshold_var.get()}
            self.display_page(); dialog.destroy()
        ttk.Button(dialog,text="저장",command=on_save).pack(pady=10)

    # ---------------- PDF 로딩/표시 ----------------
    def open_pdf(self, path=None, rois_to_load=None):
        if not path: path=filedialog.askopenfilename(title="템플릿 PDF 열기", filetypes=[("PDF Files","*.pdf")])
        if not path: return
        try:
            if self.pdf_doc: self.pdf_doc.close()
            self.pdf_doc=fitz.open(path); self.current_pdf_path=path; self.current_page=0
            self.rois=rois_to_load if rois_to_load else {}
            self.display_page()
        except Exception as e: messagebox.showerror("오류",f"PDF 열기 실패:\n{e}", parent=self.root)

    def display_page(self):
        if not self.pdf_doc: return
        page=self.pdf_doc[self.current_page]; mat=self.get_display_matrix()
        pix=page.get_pixmap(matrix=mat, alpha=False)
        img=Image.frombytes("RGB",[pix.width,pix.height],pix.samples)
        self.tk_image=ImageTk.PhotoImage(img)
        self.canvas.delete("all"); self.canvas.create_image(0,0,anchor=tk.NW,image=self.tk_image)
        self.draw_rois_on_canvas()
        self.page_label.config(text=f"페이지: {self.current_page+1}/{len(self.pdf_doc)}")
        self.update_roi_listbox()

    def draw_rois_on_canvas(self):
        for name,data in self.rois.items():
            if data.get('page')==self.current_page:
                x0,y0,x1,y1=self.pdf_to_screen_coords(data['coords'])
                color='blue' if data.get('method')=="ocr" else 'red'
                self.canvas.create_rectangle(x0,y0,x1,y1,outline=color,width=2,tags=name)
                self.canvas.create_text(x0,y0-5,text=name,anchor=tk.SW,fill=color,tags=name)
                if 'anchor_coords' in data:
                    ax0,ay0,ax1,ay1=self.pdf_to_screen_coords(data['anchor_coords'])
                    self.canvas.create_rectangle(ax0,ay0,ax1,ay1,outline="cyan",width=2,dash=(5,3),tags=name)
                    self.canvas.create_line((x0+x1)/2,(y0+y1)/2,(ax0+ax1)/2,(ay0+ay1)/2,fill="yellow",dash=(2,2),tags=name)

    def update_roi_listbox(self):
        self.roi_listbox.delete(0,tk.END)
        for name,data in sorted(self.rois.items()):
            if data.get('page')==self.current_page: self.roi_listbox.insert(tk.END,name)

    def delete_selected_roi(self,event=None):
        sel=self.roi_listbox.curselection()
        if not sel: return
        roi_name=self.roi_listbox.get(sel[0])
        if messagebox.askyesno("삭제 확인",f"'{roi_name}' 영역을 삭제하시겠습니까?", parent=self.root):
            del self.rois[roi_name]; self.display_page()

    def prev_page(self):
        if self.pdf_doc and self.current_page>0: self.current_page-=1; self.display_page()
    def next_page(self):
        if self.pdf_doc and self.current_page<len(self.pdf_doc)-1: self.current_page+=1; self.display_page()

    # ---------------- 템플릿 저장/불러오기 ----------------
    def save_template(self):
        if not self.rois or not self.current_pdf_path:
            messagebox.showwarning("경고","PDF를 열고 ROI를 하나 이상 지정해야 합니다.",parent=self.root); return
        default_name=os.path.splitext(os.path.basename(self.current_pdf_path))[0]
        template_name=simpledialog.askstring("템플릿 저장","템플릿 이름:", parent=self.root, initialvalue=default_name)
        if not template_name: return
        self.templates[template_name]={'original_pdf_path':self.current_pdf_path,'rois':self.rois}
        try:
            with open("templates.json",'w',encoding='utf-8') as f: json.dump(self.templates,f,ensure_ascii=False,indent=2)
            messagebox.showinfo("성공",f"템플릿 '{template_name}' 저장 완료", parent=self.root)
        except Exception as e: messagebox.showerror("오류", f"저장 실패: {e}", parent=self.root)

    def load_all_templates(self):
        try:
            if os.path.exists("templates.json"):
                with open("templates.json",'r',encoding='utf-8') as f: return json.load(f)
        except Exception as e: messagebox.showwarning("경고",f"templates.json 로딩 실패:\n{e}", parent=self.root)
        return {}

    def load_template_from_list(self):
        self.templates=self.load_all_templates()
        if not self.templates: messagebox.showinfo("안내","저장된 템플릿이 없습니다.", parent=self.root); return
        dialog=tk.Toplevel(self.root); dialog.title("템플릿 불러오기"); dialog.transient(self.root); dialog.grab_set()
        listbox=tk.Listbox(dialog,width=50,height=15); listbox.pack(padx=10,pady=10)
        for name in sorted(self.templates.keys()): listbox.insert(tk.END,name)
        def on_load():
            sel=listbox.curselection()
            if not sel: return
            name=listbox.get(sel[0]); template=self.templates[name]
            self.open_pdf(path=template['original_pdf_path'], rois_to_load=template['rois']); dialog.destroy()
        ttk.Button(dialog,text="불러오기",command=on_load).pack(pady=5)

    def delete_template(self): pass

def main():
    root=tk.Tk(); app=TemplateManager(root); root.mainloop()
if __name__=="__main__": main()
