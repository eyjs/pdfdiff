# 손글씨 OCR 강화 함수를 pdf_validator_gui.py에 추가할 코드

def _enhanced_handwriting_ocr(self, image):
    """손글씨 특화 OCR: 다양한 전처리 + 다중 시도"""
    import cv2
    import numpy as np
    import pytesseract
    import re
    
    results = []
    
    # 1. 기본 OCR (기존 방식)
    try:
        raw_text = pytesseract.image_to_string(image, lang='kor+eng')
        clean_text = re.sub(r'[\s\W_]+', '', raw_text)
        results.append({
            'method': '기본',
            'raw_text': raw_text,
            'clean_text': clean_text
        })
    except Exception as e:
        results.append({'method': '기본', 'raw_text': '', 'clean_text': '', 'error': str(e)})
    
    # 2. 손글씨용 전처리 1: 대비 강화 + 이진화
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
        
        # 대비 강화
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(4,4))
        enhanced = clahe.apply(gray)
        
        # 적응적 이진화
        binary = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        # 모폴로지 연산으로 노이즈 제거
        kernel = np.ones((2,2), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        raw_text = pytesseract.image_to_string(cleaned, lang='kor+eng')
        clean_text = re.sub(r'[\s\W_]+', '', raw_text)
        results.append({
            'method': '대비강화',
            'raw_text': raw_text,
            'clean_text': clean_text
        })
    except Exception as e:
        results.append({'method': '대비강화', 'raw_text': '', 'clean_text': '', 'error': str(e)})
    
    # 3. 손글씨용 전처리 2: 팽창팽 + 고해상도 변환
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
        
        # 4배 확대
        height, width = gray.shape
        upscaled = cv2.resize(gray, (width*4, height*4), interpolation=cv2.INTER_CUBIC)
        
        # 가우시안 블러로 노이즈 제거
        blurred = cv2.GaussianBlur(upscaled, (5, 5), 0)
        
        # 오츠 이진화
        _, otsu_binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 닫힌 모폴로지
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        final = cv2.morphologyEx(otsu_binary, cv2.MORPH_CLOSE, kernel)
        
        raw_text = pytesseract.image_to_string(final, lang='kor+eng')
        clean_text = re.sub(r'[\s\W_]+', '', raw_text)
        results.append({
            'method': '고해상도',
            'raw_text': raw_text,
            'clean_text': clean_text
        })
    except Exception as e:
        results.append({'method': '고해상도', 'raw_text': '', 'clean_text': '', 'error': str(e)})
    
    # 4. PSM 6 모드 (단일 균일 텍스트 블록)
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789가-힣ㄱ-ㅣㅏ-ㅣABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        raw_text = pytesseract.image_to_string(gray, lang='kor+eng', config=custom_config)
        clean_text = re.sub(r'[\s\W_]+', '', raw_text)
        results.append({
            'method': 'PSM6+문자제한',
            'raw_text': raw_text,
            'clean_text': clean_text
        })
    except Exception as e:
        results.append({'method': 'PSM6+문자제한', 'raw_text': '', 'clean_text': '', 'error': str(e)})
    
    # 5. PSM 8 모드 (단일 단어) + 고배율
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
        
        # 5배 확대
        height, width = gray.shape
        mega_upscaled = cv2.resize(gray, (width*5, height*5), interpolation=cv2.INTER_LANCZOS4)
        
        custom_config = r'--oem 3 --psm 8'
        raw_text = pytesseract.image_to_string(mega_upscaled, lang='kor+eng', config=custom_config)
        clean_text = re.sub(r'[\s\W_]+', '', raw_text)
        results.append({
            'method': 'PSM8+5배확대',
            'raw_text': raw_text,
            'clean_text': clean_text
        })
    except Exception as e:
        results.append({'method': 'PSM8+5배확대', 'raw_text': '', 'clean_text': '', 'error': str(e)})
    
    # 결과 로깅
    print(f"[손글씨 OCR] {len(results)}개 방법 시도 결과:")
    for r in results:
        char_count = len(r['clean_text'])
        error_msg = f" (오류: {r.get('error', '')})" if 'error' in r else ""
        print(f"   {r['method']}: {char_count}자{error_msg}")
    
    return results
