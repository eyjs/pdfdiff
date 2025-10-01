import requests
import uuid
import time
import json
import numpy as np
import cv2
import logging

from domain.services.ocr_service import OcrService
from shared.settings import settings

class ClovaOcrService(OcrService):
    """Naver Clova OCR API를 사용한 OCR 서비스 구현체"""

    def __init__(self):
        """Clova OCR 서비스 초기화 시, 설정 파일에서 API URL과 키를 로드합니다."""
        self.api_url = settings.clova.api_url
        self.secret_key = settings.clova.secret_key
        logging.info(f"Clova OCR 서비스 초기화 완료: {self.api_url}")

    def recognize_text(self, image: np.ndarray, config: dict = None) -> str:
        """
        이미지를 받아 Clova OCR API로 전송하고, 인식된 텍스트를 반환합니다.

        Args:
            image: 텍스트를 포함하는 이미지 (numpy 배열).
            config (dict, optional): 추가 설정 (현재 사용되지 않음).

        Returns:
            인식된 텍스트 문자열.
        """
        if not self.api_url or "YOUR_API_URL" in self.api_url:
            logging.error("Clova API URL이 설정되지 않았습니다. settings.json 파일을 확인해주세요.")
            return ""
        if not self.secret_key or "YOUR_SECRET_KEY" in self.secret_key:
            logging.error("Clova API Secret Key가 설정되지 않았습니다. settings.json 파일을 확인해주세요.")
            return ""

        start_time = time.time()

        # 1. Numpy 이미지를 JPG 바이트로 변환
        is_success, im_buf_arr = cv2.imencode(".jpg", image)
        if not is_success:
            logging.error("이미지를 JPG 형식으로 인코딩하는 데 실패했습니다.")
            return ""
        byte_im = im_buf_arr.tobytes()

        # 2. Clova API에 맞는 요청 데이터 생성
        request_json = {
            'images': [
                {
                    'format': 'jpg',
                    'name': 'image_from_pdf'
                }
            ],
            'requestId': str(uuid.uuid4()),
            'version': 'V2',
            'timestamp': int(round(time.time() * 1000))
        }

        payload = {'message': json.dumps(request_json).encode('UTF-8')}
        files = [('file', byte_im)]
        headers = {'X-OCR-SECRET': self.secret_key}

        try:
            # 3. API 요청
            response = requests.request("POST", self.api_url, headers=headers, data=payload, files=files, timeout=30)
            response.raise_for_status()  # 200이 아닌 상태 코드에 대해 예외 발생

            # 4. 결과 파싱
            result = response.json()
            extracted_texts = []
            for field in result['images'][0]['fields']:
                text = field.get('inferText', '')
                if field.get('inferConfidence', 0) > 0.8:
                    extracted_texts.append(text)
                else:
                    logging.warning(f"Clova OCR: 낮은 신뢰도로 제외 - '{text}' (신뢰도: {field.get('inferConfidence')})")

            final_text = ' '.join(extracted_texts)
            processing_time = time.time() - start_time
            logging.info(f"Clova OCR 완료: '{final_text}' (처리시간: {processing_time:.2f}초)")
            return final_text

        except requests.exceptions.RequestException as e:
            logging.error(f"Clova OCR API 요청 실패: {e}")
            return ""
        except (KeyError, IndexError) as e:
            logging.error(f"Clova OCR 응답 파싱 실패: {e}. 응답: {response.text}")
            return ""