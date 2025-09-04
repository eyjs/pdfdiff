"""
Document Repository Interface
문서 접근 계층 인터페이스
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from pathlib import Path

from domain.entities.document import Document


class DocumentRepository(ABC):
    """문서 저장소 인터페이스"""
    
    @abstractmethod
    def load_document(self, file_path: str) -> Optional[Document]:
        """문서 로드"""
        pass
    
    @abstractmethod
    def get_page_count(self, file_path: str) -> int:
        """페이지 수 조회"""
        pass
    
    @abstractmethod
    def validate_pdf(self, file_path: str) -> bool:
        """PDF 파일 유효성 검사"""
        pass
    
    @abstractmethod
    def find_pdf_files(self, directory: str) -> List[str]:
        """디렉토리에서 PDF 파일들 찾기"""
        pass
    
    @abstractmethod
    def get_file_info(self, file_path: str) -> Optional[dict]:
        """파일 메타데이터 조회"""
        pass
