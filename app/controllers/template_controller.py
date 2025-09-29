import fitz
from PIL import Image
import os

class TemplateController:
    """
    TemplateEditorWindow(View)와 TemplateService(Domain)를 연결하는 컨트롤러.
    사용자 입력을 받아 서비스에 처리를 요청하고, 그 결과를 뷰에 전달합니다.
    """
    def __init__(self, view, template_service):
        self.view = view
        self.service = template_service

        # UI/비즈니스 로직 상태
        self.pdf_doc = None
        self.current_pdf_path = None
        self.current_page_num = 0
        self.current_template_rois = {}

        # 확대/축소 및 패닝 상태
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.is_panning = False
        self.pan_start_x = 0
        self.pan_start_y = 0

    def initialize_view(self):
        pass

    def _render_current_page(self):
        if not self.pdf_doc:
            self.view.update_page_display(None, 0, 0, {})
            return

        page = self.pdf_doc[self.current_page_num]
        mat = self._get_display_matrix()

        pix = page.get_pixmap(matrix=mat, alpha=False)
        page_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        rois_on_page = {}
        for name, roi_data in self.current_template_rois.items():
            if roi_data.get('page') == self.current_page_num:
                pdf_coords = roi_data['coords']
                screen_coords = self._pdf_to_screen_coords(pdf_coords, mat)

                anchor_screen_coords = None
                if 'anchor_coords' in roi_data:
                    anchor_pdf_coords = roi_data['anchor_coords']
                    anchor_screen_coords = self._pdf_to_screen_coords(anchor_pdf_coords, mat)

                rois_on_page[name] = {**roi_data, 'screen_coords': screen_coords, 'anchor_screen_coords': anchor_screen_coords}

        # 4. 최종적으로 가공된 데이터를 View에 전달하여 화면 업데이트 요청
        total_width = page.rect.width * self.zoom
        total_height = page.rect.height * self.zoom

        self.view.update_page_display(
            page_image,
            self.current_page_num,
            len(self.pdf_doc),
            rois_on_page,
            self.pan_x, self.pan_y,
            total_width, total_height
        )

    # --- 좌표 변환 유틸리티 메서드 ---
    def _get_display_matrix(self):
        if not self.pdf_doc:
            return fitz.Matrix(1, 1)

        return fitz.Matrix(self.zoom, self.zoom)

    def _screen_to_pdf_coords(self, x1, y1, x2, y2, mat):
        # 화면 좌표에 팬 값을 빼서 이미지 기준 좌표로 변환 후 역행렬 계산
        x1, y1 = x1 - self.pan_x, y1 - self.pan_y
        x2, y2 = x2 - self.pan_x, y2 - self.pan_y
        p1 = fitz.Point(min(x1, x2), min(y1, y2)) * ~mat
        p2 = fitz.Point(max(x1, x2), max(y1, y2)) * ~mat
        return [p1.x, p1.y, p2.x, p2.y]

    def _pdf_to_screen_coords(self, pdf_coords, mat):
        p1 = fitz.Point(pdf_coords[0], pdf_coords[1]) * mat
        p2 = fitz.Point(pdf_coords[2], pdf_coords[3]) * mat
        # 팬 값을 더해서 최종 화면 좌표 계산
        return p1.x + self.pan_x, p1.y + self.pan_y, p2.x + self.pan_x, p2.y + self.pan_y

    # --- View로부터 전달받는 이벤트 핸들러 ---
    def on_window_resize(self):
        if self.pdf_doc:
            self._render_current_page()

    def open_pdf_file(self):
        path = self.view.ask_open_filename()
        if not path:
            return

        try:
            if self.pdf_doc:
                self.pdf_doc.close()

            self.pdf_doc = fitz.open(path)
            self.current_pdf_path = path
            self.current_page_num = 0
            self.current_template_rois = {}

            # 초기 'fit-to-window' 줌 설정
            page = self.pdf_doc[self.current_page_num]
            self.zoom = min(
                self.view.canvas.winfo_width() / page.rect.width,
                self.view.canvas.winfo_height() / page.rect.height
            )
            self.pan_x, self.pan_y = 0, 0

            self._render_current_page()
        except Exception as e:
            self.view.show_error("Error", f"Failed to open PDF:\n{e}")

    def handle_zoom(self, factor, x, y):
        if not self.pdf_doc:
            return

        # 줌 중심이 될 PDF 좌표 계산
        img_x, img_y = x - self.pan_x, y - self.pan_y
        pdf_p = fitz.Point(img_x, img_y) * ~fitz.Matrix(self.zoom, self.zoom)

        self.zoom *= factor
        self.zoom = max(0.1, min(self.zoom, 5.0)) # 줌 범위 제한

        # 새로운 줌 레벨에서 PDF 좌표의 새 이미지 좌표 계산
        new_img_p = pdf_p * fitz.Matrix(self.zoom, self.zoom)

        # 마우스 포인터가 같은 위치에 있도록 팬 값 조정
        self.pan_x += img_x - new_img_p.x
        self.pan_y += img_y - new_img_p.y

        self._render_current_page()

    def start_pan(self, event):
        self.is_panning = True
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def do_pan(self, event):
        if self.is_panning:
            dx = event.x - self.pan_start_x
            dy = event.y - self.pan_start_y
            self.pan_x += dx
            self.pan_y += dy
            self.pan_start_x = event.x
            self.pan_start_y = event.y
            self._render_current_page()

    def end_pan(self, event):
        self.is_panning = False

    def set_pan(self, x_offset, y_offset):
        """스크롤바로부터 직접 팬 위치를 설정합니다."""
        if not self.pdf_doc: return

        page = self.pdf_doc[self.current_page_num]
        total_width = page.rect.width * self.zoom
        total_height = page.rect.height * self.zoom
        canvas_width = self.view.canvas.winfo_width()
        canvas_height = self.view.canvas.winfo_height()

        if x_offset is not None:
            self.pan_x = -x_offset * (total_width - canvas_width)
        
        if y_offset is not None:
            self.pan_y = -y_offset * (total_height - canvas_height)
        
        self._render_current_page()

    def prev_page(self):
        if self.pdf_doc and self.current_page_num > 0:
            self.current_page_num -= 1
            self._render_current_page()

    def next_page(self):
        if self.pdf_doc and self.current_page_num < len(self.pdf_doc) - 1:
            self.current_page_num += 1
            self._render_current_page()

    def prepare_add_roi(self, x1, y1, x2, y2):
        if not self.pdf_doc:
            return

        mat = self._get_display_matrix()
        pdf_coords = self._screen_to_pdf_coords(x1, y1, x2, y2, mat)

        pdf_w = pdf_coords[2] - pdf_coords[0]
        pdf_h = pdf_coords[3] - pdf_coords[1]

        validation_scale = 3.0
        roi_pixel_area = (pdf_w * validation_scale) * (pdf_h * validation_scale)

        suggested_threshold = max(50, int(roi_pixel_area * 0.03))

        roi_info = self.view.get_roi_creation_info(suggested_threshold)
        name = roi_info.get('name')

        if not name:
            return
        if name in self.current_template_rois:
            self.view.show_error("Error", "ROI name must be unique.")
            return

        try:
            new_roi_data = self.service.create_roi_with_anchor(
                pdf_doc=self.pdf_doc,
                page_num=self.current_page_num,
                roi_coords=pdf_coords,
                method=roi_info.get('method'),
                threshold=roi_info.get('threshold'),
                ocr_config=roi_info.get('ocr_config')
            )

            self.current_template_rois[name] = new_roi_data
            self._render_current_page()
        except Exception as e:
            self.view.show_error("Anchor Error", str(e))

    def delete_selected_roi(self):
        roi_name = self.view.get_selected_roi_name()
        if not roi_name:
            return

        if self.view.ask_yes_no("Confirm Delete", f"Delete ROI '{roi_name}'?"):
            del self.current_template_rois[roi_name]
            self._render_current_page()

    def save_template(self):
        if not self.current_template_rois or not self.current_pdf_path:
            self.view.show_warning("Warning", "Open a PDF and define at least one ROI.")
            return

        default_name = os.path.splitext(os.path.basename(self.current_pdf_path))[0]
        template_name = self.view.ask_string("Save Template", "Template Name:", initial_value=default_name)
        if not template_name:
            return

        try:
            self.service.save_template(
                template_name,
                self.current_pdf_path,
                self.current_template_rois
            )
            self.view.show_info("Success", f"Template '{template_name}' saved.")
        except Exception as e:
            self.view.show_error("Save Error", str(e))

    def load_template(self):
        try:
            all_templates = self.service.get_all_template_names()
            template_name = self.view.ask_load_template(all_templates)

            if not template_name:
                return

            template_data = self.service.load_template(template_name)

            if self.pdf_doc:
                self.pdf_doc.close()

            pdf_path = template_data['original_pdf_path']
            self.pdf_doc = fitz.open(pdf_path)
            self.current_pdf_path = pdf_path
            self.current_template_rois = template_data['rois']
            self.current_page_num = 0

            # Fit to window on load
            page = self.pdf_doc[self.current_page_num]
            self.zoom = min(
                self.view.canvas.winfo_width() / page.rect.width,
                self.view.canvas.winfo_height() / page.rect.height
            )
            self.pan_x, self.pan_y = 0, 0

            self._render_current_page()

        except Exception as e:
            self.view.show_error("Load Error", str(e))

    def delete_template(self):
        try:
            all_templates = self.service.get_all_template_names()
            template_name = self.view.ask_load_template(all_templates)

            if not template_name:
                return

            if self.view.ask_yes_no("Confirm Delete", f"Are you sure you want to delete template '{template_name}'?"):
                self.service.delete_template(template_name)
                self.view.show_info("Success", f"Template '{template_name}' deleted.")
        except Exception as e:
            self.view.show_error("Delete Error", str(e))

