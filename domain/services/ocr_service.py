from abc import ABC, abstractmethod
import numpy as np

class OcrService(ABC):
    """OCR 서비스에 대한 인터페이스"""

    @abstractmethod
    def recognize_text(self, image: np.ndarray, config: dict = None) -> str:
        """
        주어진 이미지에서 텍스트를 인식합니다.

        Args:
            image: 텍스트를 포함하는 이미지 (numpy 배열).
            config (dict, optional): OCR 엔진에 전달할 추가 설정. Defaults to None.

        Returns:
            인식된 텍스트 문자열.
        """
        pass
