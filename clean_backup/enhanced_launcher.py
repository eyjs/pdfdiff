# enhanced_launcher.py (v2.1 - Window focus fix)

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox

class EnhancedLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("보험서류 검증 시스템 v2.1")
        self.root.geometry("500x350")
        self.setup_ui()
        self.center_window()

    def setup_ui(self):
        title_frame = ttk.Frame(self.root)
        title_frame.pack(pady=20)
        ttk.Label(title_frame, text="보험서류 검증 시스템", font=('Arial', 18, 'bold')).pack()
        ttk.Label(title_frame, text="v2.1", font=('Arial', 10)).pack()

        main_frame = ttk.Frame(self.root)
        main_frame.pack(pady=20, padx=30, fill=tk.X)

        step1 = ttk.LabelFrame(main_frame, text="1단계: 템플릿 관리", padding=10)
        step1.pack(fill=tk.X, pady=(0,15))

        btn1 = ttk.Button(step1, text="템플릿 생성 및 편집", command=self.open_template_manager)
        btn1.pack(fill=tk.X, pady=2)

        step2 = ttk.LabelFrame(main_frame, text="2단계: 서류 검증", padding=10)
        step2.pack(fill=tk.X)

        btn2 = ttk.Button(step2, text="검증 도구 실행", command=self.open_validator)
        btn2.pack(fill=tk.X, pady=2)

        info_frame = ttk.Frame(self.root)
        info_frame.pack(side=tk.BOTTOM, pady=10)
        ttk.Label(info_frame, text="PDF Validator Systems © 2025", font=('Arial', 8)).pack()

    def center_window(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 500) // 2
        y = (self.root.winfo_screenheight() - 350) // 2
        self.root.geometry(f"500x350+{x}+{y}")

    def open_template_manager(self):
        self.root.withdraw()
        try:
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))

            src_path = os.path.join(base_path, 'src')
            if src_path not in sys.path:
                sys.path.insert(0, src_path)

            from template_manager import TemplateManager

            template_window = tk.Toplevel(self.root)
            template_window.title("템플릿 관리자")
            template_window.geometry("1200x850")

            def on_close():
                self.root.deiconify()
                template_window.destroy()

            template_window.protocol("WM_DELETE_WINDOW", on_close)

            app = TemplateManager(template_window)

        except ImportError as e:
            messagebox.showerror("오류", f"템플릿 관리자 모듈을 찾을 수 없습니다:\n{e}", parent=self.root)
            self.root.deiconify()
        except Exception as e:
            messagebox.showerror("오류", f"템플릿 관리자 실행 실패:\n{e}", parent=self.root)
            self.root.deiconify()

    def open_validator(self):
        self.root.withdraw()
        try:
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))

            src_path = os.path.join(base_path, 'src')
            if src_path not in sys.path:
                sys.path.insert(0, src_path)

            from pdf_validator_gui import PDFValidatorGUI

            validator_window = tk.Toplevel(self.root)
            validator_window.title("PDF 검증 도구")
            validator_window.geometry("1200x900")

            def on_close():
                self.root.deiconify()
                validator_window.destroy()

            validator_window.protocol("WM_DELETE_WINDOW", on_close)

            app = PDFValidatorGUI(validator_window)

        except ImportError as e:
            messagebox.showerror("오류", f"검증 도구 모듈을 찾을 수 없습니다:\n{e}", parent=self.root)
            self.root.deiconify()
        except Exception as e:
            messagebox.showerror("오류", f"검증 도구 실행 실패:\n{e}", parent=self.root)
            self.root.deiconify()

def main():
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
        os.chdir(application_path)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(application_path)

    os.makedirs("templates", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    os.makedirs("input", exist_ok=True)

    root = tk.Tk()
    app = EnhancedLauncher(root)
    root.mainloop()

if __name__ == "__main__":
    main()