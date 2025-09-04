# 파일 경로: domain/services/template_service.py
import os

# Domain Layer (Service)
# 역할: 핵심 비즈니스 로직(Use Case)을 담당합니다.
#       - 애플리케이션의 핵심 규칙과 프로세스를 구현.
#       - 특정 기술(UI, DB, 라이브러리)에 의존하지 않음.
#       - Repository Interface와 다른 Service에만 의존.

class TemplateService:
    def __init__(self, template_repository, vision_service):
        self.repository = template_repository
        self.vision_service = vision_service

    def create_roi_with_anchor(self, pdf_doc, page_num, roi_coords, method, threshold):
        """
        앵커를 탐색하고 완전한 ROI 데이터를 생성하는 비즈니스 로직.
        """
        # Infrastructure 계층의 Vision Service를 호출하여 앵커 탐색
        best_anchor_coords = self.vision_service.find_best_anchor(
            pdf_doc=pdf_doc,
            page_num=page_num,
            roi_coords=roi_coords
        )

        if not best_anchor_coords:
            raise Exception("Could not find a suitable anchor region for this ROI.")

        # 완전한 ROI 데이터 객체 생성
        roi_data = {
            'page': page_num,
            'coords': roi_coords,
            'anchor_coords': best_anchor_coords,
            'method': method,
            'threshold': threshold
        }
        return roi_data

    def save_template(self, name, pdf_path, rois):
        # PDF 경로를 상대 경로로 변환하는 비즈니스 규칙
        try:
            relative_pdf_path = os.path.relpath(pdf_path, os.getcwd())
        except ValueError:
            relative_pdf_path = pdf_path # 다른 드라이브 등 예외 처리

        # Repository를 통해 데이터 저장
        self.repository.save(name, relative_pdf_path, rois)

    def load_template(self, name):
        template_data = self.repository.load(name)
        if not os.path.exists(template_data['original_pdf_path']):
            raise FileNotFoundError(f"Original PDF not found at: {template_data['original_pdf_path']}")
        return template_data

    def get_all_template_names(self):
        return self.repository.get_all_names()

    def delete_template(self, name):
        self.repository.delete(name)