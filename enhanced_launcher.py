# enhanced_launcher.py (최종 정리 버전)

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess

class EnhancedLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF 검증 시스템")
        self.root.geometry("500x350")
        self.setup_ui()
        self.center_window()

    def setup_ui(self):
        title_frame = ttk.Frame(self.root); title_frame.pack(pady=20)
        ttk.Label(title_frame, text="PDF 양식 검증 시스템", font=('Arial', 18, 'bold')).pack()

        main_frame = ttk.Frame(self.root); main_frame.pack(pady=20, padx=30, fill=tk.X)

        step1 = ttk.LabelFrame(main_frame, text="1단계: 템플릿 관리", padding=10)
        step1.pack(fill=tk.X, pady=(0,15))
        ttk.Button(step1, text="템플릿 생성 및 편집", command=self.open_template_manager).pack(fill=tk.X)

        step2 = ttk.LabelFrame(main_frame, text="2단계: 서류 검증", padding=10)
        step2.pack(fill=tk.X)
        ttk.Button(step2, text="검증 도구 실행", command=self.open_validator).pack(fill=tk.X)

    def center_window(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 500) // 2
        y = (self.root.winfo_screenheight() - 350) // 2
        self.root.geometry(f"500x350+{x}+{y}")

    def open_template_manager(self):
        try:
            script_path = os.path.join('src', 'template_manager.py')
            subprocess.Popen([sys.executable, script_path])
        except Exception as e:
            messagebox.showerror("오류", f"템플릿 관리 도구 실행 실패:\n{e}")

    def open_validator(self):
        try:
            script_path = os.path.join('src', 'pdf_validator_gui.py')
            subprocess.Popen([sys.executable, script_path])
        except Exception as e:
            messagebox.showerror("오류", f"검증 도구 실행 실패:\n{e}")

def main():
    # 필요한 폴더 구조 생성
    os.makedirs("templates", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    os.makedirs("input", exist_ok=True)

    root = tk.Tk()
    app = EnhancedLauncher(root)
    root.mainloop()

if __name__ == "__main__":
    main()