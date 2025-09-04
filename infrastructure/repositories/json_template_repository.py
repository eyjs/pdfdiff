"""
JSON Template Repository Implementation
JSON 파일 기반 템플릿 저장소 구현
"""
import os
from typing import List, Optional, Dict
from pathlib import Path

from domain.repositories.template_repository import TemplateRepository
from domain.entities.template import Template
from shared.utils import JSONUtils, FileUtils, TimeUtils
from shared.exceptions import *
from shared.constants import DEFAULT_TEMPLATE_FILE


class JsonTemplateRepository(TemplateRepository):
    """JSON 파일 기반 템플릿 저장소"""
    
    def __init__(self, file_path: str = DEFAULT_TEMPLATE_FILE):
        self.file_path = Path(file_path)
        self._ensure_template_file()
    
    def _ensure_template_file(self) -> None:
        """템플릿 파일 존재 확인 및 초기화"""
        if not self.file_path.exists():
            FileUtils.ensure_directory(self.file_path.parent)
            JSONUtils.save_json({}, self.file_path)
    
    def _load_templates(self) -> Dict[str, Dict]:
        """템플릿 파일 로드"""
        try:
            return JSONUtils.load_json(self.file_path)
        except Exception as e:
            raise DataPersistenceError("로드", str(e))
    
    def _save_templates(self, templates: Dict[str, Dict]) -> None:
        """템플릿 파일 저장"""
        try:
            JSONUtils.save_json(templates, self.file_path)
        except Exception as e:
            raise DataPersistenceError("저장", str(e))
    
    def save(self, template: Template) -> bool:
        """템플릿 저장"""
        try:
            templates = self._load_templates()
            templates[template.name] = template.to_dict()
            self._save_templates(templates)
            return True
        except Exception as e:
            raise DataPersistenceError("템플릿 저장", str(e))
    
    def find_by_name(self, name: str) -> Optional[Template]:
        """이름으로 템플릿 조회"""
        try:
            templates = self._load_templates()
            if name in templates:
                return Template.from_dict(name, templates[name])
            return None
        except Exception as e:
            raise DataPersistenceError("템플릿 조회", str(e))
    
    def find_all(self) -> List[Template]:
        """모든 템플릿 조회"""
        try:
            templates = self._load_templates()
            return [
                Template.from_dict(name, data) 
                for name, data in templates.items()
            ]
        except Exception as e:
            raise DataPersistenceError("템플릿 목록 조회", str(e))
    
    def delete(self, name: str) -> bool:
        """템플릿 삭제"""
        try:
            templates = self._load_templates()
            if name in templates:
                del templates[name]
                self._save_templates(templates)
                return True
            return False
        except Exception as e:
            raise DataPersistenceError("템플릿 삭제", str(e))
    
    def exists(self, name: str) -> bool:
        """템플릿 존재 여부 확인"""
        try:
            templates = self._load_templates()
            return name in templates
        except Exception as e:
            raise DataPersistenceError("템플릿 존재 확인", str(e))
    
    def get_template_names(self) -> List[str]:
        """템플릿 이름 목록 조회"""
        try:
            templates = self._load_templates()
            return list(templates.keys())
        except Exception as e:
            raise DataPersistenceError("템플릿 이름 목록 조회", str(e))
    
    def backup(self, backup_path: str) -> bool:
        """템플릿 백업"""
        try:
            if not self.file_path.exists():
                return False
            
            backup_file = FileUtils.backup_file(self.file_path, backup_path)
            return backup_file.exists()
        except Exception as e:
            raise DataPersistenceError("템플릿 백업", str(e))
    
    def restore(self, backup_path: str) -> bool:
        """템플릿 복원"""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                raise DocumentNotFoundError(backup_path)
            
            # 현재 파일 백업
            if self.file_path.exists():
                FileUtils.backup_file(self.file_path)
            
            # 백업 파일로 복원
            import shutil
            shutil.copy2(backup_file, self.file_path)
            return True
        except Exception as e:
            raise DataPersistenceError("템플릿 복원", str(e))
    
    def get_file_info(self) -> Dict[str, any]:
        """템플릿 파일 정보 조회"""
        if not self.file_path.exists():
            return {}
        
        stat = self.file_path.stat()
        return {
            "file_path": str(self.file_path.absolute()),
            "file_size": stat.st_size,
            "created_at": stat.st_ctime,
            "modified_at": stat.st_mtime,
            "template_count": len(self._load_templates())
        }
