#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tesseract 한글 OCR 자동 설정 스크립트
PDF Diff 프로젝트용 언어팩 다운로드 및 설치
"""

import os
import sys
import urllib.request
import shutil
from pathlib import Path

def download_with_progress(url, filename):
    """진행률 표시하며 파일 다운로드"""
    def progress_hook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(100, (downloaded * 100) // total_size)
            print(f"\r다운로드 중... {filename}: {percent}% [{downloaded:,}/{total_size:,} bytes]", end='')
        else:
            print(f"\r다운로드 중... {filename}: {downloaded:,} bytes", end='')
    
    try:
        urllib.request.urlretrieve(url, filename, progress_hook)
        print(f"\n✅ {filename} 다운로드 완료")
        return True
    except Exception as e:
        print(f"\n❌ {filename} 다운로드 실패: {e}")
        return False

def setup_tesseract_languages():
    """Tesseract 언어팩 설정"""
    
    print("🚀 Tesseract 한글 OCR 설정을 시작합니다...\n")
    
    # 현재 스크립트 경로 확인
    current_dir = Path(__file__).parent
    tessdata_dir = current_dir / "vendor" / "tesseract" / "tessdata"
    
    print(f"📁 설치 경로: {tessdata_dir}")
    
    # tessdata 폴더 확인
    if not tessdata_dir.exists():
        print(f"❌ tessdata 폴더를 찾을 수 없습니다: {tessdata_dir}")
        print("   vendor/tesseract/tessdata 폴더가 존재하는지 확인하세요.")
        return False
    
    # 다운로드할 언어팩 정보
    language_packs = {
        "eng.traineddata": {
            "url": "https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata",
            "name": "영어 언어팩",
            "required": True
        },
        "kor.traineddata": {
            "url": "https://github.com/tesseract-ocr/tessdata/raw/main/kor.traineddata", 
            "name": "한글 언어팩",
            "required": True
        },
        "osd.traineddata": {
            "url": "https://github.com/tesseract-ocr/tessdata/raw/main/osd.traineddata",
            "name": "방향 감지 언어팩",
            "required": False
        }
    }
    
    print(f"📥 총 {len(language_packs)}개 언어팩을 다운로드합니다...\n")
    
    success_count = 0
    
    for filename, info in language_packs.items():
        file_path = tessdata_dir / filename
        
        # 이미 파일이 있는지 확인
        if file_path.exists():
            file_size = file_path.stat().st_size
            if file_size > 1000:  # 1KB 이상이면 유효한 파일로 간주
                print(f"⏭️  {info['name']} ({filename})은 이미 존재합니다. (크기: {file_size:,} bytes)")
                success_count += 1
                continue
        
        print(f"🔽 {info['name']} 다운로드 중...")
        
        if download_with_progress(info['url'], str(file_path)):
            # 다운로드된 파일 크기 확인
            if file_path.exists():
                file_size = file_path.stat().st_size
                print(f"   파일 크기: {file_size:,} bytes")
                
                if file_size < 1000:  # 1KB 미만이면 다운로드 실패로 간주
                    print(f"❌ {filename} 파일이 너무 작습니다. 다운로드 실패 가능성이 있습니다.")
                    if info['required']:
                        return False
                else:
                    success_count += 1
            else:
                print(f"❌ {filename} 파일이 생성되지 않았습니다.")
                if info['required']:
                    return False
        else:
            if info['required']:
                return False
        
        print()  # 빈 줄 추가
    
    # 설치 완료 확인
    print("="*60)
    print(f"✅ 언어팩 설치 완료! ({success_count}/{len(language_packs)})")
    
    # 설치된 파일들 확인
    print("\n📋 설치된 언어팩 목록:")
    for filename in ["eng.traineddata", "kor.traineddata", "osd.traineddata"]:
        file_path = tessdata_dir / filename
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"  ✅ {filename:<20} ({size:,} bytes)")
        else:
            print(f"  ❌ {filename:<20} (없음)")
    
    print("\n🎉 설정 완료!")
    print("이제 PDF Diff 프로젝트에서 한글 OCR을 사용할 수 있습니다.")
    
    return True

def verify_installation():
    """설치 확인 테스트"""
    print("\n🔍 설치 확인 테스트를 실행합니다...")
    
    try:
        # 현재 경로에서 tesseract 실행 테스트
        current_dir = Path(__file__).parent
        tesseract_exe = current_dir / "vendor" / "tesseract" / "tesseract.exe"
        
        if not tesseract_exe.exists():
            print(f"❌ tesseract.exe를 찾을 수 없습니다: {tesseract_exe}")
            return False
        
        # pytesseract 설정 테스트
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = str(tesseract_exe)
            
            # tessdata 경로 설정
            tessdata_dir = current_dir / "vendor" / "tesseract" / "tessdata"
            os.environ['TESSDATA_PREFIX'] = str(tessdata_dir)
            
            # 간단한 OCR 테스트
            from PIL import Image
            import numpy as np
            
            # 간단한 테스트 이미지 생성 (흰 배경에 검은 텍스트)
            test_image = Image.new('RGB', (200, 100), 'white')
            
            # 언어팩 확인
            try:
                # 한글+영어 언어팩 테스트
                result = pytesseract.get_languages(config='')
                print(f"✅ 사용 가능한 언어: {', '.join(result)}")
                
                if 'kor' in result and 'eng' in result:
                    print("✅ 한글+영어 OCR 준비 완료!")
                    return True
                else:
                    print("❌ 한글 또는 영어 언어팩이 인식되지 않습니다.")
                    return False
                    
            except Exception as e:
                print(f"❌ 언어팩 확인 실패: {e}")
                return False
                
        except ImportError:
            print("⚠️ pytesseract가 설치되지 않았습니다. requirements.txt를 확인하세요.")
            return False
            
    except Exception as e:
        print(f"❌ 설치 확인 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("🔧 Tesseract 한글 OCR 자동 설정 스크립트")
    print("=" * 60)
    
    # 관리자 권한 확인 (선택사항)
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            print("⚠️ 관리자 권한이 없습니다. 일부 작업이 실패할 수 있습니다.")
    except:
        pass
    
    # 인터넷 연결 확인
    try:
        urllib.request.urlopen('https://www.google.com', timeout=5)
        print("✅ 인터넷 연결 확인됨\n")
    except:
        print("❌ 인터넷 연결을 확인하세요. 언어팩 다운로드를 위해 인터넷이 필요합니다.")
        return False
    
    # 언어팩 설치
    if setup_tesseract_languages():
        # 설치 확인 테스트
        if verify_installation():
            print("\n" + "="*60)
            print("🎉 모든 설정이 완료되었습니다!")
            print("이제 enhanced_launcher.py를 실행하여 한글 OCR을 사용해보세요.")
        else:
            print("\n⚠️ 설치는 완료되었지만 확인 테스트에서 문제가 발생했습니다.")
            print("수동으로 프로그램을 실행해보시기 바랍니다.")
    else:
        print("\n❌ 언어팩 설치에 실패했습니다.")
        print("수동 설치 방법을 시도해보세요.")
        return False
    
    print("\n프로그램을 종료하려면 Enter를 누르세요...")
    input()
    return True

if __name__ == "__main__":
    main()
