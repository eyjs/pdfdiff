#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROI 템플릿 편집 기능 완전 구현
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os

class TemplateEditor:
    def __init__(self, roi_selector_instance):
        self.roi_selector = roi_selector_instance
        self.current_template_name = None
    
    def load_template(self):
        """기존 템플릿 불러오기"""
        try:
            with open('templates.json', 'r', encoding='utf-8') as f:
                templates = json.load(f)
            
            if not templates:
                messagebox.showinfo("안내", "저장된 템플릿이 없습니다.")
                return
            
            # 템플릿 선택
            template_name = self.select_template(templates)
            if template_name:
                self.load_template_data(template_name, templates[template_name])
                
        except Exception as e:
            messagebox.showerror("오류", str(e))
    
    def select_template(self, templates):
        """템플릿 선택 대화상자"""
        dialog = tk.Toplevel(self.roi_selector.root)
        dialog.title("템플릿 선택")
        dialog.geometry("500x300")
        dialog.grab_set()
        
        ttk.Label(dialog, text="편집할 템플릿:", font=('Arial', 12)).pack(pady=20)
        
        listbox = tk.Listbox(dialog)
        listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0,20))
        
        template_names = list(templates.keys())
        for name in template_names:
            data = templates[name]
            roi_count = len(data.get('rois', {}))
            listbox.insert(tk.END, f"{name} ({roi_count}개 영역)")
        
        selected = None
        
        def on_select():
            nonlocal selected
            sel = listbox.curselection()
            if sel:
                selected = template_names[sel[0]]
            dialog.destroy()
        
        ttk.Button(dialog, text="선택", command=on_select).pack(pady=10)
        
        dialog.wait_window()
        return selected
    
    def load_template_data(self, name, data):
        """템플릿 데이터 로드"""
        self.current_template_name = name
        
        # PDF 로드
        pdf_path = data.get('original_pdf_path')
        if pdf_path and os.path.exists(pdf_path):
            import fitz
            
            if self.roi_selector.pdf_doc:
                self.roi_selector.pdf_doc.close()
            
            self.roi_selector.pdf_doc = fitz.open(pdf_path)
            self.roi_selector.current_pdf_path = pdf_path
            self.roi_selector.current_page = 0
            self.roi_selector.total_pages = len(self.roi_selector.pdf_doc)
            
            # ROI 데이터 로드
            self.roi_selector.rois = data.get('rois', {})
            
            # 화면 업데이트
            self.roi_selector.display_page()
            self.roi_selector.update_roi_list()
            
            messagebox.showinfo("완료", f"템플릿 '{name}'이 로드되었습니다.")

# ROI 선택기에 통합할 함수
def add_template_editing_to_roi_selector(roi_selector):
    """ROI 선택기에 템플릿 편집 기능 추가"""
    editor = TemplateEditor(roi_selector)
    
    # 기존 UI에 편집 버튼 추가
    if hasattr(roi_selector, 'control_frame'):
        edit_btn_frame = ttk.Frame(roi_selector.control_frame)
        edit_btn_frame.pack(fill=tk.X, pady=(10,0))
        
        ttk.Button(edit_btn_frame, text="📂 기존 템플릿 편집", 
                  command=editor.load_template).pack(side=tk.LEFT)
    
    return editor
