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
from PIL import Image, ImageDraw, ImageFont

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
            raise RuntimeError("EasyOCR 리더가 초기화되지 않았습니다. 모델 파일이 올바른지 확인하세요.")

        if config is None:
            config = {}

        try:
            start_time = time.time()
            processed_image = image.copy()

            # --- 1. 이미지 전처리 파이프라인 ---
            profile = config.get('preprocessing_profile', 'default_korean')

            if profile == 'default_korean':
                # 1-1. 업스케일링 (작은 텍스트용)
                min_height = config.get('upscale_min_height', 50)
                if processed_image.shape[0] < min_height:
                    scale_factor = config.get('upscale_factor', 2.0)
                    processed_image = cv2.resize(
                        processed_image,
                        (int(processed_image.shape[1] * scale_factor), int(processed_image.shape[0] * scale_factor)),
                        interpolation=cv2.INTER_LANCZOS4
                    )
                    logging.debug(f"이미지 업스케일링됨 (x{scale_factor})")

                # 1-2. 고급 노이즈 제거
                if config.get('denoising_enabled', True):
                    denoise_strength = config.get('denoise_strength', 10)
                    processed_image = cv2.fastNlMeansDenoising(processed_image, None, h=denoise_strength)
                    logging.debug(f"노이즈 제거됨 (강도: {denoise_strength})")

                # 1-3. 대비 향상 (CLAHE)
                if config.get('clahe_enabled', True):
                    clip_limit = config.get('clahe_clip_limit', 2.0)
                    tile_size = tuple(config.get('clahe_tile_size', [8, 8]))
                    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_size)
                    processed_image = clahe.apply(processed_image)
                    logging.debug(f"CLAHE 적용됨 (clip: {clip_limit}, tile: {tile_size})")

            # --- 2. EasyOCR 실행 (동적 파라미터 적용) ---
            ocr_params = {
                'width_ths': config.get('width_ths', 0.3),
                'height_ths': config.get('height_ths', 0.3),
                'y_ths': config.get('y_ths', 0.3),  # 기본값 0.5로 복원
                'detail': 1,
                'paragraph': False,
                'batch_size': 1,
                'decoder': config.get('decoder', 'beamsearch'),
                'beamWidth': config.get('beamWidth', 5),
                'text_threshold': config.get('text_threshold', 0.7),
                'low_text': config.get('low_text', 0.3)
            }
            logging.debug(f"EasyOCR 파라미터: {ocr_params}")

            results = self.reader.readtext(processed_image, **ocr_params)

            # --- DEBUG IMAGE SAVING (with Bounding Boxes) ---
            if config.get('debug_save_image', True):
                try:
                    output_dir = "output/debug"
                    os.makedirs(output_dir, exist_ok=True)
                    debug_image_color = cv2.cvtColor(processed_image, cv2.COLOR_GRAY2BGR)

                    # 1. OpenCV로 바운딩 박스 그리기
                    for (bbox, text, confidence) in results:
                        if confidence > config.get('confidence_threshold', 0.3):
                            pts = np.array(bbox, dtype=np.int32)
                            cv2.polylines(debug_image_color, [pts], isClosed=True, color=(0, 255, 0), thickness=1)

                    # 2. Pillow(PIL)를 사용하여 한글 텍스트 그리기
                    pil_img = Image.fromarray(cv2.cvtColor(debug_image_color, cv2.COLOR_BGR2RGB))
                    draw = ImageDraw.Draw(pil_img)
                    try:
                        # Windows 환경에서는 '맑은 고딕' 사용
                        font = ImageFont.truetype("malgun.ttf", 15)
                    except IOError:
                        # 폰트가 없을 경우 기본 폰트 사용
                        font = ImageFont.load_default()

                    for (bbox, text, confidence) in results:
                        if confidence > config.get('confidence_threshold', 0.3):
                            pts = np.array(bbox, dtype=np.int32)
                            text_pos = (pts[0][0], pts[0][1] - 20)
                            draw.text(text_pos, text, font=font, fill=(255, 0, 0, 255))

                    # 3. 다시 OpenCV 이미지로 변환하여 저장
                    debug_image_color = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

                    field_name = config.get('field_name', 'unknown_field')
                    filename = f"{field_name}_easyocr_output.png"
                    filepath = os.path.join(output_dir, filename)
                    cv2.imwrite(filepath, debug_image_color)

                    # 생성된 디버그 이미지 경로를 임시 파일에 저장
                    with open(os.path.join(output_dir, "last_ocr_debug_image.txt"), "w") as f:
                        f.write(os.path.abspath(filepath))
                except Exception as e:
                    logging.warning(f"Failed to save EasyOCR debug image for field {config.get('field_name', 'unknown')}: {e}")
            # --- END DEBUG ---

            # --- 3. 결과 처리 및 정리 ---
            extracted_texts = []
            confidence_scores = []

            for (bbox, text, confidence) in results:
                if confidence > config.get('confidence_threshold', 0.3):
                    cleaned_text = self._clean_and_validate_text(text)
                    if cleaned_text.strip():
                        extracted_texts.append(cleaned_text)
                        confidence_scores.append(confidence)
                        logging.debug(f"EasyOCR: '{text}' -> '{cleaned_text}' (신뢰도: {confidence:.2f})")

            if extracted_texts:
                final_text = ' '.join(extracted_texts)
                avg_confidence = sum(confidence_scores) / len(confidence_scores)
                processing_time = time.time() - start_time
                logging.info(f"EasyOCR 완료: '{final_text}' (평균 신뢰도: {avg_confidence:.2f}, 처리시간: {processing_time:.2f}초)")
                return final_text
            else:
                logging.warning("EasyOCR: 신뢰할 만한 텍스트를 찾지 못했습니다.")
                return ""

        except Exception as e:
            logging.error(f"EasyOCR 인식 중 오류 발생: {e}", exc_info=True)
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