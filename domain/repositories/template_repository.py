# 파일 경로: domain/repositories/template_repository.py
from abc import ABC, abstractmethod

# Domain Layer (Repository Interface)
# 역할: 데이터 저장소에 대한 '규칙' 또는 '명세'를 정의합니다.
#       어떻게(How) 저장할지는 신경쓰지 않고, 무엇을(What) 해야 하는지만 정의합니다.
#       이를 통해 Domain 계층은 특정 데이터 기술(JSON, DB)로부터 독립적일 수 있습니다.

class TemplateRepository(ABC):
    @abstractmethod
    def save(self, name: str, pdf_path: str, rois: dict):
        pass

    @abstractmethod
    def load(self, name: str) -> dict:
        pass

    @abstractmethod
    def get_all_names(self) -> list:
        pass

    @abstractmethod
    def delete(self, name: str):
        pass