"""
Template Repository Interface
템플릿 데이터 접근 계층 인터페이스
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict

from domain.entities.template import Template


class TemplateRepository(ABC):
    """템플릿 저장소 인터페이스"""
    
    @abstractmethod
    def save(self, template: Template) -> bool:
        """템플릿 저장"""
        pass
    
    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Template]:
        """이름으로 템플릿 조회"""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Template]:
        """모든 템플릿 조회"""
        pass
    
    @abstractmethod
    def delete(self, name: str) -> bool:
        """템플릿 삭제"""
        pass
    
    @abstractmethod
    def exists(self, name: str) -> bool:
        """템플릿 존재 여부 확인"""
        pass
    
    @abstractmethod
    def get_template_names(self) -> List[str]:
        """템플릿 이름 목록 조회"""
        pass
    
    @abstractmethod
    def backup(self, backup_path: str) -> bool:
        """템플릿 백업"""
        pass
    
    @abstractmethod
    def restore(self, backup_path: str) -> bool:
        """템플릿 복원"""
        pass
