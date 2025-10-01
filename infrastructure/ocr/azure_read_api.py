import asyncio
import aiohttp
import cv2
import numpy as np
import logging
import time
import re
from typing import Dict, Optional, Any
from io import BytesIO
from PIL import Image

from domain.services.ocr_service import OcrService


class AzureOcrService(OcrService):
    """Azure Computer Vision Read API를 사용한 OCR 서비스 구현체"""

    def __init__(self, endpoint: str, api_key: str, timeout: int = 120):
        """
        Azure OCR 서비스 초기화

        Args:
            endpoint: Azure Computer Vision 엔드포인트 URL
            api_key: Azure API 구독 키
            timeout: OCR 처리 타임아웃 (초)
        """
        self.endpoint = endpoint.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.api_version = "2023-02-01-preview"  # 최신 API 버전

        # Read API 엔드포인트 구성
        self.read_url = f"{self.endpoint}/computervision/imageanalysis:analyze"

        logging.info(f"Azure OCR 서비스 초기화 완료: {self.endpoint}")

    def recognize_text(self, image: np.ndarray, config: dict = None) -> str:
        """
        동기 방식으로 텍스트 인식 (내부에서 비동기 처리)

        Args:
            image: 입력 이미지 (numpy 배열, 그레이스케일 또는 컬러)
            config: 추가 설정 옵션
                - language: 언어 코드 (예: 'ko', 'en', 'ko,en')
                - preprocess: 전처리 적용 여부 (기본값: True)
                - confidence_threshold: 최소 신뢰도 임계값 (기본값: 0.0)

        Returns:
            인식된 텍스트 문자열
        """
        if config is None:
            config = {}

        try:
            # 비동기 함수를 동기 방식으로 실행
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self._recognize_text_async(image, config))
                return result
            finally:
                loop.close()

        except Exception as e:
            logging.error(f"Azure OCR 처리 중 오류 발생: {e}")
            return ""

    async def _recognize_text_async(self, image: np.ndarray, config: dict) -> str:
        """비동기 방식으로 텍스트 인식"""

        # 1. 이미지 전처리
        processed_image = self._preprocess_image(image, config)

        # 2. 이미지를 바이트 배열로 변환
        image_bytes = self._numpy_to_bytes(processed_image)

        # 3. Azure API 호출
        extracted_text = await self._call_azure_read_api(image_bytes, config)

        # 4. 결과 정리 및 반환
        cleaned_text = self._clean_text(extracted_text)

        logging.info(f"Azure OCR 결과: '{cleaned_text}'")
        return cleaned_text

    def _preprocess_image(self, image: np.ndarray, config: dict) -> np.ndarray:
        """
        Azure OCR에 최적화된 이미지 전처리
        """
        if not config.get('preprocess', True):
            return image

        processed = image.copy()

        # 그레이스케일 변환 (컬러 이미지인 경우)
        if len(processed.shape) == 3:
            processed = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)

        # 이미지 크기 최적화 (Azure는 큰 이미지를 선호)
        h, w = processed.shape

        # 너무 작은 이미지는 확대
        if min(h, w) < 500:
            scale_factor = 500 / min(h, w)
            new_w = int(w * scale_factor)
            new_h = int(h * scale_factor)
            processed = cv2.resize(processed, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
            logging.info(f"이미지 크기 조정: {w}x{h} -> {new_w}x{new_h}")

        # 너무 큰 이미지는 축소 (Azure 제한: 10000x10000)
        elif max(h, w) > 8000:
            scale_factor = 8000 / max(h, w)
            new_w = int(w * scale_factor)
            new_h = int(h * scale_factor)
            processed = cv2.resize(processed, (new_w, new_h), interpolation=cv2.INTER_AREA)
            logging.info(f"이미지 크기 축소: {w}x{h} -> {new_w}x{new_h}")

        # 대비 향상 (선택적)
        if config.get('enhance_contrast', True):
            processed = cv2.convertScaleAbs(processed, alpha=1.1, beta=10)

        # 노이즈 감소 (매우 약하게)
        processed = cv2.bilateralFilter(processed, 9, 75, 75)

        return processed

    def _numpy_to_bytes(self, image: np.ndarray) -> bytes:
        """numpy 배열을 바이트 배열로 변환"""
        try:
            # PIL Image로 변환
            if len(image.shape) == 2:  # 그레이스케일
                pil_image = Image.fromarray(image, mode='L')
            else:  # 컬러
                pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

            # PNG 형식으로 메모리에 저장
            buffer = BytesIO()
            pil_image.save(buffer, format='PNG', optimize=True)
            return buffer.getvalue()

        except Exception as e:
            logging.error(f"이미지 바이트 변환 실패: {e}")
            raise

    async def _call_azure_read_api(self, image_bytes: bytes, config: dict) -> str:
        """Azure Read API 호출 및 결과 폴링"""

        headers = {
            'Ocp-Apim-Subscription-Key': self.api_key,
            'Content-Type': 'application/octet-stream'
        }

        # 요청 파라미터 구성
        params = {
            'features': 'read',
            'api-version': self.api_version
        }

        # 언어 설정
        language = config.get('language', 'ko')
        if language:
            params['language'] = language

        timeout = aiohttp.ClientTimeout(total=self.timeout)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # 1. 분석 요청 전송
                async with session.post(
                    self.read_url,
                    headers=headers,
                    params=params,
                    data=image_bytes
                ) as response:

                    if response.status == 202:
                        # 비동기 처리 - 결과 URL 획득
                        operation_location = response.headers.get('Operation-Location')
                        if not operation_location:
                            # 동기 처리 - 즉시 결과 반환
                            result_data = await response.json()
                            return self._parse_read_result(result_data, config)
                    elif response.status == 200:
                        # 즉시 결과 반환 (동기 처리)
                        result_data = await response.json()
                        return self._parse_read_result(result_data, config)
                    else:
                        error_msg = await response.text()
                        raise Exception(f"Azure API 오류 ({response.status}): {error_msg}")

                # 2. 비동기 결과 폴링 (Operation-Location이 있는 경우)
                if operation_location:
                    return await self._poll_operation_result(session, operation_location, config)

        except asyncio.TimeoutError:
            raise Exception(f"Azure OCR 요청 시간 초과 ({self.timeout}초)")
        except Exception as e:
            logging.error(f"Azure API 호출 실패: {e}")
            raise

    async def _poll_operation_result(self, session: aiohttp.ClientSession, operation_url: str, config: dict) -> str:
        """비동기 작업 결과 폴링"""

        headers = {
            'Ocp-Apim-Subscription-Key': self.api_key
        }

        start_time = time.time()
        poll_interval = 1  # 1초 간격으로 시작
        max_poll_interval = 5  # 최대 5초 간격

        while time.time() - start_time < self.timeout:
            try:
                async with session.get(operation_url, headers=headers) as response:
                    if response.status != 200:
                        error_msg = await response.text()
                        raise Exception(f"결과 폴링 실패 ({response.status}): {error_msg}")

                    result_data = await response.json()
                    status = result_data.get('status', '').lower()

                    if status == 'succeeded':
                        return self._parse_read_result(result_data, config)
                    elif status == 'failed':
                        error = result_data.get('error', {})
                        error_msg = error.get('message', '알 수 없는 오류')
                        raise Exception(f"Azure OCR 처리 실패: {error_msg}")
                    elif status in ['running', 'notstarted']:
                        # 대기 후 재시도
                        await asyncio.sleep(poll_interval)
                        # 점진적으로 폴링 간격 증가
                        poll_interval = min(poll_interval * 1.2, max_poll_interval)
                    else:
                        raise Exception(f"알 수 없는 상태: {status}")

            except Exception as e:
                if "Azure OCR 처리 실패" in str(e) or "알 수 없는 상태" in str(e):
                    raise
                logging.warning(f"폴링 중 일시적 오류: {e}")
                await asyncio.sleep(poll_interval)

        raise Exception(f"OCR 처리 시간 초과 ({self.timeout}초)")

    def _parse_read_result(self, result_data: dict, config: dict) -> str:
        """
        Azure Read API 결과 파싱
        """

        try:
            # 최신 API 응답 구조 처리
            if 'readResult' in result_data:
                read_results = result_data['readResult']
            elif 'analyzeResult' in result_data and 'readResults' in result_data['analyzeResult']:
                read_results = result_data['analyzeResult']['readResults']
            else:
                logging.warning("예상되지 않은 응답 구조")
                return ""

            extracted_lines = []
            confidence_threshold = config.get('confidence_threshold', 0.0)

            # 페이지별 텍스트 추출
            for page in read_results:
                if 'lines' not in page:
                    continue

                for line in page['lines']:
                    text = line.get('text', '').strip()
                    if not text:
                        continue

                    # 신뢰도 확인 (있는 경우)
                    if 'confidence' in line:
                        confidence = line['confidence']
                        if confidence < confidence_threshold:
                            logging.debug(f"낮은 신뢰도로 제외: {text} (신뢰도: {confidence:.2f})")
                            continue

                    extracted_lines.append(text)

            # 텍스트 결합
            full_text = ' '.join(extracted_lines)

            logging.info(f"추출된 라인 수: {len(extracted_lines)}")
            return full_text

        except Exception as e:
            logging.error(f"결과 파싱 중 오류: {e}")
            logging.debug(f"응답 데이터: {result_data}")
            return ""

    def _clean_text(self, raw_text: str) -> str:
        """
        OCR 결과 텍스트 정리 (Tesseract와 유사한 방식)
        """
        if not raw_text or not raw_text.strip():
            return ""

        text = raw_text.strip()

        # 불필요한 특수문자 제거 (한국어, 영어, 숫자, 기본 구두점 유지)
        text = re.sub(r'[^\w\s가-힣()/\-.,%A-Za-z0-9]', ' ', text)

        # 연속된 공백을 하나로 통합
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def get_service_info(self) -> Dict[str, Any]:
        """서비스 정보 반환"""
        return {
            'service_name': 'Azure Computer Vision Read API',
            'endpoint': self.endpoint,
            'api_version': self.api_version,
            'timeout': self.timeout,
            'features': ['한국어', '영어', '다국어', '손글씨', '인쇄체', '비동기처리']
        }