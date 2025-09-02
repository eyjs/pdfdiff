# src/pdf_validator_gui.py (v14.0 - 전체 기능 복원 및 모든 오류 수정 최종본)

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import os
import fitz  # PyMuPDF
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import pytesseract
import sys
from PIL import Image, ImageTk
import re
import datetime
import time

def setup_tesseract():
    """배포 및 개발 환경 모두에서 Tesseract 및 언어 데이터를 안정적으로 찾는 함수"""
    tesseract_dir = None

    # 1. .exe로 배포 시, .exe와 동일한 위치의 vendor 또는 tesseract 폴더를 찾음
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
        for folder in ['vendor/tesseract', 'tesseract']:
            path = os.path.join(application_path, folder)
            if os.path.exists(os.path.join(path, 'tesseract.exe')):
                tesseract_dir = path
                break
    # 2. 개발 환경(.py)에서 실행 시, 스크립트 위치 기준 상위 폴더의 vendor를 찾음
    else:
        script_path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(script_path, '..', 'vendor', 'tesseract')
        if os.path.exists(os.path.join(path, 'tesseract.exe')):
            tesseract_dir = path

    # 3. 경로를 찾았으면 환경 변수 및 pytesseract 경로 설정
    if tesseract_dir:
        pytesseract.pytesseract.tesseract_cmd = os.path.join(tesseract_dir, 'tesseract.exe')
        # Tesseract가 언어 데이터를 찾을 수 있도록 환경 변수 설정
        tessdata_path = os.path.join(tesseract_dir, 'tessdata')
        if os.path.exists(tessdata_path):
            os.environ['TESSDATA_PREFIX'] = tessdata_path
            return True

    # 4. 위 방법으로 못 찾으면 실패
    return False

# --- 프로그램 시작 시 Tesseract 경로 설정 ---
TESSERACT_CONFIGURED = setup_tesseract()

class PDFValidator:
    """PDF 검증 엔진 (v14.0 - 지능형 앵커 추적)"""
    def __init__(self, template_data):
        self.template_data = template_data
        self.original_pdf_path = template_data["original_pdf_path"]
        self.rois = template_data["rois"]
        self.detector = cv2.AKAZE_create()
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        self.validation_results = []

    def _get_full_page_image(self, page, scale=2.0):
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    def _extract_roi_image(self, pdf_doc, page_num, coords, scale=2.0, grayscale=False):
        page = pdf_doc[page_num]; rect = fitz.Rect(coords); mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat, clip=rect, alpha=False)
        img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if grayscale: return cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        return cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB) if pix.n == 4 else img_array

    def _find_anchor_homography(self, page_img, anchor_img):
        kp_anchor, des_anchor = self.detector.detectAndCompute(anchor_img, None)
        kp_page, des_page = self.detector.detectAndCompute(page_img, None)
        if des_anchor is None or des_page is None or len(des_anchor) < 5: return None

        matches = self.matcher.match(des_anchor, des_page)
        matches = sorted(matches, key=lambda x: x.distance)

        if len(matches) > 10:
            src_pts = np.float32([kp_anchor[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp_page[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
            M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            return M
        return None

    def _validate_single_roi(self, original_doc, filled_doc, field_name, roi_info):
        page_num = roi_info.get("page", 0); coords = roi_info.get("coords")
        method = roi_info.get("method", "ocr"); threshold = roi_info.get("threshold", 500)
        anchor_coords = roi_info.get("anchor_coords")
        result = {"field_name": field_name, "page": page_num, "coords": coords, "status": "OK", "message": ""}
        if not coords or not anchor_coords:
            result["status"] = "ERROR"; result["message"] = "좌표/앵커 정보 없음"; return result

        try:
            render_scale = 2.0
            original_roi = self._extract_roi_image(original_doc, page_num, coords, render_scale)
            new_coords = coords

            anchor_template_img = self._extract_roi_image(original_doc, page_num, anchor_coords, render_scale, grayscale=True)
            filled_page_img = self._get_full_page_image(filled_doc[page_num], render_scale)
            anchor_homography = self._find_anchor_homography(page_img=filled_page_img, anchor_img=anchor_template_img)

            if anchor_homography is not None:
                roi_pts_orig = np.float32([coords[:2], [coords[2], coords[1]], coords[2:], [coords[0], coords[3]]]).reshape(-1, 1, 2)
                anchor_pts_orig = np.float32([anchor_coords[:2], [anchor_coords[2], anchor_coords[1]], anchor_coords[2:], [anchor_coords[0], anchor_coords[3]]]).reshape(-1, 1, 2)
                anchor_center_orig_scaled = np.mean(anchor_pts_orig, axis=0).flatten() * render_scale

                T_to_origin = np.array([[1, 0, -anchor_center_orig_scaled[0]], [0, 1, -anchor_center_orig_scaled[1]], [0, 0, 1]])
                T_from_origin = np.array([[1, 0, anchor_center_orig_scaled[0]], [0, 1, anchor_center_orig_scaled[1]], [0, 0, 1]])
                final_transform = T_from_origin @ anchor_homography @ T_to_origin

                roi_pts_transformed_scaled = cv2.perspectiveTransform(roi_pts_orig * render_scale, final_transform)

                if roi_pts_transformed_scaled is not None:
                    x_coords, y_coords = roi_pts_transformed_scaled[:, 0, 0], roi_pts_transformed_scaled[:, 0, 1]
                    new_coords = [min(x_coords)/render_scale, min(y_coords)/render_scale, max(x_coords)/render_scale, max(y_coords)/render_scale]
                    result['message'] += "[앵커 보정 성공] "
                else: result['message'] += "[앵커 좌표 변환 실패] "
            else: result['message'] += "[앵커 찾기 실패] "

            filled_roi = self._extract_roi_image(filled_doc, page_num, new_coords, render_scale)

            h, w, _ = original_roi.shape; filled_roi_resized = cv2.resize(filled_roi, (w, h))
            original_gray = cv2.cvtColor(original_roi, cv2.COLOR_RGB2GRAY); filled_gray = cv2.cvtColor(filled_roi_resized, cv2.COLOR_RGB2GRAY)

            if ssim(original_gray, filled_gray, data_range=255) > 0.95:
                result["status"] = "DEFICIENT"; result["message"] += "내용 없음 (Empty)"; return result

            if method == "contour":
                diff = cv2.absdiff(original_gray, filled_gray); binary = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)[1]
                contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                val = sum(cv2.contourArea(c) for c in contours)
                if val < threshold: result["status"] = "DEFICIENT"; result["message"] += f"내용 미흡 [감지 면적: {int(val)} / 필요: {threshold}]"
                else: result["message"] += f"통과 [감지 면적: {int(val)}]"
            elif method == "ocr":
                text = pytesseract.image_to_string(filled_roi, lang='kor+eng'); val = re.sub(r'[\s\W_]+', '', text)
                if len(val) < threshold: result["status"] = "DEFICIENT"; result["message"] += f"내용 미흡 [인식 글자 수: {len(val)} / 필요: {threshold}]"
                else: result["message"] += f"통과 [인식 텍스트: '{val}']"
        except Exception as e:
            result["status"] = "ERROR"; result["message"] = f"검증 오류: {str(e)}"
        return result

    def validate_pdf(self, filled_pdf_path, progress_callback=None):
        self.validation_results = []
        original_doc = fitz.open(self.original_pdf_path); filled_doc = fitz.open(filled_pdf_path)

        for i, (field_name, roi_info) in enumerate(self.rois.items()):
            if progress_callback: progress_callback(f"'{field_name}' 검증 중...", i, len(self.rois))
            result = self._validate_single_roi(original_doc, filled_doc, field_name, roi_info)
            self.validation_results.append(result)

        original_doc.close(); filled_doc.close()
        return self.validation_results

    def create_annotated_pdf(self, filled_pdf_path, output_path):
        pdf_doc = fitz.open(filled_pdf_path)
        for result in self.validation_results:
            if result["status"] != "OK":
                page = pdf_doc[result["page"]]; rect = fitz.Rect(result["coords"])
                color = (1, 0, 0) if result["status"] == "ERROR" else (1, 0.8, 0)
                highlight = page.add_highlight_annot(rect); highlight.set_colors({"stroke": color}); highlight.update()
        pdf_doc.save(output_path, garbage=4, deflate=True, clean=True); pdf_doc.close()

class PDFValidatorGUI:
    def __init__(self, root):
        self.root = root; self.root.title("2단계: ROI 검증 도구 (v14.0)"); self.root.geometry("1200x900")
        self.templates, self.selected_template, self.target_path, self.validator = {}, None, "", None
        self.original_pdf_doc, self.annotated_pdf_doc, self.current_page_num, self.total_pages = None, None, 0, 0
        self.left_photo, self.right_photo = None, None
        self.setup_ui()
        self.load_templates()

    def check_tesseract(self):
        if not TESSERACT_CONFIGURED:
            self.log("🔥 경고: Tesseract OCR 엔진을 찾을 수 없습니다.")
            self.log("  -> 'vendor/tesseract' 폴더가 있는지, 또는 시스템 PATH에 Tesseract가 등록되어 있는지 확인하세요.")
            return False
        self.log(f"✅ Tesseract OCR 엔진을 사용합니다: {pytesseract.pytesseract.tesseract_cmd}")
        return True

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10"); main_frame.pack(fill=tk.BOTH, expand=True)
        control_frame = ttk.LabelFrame(main_frame, text="검증 설정", padding="10"); control_frame.pack(fill=tk.X, pady=(0, 10))

        self.mode_var = tk.StringVar(value="폴더")
        ttk.Label(control_frame, text="검사 방식 선택:").grid(row=0, column=0, sticky=tk.W, pady=5)
        mode_frame = ttk.Frame(control_frame); mode_frame.grid(row=0, column=1, columnspan=2, sticky=tk.W)
        ttk.Radiobutton(mode_frame, text="파일 기준 검사", variable=self.mode_var, value="파일", command=self.switch_mode).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="폴더 기준 검사", variable=self.mode_var, value="폴더", command=self.switch_mode).pack(side=tk.LEFT, padx=5)

        ttk.Label(control_frame, text="템플릿 선택:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.template_var = tk.StringVar(); self.template_combo = ttk.Combobox(control_frame, textvariable=self.template_var, state="readonly", width=40)
        self.template_combo.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5); self.template_combo.bind('<<ComboboxSelected>>', self.on_template_selected)
        ttk.Button(control_frame, text="새로고침", command=self.load_templates).grid(row=1, column=2, padx=5, pady=5)

        self.target_label = ttk.Label(control_frame, text="검사 대상 폴더:"); self.target_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        self.path_var = tk.StringVar(); self.path_entry = ttk.Entry(control_frame, textvariable=self.path_var, state="readonly", width=40)
        self.path_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5); self.browse_btn = ttk.Button(control_frame, text="폴더 찾기", command=self.browse_target)
        self.browse_btn.grid(row=2, column=2, padx=5, pady=5); control_frame.columnconfigure(1, weight=1)

        self.validate_btn = ttk.Button(main_frame, text="검사 실행", command=self.run_validation, state=tk.DISABLED); self.validate_btn.pack(pady=10)

        self.viewer_frame = ttk.Frame(main_frame); viewer_pane = ttk.PanedWindow(self.viewer_frame, orient=tk.HORIZONTAL)
        viewer_pane.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        left_viewer_frame = ttk.LabelFrame(viewer_pane, text="원본 템플릿", padding="5"); viewer_pane.add(left_viewer_frame, weight=1)
        self.left_canvas = tk.Canvas(left_viewer_frame, bg="white"); self.left_canvas.pack(fill=tk.BOTH, expand=True)
        right_viewer_frame = ttk.LabelFrame(viewer_pane, text="검증된 문서 (주석)", padding="5"); viewer_pane.add(right_viewer_frame, weight=1)
        self.right_canvas = tk.Canvas(right_viewer_frame, bg="white"); self.right_canvas.pack(fill=tk.BOTH, expand=True)
        nav_frame = ttk.Frame(self.viewer_frame); nav_frame.pack(fill=tk.X, pady=5)
        self.prev_page_btn = ttk.Button(nav_frame, text="◀ 이전", command=self.prev_page, state=tk.DISABLED); self.prev_page_btn.pack(side=tk.LEFT)
        self.page_label = ttk.Label(nav_frame, text="페이지: 0/0"); self.page_label.pack(side=tk.LEFT, padx=10)
        self.next_page_btn = ttk.Button(nav_frame, text="다음 ▶", command=self.next_page, state=tk.DISABLED); self.next_page_btn.pack(side=tk.LEFT)
        self.save_file_btn = ttk.Button(nav_frame, text="결과 저장", command=self.save_single_file_result, state=tk.DISABLED); self.save_file_btn.pack(side=tk.RIGHT, padx=10)

        log_frame = ttk.LabelFrame(main_frame, text="진행 상황 로그", padding="10"); log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, font=('Consolas', 10)); self.log_text.pack(fill=tk.BOTH, expand=True)
        self.progress_bar = ttk.Progressbar(log_frame, mode='determinate'); self.progress_bar.pack(fill=tk.X, pady=(5, 0))

        self.switch_mode()

    def update_validate_button_state(self):
        state = tk.NORMAL if self.selected_template and self.target_path else tk.DISABLED
        self.validate_btn.config(state=state)

    def switch_mode(self):
        mode = self.mode_var.get(); self.path_var.set(""); self.target_path = ""
        if mode == "파일":
            self.target_label.config(text="검사 대상 파일:"); self.browse_btn.config(text="파일 찾기")
            self.viewer_frame.pack(fill=tk.BOTH, expand=True); self.save_file_btn.config(state=tk.DISABLED)
        else:
            self.target_label.config(text="검사 대상 폴더:"); self.browse_btn.config(text="폴더 찾기")
            self.viewer_frame.pack_forget()
        self.update_validate_button_state()

    def browse_target(self):
        mode = self.mode_var.get()
        path = filedialog.askopenfilename(title="PDF 파일 선택", filetypes=[("PDF files", "*.pdf")]) if mode == "파일" else filedialog.askdirectory(title="PDF 폴더 선택")
        if path: self.target_path = path; self.path_var.set(path); self.log(f"대상 선택: {path}"); self.update_validate_button_state()

    def run_validation(self):
        if not self.check_tesseract():
            messagebox.showerror("OCR 엔진 오류", "Tesseract OCR 엔진을 찾을 수 없습니다. 로그를 확인하세요.")
            return
        if self.mode_var.get() == "파일": self.run_file_validation()
        else: self.run_folder_validation()

    def log(self, message):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n"); self.log_text.see(tk.END); self.root.update_idletasks()

    def log_results(self, results):
        for result in results:
            icon = "✅" if result['status'] == 'OK' else "❌"
            self.log(f"  {icon} [{result['field_name']}]: {result['message']}")

    def run_file_validation(self):
        self.validate_btn.config(state=tk.DISABLED); self.save_file_btn.config(state=tk.DISABLED)
        self.log_text.delete('1.0', tk.END); self.log(f"파일 검증 시작: {os.path.basename(self.target_path)}")
        self.validator = PDFValidator(self.selected_template)

        self.progress_bar['maximum'] = len(self.validator.rois)
        def progress_update(msg, current, total):
            self.log(msg)
            if current >= 0: self.progress_bar['value'] = current + 1

        try:
            results = self.validator.validate_pdf(self.target_path, progress_update)
            self.log("="*50 + "\n상세 검증 결과:")
            self.log_results(results)
            deficient = sum(1 for r in results if r['status'] != 'OK')

            temp_dir = "output"; os.makedirs(temp_dir, exist_ok=True)
            temp_annot_path = os.path.join(temp_dir, f"temp_review_{int(time.time())}.pdf")
            self.validator.create_annotated_pdf(self.target_path, temp_annot_path)

            self.log("="*50); self.log(f"요약: {'❌ 검증 미흡' if deficient > 0 else '✅ 검증 통과'} ({deficient}개 항목 미흡)"); self.log("="*50)
            self.load_docs_for_viewer(self.selected_template['original_pdf_path'], temp_annot_path)
        except Exception as e:
            self.log(f"🔥 치명적 오류 발생: {e}"); messagebox.showerror("오류", f"검증 중 오류:\n{e}")
        finally:
            self.validate_btn.config(state=tk.NORMAL); self.save_file_btn.config(state=tk.NORMAL)

    def run_folder_validation(self):
        self.validate_btn.config(state=tk.DISABLED)
        template_name = self.template_var.get()
        pdf_files = [f for f in os.listdir(self.target_path) if f.lower().endswith('.pdf')]
        if not pdf_files: messagebox.showinfo("완료", "폴더에 PDF 파일이 없습니다."); self.validate_btn.config(state=tk.NORMAL); return

        output_dir = os.path.join("output", re.sub(r'[\\/*?:"<>|]', "", template_name))
        os.makedirs(output_dir, exist_ok=True)

        self.log_text.delete('1.0', tk.END)
        self.log(f"'{template_name}' 템플릿으로 일괄 검증을 시작합니다. (총 {len(pdf_files)}개)")
        self.progress_bar['maximum'] = len(pdf_files)

        validator = PDFValidator(self.selected_template)
        success_count, fail_count = 0, 0

        for i, filename in enumerate(pdf_files):
            filepath = os.path.join(self.target_path, filename)
            self.log(f"[{i+1}/{len(pdf_files)}] '{filename}' 검증 중...")
            self.progress_bar['value'] = i + 1

            try:
                results = validator.validate_pdf(filepath)
                deficient_count = sum(1 for r in results if r['status'] != 'OK')
                if deficient_count > 0:
                    fail_count += 1
                    self.log(f"  -> ❌ 미흡 ({deficient_count}개 항목). 주석 PDF를 저장합니다.")
                    out_name = f"review_{os.path.splitext(filename)[0]}.pdf"
                    out_path = os.path.join(output_dir, out_name)
                    validator.create_annotated_pdf(filepath, out_path)
                else: success_count += 1; self.log("  -> ✅ 통과.")
            except Exception as e: fail_count += 1; self.log(f"  -> 🔥 오류 발생: {e}")

        summary = f"검증 완료! (성공: {success_count}, 실패/오류: {fail_count})"
        self.log("="*50); self.log(summary)
        self.log(f"미흡 파일은 '{os.path.abspath(output_dir)}' 폴더에 저장되었습니다.")
        messagebox.showinfo("완료", summary)
        self.validate_btn.config(state=tk.NORMAL)

    def save_single_file_result(self):
        if not self.validator or not self.target_path: messagebox.showwarning("경고", "먼저 파일 검사를 실행해야 합니다."); return
        template_name = self.template_var.get()
        output_dir = os.path.join("output", re.sub(r'[\\/*?:"<>|]', "", template_name)); os.makedirs(output_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(self.target_path))[0]
        default_filename = f"review_{base_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        save_path = filedialog.asksaveasfilename(title="주석 PDF 결과 저장", initialdir=output_dir, initialfile=default_filename, defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if save_path:
            try:
                self.validator.create_annotated_pdf(self.target_path, save_path)
                messagebox.showinfo("성공", f"결과 파일이 저장되었습니다:\n{save_path}"); self.log(f"결과 파일 저장됨: {save_path}")
            except Exception as e: messagebox.showerror("오류", f"파일 저장 중 오류 발생:\n{e}"); self.log(f"🔥 파일 저장 오류: {e}")

    def load_docs_for_viewer(self, original_path, annotated_path):
        try:
            if self.original_pdf_doc: self.original_pdf_doc.close()
            if self.annotated_pdf_doc: self.annotated_pdf_doc.close()
            self.original_pdf_doc = fitz.open(original_path); self.annotated_pdf_doc = fitz.open(annotated_path)
            self.total_pages = self.original_pdf_doc.page_count; self.current_page_num = 0
            self.root.after(10, self.display_dual_pages)
        except Exception as e: self.log(f"PDF 뷰어 로딩 실패: {e}")

    def display_dual_pages(self):
        if not self.original_pdf_doc or not self.root.winfo_viewable(): return

        page_orig = self.original_pdf_doc[self.current_page_num]
        img_orig = self.render_page_to_image(page_orig, self.left_canvas)
        if img_orig:
            self.left_photo = img_orig
            self.left_canvas.delete("all"); self.left_canvas.create_image(0, 0, anchor=tk.NW, image=self.left_photo)
            self.draw_rois_on_viewer(self.left_canvas, page_orig)

        if self.annotated_pdf_doc and self.current_page_num < self.annotated_pdf_doc.page_count:
            page_annot = self.annotated_pdf_doc[self.current_page_num]
            img_annot = self.render_page_to_image(page_annot, self.right_canvas)
            if img_annot: self.right_photo = img_annot; self.right_canvas.delete("all"); self.right_canvas.create_image(0, 0, anchor=tk.NW, image=self.right_photo)

        self.update_navigation_buttons()

    def draw_rois_on_viewer(self, canvas, page):
        if not self.selected_template: return
        zoom = min(canvas.winfo_width() / page.rect.width, canvas.winfo_height() / page.rect.height)
        mat = fitz.Matrix(zoom, zoom)

        for field_name, roi_info in self.selected_template['rois'].items():
            if roi_info['page'] == self.current_page_num:
                rect = fitz.Rect(roi_info['coords']) * mat
                color = "blue" if roi_info['method'] == 'ocr' else 'red'
                canvas.create_rectangle(rect.x0, rect.y0, rect.x1, rect.y1, outline=color, width=2, dash=(4, 4))
                canvas.create_text(rect.x0, rect.y0 - 5, text=field_name, fill=color, anchor="sw")

    def render_page_to_image(self, page, canvas):
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if w < 10 or h < 10: return None
        mat = fitz.Matrix(min(w / page.rect.width, h / page.rect.height), min(w / page.rect.width, h / page.rect.height))
        pix = page.get_pixmap(matrix=mat); img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        return ImageTk.PhotoImage(image=img)

    def update_navigation_buttons(self):
        self.page_label.config(text=f"페이지: {self.current_page_num + 1}/{self.total_pages}")
        self.prev_page_btn.config(state=tk.NORMAL if self.current_page_num > 0 else tk.DISABLED)
        self.next_page_btn.config(state=tk.NORMAL if self.total_pages > 0 and self.current_page_num < self.total_pages - 1 else tk.DISABLED)

    def prev_page(self):
        if self.current_page_num > 0: self.current_page_num -= 1; self.display_dual_pages()

    def next_page(self):
        if self.current_page_num < self.total_pages - 1: self.current_page_num += 1; self.display_dual_pages()

    def load_templates(self):
        try:
            if os.path.exists("templates.json"):
                with open('templates.json', 'r', encoding='utf-8') as f: self.templates = json.load(f)
                self.template_combo['values'] = list(self.templates.keys())
                if self.templates: self.template_combo.current(0); self.on_template_selected()
            else: self.templates = {}; self.template_combo['values'] = []
        except Exception as e: self.log(f"템플릿 로드 오류: {str(e)}")

    def on_template_selected(self, event=None):
        template_name = self.template_var.get()
        if template_name in self.templates:
            self.selected_template = self.templates[template_name]
            self.update_validate_button_state()

def main():
    root = tk.Tk()
    app = PDFValidatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()