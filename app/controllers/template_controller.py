"""
Template Controller
템플릿 관리 컨트롤러
"""
import tkinter as tk
from tkinter import messagebox, ttk, filedialog, simpledialog
from typing import Optional, Callable
import json, os, fitz
from PIL import Image, ImageTk
import cv2, numpy as np

from domain.services.template_service import TemplateService
from infrastructure.repositories.json_template_repository import JsonTemplateRepository
from shared.exceptions import *


class TemplateController:
    """템플릿 관리 컨트롤러"""

    def __init__(self):
        # 의존성 주입 (Dependency Injection)
        self.template_repository = JsonTemplateRepository()
        self.template_service = TemplateService(self.template_repository)
        
        # UI 참조
        self.current_window = None
        self.status_label = None
        self.template_listbox = None
        self.canvas = None
        self.page_label = None

        # PDF 및 ROI 관련 변수
        self.pdf_doc = None
        self.current_page = 0
        self.rois = {}
        self.current_pdf_path = None
        self.start_x, self.start_y, self.current_rect = 0, 0, None

        # 템플릿 데이터 로드 (초기화 시)
        self.templates = self.template_service.get_all_templates()

    def show_template_manager(self, parent: tk.Tk, on_close: Optional[Callable] = None):
        """템플릿 관리자 창 표시"""
        try:
            # 기존 창이 있으면 포커스만 이동
            if self.current_window and self.current_window.winfo_exists():
                self.current_window.lift()
                self.current_window.focus_force()
                return

            # 새 창 생성
            self.current_window = tk.Toplevel(parent)
            self.current_window.title("템플릿 관리자")
            self.current_window.geometry("1200x850")

            # 창 닫힘 이벤트 처리
            def on_window_close():
                self.cleanup()
                if on_close:
                    on_close()

            self.current_window.protocol("WM_DELETE_WINDOW", on_window_close)

            # 실제 템플릿 관리자 UI 로드
            self._load_template_manager_ui()

        except Exception as e:
            raise TemplateException(f"템플릿 관리자 실행 실패: {str(e)}")

    def _load_template_manager_ui(self):
        """템플릿 관리자 UI 로드"""
        top_frame = ttk.Frame(self.current_window, padding=10); top_frame.pack(side=tk.TOP, fill=tk.X)
        ttk.Button(top_frame, text="새 PDF 열기", command=self.open_pdf).pack(side=tk.LEFT, padx=5)

        nav_frame = ttk.Frame(top_frame)
        ttk.Button(nav_frame, text="◀ 이전", command=self.prev_page).pack(side=tk.LEFT)
        self.page_label = ttk.Label(nav_frame, text="페이지: 0/0", width=15, anchor="center"); self.page_label.pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="다음 ▶", command=self.next_page).pack(side=tk.LEFT)
        nav_frame.pack(side=tk.LEFT, padx=10)

        ttk.Button(top_frame, text="템플릿 삭제", command=self.delete_template).pack(side=tk.RIGHT, padx=5)
        ttk.Button(top_frame, text="템플릿 저장", command=self.save_template).pack(side=tk.RIGHT)
        ttk.Button(top_frame, text="템플릿 불러오기", command=self.load_template_from_list).pack(side=tk.RIGHT, padx=5)

        main_frame = ttk.Frame(self.current_window, padding=(10, 0, 10, 10)); main_frame.pack(fill=tk.BOTH, expand=True)
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

        self.status_label = ttk.Label(self.current_window, text="템플릿 관리자가 준비되었습니다.", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)

        self.current_window.bind("<Configure>", lambda e: self.display_page() if self.pdf_doc else None)

    def create_new_template(self):
        """새 템플릿 생성"""
        try:
            from tkinter import filedialog, simpledialog

            # PDF 파일 선택
            pdf_path = filedialog.askopenfilename(
                title="템플릿용 PDF 선택",
                filetypes=[("PDF files", "*.pdf")]
            )

            if not pdf_path:
                return

            # 템플릿 이름 입력
            template_name = simpledialog.askstring(
                "템플릿 이름",
                "새 템플릿의 이름을 입력하세요:",
                parent=self.current_window
            )

            if not template_name:
                return

            # 템플릿 생성
            template = self.template_service.create_template(template_name, pdf_path)

            if self.template_service.save_template(template):
                self.update_status(f"템플릿 '{template_name}'이 생성되었습니다.")
                self.refresh_template_list()
                messagebox.showinfo("성공", f"템플릿 '{template_name}'이 생성되었습니다.")
            else:
                messagebox.showerror("오류", "템플릿 저장에 실패했습니다.")

        except TemplateAlreadyExistsError as e:
            messagebox.showerror("오류", str(e))
        except Exception as e:
            messagebox.showerror("오류", f"템플릿 생성 실패: {str(e)}")

    def edit_template(self):
        """템플릿 편집"""
        try:
            selection = self.template_listbox.curselection()
            if not selection:
                messagebox.showwarning("알림", "편집할 템플릿을 선택하세요.")
                return

            template_name = self.template_listbox.get(selection[0])
            template = self.template_service.get_template(template_name)

            if not template:
                messagebox.showerror("오류", f"템플릿 '{template_name}'을 찾을 수 없습니다.")
                return

            messagebox.showinfo("알림", f"'{template_name}' 템플릿 편집기가 곧 구현됩니다.")

        except Exception as e:
            messagebox.showerror("오류", f"템플릿 편집 실패: {str(e)}")

    def delete_template(self):
        """템플릿 삭제"""
        try:
            selection = self.template_listbox.curselection()
            if not selection:
                messagebox.showwarning("알림", "삭제할 템플릿을 선택하세요.")
                return

            template_name = self.template_listbox.get(selection[0])

            # 확인 대화상자
            if not messagebox.askyesno(
                "확인",
                f"'{template_name}' 템플릿을 정말 삭제하시겠습니까?",
                parent=self.current_window
            ):
                return

            # 템플릿 삭제
            if self.template_service.delete_template(template_name):
                self.update_status(f"템플릿 '{template_name}'이 삭제되었습니다.")
                self.refresh_template_list()
                messagebox.showinfo("성공", f"템플릿 '{template_name}'이 삭제되었습니다.")
            else:
                messagebox.showerror("오류", "템플릿 삭제에 실패했습니다.")

        except Exception as e:
            messagebox.showerror("오류", f"템플릿 삭제 실패: {str(e)}")

    def refresh_template_list(self):
        """템플릿 목록 새로고침"""
        try:
            self.template_listbox.delete(0, tk.END)

            template_names = self.template_service.get_template_names()
            for name in sorted(template_names):
                self.template_listbox.insert(tk.END, name)

            self.update_status(f"{len(template_names)}개의 템플릿이 있습니다.")

        except Exception as e:
            self.update_status(f"목록 새로고침 실패: {str(e)}")

    def update_status(self, message: str):
        """상태 메시지 업데이트"""
        if self.status_label:
            self.status_label.config(text=message)

    def cleanup(self):
        """리소스 정리"""
        if self.current_window and self.current_window.winfo_exists():
            self.current_window.destroy()
        self.current_window = None
