# 파일 경로: app/controllers/template_controller.py
import fitz
from PIL import Image
import os

# Application Layer (Controller)
# 역할: View(GUI)와 Domain(Service) 사이의 중재자.
#       - View로부터 사용자 이벤트를 받아서 처리.
#       - 필요한 데이터를 준비하여 Service에 전달하고, 로직 실행을 요청.
#       - Service로부터 결과를 받아서 View가 화면에 표시할 수 있는 형태로 가공하여 전달.

class TemplateController:
    def __init__(self, view, template_service):
        self.view = view
        self.service = template_service
        self.pdf_doc = None
        self.current_pdf_path = None
        self.current_page_num = 0
        self.current_template_rois = {}

    def _render_current_page(self):
        """현재 페이지를 이미지로 변환하고 화면 업데이트를 요청합니다."""
        if not self.pdf_doc:
            self.view.update_page_display(None, 0, 0, {})
            return

        page = self.pdf_doc[self.current_page_num]

        # 1. 페이지를 이미지로 렌더링
        mat = self._get_display_matrix()
        pix = page.get_pixmap(matrix=mat, alpha=False)
        page_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # 2. 현재 페이지의 ROI들을 화면 좌표로 변환
        rois_on_page = {}
        for name, roi_data in self.current_template_rois.items():
            if roi_data.get('page') == self.current_page_num:
                # PDF 좌표를 화면 좌표로 변환
                pdf_coords = roi_data['coords']
                screen_coords = self._pdf_to_screen_coords(pdf_coords, mat)

                # 앵커 좌표도 변환
                anchor_screen_coords = None
                if 'anchor_coords' in roi_data:
                    anchor_pdf_coords = roi_data['anchor_coords']
                    anchor_screen_coords = self._pdf_to_screen_coords(anchor_pdf_coords, mat)

                rois_on_page[name] = {**roi_data, 'screen_coords': screen_coords, 'anchor_screen_coords': anchor_screen_coords}

        # 3. View에 업데이트 요청
        self.view.update_page_display(
            page_image,
            self.current_page_num,
            len(self.pdf_doc),
            rois_on_page
        )

    # --- Coordinate Conversion ---
    def _get_display_matrix(self):
        if not self.pdf_doc or self.view.canvas.winfo_width() < 10:
            return fitz.Matrix(1, 1)
        page = self.pdf_doc[self.current_page_num]
        zoom = min(
            self.view.canvas.winfo_width() / page.rect.width,
            self.view.canvas.winfo_height() / page.rect.height
        )
        return fitz.Matrix(zoom, zoom)

    def _screen_to_pdf_coords(self, x1, y1, x2, y2, mat):
        p1 = fitz.Point(min(x1, x2), min(y1, y2)) * ~mat
        p2 = fitz.Point(max(x1, x2), max(y1, y2)) * ~mat
        return [p1.x, p1.y, p2.x, p2.y]

    def _pdf_to_screen_coords(self, pdf_coords, mat):
        p1 = fitz.Point(pdf_coords[0], pdf_coords[1]) * mat
        p2 = fitz.Point(pdf_coords[2], pdf_coords[3]) * mat
        return p1.x, p1.y, p2.x, p2.y

    # --- UI Event Handlers ---
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
            self._render_current_page()
        except Exception as e:
            self.view.show_error("Error", f"Failed to open PDF:\n{e}")

    def prev_page(self):
        if self.pdf_doc and self.current_page_num > 0:
            self.current_page_num -= 1
            self._render_current_page()

    def next_page(self):
        if self.pdf_doc and self.current_page_num < len(self.pdf_doc) - 1:
            self.current_page_num += 1
            self._render_current_page()

    def add_roi(self, x1, y1, x2, y2):
        if not self.pdf_doc:
            return

        # 1. View로부터 ROI 생성에 필요한 정보(이름, 방식 등)를 받음
        roi_info = self.view.get_roi_creation_info()
        name = roi_info.get('name')

        if not name:
            return # 사용자가 취소
        if name in self.current_template_rois:
            self.view.show_error("Error", "ROI name must be unique.")
            return

        # 2. Service에 비즈니스 로직(앵커 탐색 등) 처리 요청
        mat = self._get_display_matrix()
        pdf_coords = self._screen_to_pdf_coords(x1, y1, x2, y2, mat)

        try:
            # Service는 복잡한 이미지 처리와 앵커 탐색을 담당
            new_roi_data = self.service.create_roi_with_anchor(
                pdf_doc=self.pdf_doc,
                page_num=self.current_page_num,
                roi_coords=pdf_coords,
                method=roi_info.get('method'),
                threshold=roi_info.get('threshold')
            )

            # 3. Service로부터 받은 결과로 상태 업데이트 및 화면 갱신
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

            # 새 PDF 열고 상태 업데이트
            if self.pdf_doc:
                self.pdf_doc.close()

            pdf_path = template_data['original_pdf_path']
            self.pdf_doc = fitz.open(pdf_path)
            self.current_pdf_path = pdf_path
            self.current_template_rois = template_data['rois']
            self.current_page_num = 0 # 항상 첫 페이지부터 시작

            self._render_current_page()

        except Exception as e:
            self.view.show_error("Load Error", str(e))

    def delete_template(self):
        try:
            all_templates = self.service.get_all_template_names()
            template_name = self.view.ask_load_template(all_templates) # 선택 UI 재활용

            if not template_name:
                return

            if self.view.ask_yes_no("Confirm Delete", f"Are you sure you want to delete template '{template_name}'?"):
                self.service.delete_template(template_name)
                self.view.show_info("Success", f"Template '{template_name}' deleted.")
        except Exception as e:
            self.view.show_error("Delete Error", str(e))