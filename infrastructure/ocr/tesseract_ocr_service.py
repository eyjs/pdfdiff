import pytesseract
import re
import os
import sys
from pathlib import Path
import numpy as np
import logging
import cv2

from domain.services.ocr_service import OcrService
from shared.utils import get_bundle_path

class TesseractOcrService(OcrService):
    """Tesseract를 사용한 OCR 서비스 구현체"""

    def __init__(self):
        """Tesseract 경로를 설정하고 초기화합니다."""
        try:
            bundle_path = get_bundle_path()

            tesseract_exe = bundle_path / "resources" / "vendor" / "tesseract" / "tesseract.exe"
            tessdata_dir = bundle_path / "resources" / "vendor" / "tesseract" / "tessdata"

            if tesseract_exe.exists():
                pytesseract.pytesseract.tesseract_cmd = str(tesseract_exe)
                os.environ['TESSDATA_PREFIX'] = str(tessdata_dir)
            else:
                logging.warning(f"Tesseract를 찾을 수 없습니다: {tesseract_exe}. 시스템 PATH에서 찾기를 시도합니다.")
        except Exception as e:
            logging.error(f"Tesseract 경로 설정 중 오류 발생: {e}")

    def recognize_text(self, image: np.ndarray, config: dict = None) -> str:
        """회색조 이미지를 입력받아 Tesseract에 최적화된 전처리를 수행하고 텍스트를 인식합니다."""
        if config is None:
            config = {}

        h, w = image.shape
        if h < 50:
            scale_factor = 100 / h
            image = cv2.resize(image, (int(w * scale_factor), int(h * scale_factor)), interpolation=cv2.INTER_CUBIC)

        processed_image = cv2.GaussianBlur(image, (3, 3), 0)
        processed_image = cv2.adaptiveThreshold(
            processed_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 21, 5
        )
        kernel = np.ones((1, 1), np.uint8)
        processed_image = cv2.morphologyEx(processed_image, cv2.MORPH_OPEN, kernel)

        strategies = [
            {'lang': 'kor+eng', 'psm': '6', 'name': '한영혼합_블록'},
            {'lang': 'kor', 'psm': '7', 'name': '한글_텍스트라인'},
        ]

        best_result = ""
        best_confidence = 0

        for strategy in strategies:
            try:
                result = self._ocr_with_strategy(processed_image, strategy, config)
                confidence = self._calculate_text_confidence(result)
                if confidence > best_confidence and len(result.strip()) > 0:
                    best_result = result
                    best_confidence = confidence
                if confidence > 0.9:
                    break
            except Exception as e:
                logging.warning(f"OCR 전략 '{strategy['name']}' 실패: {e}")
                continue

        if not best_result.strip():
            try:
                best_result = self._fallback_ocr(processed_image, config)
            except Exception as e:
                logging.error(f"기본 OCR도 실패: {e}")
                best_result = ""

        logging.info(f"최종 OCR 결과: '{best_result}' (신뢰도: {best_confidence:.2f})")
        return best_result

    def _ocr_with_strategy(self, image: np.ndarray, strategy: dict, user_config: dict) -> str:
        """특정 전략으로 OCR 수행"""
        lang = strategy['lang']
        psm = strategy['psm']
        oem = user_config.get('oem', '3')
        config_str = f'--psm {psm} --oem {oem}'
        if 'kor' in lang:
            config_str += ' -c preserve_interword_spaces=1'
        whitelist = user_config.get('whitelist')
        if whitelist:
            config_str += f" -c tessedit_char_whitelist={whitelist}"
        raw_text = pytesseract.image_to_string(image, lang=lang, config=config_str)
        return self._clean_text(raw_text)

    def _clean_text(self, raw_text: str) -> str:
        """OCR 결과 텍스트를 범용적으로 정리합니다."""
        if not raw_text or not raw_text.strip():
            return ""
        text = raw_text.strip()
        text = re.sub(r'[^\w\s가-힣()/\-.,%A-Za-z0-9]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _calculate_text_confidence(self, text: str) -> float:
        """텍스트의 일반적인 품질을 기반으로 신뢰도를 계산합니다."""
        if not text or not text.strip():
            return 0.0
        confidence = 0.0
        length = len(text)
        if 3 <= length <= 50:
            confidence += 0.4
        elif length < 3:
            confidence += (length / 3.0) * 0.4
        else:
            confidence += (50.0 / length) * 0.4
        korean_chars = len(re.findall(r'[가-힣]', text))
        if korean_chars > 0:
            confidence += (korean_chars / length) * 0.4
        if re.search(r'\d', text):
            confidence += 0.2
        non_word_chars = len(re.findall(r'[^\w\s가-힣.,-/]', text))
        if length > 0:
            confidence -= (non_word_chars / length) * 0.5
        return max(0.0, min(1.0, confidence))

    def _fallback_ocr(self, image: np.ndarray, config: dict) -> str:
        """모든 전략 실패 시 기본 OCR"""
        lang = config.get('lang', 'kor')
        psm = config.get('psm', '3')
        oem = config.get('oem', '3')
        whitelist = config.get('whitelist')
        config_str = f'--psm {psm} --oem {oem}'
        if whitelist:
            config_str += f" -c tessedit_char_whitelist={whitelist}"
        raw_text = pytesseract.image_to_string(image, lang=lang, config=config_str)
        return re.sub(r'[\s\W_]+', '', raw_text)