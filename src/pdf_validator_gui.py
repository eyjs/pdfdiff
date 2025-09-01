#!/usr/bin/env python3
# -*- coding: utf-8 -*- 
"""
PDF 검증 도구 (pdf_validator_gui.py)
저장된 템플릿을 사용하여 채워진 PDF 양식의 완성도와 정확성을 자동으로 검사하는 GUI 애플리케이션
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import os
import fitz  # PyMuPDF
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import pytesseract
from PIL import Image, ImageTk
import io
import re
import datetime


class PDFValidator:
    """PDF 검증 엔진 클래스"""

    def __init__(self, template_data):
        self.template_data = template_data
        self.original_pdf_path = template_data["original_pdf_path"]
        self.rois = template_data["rois"]
        self.validation_results = []

    def validate_pdf(self, filled_pdf_path, progress_callback=None):
        """PDF 검증 실행"""
        try:
            # 원본 및 채워진 PDF 열기
            original_doc = fitz.open(self.original_pdf_path)
            filled_doc = fitz.open(filled_pdf_path)

            self.validation_results = []
            total_rois = len(self.rois)

            for i, (field_name, roi_info) in enumerate(self.rois.items()):
                if progress_callback:
                    progress_callback(f"검증 중: {field_name}", i, total_rois)

                result = self._validate_single_roi(
                    original_doc, filled_doc, field_name, roi_info
                )
                self.validation_results.append(result)

            original_doc.close()
            filled_doc.close()

            return self.validation_results

        except Exception as e:
            raise Exception(f"PDF 검증 중 오류 발생: {str(e)}")

    def _validate_single_roi(self, original_doc, filled_doc, field_name, roi_info):
        """단일 ROI 검증"""
        page_num = roi_info["page"]
        coords = roi_info["coords"]
        method = roi_info["method"]
        threshold = roi_info["threshold"]

        result = {
            "field_name": field_name,
            "page": page_num,
            "coords": coords,
            "method": method,
            "threshold": threshold,
            "status": "OK",
            "message": "",
            "is_empty": False
        }

        try:
            # 페이지에서 ROI 영역 추출
            original_roi = self._extract_roi_image(original_doc, page_num, coords)
            filled_roi = self._extract_roi_image(filled_doc, page_num, coords)

            # 1단계: 비어있는지 확인 (SSIM 사용)
            if self._is_field_empty(original_roi, filled_roi, field_name):
                result["status"] = "DEFICIENT"
                result["message"] = "Empty"
                result["is_empty"] = True
                return result

            # 2단계: 필드별 검증
            if method == "contour":
                if not self._validate_contour(filled_roi, threshold):
                    result["status"] = "DEFICIENT"
                    result["message"] = "Illegible or insufficient content"
            elif method == "ocr":
                if not self._validate_ocr(filled_roi, threshold):
                    result["status"] = "DEFICIENT"
                    result["message"] = "Insufficient text"

            if result["status"] == "OK":
                result["message"] = "Validation passed"

        except Exception as e:
            result["status"] = "ERROR"
            result["message"] = f"Validation error: {str(e)}"

        return result

    def _extract_roi_image(self, pdf_doc, page_num, coords):
        """PDF에서 ROI 영역의 이미지 추출"""
        page = pdf_doc[page_num]

        # 좌표를 fitz.Rect로 변환
        rect = fitz.Rect(coords[0], coords[1], coords[2], coords[3])

        # 고해상도로 렌더링
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat, clip=rect)

        # numpy 배열로 변환
        img_data = pix.samples
        img_array = np.frombuffer(img_data, dtype=np.uint8)
        img_array = img_array.reshape(pix.height, pix.width, pix.n)

        # RGBA인 경우 RGB로 변환
        if pix.n == 4:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
        elif pix.n == 1:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)

        return img_array

    def _is_field_empty(self, original_roi, filled_roi, field_name, threshold=0.995):
        """SSIM을 사용하여 필드가 비어있는지 확인"""
        try:
            # 그레이스케일로 변환
            if len(original_roi.shape) == 3:
                original_gray = cv2.cvtColor(original_roi, cv2.COLOR_RGB2GRAY)
            else:
                original_gray = original_roi

            if len(filled_roi.shape) == 3:
                filled_gray = cv2.cvtColor(filled_roi, cv2.COLOR_RGB2GRAY)
            else:
                filled_gray = filled_roi

            # 크기가 다른 경우 조정
            if original_gray.shape != filled_gray.shape:
                filled_gray = cv2.resize(filled_gray, (original_gray.shape[1], original_gray.shape[0]))

            # SSIM 계산
            ssim_score = ssim(original_gray, filled_gray)
            # print(f"[DEBUG] {field_name}: SSIM = {ssim_score:.4f}, threshold = {threshold}")
            is_empty = ssim_score > threshold
            # print(f"[DEBUG] {field_name}: Empty = {is_empty}")
            return is_empty

        except Exception:
            # 오류 발생 시 안전하게 False 반환
            return False

    def _validate_contour(self, roi_image, threshold):
        """컨투어 기반 검증"""
        try:
            # 그레이스케일로 변환
            if len(roi_image.shape) == 3:
                gray = cv2.cvtColor(roi_image, cv2.COLOR_RGB2GRAY)
            else:
                gray = roi_image

            # 이진화
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # 컨투어 찾기
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # 전체 컨투어 면적 계산
            total_area = sum(cv2.contourArea(contour) for contour in contours)

            return total_area >= threshold

        except Exception:
            return False

    def _validate_ocr(self, roi_image, threshold):
        """OCR 기반 검증"""
        try:
            # PIL 이미지로 변환
            if isinstance(roi_image, np.ndarray):
                pil_image = Image.fromarray(roi_image)
            else:
                pil_image = roi_image

            # OCR 실행
            text = pytesseract.image_to_string(pil_image, lang='kor+eng')

            # 텍스트 정리 (공백, 특수문자 제거)
            cleaned_text = re.sub(r'[\s\n\r\t]+', '', text)
            cleaned_text = re.sub(r'[^\w가-힣]', '', cleaned_text)

            return len(cleaned_text) >= threshold

        except Exception:
            return False

    def create_annotated_pdf(self, filled_pdf_path, output_path):
        """검증 결과가 포함된 주석 PDF 생성"""
        try:
            pdf_doc = fitz.open(filled_pdf_path)

            for result in self.validation_results:
                if result["status"] == "DEFICIENT":
                    page_num = result["page"]
                    coords = result["coords"]

                    page = pdf_doc[page_num]
                    rect = fitz.Rect(coords[0], coords[1], coords[2], coords[3])

                    # 노란색 하이라이트 주석 추가
                    highlight = page.add_highlight_annot(rect)
                    highlight.set_colors({"stroke": [1, 1, 0]})  # 노란색
                    highlight.update()

                    # 텍스트 주석 추가
                    info_text = f"Field: {result['field_name']}\nStatus: DEFICIENT\nMessage: {result['message']}"
                    text_annot = page.add_text_annot(
                        fitz.Point(coords[0], coords[1] - 10),
                        f"[{result['field_name']}] {result['message']}"
                    )
                    text_annot.set_info(
                        content=info_text,
                        title="Validation Error"
                    )
                    text_annot.update(opacity=0.8)

            pdf_doc.save(output_path, incremental=False)
            pdf_doc.close()

            return True

        except Exception as e:
            raise Exception(f"주석 PDF 생성 실패: {str(e)}")


class PDFValidatorGUI:
    """PDF 검증 GUI 애플리케이션"""

    def __init__(self, root):
        self.root = root
        self.root.title("PDF 검증 도구")
        self.root.geometry("1200x800") # 초기 윈도우 크기 설정

        self.templates = {}
        self.selected_template = None
        self.filled_pdf_path = ""

        # 듀얼 뷰어 관련 변수 초기화
        self.original_pdf_doc = None
        self.annotated_pdf_doc = None
        self.current_page_num = 0
        self.total_pages = 0

        self.left_photo = None # 왼쪽 캔버스에 표시될 이미지
        self.right_photo = None # 오른쪽 캔버스에 표시될 이미지

        self.setup_ui()
        self.load_templates()

    def setup_ui(self):
        """UI 구성 요소 설정"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 그리드 레이아웃 설정
        main_frame.grid_rowconfigure(0, weight=0) # control_frame
        main_frame.grid_rowconfigure(1, weight=10) # viewer_pane (더 크게 확장)
        main_frame.grid_rowconfigure(2, weight=0) # nav_frame
        main_frame.grid_rowconfigure(3, weight=1) # log_frame
        main_frame.grid_rowconfigure(4, weight=0) # result_frame
        main_frame.grid_columnconfigure(0, weight=1)

        row_idx = 0

        # 상단 컨트롤 패널
        control_frame = ttk.LabelFrame(main_frame, text="검증 설정", padding="10")
        control_frame.grid(row=row_idx, column=0, sticky=tk.EW, pady=(0, 10))
        row_idx += 1

        # 템플릿 선택
        ttk.Label(control_frame, text="템플릿 선택:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.template_var = tk.StringVar()
        self.template_combo = ttk.Combobox(control_frame, textvariable=self.template_var,
                                          state="readonly", width=40)
        self.template_combo.grid(row=0, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
        self.template_combo.bind('<<ComboboxSelected>>', self.on_template_selected)

        # 템플릿 새로고침 버튼
        ttk.Button(control_frame, text="새로고침",
                  command=self.load_templates).grid(row=0, column=2, padx=(10, 0), pady=5)

        # 검증할 PDF 파일 선택
        ttk.Label(control_frame, text="검증할 PDF:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.pdf_path_var = tk.StringVar()
        self.pdf_path_entry = ttk.Entry(control_frame, textvariable=self.pdf_path_var,
                                       state="readonly", width=40)
        self.pdf_path_entry.grid(row=1, column=1, sticky=tk.EW, padx=(10, 0), pady=5)

        ttk.Button(control_frame, text="찾아보기",
                  command=self.browse_pdf).grid(row=1, column=2, padx=(10, 0), pady=5)

        # 검증 실행 버튼
        self.validate_btn = ttk.Button(control_frame, text="검증 실행",
                                      command=self.run_validation, state=tk.DISABLED)
        self.validate_btn.grid(row=2, column=1, pady=(10, 0))

        # 그리드 가중치 설정
        control_frame.columnconfigure(1, weight=1)

        # 진행률 표시
        self.progress_var = tk.StringVar(value="대기 중...")
        self.progress_label = ttk.Label(control_frame, textvariable=self.progress_var)
        self.progress_label.grid(row=3, column=0, columnspan=3, pady=(5, 0))

        self.progress_bar = ttk.Progressbar(control_frame, mode='determinate')
        self.progress_bar.grid(row=4, column=0, columnspan=3, sticky=tk.EW, pady=(5, 0))

        # 듀얼 뷰어 영역
        viewer_pane = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        viewer_pane.grid(row=row_idx, column=0, sticky=tk.NSEW, pady=(10, 0))
        row_idx += 1

        # 왼쪽 뷰어 (원본 템플릿)
        left_viewer_frame = ttk.LabelFrame(viewer_pane, text="원본 템플릿", padding="5")
        viewer_pane.add(left_viewer_frame, weight=1)

        self.left_canvas = tk.Canvas(left_viewer_frame, bg="white", bd=2, relief="sunken")
        self.left_canvas.pack(fill=tk.BOTH, expand=True)
        self.left_canvas.bind('<Configure>', self._on_canvas_resize)

        # 오른쪽 뷰어 (검증된 문서)
        right_viewer_frame = ttk.LabelFrame(viewer_pane, text="검증된 문서", padding="5")
        viewer_pane.add(right_viewer_frame, weight=1)

        self.right_canvas = tk.Canvas(right_viewer_frame, bg="white", bd=2, relief="sunken")
        self.right_canvas.pack(fill=tk.BOTH, expand=True)
        self.right_canvas.bind('<Configure>', self._on_canvas_resize)

        # 페이지 네비게이션 (공유)
        nav_frame = ttk.Frame(main_frame)
        nav_frame.grid(row=row_idx, column=0, sticky=tk.EW, pady=(5, 0))
        row_idx += 1

        self.prev_page_btn = ttk.Button(nav_frame, text="◀ 이전", command=self.prev_page, state=tk.DISABLED)
        self.prev_page_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.page_label = ttk.Label(nav_frame, text="페이지: 0/0")
        self.page_label.pack(side=tk.LEFT, padx=(0, 5))

        self.next_page_btn = ttk.Button(nav_frame, text="다음 ▶", command=self.next_page, state=tk.DISABLED)
        self.next_page_btn.pack(side=tk.LEFT)

        # 로그 패널
        log_frame = ttk.LabelFrame(main_frame, text="검증 로그", padding="10")
        log_frame.grid(row=row_idx, column=0, sticky=tk.NSEW, pady=(10, 0))
        row_idx += 1

        self.log_text = scrolledtext.ScrolledText(log_frame, height=5, font=('Consolas', 10)) # 높이 줄임
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 결과 패널
        result_frame = ttk.LabelFrame(main_frame, text="검증 결과", padding="10")
        result_frame.grid(row=row_idx, column=0, sticky=tk.EW, pady=(10, 0))
        row_idx += 1

        # 결과 요약
        self.result_var = tk.StringVar(value="검증을 실행해주세요.")
        self.result_label = ttk.Label(result_frame, textvariable=self.result_var,
                                     font=('Arial', 12, 'bold'))
        self.result_label.pack(pady=5)

        # 주석 PDF 저장 버튼
        self.save_btn = ttk.Button(result_frame, text="주석 PDF 저장",
                                  command=self.save_annotated_pdf, state=tk.DISABLED)
        self.save_btn.pack(pady=5)

        # 초기 윈도우 크기 설정
        self.root.geometry("1600x1000") # 초기 윈도우 크기 더 크게 설정

    def load_templates(self):
        """템플릿 목록 로드"""
        templates_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates.json")

        try:
            if os.path.exists(templates_path):
                with open(templates_path, 'r', encoding='utf-8') as f:
                    self.templates = json.load(f)

                # 콤보박스 업데이트
                template_names = list(self.templates.keys())
                self.template_combo['values'] = template_names

                if template_names:
                    self.template_combo.set(template_names[0])
                    self.on_template_selected()

                self.log(f"템플릿 {len(template_names)}개 로드됨")
            else:
                self.templates = {}
                self.template_combo['values'] = []
                self.log("templates.json 파일을 찾을 수 없습니다. ROI 선택 도구를 먼저 실행해주세요.")

        except Exception as e:
            self.log(f"템플릿 로드 오류: {str(e)}")

    def on_template_selected(self, event=None):
        """템플릿 선택 이벤트"""
        template_name = self.template_var.get()
        if template_name and template_name in self.templates:
            self.selected_template = self.templates[template_name]
            roi_count = len(self.selected_template.get('rois', {}))
            self.log(f"템플릿 '{template_name}' 선택됨 (ROI {roi_count}개)")
            self.update_validate_button_state()

    def browse_pdf(self):
        """검증할 PDF 파일 선택"""
        file_path = filedialog.askopenfilename(
            title="검증할 PDF 파일 선택",
            filetypes=[("PDF files", "*.pdf")]
        )

        if file_path:
            self.filled_pdf_path = file_path
            self.pdf_path_var.set(os.path.basename(file_path))
            self.log(f"검증 대상 파일 선택: {os.path.basename(file_path)}")
            self.update_validate_button_state()

    def _on_canvas_resize(self, event):
        """캔버스 크기 변경 시 호출되어 내용을 다시 그림"""
        self.display_dual_pages()

    def update_validate_button_state(self):
        """검증 버튼 활성화 상태 업데이트"""
        if self.selected_template and self.filled_pdf_path:
            self.validate_btn.config(state=tk.NORMAL)
        else:
            self.validate_btn.config(state=tk.DISABLED)

    def log(self, message):
        """로그 메시지 추가"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"

        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.root.update()

    def display_dual_pages(self):
        """두 캔버스에 PDF 페이지 표시"""
        if not self.original_pdf_doc or not self.annotated_pdf_doc:
            return

        # 캔버스 지우기
        self.left_canvas.delete("all")
        self.right_canvas.delete("all")

        # 원본 PDF 페이지 렌더링 (왼쪽 캔버스)
        if self.current_page_num < len(self.original_pdf_doc):
            original_page = self.original_pdf_doc[self.current_page_num]
            original_pix = original_page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2배 해상도
            original_img = Image.frombytes("RGB", [original_pix.width, original_pix.height], original_pix.samples)
            
            # 캔버스 크기에 맞게 이미지 크기 조정
            canvas_width = self.left_canvas.winfo_width()
            canvas_height = self.left_canvas.winfo_height()
            if canvas_width > 1 and canvas_height > 1:
                original_img = self._resize_image_to_fit_canvas(original_img, canvas_width, canvas_height)
            
            self.left_photo = ImageTk.PhotoImage(original_img)
            self.left_canvas.create_image(10, 10, anchor=tk.NW, image=self.left_photo)

            # 왼쪽 캔버스에 ROI 그리기
            self._draw_rois_on_canvas(self.left_canvas, original_page)

        # 주석 PDF 페이지 렌더링 (오른쪽 캔버스)
        if self.current_page_num < len(self.annotated_pdf_doc):
            annotated_page = self.annotated_pdf_doc[self.current_page_num]
            annotated_pix = annotated_page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2배 해상도
            annotated_img = Image.frombytes("RGB", [annotated_pix.width, annotated_pix.height], annotated_pix.samples)

            # 캔버스 크기에 맞게 이미지 크기 조정
            canvas_width = self.right_canvas.winfo_width()
            canvas_height = self.right_canvas.winfo_height()
            if canvas_width > 1 and canvas_height > 1:
                annotated_img = self._resize_image_to_fit_canvas(annotated_img, canvas_width, canvas_height)

            self.right_photo = ImageTk.PhotoImage(annotated_img)
            self.right_canvas.create_image(10, 10, anchor=tk.NW, image=self.right_photo)

        self.update_navigation_buttons()

    def _resize_image_to_fit_canvas(self, pil_image, canvas_width, canvas_height):
        """PIL 이미지를 캔버스 크기에 맞게 비율 유지하며 조정"""
        img_ratio = pil_image.width / pil_image.height
        canvas_ratio = canvas_width / canvas_height

        if img_ratio > canvas_ratio:
            new_width = canvas_width - 20
            new_height = int(new_width / img_ratio)
        else:
            new_height = canvas_height - 20
            new_width = int(new_height * img_ratio)
        
        return pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def _draw_rois_on_canvas(self, canvas, pdf_page):
        """캔버스에 ROI 사각형 및 라벨 그리기"""
        if not self.selected_template or 'rois' not in self.selected_template:
            return

        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            return

        original_page_width = pdf_page.rect.width
        original_page_height = pdf_page.rect.height

        img_ratio = original_page_width / original_page_height
        canvas_ratio = canvas_width / canvas_height

        if img_ratio > canvas_ratio:
            new_width = canvas_width - 20
            current_display_scale = original_page_width / new_width
        else:
            new_height = canvas_height - 20
            current_display_scale = original_page_height / new_height

        for field_name, roi_info in self.selected_template['rois'].items():
            if roi_info['page'] == self.current_page_num:
                # PDF 좌표를 캔버스 좌표로 변환
                x1 = roi_info['coords'][0] / current_display_scale + 10
                y1 = roi_info['coords'][1] / current_display_scale + 10
                x2 = roi_info['coords'][2] / current_display_scale + 10
                y2 = roi_info['coords'][3] / current_display_scale + 10

                canvas.create_rectangle(x1, y1, x2, y2, outline="blue", width=2, tags="roi_overlay")
                canvas.create_text(x1, y1 - 5, anchor=tk.SW, text=field_name, fill="blue", font=("Arial", 8, "bold"), tags="roi_overlay")

    def update_navigation_buttons(self):
        """페이지 네비게이션 버튼 상태 및 라벨 업데이트"""
        self.page_label.config(text=f"페이지: {self.current_page_num + 1}/{self.total_pages}")
        
        if self.current_page_num == 0:
            self.prev_page_btn.config(state=tk.DISABLED)
        else:
            self.prev_page_btn.config(state=tk.NORMAL)

        if self.current_page_num >= self.total_pages - 1:
            self.next_page_btn.config(state=tk.DISABLED)
        else:
            self.next_page_btn.config(state=tk.NORMAL)

    def prev_page(self):
        """이전 페이지로 이동"""
        if self.current_page_num > 0:
            self.current_page_num -= 1
            self.display_dual_pages()

    def next_page(self):
        """다음 페이지로 이동"""
        if self.current_page_num < self.total_pages - 1:
            self.current_page_num += 1
            self.display_dual_pages()

    def run_validation(self):
        """검증 실행"""
        if not self.selected_template or not self.filled_pdf_path:
            messagebox.showwarning("경고", "템플릿과 PDF 파일을 모두 선택해주세요.")
            return

        try:
            self.validate_btn.config(state=tk.DISABLED)
            self.save_btn.config(state=tk.DISABLED)

            self.log("검증을 시작합니다...")

            # PDF 검증기 생성
            validator = PDFValidator(self.selected_template)

            # 진행률 콜백 함수
            def progress_callback(message, current, total):
                progress = int((current / total) * 100)
                self.progress_bar['value'] = progress
                self.progress_var.set(f"{message} ({current + 1}/{total})")
                self.log(f"  → {message}")
                self.root.update()

            # 검증 실행
            results = validator.validate_pdf(self.filled_pdf_path, progress_callback)

            # 결과 분석
            total_fields = len(results)
            deficient_fields = sum(1 for r in results if r['status'] == 'DEFICIENT')
            ok_fields = sum(1 for r in results if r['status'] == 'OK')
            error_fields = sum(1 for r in results if r['status'] == 'ERROR')

            # 결과 로그
            self.log("\n=== 검증 결과 ===")
            for result in results:
                status_icon = "✓" if result['status'] == 'OK' else "✗" if result['status'] == 'DEFICIENT' else "!"
                self.log(f"{status_icon} [{result['field_name']}] {result['message']}")

            # 요약 결과
            if deficient_fields > 0 or error_fields > 0:
                total_issues = deficient_fields + error_fields
                summary = f"검증 완료: 총 {total_fields}개 필드 중 {total_issues}개 필드에서 문제 발견"
                self.result_var.set(summary)
                self.result_label.config(foreground="red")
            else:
                summary = f"검증 완료: 모든 {total_fields}개 필드가 정상입니다"
                self.result_var.set(summary)
                self.result_label.config(foreground="green")

            self.log(f"\n{summary}")

            # 검증기를 인스턴스 변수로 저장 (주석 PDF 생성용)
            self.validator = validator

            # --- 듀얼 뷰어 관련 로직 추가 ---
            # 주석 PDF 생성 (임시 파일로 생성 후 로드)
            output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
            os.makedirs(output_dir, exist_ok=True)
            temp_annotated_pdf_path = os.path.join(output_dir, "temp_annotated_review.pdf")

            success = self.validator.create_annotated_pdf(self.filled_pdf_path, temp_annotated_pdf_path)

            if success:
                # 원본 PDF 로드
                if self.original_pdf_doc:
                    self.original_pdf_doc.close()
                self.original_pdf_doc = fitz.open(self.selected_template["original_pdf_path"])

                # 주석 PDF 로드
                if self.annotated_pdf_doc:
                    self.annotated_pdf_doc.close()
                self.annotated_pdf_doc = fitz.open(temp_annotated_pdf_path)

                self.total_pages = max(len(self.original_pdf_doc), len(self.annotated_pdf_doc))
                self.current_page_num = 0 # 첫 페이지부터 시작

                self.display_dual_pages() # 듀얼 뷰어 업데이트
                self.update_navigation_buttons() # 네비게이션 버튼 상태 업데이트

                self.save_btn.config(state=tk.NORMAL) # 주석 PDF 저장 버튼 활성화
            else:
                messagebox.showerror("오류", "주석 PDF 생성에 실패했습니다.")
            # --- 듀얼 뷰어 관련 로직 끝 ---

            self.progress_var.set("검증 완료")
            self.progress_bar['value'] = 100

        except Exception as e:
            self.log(f"검증 중 오류 발생: {str(e)}")
            messagebox.showerror("오류", f"검증 실행 실패: {str(e)}")

        finally:
            self.validate_btn.config(state=tk.NORMAL)

    def save_annotated_pdf(self):
        """주석이 포함된 PDF 저장"""
        if not hasattr(self, 'validator'):
            messagebox.showwarning("경고", "검증을 먼저 실행해주세요.")
            return

        # output 폴더 생성 (없으면)
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
        os.makedirs(output_dir, exist_ok=True)

        # 자동 파일명 생성
        base_name = os.path.splitext(os.path.basename(self.filled_pdf_path))[0]
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"review_{base_name}_{timestamp}.pdf"
        default_path = os.path.join(output_dir, default_filename)

        # 저장할 파일 경로 선택
        output_path = filedialog.asksaveasfilename(
            title="주석 PDF 저장",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialdir=output_dir,
            initialfile=default_filename
        )

        if output_path:
            try:
                success = self.validator.create_annotated_pdf(self.filled_pdf_path, output_path)
                if success:
                    self.log(f"주석 PDF 저장 완료: {os.path.basename(output_path)}")
                    self.log(f"저장 위치: {output_path}")
                    messagebox.showinfo("성공",
                        f"주석이 포함된 PDF가 저장되었습니다:\n\n"
                        f"파일명: {os.path.basename(output_path)}\n"
                        f"위치: {output_path}\n\n"
                        f"폴더 열기를 클릭하시겠습니까?",
                        detail="예를 클릭하면 파일 위치를 엽니다.")

                    # 파일 위치 열기 옵션
                    result = messagebox.askyesno("폴더 열기", "저장된 파일이 있는 폴더를 열까요?")
                    if result:
                        import subprocess
                        subprocess.run(["explorer", "/select,", os.path.normpath(output_path)])

            except Exception as e:
                self.log(f"주석 PDF 저장 실패: {str(e)}")
                messagebox.showerror("오류", f"주석 PDF 저장 실패: {str(e)}")


def main():
    """메인 함수"""
    root = tk.Tk()
    app = PDFValidatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
