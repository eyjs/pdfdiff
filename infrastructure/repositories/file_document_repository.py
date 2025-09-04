"""
File Document Repository Implementation
파일 시스템 기반 문서 저장소 구현
"""
import os
from typing import List, Optional, Dict
from pathlib import Path

from domain.repositories.document_repository import DocumentRepository
from domain.entities.document import Document
from shared.utils import FileUtils
from shared.exceptions import *
from shared.constants import *


class FileDocumentRepository(DocumentRepository):
    """파일 시스템 기반 문서 저장소"""
    
    def __init__(self):
        pass
    
    def load_document(self, file_path: str) -> Optional[Document]:
        """문서 로드"""
        try:
            if not os.path.exists(file_path):
                return None
            
            document = Document(file_path=file_path)
            
            # PDF 파일인 경우 페이지 수 계산
            if document.is_pdf:
                try:
                    document.page_count = self.get_page_count(file_path)
                except Exception:
                    document.page_count = 0
            
            return document
        except Exception as e:
            raise DocumentException(f"문서 로드 실패: {str(e)}")
    
    def get_page_count(self, file_path: str) -> int:
        """페이지 수 조회"""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            page_count = doc.page_count
            doc.close()
            return page_count
        except Exception as e:
            raise PDFServiceError(f"페이지 수 조회 실패: {str(e)}")
    
    def validate_pdf(self, file_path: str) -> bool:
        """PDF 파일 유효성 검사"""
        try:
            # 기본 파일 존재 및 확장자 확인
            if not os.path.exists(file_path):
                return False
            
            if not FileUtils.is_pdf_file(file_path):
                return False
            
            # 파일 크기 확인
            if FileUtils.get_file_size_mb(file_path) > MAX_PDF_SIZE_MB:
                return False
            
            # PyMuPDF로 PDF 구조 검증
            import fitz
            try:
                doc = fitz.open(file_path)
                page_count = doc.page_count
                doc.close()
                return page_count > 0
            except Exception:
                return False
                
        except Exception:
            return False
    
    def find_pdf_files(self, directory: str) -> List[str]:
        """디렉토리에서 PDF 파일들 찾기"""
        try:
            pdf_files = []
            directory_path = Path(directory)
            
            if not directory_path.exists():
                return pdf_files
            
            for file_path in directory_path.rglob("*.pdf"):
                if file_path.is_file():
                    pdf_files.append(str(file_path))
            
            return sorted(pdf_files)
        except Exception as e:
            raise DocumentException(f"PDF 파일 검색 실패: {str(e)}")
    
    def get_file_info(self, file_path: str) -> Optional[Dict]:
        """파일 메타데이터 조회"""
        try:
            path = Path(file_path)
            if not path.exists():
                return None
            
            stat = path.stat()
            info = {
                "file_name": path.name,
                "file_size": stat.st_size,
                "file_size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created_at": stat.st_ctime,
                "modified_at": stat.st_mtime,
                "extension": path.suffix.lower(),
                "is_pdf": path.suffix.lower() == PDF_EXTENSION
            }
            
            # PDF 전용 정보
            if info["is_pdf"]:
                try:
                    info["page_count"] = self.get_page_count(file_path)
                    info["is_valid_pdf"] = self.validate_pdf(file_path)
                except Exception:
                    info["page_count"] = 0
                    info["is_valid_pdf"] = False
            
            return info
        except Exception as e:
            raise DocumentException(f"파일 정보 조회 실패: {str(e)}")
    
    def get_directory_stats(self, directory: str) -> Dict:
        """디렉토리 통계 정보"""
        try:
            directory_path = Path(directory)
            if not directory_path.exists():
                return {
                    "total_files": 0,
                    "pdf_files": 0,
                    "total_size_mb": 0.0,
                    "valid_pdfs": 0,
                    "invalid_pdfs": 0
                }
            
            total_files = 0
            pdf_files = 0
            total_size = 0
            valid_pdfs = 0
            invalid_pdfs = 0
            
            for file_path in directory_path.rglob("*"):
                if file_path.is_file():
                    total_files += 1
                    file_size = file_path.stat().st_size
                    total_size += file_size
                    
                    if file_path.suffix.lower() == PDF_EXTENSION:
                        pdf_files += 1
                        if self.validate_pdf(str(file_path)):
                            valid_pdfs += 1
                        else:
                            invalid_pdfs += 1
            
            return {
                "total_files": total_files,
                "pdf_files": pdf_files,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "valid_pdfs": valid_pdfs,
                "invalid_pdfs": invalid_pdfs
            }
        except Exception as e:
            raise DocumentException(f"디렉토리 통계 조회 실패: {str(e)}")
    
    def move_document(self, source_path: str, target_path: str) -> bool:
        """문서 이동"""
        try:
            source = Path(source_path)
            target = Path(target_path)
            
            if not source.exists():
                raise DocumentNotFoundError(source_path)
            
            # 대상 디렉토리 생성
            FileUtils.ensure_directory(target.parent)
            
            # 파일 이동
            import shutil
            shutil.move(str(source), str(target))
            return target.exists()
        except Exception as e:
            raise DocumentException(f"문서 이동 실패: {str(e)}")
    
    def copy_document(self, source_path: str, target_path: str) -> bool:
        """문서 복사"""
        try:
            source = Path(source_path)
            target = Path(target_path)
            
            if not source.exists():
                raise DocumentNotFoundError(source_path)
            
            # 대상 디렉토리 생성
            FileUtils.ensure_directory(target.parent)
            
            # 파일 복사
            import shutil
            shutil.copy2(str(source), str(target))
            return target.exists()
        except Exception as e:
            raise DocumentException(f"문서 복사 실패: {str(e)}")
