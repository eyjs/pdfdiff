import pytesseract
import re
import os
import sys
from pathlib import Path
import numpy as np
import logging

from domain.services.ocr_service import OcrService
from shared.utils import get_base_path

class TesseractOcrService(OcrService):
    """Tesseract를 사용한 OCR 서비스 구현체"""

    def __init__(self):
        """
        Tesseract 경로를 설정하고 초기화합니다.
        """
        try:
            base_path = get_base_path()
            tesseract_exe = base_path / "resources" / "vendor" / "tesseract" / "tesseract.exe"
            tessdata_dir = base_path / "resources" / "vendor" / "tesseract" / "tessdata"

            if tesseract_exe.exists():
                pytesseract.pytesseract.tesseract_cmd = str(tesseract_exe)
                os.environ['TESSDATA_PREFIX'] = str(tessdata_dir)
                logging.info(f"Tesseract 경로 설정 완료 (TesseractOcrService): {tesseract_exe}")
            else:
                logging.warning(f"지정된 경로에 Tesseract가 없습니다: {tesseract_exe}. 시스템 PATH에서 찾기를 시도합니다.")
        except Exception as e:
            logging.error(f"Tesseract 경로 설정 중 오류 발생 (TesseractOcrService): {e}")

    def recognize_text(self, image: np.ndarray, config: dict = None) -> str:
        """
        Tesseract를 사용하여 주어진 이미지에서 텍스트를 인식합니다.
        config 딕셔너리를 통해 언어, whitelist 등을 설정할 수 있습니다.
        """
        if config is None:
            config = {}

        # 설정에서 언어와 whitelist를 가져옵니다. 기본값은 'kor'.
        lang = config.get('lang', 'kor')
        whitelist = config.get('whitelist')

        # Tesseract는 흰 배경에 검은 글씨를 더 잘 인식하므로, 색상 반전
        inverted_image = np.invert(image)

        # Tesseract 설정 문자열을 구성합니다.
        psm = config.get('psm', '7') # 페이지 세분화 모드
        oem = config.get('oem', '3') # OCR 엔진 모드
        config_str = f'--psm {psm} --oem {oem}'
        if whitelist:
            config_str += f" -c tessedit_char_whitelist={whitelist}"

        raw_text = pytesseract.image_to_string(inverted_image, lang=lang, config=config_str)
        
        # 인식된 텍스트에서 공백, 특수문자 등을 제거합니다.
        clean_text = re.sub(r'[\s\W_]+', '', raw_text)
        
        return clean_text
