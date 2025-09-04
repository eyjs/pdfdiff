"""
Template Service
템플릿 관리 도메인 서비스
"""
from typing import List, Optional, Dict
from datetime import datetime

from domain.entities.template import Template
from domain.entities.roi import ROI, ValidationMethod
from domain.repositories.template_repository import TemplateRepository


class TemplateService:
    """템플릿 도메인 서비스"""

    def __init__(self, template_repository: TemplateRepository):
        self._repository = template_repository

    def create_template(self, name: str, pdf_path: str, description: str = None) -> Template:
        """새 템플릿 생성"""
        if self._repository.exists(name):
            raise ValueError(f"템플릿 '{name}'이 이미 존재합니다")

        template = Template(
            name=name,
            original_pdf_path=pdf_path,
            description=description,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

        return template

    def save_template(self, template: Template) -> bool:
        """템플릿 저장"""
        template.updated_at = datetime.now().isoformat()
        return self._repository.save(template)

    def get_template(self, name: str) -> Optional[Template]:
        """템플릿 조회"""
        return self._repository.find_by_name(name)

    def get_all_templates(self) -> List[Template]:
        """모든 템플릿 조회"""
        return self._repository.find_all()

    def get_template_names(self) -> List[str]:
        """템플릿 이름 목록"""
        return self._repository.get_template_names()

    def delete_template(self, name: str) -> bool:
        """템플릿 삭제"""
        return self._repository.delete(name)

    def template_exists(self, name: str) -> bool:
        """템플릿 존재 여부"""
        return self._repository.exists(name)

    def add_roi_to_template(self, template_name: str, roi: ROI) -> bool:
        """템플릿에 ROI 추가"""
        template = self._repository.find_by_name(template_name)
        if not template:
            return False

        try:
            template.add_roi(roi)
            return self.save_template(template)
        except ValueError:
            return False

    def remove_roi_from_template(self, template_name: str, roi_name: str) -> bool:
        """템플릿에서 ROI 제거"""
        template = self._repository.find_by_name(template_name)
        if not template:
            return False

        if template.remove_roi(roi_name):
            return self.save_template(template)
        return False

    def update_roi_in_template(self, template_name: str, roi: ROI) -> bool:
        """템플릿의 ROI 업데이트"""
        template = self._repository.find_by_name(template_name)
        if not template:
            return False

        # 기존 ROI 제거 후 새 ROI 추가
        if roi.name in template.rois:
            template.rois[roi.name] = roi
            return self.save_template(template)

        return False

    def duplicate_template(self, source_name: str, target_name: str) -> bool:
        """템플릿 복제"""
        if self._repository.exists(target_name):
            raise ValueError(f"대상 템플릿 '{target_name}'이 이미 존재합니다")

        source_template = self._repository.find_by_name(source_name)
        if not source_template:
            return False

        # 새 템플릿 생성
        new_template = Template(
            name=target_name,
            original_pdf_path=source_template.original_pdf_path,
            rois=source_template.rois.copy(),
            description=f"{source_template.description} (복제본)" if source_template.description else "복제된 템플릿",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

        return self._repository.save(new_template)

    def validate_template(self, template: Template) -> Dict[str, List[str]]:
        """템플릿 유효성 검사"""
        warnings = []
        errors = []

        # 기본 검증
        if not template.name.strip():
            errors.append("템플릿 이름이 비어있습니다")

        if not template.original_pdf_path.strip():
            errors.append("원본 PDF 경로가 비어있습니다")

        if not template.pdf_path_exists:
            warnings.append("원본 PDF 파일이 존재하지 않습니다")

        # ROI 검증
        if not template.rois:
            warnings.append("ROI가 정의되지 않았습니다")

        # ROI별 상세 검증
        for roi_name, roi in template.rois.items():
            if roi.area <= 0:
                errors.append(f"ROI '{roi_name}': 유효하지 않은 면적")

            if not roi.has_anchor():
                warnings.append(f"ROI '{roi_name}': 앵커가 정의되지 않았습니다")

        # 중복 ROI 검사
        roi_coords = [tuple(roi.coords) for roi in template.rois.values()]
        if len(roi_coords) != len(set(roi_coords)):
            warnings.append("중복된 좌표의 ROI가 있습니다")

        return {
            "errors": errors,
            "warnings": warnings
        }

    def get_template_statistics(self, template_name: str) -> Optional[Dict]:
        """템플릿 통계 정보"""
        template = self._repository.find_by_name(template_name)
        if not template:
            return None

        return {
            "name": template.name,
            "roi_count": template.get_roi_count(),
            "anchored_roi_count": template.get_anchored_roi_count(),
            "total_pages": template.get_total_pages(),
            "pdf_exists": template.pdf_path_exists,
            "created_at": template.created_at,
            "updated_at": template.updated_at
        }
