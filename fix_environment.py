"""
PyInstaller 설치 및 환경 확인 스크립트
"""

import subprocess
import sys
import os
from pathlib import Path

def install_pyinstaller():
    """PyInstaller 설치"""
    print("🔧 PyInstaller 설치 중...")
    
    try:
        # pip 업그레이드
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        
        # PyInstaller 설치
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], 
                      check=True, capture_output=True)
        
        print("✅ PyInstaller 설치 완료")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 설치 실패: {e}")
        
        # 대안 방법 시도
        print("🔄 대안 방법으로 재시도...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "--user", "pyinstaller"], 
                          check=True, capture_output=True)
            print("✅ PyInstaller 설치 완료 (--user 옵션)")
            return True
        except subprocess.CalledProcessError as e2:
            print(f"❌ 대안 방법도 실패: {e2}")
            return False

def verify_installation():
    """설치 확인"""
    print("🔍 설치 확인 중...")
    
    try:
        import PyInstaller
        print(f"✅ PyInstaller 버전: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("❌ PyInstaller 가져오기 실패")
        return False

def check_environment():
    """환경 확인"""
    print("🔍 환경 확인 중...")
    
    # Python 버전 확인
    print(f"Python 버전: {sys.version}")
    
    # 가상환경 확인
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ 가상환경에서 실행 중")
    else:
        print("⚠️ 시스템 Python 사용 중")
    
    # 필수 라이브러리 확인
    required_libs = ['cv2', 'PIL', 'numpy', 'fitz', 'pytesseract', 'skimage']
    missing_libs = []
    
    for lib in required_libs:
        try:
            __import__(lib)
            print(f"✅ {lib} 사용 가능")
        except ImportError:
            missing_libs.append(lib)
            print(f"❌ {lib} 없음")
    
    if missing_libs:
        print(f"\n⚠️ 누락된 라이브러리: {', '.join(missing_libs)}")
        print("다음 명령어로 설치하세요:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def main():
    """메인 함수"""
    print("=" * 60)
    print("🔧 PyInstaller 설치 및 환경 확인")
    print("=" * 60)
    
    # 환경 확인
    if not check_environment():
        print("\n❌ 환경 설정이 완료되지 않았습니다.")
        return
    
    # PyInstaller 확인 및 설치
    if not verify_installation():
        print("\n📦 PyInstaller를 설치합니다...")
        if not install_pyinstaller():
            print("\n❌ PyInstaller 설치에 실패했습니다.")
            print("수동으로 설치해보세요:")
            print("pip install pyinstaller")
            return
        
        # 재확인
        if not verify_installation():
            print("❌ 설치 후에도 PyInstaller를 가져올 수 없습니다.")
            return
    
    print("\n" + "=" * 60)
    print("🎉 환경 설정 완료!")
    print("=" * 60)
    print("이제 다음 명령어를 실행할 수 있습니다:")
    print("- python build_for_windows.py")
    print("- deploy_windows.bat")

if __name__ == "__main__":
    main()
