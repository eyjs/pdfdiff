from domain.repositories.template_repository import TemplateRepository
from domain.entities.template import Template
from domain.entities.roi import ROI
from shared.types import FieldName
from shared.exceptions import AppError, NotFoundError, DuplicateError

class TemplateService:
    """
    템플릿과 관련된 핵심 비즈니스 로직을 처리하는 서비스.
    컨트롤러로부터 요청을 받아 Repository를 통해 데이터를 처리하고 결과를 반환합니다.
    """
    def __init__(self, template_repository: TemplateRepository):
        self.repository = template_repository

    def get_all_templates(self) -> list[Template]:
        """모든 템플릿 목록을 반환합니다."""
        return self.repository.get_all()

    def get_template_by_id(self, template_id: str) -> Template:
        """ID로 특정 템플릿을 찾아 반환합니다."""
        template = self.repository.get_by_id(template_id)
        if not template:
            raise NotFoundError(f"Template with id '{template_id}' not found.")
        return template

    def create_template(self, name: str, pdf_path: str) -> Template:
        """새로운 템플릿을 생성하고 저장합니다."""
        if self.repository.get_by_id(name):
             raise DuplicateError(f"Template with name '{name}' already exists.")

        new_template = Template(name=name, original_pdf_path=pdf_path)
        self.repository.save(new_template)
        return new_template

    def save_template(self, template: Template):
        """템플릿을 저장소에 저장(업데이트)합니다."""
        self.repository.save(template)

    def delete_template(self, template_id: str):
        """ID로 템플릿을 삭제합니다."""
        self.repository.delete(template_id)

    def add_roi(self, template_id: str, roi: ROI) -> Template:
        """템플릿에 ROI를 추가합니다. ROI 이름 중복을 허용하지 않습니다."""
        template = self.get_template_by_id(template_id)
        if roi.name in template.rois:
            raise DuplicateError(f"ROI with name '{roi.name}' already exists in template '{template_id}'.")

        template.rois[roi.name] = roi
        self.save_template(template)
        return template

    def update_roi(self, template_id: str, old_roi_name: FieldName, updated_roi: ROI) -> Template:
        """템플릿의 ROI를 업데이트합니다."""
        template = self.get_template_by_id(template_id)
        if old_roi_name not in template.rois:
            raise NotFoundError(f"ROI with name '{old_roi_name}' not found in template '{template_id}'.")

        # ROI 이름이 변경된 경우, 기존 키를 삭제하고 새 키로 추가
        if old_roi_name != updated_roi.name:
            if updated_roi.name in template.rois:
              raise DuplicateError(f"Another ROI with name '{updated_roi.name}' already exists.")
            del template.rois[old_roi_name]

        template.rois[updated_roi.name] = updated_roi
        self.save_template(template)
        return template

    def delete_roi(self, template_id: str, roi_name: FieldName) -> Template:
        """템플릿에서 ROI를 삭제합니다."""
        template = self.get_template_by_id(template_id)
        if roi_name not in template.rois:
            raise NotFoundError(f"ROI with name '{roi_name}' not found in template '{template_id}'.")

        del template.rois[roi_name]
        self.save_template(template)
        return template
