#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
보험 서류 템플릿 관리자
1단계: 원본 템플릿 설정 및 ROI 지정
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json
import os
import fitz
from PIL import Image, ImageTk
import io

class TemplateManager:
    def __init__(self, root):
        self.root = root
        self.root.title("1단계: 원본 템플릿 설정")
        self.root.geometry("1200x800")
        
        self.pdf_doc = None
        self.current_page = 0
        self.current_company = ""
        self.scale_factor = 1.0
        self.rois = {}
        
        self.start_x = 0
        self.start_y = 0
        self.is_dragging = False
        
        self.setup_ui()
        self.load_companies()
    
    def setup_ui(self):
        # 좌측 패널
        left_frame = ttk.Frame(self.root, width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        left_frame.pack_propagate(False)
        
        # 보험사 선택
        ttk.Label(left_frame, text="보험사:").pack(anchor=tk.W, pady=(0,5))
        
        self.company_var = tk.StringVar()
        self.company_combo = ttk.Combobox(left_frame, textvariable=self.company_var)
        self.company_combo.pack(fill=tk.X, pady=(0,10))
        self.company_combo.bind('<<ComboboxSelected>>', self.on_company_selected)
        
        ttk.Button(left_frame, text="+ 새 보험사", command=self.add_new_company).pack(fill=tk.X, pady=(0,20))
        
        # PDF 선택
        ttk.Label(left_frame, text="원본 PDF (빈 서류):").pack(anchor=tk.W, pady=(0,5))
        ttk.Button(left_frame, text="PDF 선택", command=self.select_pdf).pack(fill=tk.X, pady=(0,5))
        
        self.file_label = ttk.Label(left_frame, text="파일을 선택하세요", foreground="gray")
        self.file_label.pack(anchor=tk.W, pady=(0,20))
        
        # 템플릿 이름
        ttk.Label(left_frame, text="템플릿 이름:").pack(anchor=tk.W, pady=(0,5))
        self.template_name_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.template_name_var).pack(fill=tk.X, pady=(0,20))
        
        # ROI 목록
        ttk.Label(left_frame, text="검증 영역:").pack(anchor=tk.W, pady=(0,5))
        
        self.roi_listbox = tk.Listbox(left_frame, height=10)
        self.roi_listbox.pack(fill=tk.BOTH, expand=True, pady=(0,10))
        
        # 버튼
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="영역 삭제", command=self.delete_roi).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="저장", command=self.save_template).pack(side=tk.RIGHT)
        
        # 우측 PDF 뷰어
        right_frame = ttk.Frame(self.root)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(0,10), pady=10)
        
        # 페이지 네비게이션
        nav_frame = ttk.Frame(right_frame)
        nav_frame.pack(fill=tk.X, pady=(0,10))
        
        ttk.Button(nav_frame, text="◀", command=self.prev_page).pack(side=tk.LEFT)
        self.page_label = ttk.Label(nav_frame, text="페이지: 0/0")
        self.page_label.pack(side=tk.LEFT, padx=20)
        ttk.Button(nav_frame, text="▶", command=self.next_page).pack(side=tk.LEFT)
        
        # 캔버스
        self.canvas = tk.Canvas(right_frame, bg='white', cursor='crosshair')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self.end_drag)
    
    def load_companies(self):
        if os.path.exists("templates"):
            companies = [d for d in os.listdir("templates") 
                        if os.path.isdir(os.path.join("templates", d))]
            self.company_combo['values'] = companies
    
    def add_new_company(self):
        company_name = simpledialog.askstring("새 보험사", "보험사 이름:")
        if company_name:
            os.makedirs(f'templates/{company_name}', exist_ok=True)
            os.makedirs(f'output/{company_name}', exist_ok=True)
            self.load_companies()
            self.company_var.set(company_name)
    
    def on_company_selected(self, event=None):
        self.current_company = self.company_var.get()
    
    def select_pdf(self):
        if not self.current_company:
            messagebox.showwarning("경고", "먼저 보험사를 선택하세요.")
            return
        
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            try:
                self.pdf_doc = fitz.open(file_path)
                self.current_page = 0
                
                # 파일 복사
                import shutil
                target = os.path.join('templates', self.current_company, os.path.basename(file_path))
                shutil.copy2(file_path, target)
                
                filename = os.path.splitext(os.path.basename(file_path))[0]
                self.template_name_var.set(filename)
                
                self.file_label.config(text=f"선택됨: {os.path.basename(file_path)}", foreground="green")
                self.display_page()
                
            except Exception as e:
                messagebox.showerror("오류", str(e))
    
    def display_page(self):
        if not self.pdf_doc:
            return
        
        try:
            page = self.pdf_doc[self.current_page]
            mat = fitz.Matrix(1.5, 1.5)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("ppm")
            
            pil_image = Image.open(io.BytesIO(img_data))
            
            # 크기 조정
            canvas_width = 800
            canvas_height = 600
            img_width, img_height = pil_image.size
            
            scale_x = canvas_width / img_width
            scale_y = canvas_height / img_height
            self.scale_factor = min(scale_x, scale_y, 1.0)
            
            new_width = int(img_width * self.scale_factor)
            new_height = int(img_height * self.scale_factor)
            
            pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.tk_image = ImageTk.PhotoImage(pil_image)
            
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
            
            # 기존 ROI 표시
            for roi_name, roi_data in self.rois.items():
                if roi_data.get('page') == self.current_page:
                    coords = roi_data['coords']
                    x1, y1, x2, y2 = [c * self.scale_factor for c in coords]
                    color = 'red' if roi_data['method'] == 'contour' else 'blue'
                    self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=2)
                    self.canvas.create_text(x1, y1-10, text=roi_name, anchor=tk.SW, fill=color)
            
            total_pages = len(self.pdf_doc)
            self.page_label.config(text=f"페이지: {self.current_page + 1}/{total_pages}")
            
        except Exception as e:
            messagebox.showerror("오류", str(e))
    
    def prev_page(self):
        if self.pdf_doc and self.current_page > 0:
            self.current_page -= 1
            self.display_page()
    
    def next_page(self):
        if self.pdf_doc and self.current_page < len(self.pdf_doc) - 1:
            self.current_page += 1
            self.display_page()
    
    def start_drag(self, event):
        if not self.pdf_doc:
            return
        self.start_x = event.x
        self.start_y = event.y
        self.is_dragging = True
        self.canvas.delete("temp_rect")
    
    def drag_motion(self, event):
        if not self.is_dragging:
            return
        self.canvas.delete("temp_rect")
        self.canvas.create_rectangle(self.start_x, self.start_y, event.x, event.y,
                                   outline="green", width=2, tags="temp_rect")
    
    def end_drag(self, event):
        if not self.is_dragging:
            return
        self.is_dragging = False
        
        # 최소 크기 확인
        if abs(event.x - self.start_x) < 20 or abs(event.y - self.start_y) < 20:
            self.canvas.delete("temp_rect")
            return
        
        self.configure_roi(self.start_x, self.start_y, event.x, event.y)
    
    def configure_roi(self, x1, y1, x2, y2):
        dialog = tk.Toplevel(self.root)
        dialog.title("검증 영역 설정")
        dialog.geometry("350x200")
        
        # 이름
        ttk.Label(dialog, text="영역 이름:").pack(padx=20, pady=(20,5))
        name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=name_var).pack(padx=20, pady=(0,15))
        
        # 방법
        ttk.Label(dialog, text="검증 방법:").pack(padx=20, pady=(0,5))
        method_var = tk.StringVar(value="ocr")
        
        ttk.Radiobutton(dialog, text="OCR (텍스트)", variable=method_var, value="ocr").pack(padx=20)
        ttk.Radiobutton(dialog, text="Contour (도형)", variable=method_var, value="contour").pack(padx=20)
        
        # 임계값
        ttk.Label(dialog, text="민감도:").pack(padx=20, pady=(10,5))
        threshold_var = tk.IntVar(value=5)
        ttk.Scale(dialog, from_=1, to=20, variable=threshold_var, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=20)
        
        # 버튼
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)
        
        def save_roi():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("경고", "이름을 입력하세요.")
                return
            
            real_coords = [x1/self.scale_factor, y1/self.scale_factor, x2/self.scale_factor, y2/self.scale_factor]
            
            self.rois[name] = {
                'page': self.current_page,
                'coords': real_coords,
                'method': method_var.get(),
                'threshold': threshold_var.get()
            }
            
            self.canvas.delete("temp_rect")
            color = 'red' if method_var.get() == 'contour' else 'blue'
            self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=2)
            self.canvas.create_text(x1, y1-10, text=name, anchor=tk.SW, fill=color)
            
            self.update_roi_list()
            dialog.destroy()
        
        ttk.Button(btn_frame, text="저장", command=save_roi).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="취소", command=lambda: (self.canvas.delete("temp_rect"), dialog.destroy())).pack(side=tk.LEFT)
    
    def update_roi_list(self):
        self.roi_listbox.delete(0, tk.END)
        for name, data in self.rois.items():
            method = "텍스트" if data['method'] == 'ocr' else "도형"
            self.roi_listbox.insert(tk.END, f"{name} (페이지{data['page']+1}, {method})")
    
    def delete_roi(self):
        selection = self.roi_listbox.curselection()
        if selection:
            roi_names = list(self.rois.keys())
            del self.rois[roi_names[selection[0]]]
            self.update_roi_list()
            self.display_page()
    
    def save_template(self):
        if not self.current_company or not self.template_name_var.get().strip() or not self.rois:
            messagebox.showwarning("경고", "모든 항목을 입력하세요.")
            return
        
        template_data = {
            'company': self.current_company,
            'template_name': self.template_name_var.get().strip(),
            'pdf_file': os.path.basename(self.pdf_doc.name),
            'rois': self.rois
        }
        
        template_file = os.path.join('templates', self.current_company, f"{self.template_name_var.get().strip()}.json")
        
        try:
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("완료", f"템플릿 저장됨:\n{template_file}")
            self.rois = {}
            self.update_roi_list()
            
        except Exception as e:
            messagebox.showerror("오류", str(e))

def main():
    root = tk.Tk()
    app = TemplateManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()
