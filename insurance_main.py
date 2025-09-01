#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
보험 서류 검증 시스템 - 메인 실행
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

class InsuranceDocumentValidator:
    def __init__(self, root):
        self.root = root
        self.root.title("보험 서류 검증 시스템")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        # 폴더 구조 확인 및 생성
        self.ensure_folder_structure()
        
        # UI 구성
        self.setup_ui()
        
        # 중앙 배치
        self.center_window()
    
    def ensure_folder_structure(self):
        """폴더 구조 확인 및 생성"""
        base_folders = ['templates', 'output']
        
        for folder in base_folders:
            if not os.path.exists(folder):
                os.makedirs(folder)
        
        # 보험사 예시 폴더 생성 (처음 실행 시)
        insurance_companies = ['삼성화재', 'DB손해보험', '현대해상', 'KB손해보험', '메리츠화재']
        
        for company in insurance_companies:
            template_path = os.path.join('templates', company)
            output_path = os.path.join('output', company)
            
            if not os.path.exists(template_path):
                os.makedirs(template_path)
            
            if not os.path.exists(output_path):
                os.makedirs(output_path)
    
    def setup_ui(self):
        """UI 구성"""
        # 타이틀
        title_label = ttk.Label(self.root, text="보험 서류 검증 시스템", 
                               font=('Arial', 18, 'bold'))
        title_label.pack(pady=20)
        
        # 설명
        desc_label = ttk.Label(self.root, 
                              text="보험 서류가 올바르게 작성되었는지 자동으로 검증합니다",
                              font=('Arial', 10))
        desc_label.pack(pady=5)
        
        # 버튼 프레임
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=30)
        
        # 1단계: 템플릿 설정
        step1_btn = ttk.Button(button_frame, 
                              text="1단계: 원본 템플릿 설정\n(빈 서류 → 검증 영역 지정)",
                              command=self.open_template_manager,
                              width=30)
        step1_btn.pack(pady=10)
        
        # 2단계: 서류 검증
        step2_btn.pack(pady=15)
        
        # 3단계 버튼
        step3_btn = ttk.Button(btn_frame,
                              text="3단계: 검증 결과 확인\n(output 폴더 열기)",
                              command=self.open_output_folder,
                              width=35)
        step3_btn.pack(pady=15)
        
        # 하단 정보
        info_frame = ttk.Frame(self.root)
        info_frame.pack(side=tk.BOTTOM, pady=20)
        
        ttk.Label(info_frame, text="📁 templates: 보험사별 원본 템플릿").pack()
        ttk.Label(info_frame, text="📁 output: 보험사별 검증 결과").pack()
    
    def center_window(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.root.winfo_screenheight() // 2) - (400 // 2)
        self.root.geometry(f"500x400+{x}+{y}")
    
    def open_template_manager(self):
        try:
            from template_manager import TemplateManager
            template_window = tk.Toplevel(self.root)
            TemplateManager(template_window)
        except Exception as e:
            messagebox.showerror("오류", f"템플릿 관리자 실행 실패:\n{str(e)}")
    
    def open_validator(self):
        try:
            from document_validator import DocumentValidator
            validator_window = tk.Toplevel(self.root)
            DocumentValidator(validator_window)
        except Exception as e:
            messagebox.showerror("오류", f"검증 도구 실행 실패:\n{str(e)}")
    
    def open_output_folder(self):
        output_path = os.path.join(os.getcwd(), 'output')
        if os.path.exists(output_path):
            os.startfile(output_path)
        else:
            messagebox.showinfo("안내", "아직 검증 결과가 없습니다.")

def main():
    root = tk.Tk()
    app = InsuranceValidator(root)
    root.mainloop()

if __name__ == "__main__":
    main() = ttk.Button(button_frame,
                              text="2단계: 서류 검증 실행\n(작성된 서류 → 자동 검증)",
                              command=self.open_validator,
                              width=30)
        step2_btn.pack(pady=10)
        
        # 3단계: 결과 확인
        step3_btn = ttk.Button(button_frame,
                              text="3단계: 검증 결과 확인\n(output 폴더 열기)",
                              command=self.open_output_folder,
                              width=30)
        step3_btn.pack(pady=10)
        
        # 하단 정보
        info_frame = ttk.Frame(self.root)
        info_frame.pack(side=tk.BOTTOM, pady=20)
        
        ttk.Label(info_frame, text="📁 templates: 보험사별 원본 템플릿 저장", 
                 font=('Arial', 9)).pack()
        ttk.Label(info_frame, text="📁 output: 보험사별 검증 결과 저장", 
                 font=('Arial', 9)).pack()
    
    def center_window(self):
        """창을 화면 중앙에 배치"""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.root.winfo_screenheight() // 2) - (400 // 2)
        self.root.geometry(f"600x400+{x}+{y}")
    
    def open_template_manager(self):
        """템플릿 관리 도구 열기"""
        try:
            from template_manager import TemplateManager
            
            # 새 창에서 템플릿 관리자 실행
            template_window = tk.Toplevel(self.root)
            app = TemplateManager(template_window)
            
        except ImportError:
            messagebox.showerror("오류", "템플릿 관리 모듈을 찾을 수 없습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"템플릿 관리자 실행 실패:\n{str(e)}")
    
    def open_validator(self):
        """검증 도구 열기"""
        try:
            from document_validator import DocumentValidator
            
            # 새 창에서 검증 도구 실행
            validator_window = tk.Toplevel(self.root)
            app = DocumentValidator(validator_window)
            
        except ImportError:
            messagebox.showerror("오류", "검증 모듈을 찾을 수 없습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"검증 도구 실행 실패:\n{str(e)}")
    
    def open_output_folder(self):
        """결과 폴더 열기"""
        output_path = os.path.join(os.getcwd(), 'output')
        if os.path.exists(output_path):
            os.startfile(output_path)
        else:
            messagebox.showinfo("안내", "아직 검증 결과가 없습니다.\n먼저 서류 검증을 실행해주세요.")

def main():
    """메인 함수"""
    root = tk.Tk()
    app = InsuranceDocumentValidator(root)
    root.mainloop()

if __name__ == "__main__":
    main()
