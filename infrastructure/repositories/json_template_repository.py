# 파일 경로: infrastructure/repositories/json_template_repository.py
import json
import os
from domain.repositories.template_repository import TemplateRepository

# Infrastructure Layer (Repository Implementation)
# 역할: Domain 계층에 정의된 Repository Interface를 실제로 구현합니다.
#       - 이 파일은 'JSON 파일'이라는 특정 기술을 사용하여 데이터를 저장하고 불러옵니다.
#       - 만약 DB로 변경된다면 이 파일만 수정하면 됩니다.

class JsonTemplateRepository(TemplateRepository):
    def __init__(self, file_path='templates.json'):
        self.file_path = file_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump({}, f)

    def _load_all(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_all(self, templates):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)

    def save(self, name, pdf_path, rois):
        templates = self._load_all()
        templates[name] = {
            'original_pdf_path': pdf_path,
            'rois': rois
        }
        self._save_all(templates)

    def load(self, name):
        templates = self._load_all()
        if name not in templates:
            raise KeyError(f"Template '{name}' not found.")
        return templates[name]

    def get_all_names(self):
        templates = self._load_all()
        return list(templates.keys())

    def delete(self, name):
        templates = self._load_all()
        if name in templates:
            del templates[name]
            self._save_all(templates)