"""
Document Entity
PDF 문서 정보
"""
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
from datetime import datetime


@dataclass
class Document:
    """
    PDF 문서 엔티티
    
    Attributes:
        file_path: 파일 경로
        file_name: 파일명
        file_size: 파일 크기 (bytes)
        page_count: 페이지 수
        created_at: 생성일시
        modified_at: 수정일시
    """
    file_path: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    page_count: Optional[int] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    
    def __post_init__(self):
        """파일 정보 자동 설정"""
        if not self.file_path:
            raise ValueError("파일 경로는 필수입니다")
        
        path = Path(self.file_path)
        
        # 파일명 자동 설정
        if not self.file_name:
            self.file_name = path.name
        
        # 파일 정보 자동 수집 (파일이 존재하는 경우)
        if path.exists():
            stat = path.stat()
            if not self.file_size:
                self.file_size = stat.st_size
            if not self.created_at:
                self.created_at = datetime.fromtimestamp(stat.st_ctime)
            if not self.modified_at:
                self.modified_at = datetime.fromtimestamp(stat.st_mtime)
    
    @property
    def exists(self) -> bool:
        """파일 존재 여부"""
        return Path(self.file_path).exists()
    
    @property
    def extension(self) -> str:
        """파일 확장자"""
        return Path(self.file_path).suffix.lower()
    
    @property
    def is_pdf(self) -> bool:
        """PDF 파일 여부"""
        return self.extension == '.pdf'
    
    @property
    def size_mb(self) -> float:
        """파일 크기 (MB)"""
        return self.file_size / (1024 * 1024) if self.file_size else 0.0
    
    def get_absolute_path(self) -> str:
        """절대 경로 반환"""
        return str(Path(self.file_path).absolute())
    
    def get_relative_path(self, base_path: str) -> str:
        """상대 경로 반환"""
        try:
            return str(Path(self.file_path).relative_to(base_path))
        except ValueError:
            return self.file_path
