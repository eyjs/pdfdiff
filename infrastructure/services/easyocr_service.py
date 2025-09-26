import easyocr
import numpy as np
import cv2
import logging
import time
import os
import sys
import re
from pathlib import Path
from typing import List, Tuple, Optional

from domain.services.ocr_service import OcrService
from shared.settings import settings

class EasyOCRService(OcrService):
    """내장형 EasyOCR 서비스 - 모델 파일이 번들링된 버전"""

    def __init__(self):
        """내장 EasyOCR 모델을 사용한 초기화"""
        self.reader = None
        self.models_path = None
        self._setup_bundled_models()
        self._initialize_reader()

    def _setup_bundled_models(self):
        """번들링된 모델 경로 설정"""
        try:
            # settings에서 모델 경로를 가져옵니다.
            self.models_path = Path(settings.easyocr.model_storage_directory)

            logging.info(f"EasyOCR 번들 모델 경로: {self.models_path}")

            # 필수 모델 파일 확인
            required_models = ["korean_g2.pth", "english_g2.pth", "craft_mlt_25k.pth"]
            missing_models = []

            for model_file in required_models:
                model_path = self.models_path / model_file
                if not model_path.exists():
                    missing_models.append(model_file)
                else:
                    logging.info(f"✓ 번들 모델 확인: {model_file}")

            if missing_models:
                raise FileNotFoundError(f"필수 EasyOCR 모델 파일 누락: {missing_models}")

        except Exception as e:
            logging.error(f"EasyOCR 번들 모델 설정 실패: {e}")
            raise

        def _initialize_reader(self):
            """내장 모델을 사용한 EasyOCR 리더를 초기화합니다."""
            logging.info("내장 EasyOCR 모델 로딩 중...")
            logging.info(f"EasyOCR가 사용할 모델 경로: {self.models_path}")
    
            # PyInstaller 환경에서 가장 안정적인 초기화 방법입니다.
            # model_storage_directory와 user_network_directory를 동일한 경로로 지정하여
            # 라이브러리가 다른 곳(예: C:\Users\USER\.EasyOCR)을 참조하는 것을 방지합니다.
            self.reader = easyocr.Reader(
                lang_list=['ko', 'en'], 
                gpu=settings.ocr_engine_selection.easyocr_gpu_enabled,
                model_storage_directory=settings.easyocr.model_storage_directory,
                user_network_directory=settings.easyocr.model_storage_directory,
                download_enabled=False,
                verbose=True  # 라이브러리에서 더 자세한 로그를 출력하도록 설정
            )
            
            logging.info("EasyOCR 초기화 완료.")
    def recognize_text(self, image: np.ndarray, config: dict = None) -> str:
        """내장 EasyOCR을 사용한 텍스트 인식"""

        if self.reader is None:
            # __init__에서 예외가 발생했을 경우
            raise RuntimeError("EasyOCR 리더가 초기화되지 않았습니다. 모델 파일이 올바른지 확인하세요.")

        if config is None:
            config = {}

        try:
            start_time = time.time()

            # EasyOCR 실행 (한글 최적화 파라미터)
            results = self.reader.readtext(
                image,
                width_ths=0.7,
                height_ths=0.7,
                detail=1,
                paragraph=False,
                batch_size=1,
                # 한글 처리 개선을 위한 추가 파라미터
                decoder='beamsearch',  # 빔서치 디코딩 (정확도 향상)
                beamWidth=5,           # 빔 너비
                text_threshold=0.7,    # 텍스트 감지 임계값
                low_text=0.4           # 낮은 신뢰도 텍스트 임계값
            )

            # 결과 처리 및 정리
            extracted_texts = []
            confidence_scores = []

            for detection in results:
                bbox, text, confidence = detection

                # 신뢰도 필터링 (번들 모델에서는 더 관대하게)
                if confidence > 0.3:  # 30% 이상
                    cleaned_text = self._clean_and_validate_text(text)
                    if cleaned_text.strip():
                        extracted_texts.append(cleaned_text)
                        confidence_scores.append(confidence)

                        logging.debug(f"EasyOCR(번들): '{text}' -> '{cleaned_text}' (신뢰도: {confidence:.2f})")

            # 최종 결과 조합
            if extracted_texts:
                final_text = ' '.join(extracted_texts)
                avg_confidence = sum(confidence_scores) / len(confidence_scores)

                processing_time = time.time() - start_time
                logging.info(f"내장 EasyOCR 완료: '{final_text}' (평균 신뢰도: {avg_confidence:.2f}, 처리시간: {processing_time:.2f}초)")

                return final_text
            else:
                logging.warning("내장 EasyOCR: 신뢰할 만한 텍스트 없음")
                return ""

        except Exception as e:
            logging.error(f"내장 EasyOCR 인식 중 오류: {e}")
            return ""

    def _clean_and_validate_text(self, text: str) -> str:
        """EasyOCR 결과 텍스트를 범용적으로 정리합니다."""

        if not text or not text.strip():
            return ""

        # 기본 정리
        text = text.strip()

        # 의미있는 문자를 제외한 나머지를 공백으로 치환
        # 허용: 한글, 영문, 숫자, 공백, 그리고 일반적인 구두점 ( ) / - . , %
        text = re.sub(r'[^\w\s가-힣()/\-.,%A-Za-z0-9]', ' ', text)

        # 연속 공백을 단일 공백으로 변경
        text = re.sub(r'\s+', ' ', text).strip()

        return text