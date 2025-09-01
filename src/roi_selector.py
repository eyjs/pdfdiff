#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROI 선택 도구 (roi_selector.py)
PDF 템플릿에서 검증할 영역을 시각적으로 정의하고 저장하는 GUI 애플리케이션
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json
import os
import io
import fitz  # PyMuPDF
from PIL import Image, ImageTk
import cv2
import numpy as np


class ROISelector:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF ROI 선택 도구")
        self.root.geometry("1200x800")

        # 변수 초기화
        self.pdf_doc = None
        self.current_page = 0
        self.total_pages = 0
        self.current_pdf_path = ""
        self.scale_factor = 1.0
        self.rois = {}

        # 마우스 드래그 관련 변수
        self.start_x = 0
        self.start_y = 0
        self.rect_id = None
        self.is_dragging = False

        # 템플릿 편집 기능 추가 (ENHANCED_MODE일 때)
        if os.environ.get('ENHANCED_MODE') == '1':
            try:
                from template_editor import TemplateEditor
                self.template_editor = TemplateEditor(self)
                print("✅ 템플맿 편집 기능 활성화됨")
            except ImportError:
                print("⚠️ 템플맿 편집 모듈을 찾을 수 없습니다")

        # GUI 구성 요소
        self.setup_ui()
        self.load_existing_templates()

    def setup_ui(self):
        """UI 구성 요소 설정"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 상단 컨트롤 패널
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        # 🔧 템플릿 편집 기능 추가
        template_frame = ttk.LabelFrame(control_frame, text="템플릿 관리", padding=5)
        template_frame.pack(fill=tk.X, pady=(0,10))

        # 템플릿 관리 버튼들
        template_btn_frame = ttk.Frame(template_frame)
        template_btn_frame.pack(fill=tk.X)

        ttk.Button(template_btn_frame, text="📂 기존 템플릿 편집",
                  command=self.load_existing_templates).pack(side=tk.LEFT, padx=(0,5))

        ttk.Button(template_btn_frame, text="📋 템플릿 목록",
                  command=self.show_template_list).pack(side=tk.LEFT, padx=(0,5))

        # 현재 편집 상태 표시
        self.template_status_label = ttk.Label(template_btn_frame, text="새 템플릿 생성 모드",
                                              foreground="blue")
        self.template_status_label.pack(side=tk.LEFT, padx=(20,0))

        # 템플릿 편집 관련 변수
        self.current_editing_template = None

        # PDF 로드 프레임
        pdf_frame = ttk.Frame(control_frame)

        pdf_frame.pack(fill=tk.X, pady=(0,10))

        # PDF 로드 버튼
        ttk.Button(pdf_frame, text="PDF 파일 열기",
                  command=self.load_pdf).pack(side=tk.LEFT, padx=(0, 5))

        # 페이지 네비게이션
        nav_frame = ttk.Frame(control_frame)
        nav_frame.pack(side=tk.LEFT, padx=(10, 0))

        self.prev_btn = ttk.Button(nav_frame, text="◀ 이전",
                                  command=self.prev_page, state=tk.DISABLED)
        self.prev_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.page_label = ttk.Label(nav_frame, text="페이지: 0/0")
        self.page_label.pack(side=tk.LEFT, padx=(0, 5))

        self.next_btn = ttk.Button(nav_frame, text="다음 ▶",
                                  command=self.next_page, state=tk.DISABLED)
        self.next_btn.pack(side=tk.LEFT)

        # 저장 관련 컨트롤
        save_frame = ttk.Frame(control_frame)
        save_frame.pack(side=tk.RIGHT)

        ttk.Button(save_frame, text="템플릿 저장",
                  command=self.save_template).pack(side=tk.RIGHT, padx=(5, 0))

        # 중간 프레임 (PDF 뷰어 + ROI 리스트)
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # PDF 뷰어 프레임
        viewer_frame = ttk.Frame(content_frame)
        viewer_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # PDF 캔버스
        self.canvas = tk.Canvas(viewer_frame, bg="white", cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 마우스 이벤트 바인딩
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        # ROI 관리 프레임
        roi_frame = ttk.LabelFrame(content_frame, text="ROI 목록", width=300)
        roi_frame.pack(side=tk.RIGHT, fill=tk.Y)
        roi_frame.pack_propagate(False)

        # ROI 리스트박스
        self.roi_listbox = tk.Listbox(roi_frame, selectmode=tk.SINGLE)
        self.roi_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ROI 삭제 버튼
        ttk.Button(roi_frame, text="선택된 ROI 삭제",
                  command=self.delete_roi).pack(pady=(0, 10))

        # 상태바
        self.status_label = ttk.Label(main_frame, text="PDF 파일을 열어주세요.")
        self.status_label.pack(fill=tk.X, pady=(10, 0))

    def load_pdf(self):
        """PDF 파일 로드"""
        file_path = filedialog.askopenfilename(
            title="PDF 파일 선택",
            filetypes=[("PDF files", "*.pdf")]
        )

        if file_path:
            try:
                if self.pdf_doc:
                    self.pdf_doc.close()

                self.pdf_doc = fitz.open(file_path)
                self.current_pdf_path = file_path
                self.total_pages = len(self.pdf_doc)
                self.current_page = 0
                self.rois.clear()

                # UI 업데이트
                self.update_navigation()
                self.display_page()
                self.update_roi_list()

                self.status_label.config(text=f"로드된 파일: {os.path.basename(file_path)}")

            except Exception as e:
                messagebox.showerror("오류", f"PDF 로드 실패: {str(e)}")

    def display_page(self):
        """현재 페이지 표시"""
        if not self.pdf_doc:
            return

        try:
            # PDF 페이지를 이미지로 변환
            page = self.pdf_doc[self.current_page]

            # 원본 PDF 페이지 크기 저장
            self.current_page_original_size = (page.rect.width, page.rect.height)

            mat = fitz.Matrix(2, 2)  # 2배 확대
            pix = page.get_pixmap(matrix=mat)

            # numpy 배열로 변환
            img_data = pix.samples
            img_array = np.frombuffer(img_data, dtype=np.uint8)
            img_array = img_array.reshape(pix.height, pix.width, pix.n)

            # RGBA인 경우 RGB로 변환
            if pix.n == 4:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
            elif pix.n == 1:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)

            # PIL 이미지로 변환
            pil_image = Image.fromarray(img_array)

            # 캔버스 크기에 맞게 조정
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            if canvas_width > 1 and canvas_height > 1:
                # 비율 유지하면서 크기 조정
                img_ratio = pil_image.width / pil_image.height
                canvas_ratio = canvas_width / canvas_height

                if img_ratio > canvas_ratio:
                    new_width = canvas_width - 20
                    new_height = int(new_width / img_ratio)
                else:
                    new_height = canvas_height - 20
                    new_width = int(new_height * img_ratio)

                # PDF 원본 크기 대비 캔버스에 표시되는 이미지의 스케일 팩터 계산
                # 이 스케일은 PDF 좌표 -> 캔버스 좌표 변환에 사용됨
                self.display_scale = self.current_page_original_size[0] / new_width

                pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # 캔버스에 이미지 표시
            self.photo = ImageTk.PhotoImage(pil_image)
            self.canvas.delete("all")
            self.canvas.create_image(10, 10, anchor=tk.NW, image=self.photo)

        except Exception as e:
            messagebox.showerror("오류", f"페이지 표시 실패: {str(e)}")

    def update_navigation(self):
        """네비게이션 버튼 상태 업데이트"""
        self.page_label.config(text=f"페이지: {self.current_page + 1}/{self.total_pages}")

        self.prev_btn.config(state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)
        self.next_btn.config(state=tk.NORMAL if self.current_page < self.total_pages - 1 else tk.DISABLED)

    def prev_page(self):
        """이전 페이지로 이동"""
        if self.current_page > 0:
            self.current_page -= 1
            self.display_page()
            self.update_navigation()

    def next_page(self):
        """다음 페이지로 이동"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.display_page()
            self.update_navigation()

    def on_mouse_down(self, event):
        """마우스 다운 이벤트"""
        self.start_x = event.x
        self.start_y = event.y
        self.is_dragging = True

    def on_mouse_drag(self, event):
        """마우스 드래그 이벤트"""
        if self.is_dragging:
            # 기존 임시 사각형 삭제
            if self.rect_id:
                self.canvas.delete(self.rect_id)

            # 새 사각형 그리기
            self.rect_id = self.canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y,
                outline="red", width=2
            )

    def on_mouse_up(self, event):
        """마우스 업 이벤트"""
        if self.is_dragging:
            self.is_dragging = False

            # 최소 크기 검사
            if abs(event.x - self.start_x) > 10 and abs(event.y - self.start_y) > 10:
                self.create_roi(self.start_x, self.start_y, event.x, event.y)

            # 임시 사각형 삭제
            if self.rect_id:
                self.canvas.delete(self.rect_id)
                self.rect_id = None

    def create_roi(self, x1, y1, x2, y2):
        """ROI 생성"""
        # 좌표 정규화
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)

        # PDF 좌표계로 변환 (이미지 오프셋 10픽셀 고려)
        pdf_x1 = (min_x - 10) * self.display_scale
        pdf_y1 = (min_y - 10) * self.display_scale
        pdf_x2 = (max_x - 10) * self.display_scale
        pdf_y2 = (max_y - 10) * self.display_scale

        # ROI 정보 입력 대화상자
        roi_dialog = ROIDialog(self.root)
        result = roi_dialog.get_roi_info()

        if result:
            field_name, method, threshold = result

            # ROI 정보 저장
            roi_key = f"{field_name}_p{self.current_page}"
            self.rois[roi_key] = {
                "page": self.current_page,
                "coords": [pdf_x1, pdf_y1, pdf_x2, pdf_y2],
                "method": method,
                "threshold": threshold,
                "field_name": field_name
            }

            self.update_roi_list()
            self.draw_roi_rectangle(min_x, min_y, max_x, max_y, field_name)

    def draw_roi_rectangle(self, x1, y1, x2, y2, label):
        """ROI 사각형 그리기"""
        # 사각형 그리기
        rect_id = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline="blue", width=2, tags="roi"
        )

        # 라벨 그리기
        text_id = self.canvas.create_text(
            x1, y1 - 5, text=label, anchor=tk.SW,
            fill="blue", font=("Arial", 10, "bold"), tags="roi"
        )

    def update_roi_list(self):
        """ROI 목록 업데이트"""
        self.roi_listbox.delete(0, tk.END)

        for roi_key, roi_info in self.rois.items():
            display_text = f"[P{roi_info['page'] + 1}] {roi_info['field_name']} ({roi_info['method']})"
            self.roi_listbox.insert(tk.END, display_text)

    def delete_roi(self):
        """선택된 ROI 삭제"""
        selection = self.roi_listbox.curselection()
        if selection:
            index = selection[0]
            roi_keys = list(self.rois.keys())
            if index < len(roi_keys):
                del self.rois[roi_keys[index]]
                self.update_roi_list()

                # 캔버스에서 ROI 표시 다시 그리기
                self.redraw_rois()

    def redraw_rois(self):
        """현재 페이지의 ROI들 다시 그리기"""
        # 기존 ROI 표시 삭제
        self.canvas.delete("roi")

        # 현재 페이지의 ROI들만 다시 그리기
        for roi_info in self.rois.values():
            if roi_info['page'] == self.current_page:
                # 현재 캔버스 크기 가져오기
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()

                if canvas_width <= 1 or canvas_height <= 1: # Canvas not yet rendered
                    continue

                # 현재 페이지의 원본 크기 가져오기
                original_page_width, original_page_height = self.current_page_original_size

                # 현재 캔버스에 맞게 이미지가 어떻게 스케일되었는지 계산
                # display_page 로직과 동일하게 스케일 계산
                img_ratio = original_page_width / original_page_height
                canvas_ratio = canvas_width / canvas_height

                if img_ratio > canvas_ratio:
                    new_width = canvas_width - 20
                    current_display_scale = original_page_width / new_width
                else:
                    new_height = canvas_height - 20
                    current_display_scale = original_page_height / new_height

                # PDF 좌표를 화면 좌표로 변환
                x1 = roi_info['coords'][0] / current_display_scale + 10
                y1 = roi_info['coords'][1] / current_display_scale + 10
                x2 = roi_info['coords'][2] / current_display_scale + 10
                y2 = roi_info['coords'][3] / current_display_scale + 10

                self.draw_roi_rectangle(x1, y1, x2, y2, roi_info['field_name'])

    def save_template(self):
        """템플릿 저장 (편집 모드 고려)"""
        if not self.pdf_doc or not self.rois:
            messagebox.showwarning("경고", "PDF가 로드되지 않았거나 ROI가 정의되지 않았습니다.")
            return

        # 편집 모드 처리
        if hasattr(self, 'current_editing_template') and self.current_editing_template:
            # 편집 모드: 저장 방식 선택
            result = messagebox.askyesnocancel(
                "저장 방식 선택",
                f"현재 '{self.current_editing_template}' 템플릿을 편집 중입니다.\n\n"
                f"어떻게 저장하시겠습니까?\n\n"
                f"예: 기존 템플릿 덮어쓰기\n"
                f"아니오: 새 이름으로 저장\n"
                f"취소: 저장 취소"
            )

            if result is True:
                # 기존 템플릿 덮어쓰기
                self.update_existing_template()
            elif result is False:
                # 새 이름으로 저장
                self.save_as_new_template()
            # None이면 취소

        else:
            # 새 템플릿 생성 모드
            self.save_new_template()

    def update_existing_template(self):
        """기존 템플릿 업데이트"""
        try:
            # templates.json 로드
            with open('templates.json', 'r', encoding='utf-8') as f:
                templates = json.load(f)

            # 기존 템플릿 업데이트
            templates[self.current_editing_template] = {
                "original_pdf_path": self.current_pdf_path,
                "rois": self.rois.copy()
            }

            # 저장
            with open('templates.json', 'w', encoding='utf-8') as f:
                json.dump(templates, f, ensure_ascii=False, indent=2)

            messagebox.showinfo("완료",
                f"템플릿 '{self.current_editing_template}'이 업데이트되었습니다.\n\n"
                f"ROI 개수: {len(self.rois)}개")

        except Exception as e:
            messagebox.showerror("오류", f"템플릿 업데이트 실패:\n{str(e)}")

    def save_as_new_template(self):
        """새 이름으로 템플릿 저장"""
        # 새 이름 입력
        new_name = simpledialog.askstring("새 템플릿 이름",
                                          "새 템플맿 이름을 입력하세요:",
                                          initialvalue=f"{self.current_editing_template}_복사본" if self.current_editing_template else "")

        if new_name:
            try:
                # 기존 templates.json 로드
                try:
                    with open('templates.json', 'r', encoding='utf-8') as f:
                        templates = json.load(f)
                except FileNotFoundError:
                    templates = {}

                # 새 템플맿 데이터 생성
                templates[new_name] = {
                    "original_pdf_path": self.current_pdf_path,
                    "rois": self.rois.copy()
                }

                # 저장
                with open('templates.json', 'w', encoding='utf-8') as f:
                    json.dump(templates, f, ensure_ascii=False, indent=2)

                messagebox.showinfo("완료",
                    f"새 템플릿 '{new_name}'로 저장되었습니다.\n\n"
                    f"ROI 개수: {len(self.rois)}개")

                # 현재 편집 템플릿을 새 이름으로 설정
                self.current_editing_template = new_name
                self.template_status_label.config(text=f"편집 중: {new_name}", foreground="green")

            except Exception as e:
                messagebox.showerror("오류", f"템플맿 저장 실패:\n{str(e)}")

    def save_new_template(self):
        """완전히 새로운 템플릿 생성"""
        template_name = simpledialog.askstring("템플맿 이름", "템플맿 이름을 입력하세요:")

        if template_name:
            try:
                # 기존 templates.json 로드
                try:
                    with open('templates.json', 'r', encoding='utf-8') as f:
                        templates = json.load(f)
                except FileNotFoundError:
                    templates = {}

                # 새 템플맿 데이터
                template_data = {
                    "original_pdf_path": self.current_pdf_path,
                    "rois": self.rois.copy()
                }

                templates[template_name] = template_data

                # 저장
                with open('templates.json', 'w', encoding='utf-8') as f:
                    json.dump(templates, f, ensure_ascii=False, indent=2)

                messagebox.showinfo("완료",
                    f"템플릿 '{template_name}'이 저장되었습니다.\n\n"
                    f"PDF: {os.path.basename(self.current_pdf_path)}\n"
                    f"ROI 개수: {len(self.rois)}개")

                # 편집 모드로 전환
                self.current_editing_template = template_name
                self.template_status_label.config(text=f"편집 중: {template_name}", foreground="green")

            except Exception as e:
                messagebox.showerror("오류", f"템플맟 저장 실패:\n{str(e)}")

        # 템플릿 이름 입력
        template_name = simpledialog.askstring("템플릿 저장", "템플릿 이름을 입력하세요:")
        if not template_name:
            return

        try:
            # 기존 templates.json 로드 또는 새로 생성
            templates_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates.json")
            templates = {}

            if os.path.exists(templates_path):
                with open(templates_path, 'r', encoding='utf-8') as f:
                    templates = json.load(f)

            # 새 템플릿 추가
            roi_dict = {}
            for roi_key, roi_info in self.rois.items():
                field_name = roi_info['field_name']
                roi_dict[field_name] = {
                    "page": roi_info['page'],
                    "coords": roi_info['coords'],
                    "method": roi_info['method'],
                    "threshold": roi_info['threshold']
                }

            templates[template_name] = {
                "original_pdf_path": self.current_pdf_path,
                "rois": roi_dict
            }

            # 파일 저장
            with open(templates_path, 'w', encoding='utf-8') as f:
                json.dump(templates, f, ensure_ascii=False, indent=2)

            messagebox.showinfo("성공", f"템플릿 '{template_name}'이 저장되었습니다.")
            self.load_existing_templates()

        except Exception as e:
            messagebox.showerror("오류", f"템플릿 저장 실패: {str(e)}")

    def load_existing_templates(self):
        """기존 템플릿 목록 로드"""
        templates_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates.json")
        if os.path.exists(templates_path):
            try:
                with open(templates_path, 'r', encoding='utf-8') as f:
                    templates = json.load(f)
                    self.status_label.config(
                        text=f"기존 템플릿 {len(templates)}개 로드됨"
                    )
            except Exception as e:
                self.status_label.config(text=f"템플릿 로드 오류: {str(e)}")


class ROIDialog:
    """ROI 정보 입력 대화상자"""

    def __init__(self, parent):
        self.result = None

        # 대화상자 창 생성
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("ROI 정보 입력")
        self.dialog.geometry("400x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 중앙 위치
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (400 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (200 // 2)
        self.dialog.geometry(f"400x200+{x}+{y}")

        self.setup_dialog()

    def setup_dialog(self):
        """대화상자 UI 설정"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 필드명 입력
        ttk.Label(main_frame, text="필드명:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.field_name_entry = ttk.Entry(main_frame, width=30)
        self.field_name_entry.grid(row=0, column=1, sticky=tk.EW, padx=(10, 0), pady=5)

        # 검증 방법 선택
        ttk.Label(main_frame, text="검증 방법:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.method_var = tk.StringVar(value="ocr")
        method_combo = ttk.Combobox(main_frame, textvariable=self.method_var,
                                  values=["ocr", "contour"], state="readonly", width=27)
        method_combo.grid(row=1, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
        method_combo.bind('<<ComboboxSelected>>', self.on_method_changed)

        # 검증 방법 설명
        self.method_help = ttk.Label(main_frame, text="📝 OCR: 텍스트 내용을 검사합니다 (이름, 주소, 전화번호 등)",
                                   font=('Arial', 8), foreground='blue')
        self.method_help.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        # 임계값 입력
        ttk.Label(main_frame, text="임계값:").grid(row=3, column=0, sticky=tk.W, pady=5)

        # 임계값 입력 프레임 (입력창 + 도움말 버튼)
        threshold_frame = ttk.Frame(main_frame)
        threshold_frame.grid(row=3, column=1, sticky=tk.EW, padx=(10, 0), pady=5)

        self.threshold_entry = ttk.Entry(threshold_frame, width=20)
        self.threshold_entry.pack(side=tk.LEFT)
        self.threshold_entry.insert(0, "3")  # OCR 기본값

        # 도움말 버튼
        help_btn = ttk.Button(threshold_frame, text="❓", width=3, command=self.show_threshold_help)
        help_btn.pack(side=tk.LEFT, padx=(5, 0))

        # 임계값 설명 라벨
        self.threshold_help = ttk.Label(main_frame,
            text="📏 OCR: 최소 글자 수 (예: 3 = 최소 3글자 이상 입력되어야 통과)",
            font=('Arial', 8), foreground='green', wraplength=350)
        self.threshold_help.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=(20, 0))

        ttk.Button(button_frame, text="확인", command=self.ok_clicked).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="취소", command=self.cancel_clicked).pack(side=tk.LEFT)

        # 그리드 가중치 설정
        main_frame.columnconfigure(1, weight=1)
        threshold_frame.columnconfigure(0, weight=1)

        # 엔터 키로 확인
        self.dialog.bind('<Return>', lambda e: self.ok_clicked())
        self.field_name_entry.focus()

    def on_method_changed(self, event=None):
        """검증 방법 변경 시 도움말 업데이트"""
        method = self.method_var.get()
        if method == "ocr":
            self.method_help.config(text="📝 OCR: 텍스트 내용을 검사합니다 (이름, 주소, 전화번호 등)")
            self.threshold_help.config(text="📏 OCR: 최소 글자 수 (예: 3 = 최소 3글자 이상 입력되어야 통과)")
            self.threshold_entry.delete(0, tk.END)
            self.threshold_entry.insert(0, "3")
        elif method == "contour":
            self.method_help.config(text="✏️ Contour: 도형이나 서명을 검사합니다 (서명, 체크박스, 도장 등)")
            self.threshold_help.config(text="📏 Contour: 최소 픽셀 면적 (예: 500 = 최소 500픽셀 이상 그려져야 통과)")
            self.threshold_entry.delete(0, tk.END)
            self.threshold_entry.insert(0, "500")

    def show_threshold_help(self):
        """임계값 상세 도움말 표시"""
        method = self.method_var.get()

        if method == "ocr":
            help_text = (
                "📝 OCR 임계값 가이드\n\n"
                "• 1-2: 매우 관대함 (1-2글자만 있어도 통과)\n"
                "• 3-5: 일반적 (이름, 짧은 텍스트용) ⭐ 추천\n"
                "• 6-10: 엄격함 (주소, 긴 텍스트용)\n"
                "• 11+: 매우 엄격함 (긴 설명문용)\n\n"
                "예시:\n"
                "• 이름 필드: 2-3\n"
                "• 전화번호: 8-11\n"
                "• 주소: 10-20"
            )
        else:  # contour
            help_text = (
                "✏️ Contour 임계값 가이드\n\n"
                "• 100-300: 매우 관대함 (작은 점이나 선도 통과)\n"
                "• 500-1000: 일반적 (서명, 체크표시용) ⭐ 추천\n"
                "• 1500-3000: 엄격함 (큰 서명용)\n"
                "• 3000+: 매우 엄격함 (도장, 큰 그림용)\n\n"
                "예시:\n"
                "• 체크박스: 200-500\n"
                "• 서명: 800-1500\n"
                "• 도장: 2000-5000"
            )

        messagebox.showinfo("임계값 도움말", help_text)

    def ok_clicked(self):
        """확인 버튼 클릭"""
        field_name = self.field_name_entry.get().strip()
        method = self.method_var.get()

        try:
            threshold = int(self.threshold_entry.get())
        except ValueError:
            messagebox.showerror("오류", "임계값은 숫자여야 합니다.")
            return

        if not field_name:
            messagebox.showerror("오류", "필드명을 입력해주세요.")
            return

        self.result = (field_name, method, threshold)
        self.dialog.destroy()

    def cancel_clicked(self):
        """취소 버튼 클릭"""
        self.dialog.destroy()

        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 템플릿 정보 표시
        template_names = list(templates.keys())
        for name in template_names:
            template_data = templates[name]
            roi_count = len(template_data.get('rois', {}))
            pdf_name = os.path.basename(template_data.get('original_pdf_path', 'Unknown'))
            display_text = f"{name} | {roi_count}개 영역 | {pdf_name}"
            template_listbox.insert(tk.END, display_text)

        # 선택된 템플릿 저장
        selected_template = None

        def on_select():
            nonlocal selected_template
            selection = template_listbox.curselection()
            if selection:
                selected_template = template_names[selection[0]]
                dialog.destroy()

        def on_cancel():
            dialog.destroy()

        # 버튼 프레임
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)

        ttk.Button(btn_frame, text="선택", command=on_select, width=10).pack(side=tk.LEFT, padx=(0,10))
        ttk.Button(btn_frame, text="취소", command=on_cancel, width=10).pack(side=tk.LEFT)

        # 더블클릭으로도 선택 가능
        template_listbox.bind("<Double-Button-1>", lambda e: on_select())

        dialog.wait_window()
        return selected_template

    def load_template_for_editing(self, template_name, template_data):
        """선택된 템플릿 데이터를 편집용으로 로드"""
        try:
            # 현재 편집 중인 템플릿 설정
            self.current_editing_template = template_name
            self.template_status_label.config(text=f"편집 중: {template_name}", foreground="green")

            # PDF 파일 로드
            pdf_path = template_data.get('original_pdf_path')
            if pdf_path and os.path.exists(pdf_path):
                # 기존 PDF 닫기
                if self.pdf_doc:
                    self.pdf_doc.close()

                # 새 PDF 열기
                self.pdf_doc = fitz.open(pdf_path)
                self.current_pdf_path = pdf_path
                self.current_page = 0
                self.total_pages = len(self.pdf_doc)

                # ROI 데이터 로드
                self.rois = template_data.get('rois', {})

                # 화면 업데이트
                self.display_page()
                self.update_roi_list()
                self.update_navigation_buttons()

                messagebox.showinfo("완료",
                    f"템플릿 '{template_name}'이 로드되었습니다.\n\n"
                    f"PDF: {os.path.basename(pdf_path)}\n"
                    f"ROI 개수: {len(self.rois)}개\n\n"
                    f"편집 후 '템플릿 저장'을 클릭하세요.")

            else:
                messagebox.showerror("오류", f"PDF 파일을 찾을 수 없습니다:\n{pdf_path}")

        except Exception as e:
            messagebox.showerror("오류", f"템플릿 로드 실패:\n{str(e)}")

    def show_template_list(self):
        """전체 템플릿 목록 보기"""
        try:
            with open('templates.json', 'r', encoding='utf-8') as f:
                templates = json.load(f)

            if not templates:
                messagebox.showinfo("안내", "저장된 템플릿이 없습니다.")
                return

            # 목록 창
            list_window = tk.Toplevel(self.root)
            list_window.title("템플릿 목록")
            list_window.geometry("700x500")
            list_window.transient(self.root)

            # 중앙 배치
            x = (list_window.winfo_screenwidth() // 2) - 350
            y = (list_window.winfo_screenheight() // 2) - 250
            list_window.geometry(f"700x500+{x}+{y}")

            # 메인 프레임
            main_frame = ttk.Frame(list_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

            ttk.Label(main_frame, text="저장된 템플릿 목록",
                     font=('Arial', 14, 'bold')).pack(pady=(0,20))

            # 트리뷰로 상세 정보 표시
            tree_frame = ttk.Frame(main_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True)

            columns = ('템플릿명', 'PDF파일', 'ROI개수', '경로')
            tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)

            # 컬럼 설정
            tree.heading('템플릿명', text='템플릿명')
            tree.heading('PDF파일', text='PDF파일')
            tree.heading('ROI개수', text='ROI개수')
            tree.heading('경로', text='경로')

            tree.column('템플릿명', width=150)
            tree.column('PDF파일', width=200)
            tree.column('ROI개수', width=80)
            tree.column('경로', width=250)

            # 스크롤바
            tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
            tree.config(yscrollcommand=tree_scroll.set)

            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

            # 템플릿 데이터 입력
            for name, data in templates.items():
                pdf_path = data.get('original_pdf_path', '')
                pdf_file = os.path.basename(pdf_path) if pdf_path else 'Unknown'
                roi_count = len(data.get('rois', {}))

                # 경로 단축 표시
                short_path = pdf_path[:50] + '...' if len(pdf_path) > 50 else pdf_path

                tree.insert('', 'end', values=(name, pdf_file, roi_count, short_path))

            # 버튼 프레임
            btn_frame = ttk.Frame(main_frame)
            btn_frame.pack(fill=tk.X, pady=(20,0))

            def edit_selected():
                selection = tree.selection()
                if selection:
                    item = tree.item(selection[0])
                    template_name = item['values'][0]
                    self.load_template_for_editing(template_name, templates[template_name])
                    list_window.destroy()
                else:
                    messagebox.showinfo("안내", "편집할 템플릿을 선택해주세요.")

            def delete_selected():
                selection = tree.selection()
                if selection:
                    item = tree.item(selection[0])
                    template_name = item['values'][0]

                    if messagebox.askyesno("템플릿 삭제",
                                          f"'{template_name}' 템플릿을 삭제하시겠습니까?\n\n"
                                          f"이 작업은 되돌릴 수 없습니다."):
                        self.delete_template(template_name)
                        list_window.destroy()
                        self.show_template_list()  # 목록 새로고침
                else:
                    messagebox.showinfo("안내", "삭제할 템플릿을 선택해주세요.")

            # 버튼들
            ttk.Button(btn_frame, text="선택한 템플릿 편집",
                      command=edit_selected).pack(side=tk.LEFT, padx=(0,10))

            ttk.Button(btn_frame, text="선택한 템플릿 삭제",
                      command=delete_selected).pack(side=tk.LEFT, padx=(0,10))

            ttk.Button(btn_frame, text="닫기",
                      command=list_window.destroy).pack(side=tk.RIGHT)

        except Exception as e:
            messagebox.showerror("오류", f"템플릿 목록 표시 실패:\n{str(e)}")

    def delete_template(self, template_name):
        """템플릿 삭제"""
        try:
            with open('templates.json', 'r', encoding='utf-8') as f:
                templates = json.load(f)

            if template_name in templates:
                del templates[template_name]

                with open('templates.json', 'w', encoding='utf-8') as f:
                    json.dump(templates, f, ensure_ascii=False, indent=2)

                messagebox.showinfo("완료", f"템플릿 '{template_name}'이 삭제되었습니다.")

                # 현재 편집 중이었다면 초기화
                if hasattr(self, 'current_editing_template') and self.current_editing_template == template_name:
                    self.reset_editing_mode()

            else:
                messagebox.showwarning("경고", "템플릿을 찾을 수 없습니다.")

        except Exception as e:
            messagebox.showerror("오류", f"템플릿 삭제 실패:\n{str(e)}")

    def reset_editing_mode(self):
        """편집 모드 초기화"""
        if hasattr(self, 'current_editing_template'):
            self.current_editing_template = None

        if hasattr(self, 'template_status_label'):
            self.template_status_label.config(text="새 템플릿 생성 모드", foreground="blue")

        # ROI 데이터 초기화
        self.rois = {}
        self.update_roi_list()

        # 캔버스 초기화
        if hasattr(self, 'canvas'):
            self.canvas.delete("all")


def main():
    """메인 함수"""
    root = tk.Tk()
    app = ROISelector(root)
    root.mainloop()


if __name__ == "__main__":
    main()
