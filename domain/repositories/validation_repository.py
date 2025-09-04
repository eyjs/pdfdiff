"""
Validation Repository Interface
검증 결과 저장소 인터페이스
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from domain.entities.validation_result import ValidationResult


class ValidationRepository(ABC):
    """검증 결과 저장소 인터페이스"""
    
    @abstractmethod
    def save_result(self, result: ValidationResult) -> bool:
        """검증 결과 저장"""
        pass
    
    @abstractmethod
    def find_by_document_name(self, document_name: str) -> List[ValidationResult]:
        """문서명으로 검증 결과 조회"""
        pass
    
    @abstractmethod
    def find_by_template_name(self, template_name: str) -> List[ValidationResult]:
        """템플릿명으로 검증 결과 조회"""
        pass
    
    @abstractmethod
    def find_by_date_range(self, start_date: datetime, end_date: datetime) -> List[ValidationResult]:
        """날짜 범위로 검증 결과 조회"""
        pass
    
    @abstractmethod
    def get_recent_results(self, limit: int = 10) -> List[ValidationResult]:
        """최근 검증 결과 조회"""
        pass
    
    @abstractmethod
    def delete_old_results(self, days: int = 30) -> int:
        """오래된 결과 삭제 (반환값: 삭제된 개수)"""
        pass
    
    @abstractmethod
    def get_statistics(self) -> dict:
        """검증 통계 정보"""
        pass
