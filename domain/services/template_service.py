# 파일 경로: domain/services/template_service.py
import os
from domain.entities.template import Template
from domain.entities.roi import ROI, ValidationMethod
from domain.repositories.template_repository import TemplateRepository
from shared.exceptions import TemplateNotFoundError

# Domain Layer (Service)
# 역할: 핵심 비즈니스 로직(Use Case)을 담당합니다.
#       - 애플리케이션의 핵심 규칙과 프로세스를 구현.
#       - 특정 기술(UI, DB, 라이브러리)에 의존하지 않음.
#       - Repository Interface와 다른 Service에만 의존.

class TemplateService:
    def __init__(self, template_repository: TemplateRepository, vision_service):
        self.repository = template_repository
        self.vision_service = vision_service

    def create_roi_with_anchor(self, pdf_doc, page_num, roi_coords, method, threshold):
        """
        앵커를 탐색하고 완전한 ROI 데이터를 생성하는 비즈니스 로직.
        """
        best_anchor_coords = self.vision_service.find_best_anchor(
            pdf_doc=pdf_doc,
            page_num=page_num,
            roi_coords=roi_coords
        )

        if not best_anchor_coords:
            raise Exception("Could not find a suitable anchor region for this ROI.")

        roi_data = {
            'page': page_num,
            'coords': roi_coords,
            'anchor_coords': best_anchor_coords,
            'method': method,
            'threshold': threshold
        }
        return roi_data

    def save_template(self, name: str, pdf_path: str, rois_data: dict):
        """
        템플릿 데이터를 받아 엔티티로 변환 후 Repository에 저장을 위임합니다.
        """
        try:
            relative_pdf_path = os.path.relpath(pdf_path, os.getcwd())
        except ValueError:
            relative_pdf_path = pdf_path

        roi_objects = {
            roi_name: ROI(
                name=roi_name,
                page=roi_data['page'],
                coords=roi_data['coords'],
                anchor_coords=roi_data.get('anchor_coords'),
                method=ValidationMethod(roi_data['method']),
                threshold=roi_data['threshold']
            )
            for roi_name, roi_data in rois_data.items()
        }

        template = Template(
            name=name,
            original_pdf_path=relative_pdf_path,
            rois=roi_objects
        )

        self.repository.save(template)

    def load_template(self, name: str) -> dict:
        """
        템플릿을 로드하고, 컨트롤러가 사용하기 쉬운 dict 형태로 변환하여 반환합니다.
        """
        template = self.repository.load(name)
        if not template:
            raise TemplateNotFoundError(f"템플릿 '{name}'을(를) 찾을 수 없습니다.")

        # 비즈니스 규칙: 원본 PDF 파일의 존재 여부 확인
        abs_pdf_path = os.path.abspath(template.original_pdf_path)
        if not os.path.exists(abs_pdf_path):
            raise FileNotFoundError(f"원본 PDF 파일을 찾을 수 없습니다: {abs_pdf_path}")

        # 컨트롤러가 파일 경로를 바로 사용할 수 있도록 절대 경로로 업데이트
        template_data = template.to_dict()
        template_data['original_pdf_path'] = abs_pdf_path
        
        return template_data

    def get_all_template_names(self) -> list:
        return self.repository.get_all_names()

    def delete_template(self, name: str):
        self.repository.delete(name)
