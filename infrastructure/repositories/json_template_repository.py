import json
import os
from typing import List, Optional
from domain.entities.template import Template
from domain.entities.roi import ROI
from domain.repositories.template_repository import TemplateRepository
from shared.exceptions import TemplateNotFoundError, DataPersistenceError, DataIntegrityError

# 'settings' 객체를 import하여 중앙에서 설정을 관리합니다.
from shared.settings import settings

class JsonTemplateRepository(TemplateRepository):
    """
    JSON 파일 기반으로 템플릿 데이터를 관리하는 리포지토리 구현체.
    중앙 설정 객체(settings)를 통해 파일 경로를 관리하여 안정성을 높였습니다.
    """
    def __init__(self, file_path: str = None):
        """
        리포지토리를 초기화합니다.
        Args:
            file_path (str, optional): 템플릿 JSON 파일의 경로.
                                       None이면 중앙 설정 객체에서 경로를 가져옵니다.
        """
        if file_path is None:
            self.file_path = settings.storage.templates_file
        else:
            self.file_path = file_path

        # 클래스 내부에 템플릿 데이터를 저장할 변수 초기화
        self._templates: List[Template] = []
        # 초기 데이터 로드
        self._load_from_file()

    def _load_from_file(self) -> None:
        """
        JSON 파일에서 템플릿 데이터를 로드하여 내부 상태(_templates)를 업데이트합니다.
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Template.from_dict를 사용하여 안전하게 객체 복원
            self._templates = [Template.from_dict(item['name'], item) for item in data]

        except FileNotFoundError:
            self._templates = [] # 파일이 없으면 빈 리스트로 초기화
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            raise DataIntegrityError(f"Template file '{self.file_path}' is corrupted or in an invalid format: {e}")

    def load(self, name: str) -> Optional[Template]:
        """이름으로 특정 템플릿을 찾습니다."""
        return self.get_by_name(name)

    def get_by_name(self, name: str) -> Optional[Template]:
        """이름으로 특정 템플릿을 찾습니다. (내부용 헬퍼)"""
        return next((template for template in self._templates if template.name == name), None)

    def get_all(self) -> List[Template]:
        """저장된 모든 템플릿의 목록을 반환합니다."""
        return self._templates

    def get_all_names(self) -> List[str]:
        """
        저장된 모든 템플릿의 이름 목록을 반환합니다.
        """
        return [template.name for template in self._templates]

    def save(self, template: Template):
        """새 템플릿을 저장하거나 기존 템플릿을 업데이트합니다."""
        existing_template = self.get_by_name(template.name)
        if existing_template:
            # 기존 템플릿 정보 업데이트
            existing_template.rois = template.rois
            existing_template.original_pdf_path = template.original_pdf_path
        else:
            self._templates.append(template)
        self._save_all()

    def delete(self, name: str):
        """이름으로 특정 템플릿을 삭제합니다."""
        template_to_delete = self.get_by_name(name)
        if not template_to_delete:
            raise TemplateNotFoundError(f"템플릿을 찾을 수 없습니다: {name}")

        self._templates.remove(template_to_delete)
        self._save_all()

    def _save_all(self):
        """메모리의 모든 템플릿 데이터를 JSON 파일에 저장합니다."""
        try:
            directory = os.path.dirname(self.file_path)
            if not os.path.exists(directory):
                os.makedirs(directory)

            data = [template.to_dict() for template in self._templates]
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except IOError as e:
            raise DataPersistenceError(operation="save templates", details=str(e))

