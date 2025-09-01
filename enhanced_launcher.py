#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
강화된 보험 서류 검증 시스템 런처
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox

class EnhancedLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("보험 서류 검증 시스템 v2.0")
        self.root.geometry("600x500")
        self.setup_ui()
        self.center_window()
    
    def setup_ui(self):
        # 제목
        title_frame = ttk.Frame(self.root)
        title_frame.pack(pady=20)
        
        ttk.Label(title_frame, text="보험 서류 검증 시스템", 
                 font=('Arial', 18, 'bold')).pack()
        ttk.Label(title_frame, text="v2.0 강화판", 
                 font=('Arial', 10), foreground="blue").pack()
        
        # 단계별 버튼
        main_frame = ttk.Frame(self.root)
        main_frame.pack(pady=30)
        
        # 1단계
        step1 = ttk.LabelFrame(main_frame, text="1단계: 템플릿 관리", padding=15)
        step1.pack(fill=tk.X, pady=(0,15))
        
        ttk.Button(step1, text="🎯 템플릿 설정 (편집 지원)",
                  command=self.open_roi_selector, width=40).pack()
        ttk.Label(step1, text="• 새 템플릿 생성 및 기존 템플릿 편집", 
                 foreground="gray").pack()
        
        # 2단계
        step2 = ttk.LabelFrame(main_frame, text="2단계: 서류 검증", padding=15)
        step2.pack(fill=tk.X, pady=(0,15))
        
        ttk.Button(step2, text="📋 서류 검증 (디버깅 지원)",
                  command=self.open_validator, width=40).pack()
        ttk.Label(step2, text="• PDF 재업로드, 연속 검사, 실패 원인 분석", 
                 foreground="gray").pack()
        
        # 3단계
        step3 = ttk.LabelFrame(main_frame, text="3단계: 결과 확인", padding=15)
        step3.pack(fill=tk.X)
        
        btn_frame = ttk.Frame(step3)
        btn_frame.pack()
        
        ttk.Button(btn_frame, text="📁 결과 폴더",
                  command=self.open_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📊 폴더 정보",
                  command=self.show_info).pack(side=tk.LEFT, padx=5)
        
        # 하단 정보
        info_frame = ttk.Frame(self.root)
        info_frame.pack(side=tk.BOTTOM, pady=20)
        
        ttk.Label(info_frame, text="🚀 새 기능: 템플릿편집, PDF재업로드, 디버깅, 체계적저장", 
                 foreground="blue").pack()
    
    def center_window(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - 300
        y = (self.root.winfo_screenheight() // 2) - 250
        self.root.geometry(f"600x500+{x}+{y}")
    
    def open_roi_selector(self):
        """ROI 선택기 실행"""
        try:
            import subprocess
            script_path = os.path.join('src', 'roi_selector.py')
            subprocess.Popen([sys.executable, script_path])
        except Exception as e:
            messagebox.showerror("오류", str(e))
    
    def open_validator(self):
        """PDF 검증기 실행"""
        try:
            import subprocess
            script_path = os.path.join('src', 'pdf_validator_gui.py')
            subprocess.Popen([sys.executable, script_path])
        except Exception as e:
            messagebox.showerror("오류", str(e))
    
    def open_results(self):
        """결과 폴더 열기"""
        output_path = "output"
        if os.path.exists(output_path):
            os.startfile(output_path)
        else:
            messagebox.showinfo("안내", "결과 폴더가 없습니다.")
    
    def show_info(self):
        """폴더 구조 정보 표시"""
        info_window = tk.Toplevel(self.root)
        info_window.title("시스템 정보")
        info_window.geometry("500x400")
        
        text = tk.Text(info_window, wrap=tk.WORD)
        scroll = ttk.Scrollbar(info_window, command=text.yview)
        text.config(yscrollcommand=scroll.set)
        
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)
        scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=20)
        
        info_text = """📁 시스템 구조:

🏢 templates/
  ├── 삼성화재/
  ├── DB손해보험/
  └── 기타 보험사/

📊 output/
  ├── 보험사명/
  │   ├── 템플릿명/
  │   │   ├── fail/      ← 실패 케이스
  │   │   └── success/   ← 성공 케이스
  │   └── ...

🚀 새로운 기능:

1️⃣ 템플릿 편집
  • 기존 템플릿 불러와서 수정
  • 다른 이름으로 저장
  • 템플릿 삭제

2️⃣ PDF 재업로드
  • 다른 PDF로 즉시 재검사
  • 연속 검사 모드
  • 검사 이력 관리

3️⃣ 디버깅 모드
  • 실패 원인 상세 분석
  • ROI별 이미지 저장
  • 개선 권장사항 제공

4️⃣ 체계적 저장
  • 보험사별 분류
  • 템플릿별 정리
  • 성공/실패 구분"""
        
        text.insert(tk.END, info_text)
        text.config(state='disabled')

def main():
    root = tk.Tk()
    app = EnhancedLauncher(root)
    root.mainloop()

if __name__ == "__main__":
    main()
