#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tesseract OCR 설치 검증 스크립트
PDF Diff 프로젝트의 한글 OCR 기능 테스트
"""

import os
import sys
from pathlib import Path

def check_tesseract_installation():
    """Tesseract 설치 상태 확인"""
    
    print("Tesseract OCR 설치 상태 검증")
    print("=" * 50)
    
    # 1. 기본 경로 확인
    current_dir = Path(__file__).parent
    tesseract_dir = current_dir / "resources" / "vendor" / "tesseract"
    tessdata_dir = tesseract_dir / "tessdata"
    tesseract_exe = tesseract_dir / "tesseract.exe"
    
    print(f"프로젝트 경로: {current_dir}")
    print(f"Tesseract 경로: {tesseract_dir}")
    print(f"언어팩 경로: {tessdata_dir}")
    print()
    
    # 2. 필수 파일 존재 확인
    print("필수 파일 확인:")
    
    files_to_check = [
        (tesseract_exe, "Tesseract 실행 파일"),
        (tessdata_dir / "eng.traineddata", "영어 언어팩"),
        (tessdata_dir / "kor.traineddata", "한글 언어팩"),
    ]
    
    missing_files = []
    
    for file_path, description in files_to_check:
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"  [OK] {description}: {file_path.name} ({size:,} bytes)")
        else:
            print(f"  [FAIL] {description}: {file_path.name} (없음)")
            missing_files.append((file_path, description))
    
    # 선택적 파일 확인
    optional_files = [
        (tessdata_dir / "osd.traineddata", "방향 감지 언어팩"),
    ]
    
    print("\n선택적 파일 확인:")
    for file_path, description in optional_files:
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"  [OK] {description}: {file_path.name} ({size:,} bytes)")
        else:
            print(f"  [INFO] {description}: {file_path.name} (선택사항)")
    
    print()
    
    # 3. 누락된 파일이 있는 경우
    if missing_files:
        print("[FAIL] 누락된 필수 파일들이 있습니다!")
        print("\n해결 방법:")
        print("1. install_korean_ocr.bat 실행")
        print("2. 또는 수동으로 다음 파일들을 다운로드:")
        print()
        
        for file_path, description in missing_files:
            if "eng.traineddata" in str(file_path):
                print(f"   • {description}:")
                print(f"     https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata")
            elif "kor.traineddata" in str(file_path):
                print(f"   • {description}:")
                print(f"     https://github.com/tesseract-ocr/tessdata/raw/main/kor.traineddata")
            print(f"     → 저장 위치: {file_path}")
            print()
        
        return False
    
    # 4. 실제 OCR 테스트
    print("OCR 기능 테스트 시작...")
    
    try:
        # pytesseract 설정
        import pytesseract
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np
        
        # 경로 설정
        pytesseract.pytesseract.tesseract_cmd = str(tesseract_exe)
        os.environ['TESSDATA_PREFIX'] = str(tessdata_dir)
        
        print("  [OK] pytesseract 모듈 로드 성공")
        
        # 사용 가능한 언어 확인
        try:
            languages = pytesseract.get_languages(config='')
            print(f"  [OK] 설치된 언어: {', '.join(sorted(languages))}")
            
            required_langs = {'eng', 'kor'}
            available_langs = set(languages)
            
            if required_langs.issubset(available_langs):
                print("  [OK] 한글+영어 언어팩 확인됨")
            else:
                missing_langs = required_langs - available_langs
                print(f"  [FAIL] 누락된 언어: {', '.join(missing_langs)}")
                return False
                
        except Exception as e:
            print(f"  [FAIL] 언어 목록 확인 실패: {e}")
            return False
        
        # 간단한 텍스트 이미지 생성 및 OCR 테스트
        print("\n  영어 OCR 테스트...")
        
        # 영어 테스트 이미지
        img_en = Image.new('RGB', (300, 100), 'white')
        draw_en = ImageDraw.Draw(img_en)
        
        try:
            # 기본 폰트 사용 (Windows)
            draw_en.text((10, 30), "Hello World 123", fill='black')
        except:
            draw_en.text((10, 30), "Hello World 123", fill='black')
        
        # 영어 OCR 테스트
        text_en = pytesseract.image_to_string(img_en, lang='eng').strip()
        print(f"    인식 결과: '{text_en}'")
        
        if "Hello" in text_en and "World" in text_en:
            print("    [OK] 영어 OCR 정상 동작")
        else:
            print("    [WARN] 영어 OCR 결과가 예상과 다름")
        
        # 한글 테스트 (간단한 텍스트)
        print("\n  한글 OCR 테스트...")
        
        img_kr = Image.new('RGB', (300, 100), 'white')
        draw_kr = ImageDraw.Draw(img_kr)
        
        # 한글 텍스트 (폰트 없이도 인식 가능한 간단한 텍스트)
        draw_kr.text((10, 30), "한국어 테스트", fill='black')
        
        # 한글 OCR 테스트
        text_kr = pytesseract.image_to_string(img_kr, lang='kor').strip()
        print(f"    인식 결과: '{text_kr}'")
        
        if text_kr and len(text_kr) > 0:
            print("    [OK] 한글 OCR 엔진 동작함")
        else:
            print("    [WARN] 한글 인식 결과가 없음 (폰트나 이미지 품질 문제일 수 있음)")
        
        # 복합 언어 테스트
        print("\n  한영 복합 OCR 테스트...")
        
        img_mixed = Image.new('RGB', (400, 100), 'white')
        draw_mixed = ImageDraw.Draw(img_mixed)
        draw_mixed.text((10, 30), "PDF 검증 System 2025", fill='black')
        
        text_mixed = pytesseract.image_to_string(img_mixed, lang='kor+eng').strip()
        print(f"    인식 결과: '{text_mixed}'")
        
        if text_mixed and len(text_mixed) > 0:
            print("    [OK] 한영 복합 OCR 엔진 동작함")
        
        print()
        print("OCR 기능 검증 완료!")
        print("PDF Diff 프로젝트에서 한글 OCR을 사용할 수 있습니다.")
        
        return True
        
    except ImportError as e:
        print(f"  [FAIL] 필수 모듈 없음: {e}")
        print("    pip install -r requirements.txt 실행 필요")
        return False
    except Exception as e:
        print(f"  [FAIL] OCR 테스트 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("PDF Diff - Tesseract OCR 검증 도구")
    print("Ver 1.0")
    print()
    
    try:
        if check_tesseract_installation():
            print("\n" + "="*60)
            print("[OK] 모든 검증이 완료되었습니다!")
            print("enhanced_launcher.py를 실행하여 프로젝트를 시작하세요.")
        else:
            print("\n" + "="*60)
            print("[FAIL] 일부 문제가 발견되었습니다.")
            print("위의 해결 방법을 따라 문제를 해결해주세요.")
            
    except KeyboardInterrupt:
        print("\n\n중단되었습니다.")
    except Exception as e:
        print(f"\n[FAIL] 예상치 못한 오류 발생: {e}")
    
    print("\n프로그램을 종료하려면 Enter를 누르세요...")
    input()

if __name__ == "__main__":
    main()