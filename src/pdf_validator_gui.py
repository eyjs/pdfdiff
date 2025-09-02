# src/pdf_validator_gui.py (v4.5 - English UI & Dialog Fix)

import pytesseract
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter import scrolledtext
import json
import os
import fitz  # PyMuPDF
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import sys
from PIL import Image, ImageTk
import re
import datetime
import time

# Set Tesseract path for bundled executable
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
    # Corrected path to vendor directory
    tesseract_path = os.path.join(application_path, 'vendor', 'tesseract', 'tesseract.exe')
    if os.path.exists(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

class PDFValidator:
    """
    [v4.5 Final] PDF Validation Engine with detailed logging and diff-based contour validation.
    """
    def __init__(self, template_data):
        self.template_data = template_data
        self.original_pdf_path = template_data["original_pdf_path"]
        self.rois = template_data["rois"]
        self.validation_results = []
        self.detector = cv2.AKAZE_create()

    def _get_full_page_image(self, page, scale=1.5):
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    def _get_homography_matrix(self, img1, img2):
        kp1, des1 = self.detector.detectAndCompute(img1, None)
        kp2, des2 = self.detector.detectAndCompute(img2, None)
        if des1 is None or des2 is None or len(des1) < 2 or len(des2) < 2:
            return None
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = sorted(bf.match(des1, des2), key=lambda x: x.distance)
        good_matches = matches[:50]
        if len(good_matches) > 10:
            src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            matrix, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            return matrix
        return None

    def validate_pdf(self, filled_pdf_path, progress_callback=None):
        original_doc = fitz.open(self.original_pdf_path)
        filled_doc = fitz.open(filled_pdf_path)
        page_matrices = {}
        for i in range(min(len(original_doc), len(filled_doc))):
            if progress_callback:
                progress_callback(f"  - Analyzing scale/rotation for page {i+1}...", -1, -1)
            img_orig = self._get_full_page_image(original_doc[i])
            img_filled = self._get_full_page_image(filled_doc[i])
            page_matrices[i] = self._get_homography_matrix(img_orig, img_filled)
        
        self.validation_results = []
        for i, (field_name, roi_info) in enumerate(self.rois.items()):
            if progress_callback:
                progress_callback(f"  - Validating '{field_name}'...", i, len(self.rois))
            result = self._validate_single_roi(original_doc, filled_doc, field_name, roi_info, page_matrices.get(roi_info.get("page", 0)))
            self.validation_results.append(result)
        
        original_doc.close()
        filled_doc.close()
        return self.validation_results

    def _validate_single_roi(self, original_doc, filled_doc, field_name, roi_info, homography_matrix):
        page_num = roi_info.get("page", 0)
        coords = roi_info.get("coords")
        method = roi_info.get("method", "ocr")
        threshold = roi_info.get("threshold", 500)
        anchor_coords = roi_info.get("anchor_coords")
        
        result = {"field_name": field_name, "page": page_num, "coords": coords, "status": "OK", "message": ""}
        if not coords:
            result["status"] = "ERROR"
            result["message"] = "Coordinate information missing"
            return result

        try:
            render_scale = 2.0
            original_roi = self._extract_roi_image(original_doc, page_num, coords, render_scale)
            
            if anchor_coords:
                anchor_template_img = self._extract_roi_image(original_doc, page_num, anchor_coords, render_scale, grayscale=True)
                filled_page_img = self._get_full_page_image(filled_doc[page_num], render_scale)
                top_left, _ = self._find_roi_with_template_matching(filled_page_img, anchor_template_img)
                if top_left:
                    relative_x0 = (coords[0] - anchor_coords[0]) * render_scale
                    relative_y0 = (coords[1] - anchor_coords[1]) * render_scale
                    roi_width = (coords[2] - coords[0]) * render_scale
                    roi_height = (coords[3] - coords[1]) * render_scale
                    final_x0 = top_left[0] + relative_x0
                    final_y0 = top_left[1] + relative_y0
                    new_coords = [final_x0 / render_scale, final_y0 / render_scale, (final_x0 + roi_width) / render_scale, (final_y0 + roi_height) / render_scale]
                else:
                    new_coords = coords
                    result['message'] += "[Anchor not found] "
            elif homography_matrix is not None:
                pts = np.float32([[c[0], c[1]] for c in [coords[:2], [coords[2], coords[1]], coords[2:], [coords[0], coords[3]]]]).reshape(-1, 1, 2)
                pts *= render_scale
                dst_pts = cv2.perspectiveTransform(pts, homography_matrix)
                x_coords, y_coords = [p[0][0] for p in dst_pts], [p[0][1] for p in dst_pts]
                new_coords = [min(x_coords)/render_scale, min(y_coords)/render_scale, max(x_coords)/render_scale, max(y_coords)/render_scale]
            else:
                new_coords = coords

            filled_roi = self._extract_roi_image(filled_doc, page_num, new_coords, render_scale)

            if self._is_field_empty(original_roi, filled_roi):
                result["status"] = "DEFICIENT"
                result["message"] += "Field is empty"
                return result

            if method == "contour":
                is_valid, detected_area = self._validate_contour_by_diff(original_roi, filled_roi, threshold)
                if not is_valid:
                    result["status"] = "DEFICIENT"
                    result["message"] += f"Content deficient [Detected Area: {detected_area} / Required: {threshold}]"
                else:
                    result["message"] += f"OK [Detected Area: {detected_area} / Required: {threshold} ({(detected_area/threshold)*100:.0f}%)]"
            elif method == "ocr":
                is_valid, detected_text = self._validate_ocr(filled_roi, threshold)
                if not is_valid:
                    result["status"] = "DEFICIENT"
                    result["message"] += f"Content deficient [Detected Text: '{detected_text}']"
                else:
                    result["message"] += f"OK [Detected Text: '{detected_text}']"
        except Exception as e:
            result["status"] = "ERROR"
            result["message"] = f"Validation Error: {str(e)}"
        return result

    def _find_roi_with_template_matching(self, page_img, anchor_template_img):
        res = cv2.matchTemplate(page_img, anchor_template_img, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val > 0.6:
            return max_loc, anchor_template_img.shape
        return None, None

    def _extract_roi_image(self, pdf_doc, page_num, coords, scale=2.0, grayscale=False):
        page = pdf_doc[page_num]
        rect = fitz.Rect(coords)
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat, clip=rect, alpha=False)
        img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if grayscale:
            return cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        if pix.n == 4: # Handle RGBA
            return cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
        return img_array

    def _is_field_empty(self, original_roi, filled_roi, ssim_threshold=0.90):
        h, w, _ = original_roi.shape
        try:
            filled_roi_resized = cv2.resize(filled_roi, (w, h))
        except cv2.error:
            return True # Cannot resize, likely empty or invalid
        original_gray = cv2.cvtColor(original_roi, cv2.COLOR_RGB2GRAY)
        filled_gray = cv2.cvtColor(filled_roi_resized, cv2.COLOR_RGB2GRAY)
        return ssim(original_gray, filled_gray, data_range=255) > ssim_threshold

    def _validate_contour_by_diff(self, original_roi, filled_roi, threshold):
        """Validates contour based on the difference from the original."""
        h, w, _ = original_roi.shape
        filled_roi_resized = cv2.resize(filled_roi, (w, h))
        original_gray = cv2.cvtColor(original_roi, cv2.COLOR_RGB2GRAY)
        filled_gray = cv2.cvtColor(filled_roi_resized, cv2.COLOR_RGB2GRAY)
        
        # 1. Calculate difference
        diff = cv2.absdiff(original_gray, filled_gray)
        
        # 2. Binarize the difference to extract new marks
        binary = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)[1]
        
        # 3. Calculate contours on the difference
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        total_area = sum(cv2.contourArea(c) for c in contours)
        return total_area >= threshold, int(total_area)

    def _validate_ocr(self, roi_image, threshold):
        text = pytesseract.image_to_string(roi_image, lang='kor+eng')
        cleaned_text = re.sub(r'[\s\W_]+', '', text)
        return len(cleaned_text) >= threshold, cleaned_text

    def create_annotated_pdf(self, filled_pdf_path, output_path):
        try:
            pdf_doc = fitz.open(filled_pdf_path)
            for result in self.validation_results:
                if result["status"] == "DEFICIENT":
                    page = pdf_doc[result["page"]]
                    rect = fitz.Rect(result["coords"])
                    highlight = page.add_highlight_annot(rect)
                    highlight.set_colors({"stroke": (1, 1, 0)}) # Yellow
                    highlight.update()
            pdf_doc.save(output_path, garbage=4, deflate=True, clean=True)
            pdf_doc.close()
            return True
        except Exception as e:
            raise Exception(f"Failed to create annotated PDF: {str(e)}")

class PDFValidatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Step 2: Document Validator (v4.5)")
        self.root.geometry("1200x900")
        self.templates, self.selected_template, self.target_path, self.validator = {}, None, "", None
        self.original_pdf_doc, self.annotated_pdf_doc, self.current_page_num, self.total_pages = None, None, 0, 0
        self.left_photo, self.right_photo = None, None
        self.setup_ui()
        self.load_templates()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        control_frame = ttk.LabelFrame(main_frame, text="Validation Settings", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.mode_var = tk.StringVar(value="Folder")
        ttk.Label(control_frame, text="Validation Mode:").grid(row=0, column=0, sticky=tk.W, pady=5)
        mode_frame = ttk.Frame(control_frame)
        mode_frame.grid(row=0, column=1, columnspan=2, sticky=tk.W)
        ttk.Radiobutton(mode_frame, text="Validate by File", variable=self.mode_var, value="File", command=self.switch_mode).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="Validate by Folder", variable=self.mode_var, value="Folder", command=self.switch_mode).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame, text="Select Template:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.template_var = tk.StringVar()
        self.template_combo = ttk.Combobox(control_frame, textvariable=self.template_var, state="readonly", width=40)
        self.template_combo.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        self.template_combo.bind('<<ComboboxSelected>>', self.on_template_selected)
        ttk.Button(control_frame, text="Reload", command=self.load_templates).grid(row=1, column=2, padx=5, pady=5)
        
        self.target_label = ttk.Label(control_frame, text="Target Folder:")
        self.target_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(control_frame, textvariable=self.path_var, state="readonly", width=40)
        self.path_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        self.browse_btn = ttk.Button(control_frame, text="Browse...", command=self.browse_target)
        self.browse_btn.grid(row=2, column=2, padx=5, pady=5)
        control_frame.columnconfigure(1, weight=1)
        
        self.validate_btn = ttk.Button(main_frame, text="Run Validation", command=self.run_validation, state=tk.DISABLED)
        self.validate_btn.pack(pady=10)
        
        self.viewer_frame = ttk.Frame(main_frame)
        viewer_pane = ttk.PanedWindow(self.viewer_frame, orient=tk.HORIZONTAL)
        viewer_pane.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        left_viewer_frame = ttk.LabelFrame(viewer_pane, text="Original Template", padding="5")
        viewer_pane.add(left_viewer_frame, weight=1)
        self.left_canvas = tk.Canvas(left_viewer_frame, bg="white")
        self.left_canvas.pack(fill=tk.BOTH, expand=True)
        
        right_viewer_frame = ttk.LabelFrame(viewer_pane, text="Validated Document (Annotated)", padding="5")
        viewer_pane.add(right_viewer_frame, weight=1)
        self.right_canvas = tk.Canvas(right_viewer_frame, bg="white")
        self.right_canvas.pack(fill=tk.BOTH, expand=True)
        
        nav_frame = ttk.Frame(self.viewer_frame)
        nav_frame.pack(fill=tk.X, pady=5)
        self.prev_page_btn = ttk.Button(nav_frame, text="< Prev", command=self.prev_page, state=tk.DISABLED)
        self.prev_page_btn.pack(side=tk.LEFT)
        self.page_label = ttk.Label(nav_frame, text="Page: 0/0")
        self.page_label.pack(side=tk.LEFT, padx=10)
        self.next_page_btn = ttk.Button(nav_frame, text="Next >", command=self.next_page, state=tk.DISABLED)
        self.next_page_btn.pack(side=tk.LEFT)
        self.save_file_btn = ttk.Button(nav_frame, text="Save Result", command=self.save_single_file_result, state=tk.DISABLED)
        self.save_file_btn.pack(side=tk.RIGHT, padx=10)
        
        log_frame = ttk.LabelFrame(main_frame, text="Progress Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, font=('Consolas', 10))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.progress_bar = ttk.Progressbar(log_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        self.switch_mode()

    def update_validate_button_state(self):
        if self.selected_template and self.target_path:
            self.validate_btn.config(state=tk.NORMAL)
        else:
            self.validate_btn.config(state=tk.DISABLED)

    def switch_mode(self):
        mode = self.mode_var.get()
        self.path_var.set("")
        self.target_path = ""
        if mode == "File":
            self.target_label.config(text="Target File:")
            self.browse_btn.config(text="Browse File...")
            self.viewer_frame.pack(fill=tk.BOTH, expand=True)
            self.save_file_btn.config(state=tk.DISABLED)
        else: # Folder
            self.target_label.config(text="Target Folder:")
            self.browse_btn.config(text="Browse Folder...")
            self.viewer_frame.pack_forget()
        self.update_validate_button_state()

    def browse_target(self):
        mode = self.mode_var.get()
        if mode == "File":
            path = filedialog.askopenfilename(title="Select PDF File", filetypes=[("PDF files", "*.pdf")])
        else:
            path = filedialog.askdirectory(title="Select PDF Folder")
        if path:
            self.target_path = path
            self.path_var.set(path)
            self.log(f"Target selected: {path}")
            self.update_validate_button_state()

    def run_validation(self):
        if self.mode_var.get() == "File":
            self.run_file_validation()
        else:
            self.run_folder_validation()

    def log_results(self, results):
        for result in results:
            icon = "OK" if result['status'] == 'OK' else "FAIL"
            self.log(f"  {icon} [{result['field_name']}]: {result['message']}")

    def run_file_validation(self):
        self.validate_btn.config(state=tk.DISABLED)
        self.save_file_btn.config(state=tk.DISABLED)
        self.log_text.delete('1.0', tk.END)
        self.log(f"Starting file validation: {os.path.basename(self.target_path)}")
        self.validator = PDFValidator(self.selected_template)
        results = self.validator.validate_pdf(self.target_path, lambda msg, c, t: self.log(msg))
        self.log("="*50 + "\nDetailed Validation Results:")
        self.log_results(results)
        deficient = sum(1 for r in results if r['status'] == 'DEFICIENT')
        temp_dir = "output"
        os.makedirs(temp_dir, exist_ok=True)
        temp_annot_path = os.path.join(temp_dir, f"temp_review_{int(time.time())}.pdf")
        self.validator.create_annotated_pdf(self.target_path, temp_annot_path)
        self.log("="*50)
        self.log(f"Summary: {'FAIL' if deficient > 0 else 'PASS'} ({deficient} deficient items)")
        self.log("="*50)
        self.load_docs_for_viewer(self.selected_template['original_pdf_path'], temp_annot_path)
        self.validate_btn.config(state=tk.NORMAL)
        self.save_file_btn.config(state=tk.NORMAL)

    def run_folder_validation(self):
        self.validate_btn.config(state=tk.DISABLED)
        self.log_text.delete('1.0', tk.END)
        self.log("="*50 + "\nStarting batch validation.")
        pdf_files = [f for f in os.listdir(self.target_path) if f.lower().endswith('.pdf')]
        if not pdf_files:
            messagebox.showinfo("Done", "No PDF files found in the folder.", parent=self.root)
            self.validate_btn.config(state=tk.NORMAL)
            return
        template_name = self.template_var.get()
        output_dir = os.path.join("output", template_name)
        os.makedirs(output_dir, exist_ok=True)
        self.validator = PDFValidator(self.selected_template)
        total_files = len(pdf_files)
        self.progress_bar['maximum'] = total_files
        success_count, fail_count = 0, 0
        start_time = time.time()
        for i, pdf_file in enumerate(pdf_files):
            self.progress_bar['value'] = i + 1
            path = os.path.join(self.target_path, pdf_file)
            self.log(f"[{i+1}/{total_files}] Validating '{pdf_file}'...")
            try:
                results = self.validator.validate_pdf(path, lambda msg, c, t: self.log(msg) if c > -1 else None)
                self.log_results(results)
                deficient = sum(1 for r in results if r['status'] == 'DEFICIENT')
                if deficient > 0:
                    fail_count += 1
                    out_path = os.path.join(output_dir, f"review_{os.path.splitext(pdf_file)[0]}_{int(time.time())}.pdf")
                    self.validator.create_annotated_pdf(path, out_path)
                    self.log(f"  -> FAIL ({deficient} items). Saved to: {out_path}\n")
                else:
                    success_count += 1
                    self.log("  -> PASS.\n")
            except Exception as e:
                fail_count += 1
                self.log(f"  -> ERROR: {e}\n")
        total_time = time.time() - start_time
        self.log("="*50 + "\nBatch validation complete.")
        summary = f"Total {total_files} files processed\n\nPASS: {success_count}\nFAIL: {fail_count}\n\n(Duration: {total_time:.2f}s)"
        self.log(summary)
        messagebox.showinfo("Validation Complete", summary, parent=self.root)
        self.validate_btn.config(state=tk.NORMAL)

    def save_single_file_result(self):
        if not self.validator or not self.target_path:
            messagebox.showwarning("Warning", "You must run a file validation first.", parent=self.root)
            return
        template_name = self.template_var.get()
        output_dir = os.path.join("output", template_name)
        os.makedirs(output_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(self.target_path))[0]
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"review_{base_name}_{timestamp}.pdf"
        save_path = filedialog.asksaveasfilename(title="Save Annotated PDF Result", initialdir=output_dir, initialfile=default_filename, defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if save_path:
            try:
                self.validator.create_annotated_pdf(self.target_path, save_path)
                messagebox.showinfo("Success", f"Result file saved successfully:\n{save_path}", parent=self.root)
                self.log(f"Result file saved: {save_path}")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while saving the file:\n{e}", parent=self.root)
                self.log(f"ERROR saving file: {e}")

    def load_docs_for_viewer(self, original_path, annotated_path):
        if self.original_pdf_doc: self.original_pdf_doc.close()
        if self.annotated_pdf_doc: self.annotated_pdf_doc.close()
        self.original_pdf_doc = fitz.open(original_path)
        self.annotated_pdf_doc = fitz.open(annotated_path)
        self.total_pages = self.original_pdf_doc.page_count
        self.current_page_num = 0
        self.display_dual_pages()

    def display_dual_pages(self):
        if not self.original_pdf_doc: return
        page_orig = self.original_pdf_doc[self.current_page_num]
        img_orig = self.render_page_to_image(page_orig, self.left_canvas)
        if img_orig:
            self.left_photo = img_orig
            self.left_canvas.delete("all")
            self.left_canvas.create_image(0, 0, anchor=tk.NW, image=self.left_photo)
            self.draw_rois_on_viewer(self.left_canvas, page_orig)
        
        if self.annotated_pdf_doc and self.current_page_num < self.annotated_pdf_doc.page_count:
            page_annot = self.annotated_pdf_doc[self.current_page_num]
            img_annot = self.render_page_to_image(page_annot, self.right_canvas)
            if img_annot:
                self.right_photo = img_annot
                self.right_canvas.delete("all")
                self.right_canvas.create_image(0, 0, anchor=tk.NW, image=self.right_photo)
        
        self.update_navigation_buttons()

    def draw_rois_on_viewer(self, canvas, page):
        if not self.selected_template: return
        mat = fitz.Matrix(min(canvas.winfo_width() / page.rect.width, canvas.winfo_height() / page.rect.height), min(canvas.winfo_width() / page.rect.width, canvas.winfo_height() / page.rect.height))
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
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        return ImageTk.PhotoImage(image=img)

    def update_navigation_buttons(self):
        self.page_label.config(text=f"Page: {self.current_page_num + 1}/{self.total_pages}")
        self.prev_page_btn.config(state=tk.NORMAL if self.current_page_num > 0 else tk.DISABLED)
        self.next_page_btn.config(state=tk.NORMAL if self.total_pages > 0 and self.current_page_num < self.total_pages - 1 else tk.DISABLED)

    def prev_page(self):
        if self.current_page_num > 0:
            self.current_page_num -= 1
            self.display_dual_pages()

    def next_page(self):
        if self.current_page_num < self.total_pages - 1:
            self.current_page_num += 1
            self.display_dual_pages()

    def log(self, message):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def load_templates(self):
        templates_path = "templates.json"
        try:
            if os.path.exists(templates_path):
                with open(templates_path, 'r', encoding='utf-8') as f:
                    self.templates = json.load(f)
                self.template_combo['values'] = list(self.templates.keys())
                if self.templates:
                    self.template_combo.set(list(self.templates.keys())[0])
                    self.on_template_selected()
            else:
                self.templates = {}
                self.template_combo['values'] = []
        except Exception as e:
            self.log(f"Error loading templates: {str(e)}")

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
