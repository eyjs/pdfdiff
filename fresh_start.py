"""
가상환경 재설정 및 배포를 위한 Python 스크립트
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def get_project_root():
    """프로젝트 루트 디렉토리 반환"""
    return Path(__file__).parent

def remove_old_environment():
    """기존 환경 정리"""
    project_root = get_project_root()
    
    directories_to_remove = [
        "venv",
        "build", 
        "dist",
        "deployment",
        "portable"
    ]
    
    print("🧹 기존 환경 정리 중...")
    
    for dir_name in directories_to_remove:
        dir_path = project_root / dir_name
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                print(f"✅ {dir_name}/ 삭제 완료")
            except Exception as e:
                print(f"⚠️ {dir_name}/ 삭제 실패: {e}")
    
    # 임시 파일들도 정리
    temp_files = list(project_root.glob("temp_*.pdf"))
    temp_files.extend(project_root.glob("*.zip"))
    temp_files.extend(project_root.glob("*.spec"))
    
    for temp_file in temp_files:
        try:
            temp_file.unlink()
            print(f"✅ {temp_file.name} 삭제 완료")
        except:
            pass

def create_virtual_environment():
    """새 가상환경 생성"""
    project_root = get_project_root()
    
    print("🔧 새 가상환경 생성 중...")
    
    try:
        # 가상환경 생성
        subprocess.run([sys.executable, "-m", "venv", "venv"], 
                      check=True, cwd=project_root)
        print("✅ 가상환경 생성 완료")
        
        # pip 업그레이드
        venv_python = project_root / "venv" / "Scripts" / "python.exe"
        subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True)
        print("✅ pip 업그레이드 완료")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 가상환경 생성 실패: {e}")
        return False

def install_dependencies():
    """의존성 설치"""
    project_root = get_project_root()
    venv_python = project_root / "venv" / "Scripts" / "python.exe"
    
    print("📦 의존성 설치 중...")
    
    try:
        # requirements.txt 설치
        subprocess.run([str(venv_python), "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, cwd=project_root)
        print("✅ requirements.txt 설치 완료")
        
        # PyInstaller 설치
        subprocess.run([str(venv_python), "-m", "pip", "install", "pyinstaller"], 
                      check=True)
        print("✅ PyInstaller 설치 완료")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 의존성 설치 실패: {e}")
        return False

def verify_environment():
    """환경 검증"""
    project_root = get_project_root()
    venv_python = project_root / "venv" / "Scripts" / "python.exe"
    
    print("🔍 환경 검증 중...")
    
    try:
        # Python 버전 확인
        result = subprocess.run([str(venv_python), "--version"], 
                               capture_output=True, text=True, check=True)
        print(f"✅ Python: {result.stdout.strip()}")
        
        # PyInstaller 확인
        result = subprocess.run([str(venv_python), "-c", "import PyInstaller; print('PyInstaller:', PyInstaller.__version__)"], 
                               capture_output=True, text=True, check=True)
        print(f"✅ {result.stdout.strip()}")
        
        # 필수 라이브러리 확인
        required_libs = ['cv2', 'PIL', 'numpy', 'fitz', 'pytesseract']
        for lib in required_libs:
            try:
                subprocess.run([str(venv_python), "-c", f"import {lib}"], 
                              check=True, capture_output=True)
                print(f"✅ {lib} 사용 가능")
            except subprocess.CalledProcessError:
                print(f"❌ {lib} 없음")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 환경 검증 실패: {e}")
        return False

def build_and_deploy():
    """빌드 및 배포"""
    project_root = get_project_root()
    venv_python = project_root / "venv" / "Scripts" / "python.exe"
    
    print("🔨 빌드 및 배포 시작...")
    
    try:
        # 1. 정리
        print("\\n1️⃣ 프로젝트 정리...")
        subprocess.run([str(venv_python), "clean_for_deployment.py"], 
                      check=True, cwd=project_root)
        
        # 2. 빌드
        print("\\n2️⃣ 실행파일 빌드...")
        subprocess.run([str(venv_python), "simple_build.py"], 
                      check=True, cwd=project_root)
        
        # 3. 패키지 생성
        print("\\n3️⃣ 배포 패키지 생성...")
        subprocess.run([str(venv_python), "create_zip_package.py"], 
                      check=True, cwd=project_root)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 빌드/배포 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("=" * 60)
    print("🔄 가상환경 완전 재설정 및 배포")
    print("=" * 60)
    
    print("⚠️  이 작업은 다음을 수행합니다:")
    print("- 기존 venv/ 폴더 완전 삭제")
    print("- build/, dist/, deployment/ 폴더 삭제") 
    print("- 새 가상환경 생성")
    print("- 모든 의존성 재설치")
    print("- 빌드 및 배포 실행")
    print()
    
    response = input("계속 진행하시겠습니까? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ 작업이 취소되었습니다.")
        return
    
    try:
        # 1. 기존 환경 정리
        print("\\n1️⃣ 기존 환경 정리...")
        remove_old_environment()
        
        # 2. 새 가상환경 생성
        print("\\n2️⃣ 새 가상환경 생성...")
        if not create_virtual_environment():
            return
        
        # 3. 의존성 설치
        print("\\n3️⃣ 의존성 설치...")
        if not install_dependencies():
            return
        
        # 4. 환경 검증
        print("\\n4️⃣ 환경 검증...")
        if not verify_environment():
            return
        
        # 5. 빌드 및 배포
        print("\\n5️⃣ 빌드 및 배포...")
        if not build_and_deploy():
            return
        
        print("\\n" + "=" * 60)
        print("🎉 완전 재설정 및 배포 완료!")
        print("=" * 60)
        print("생성된 파일들:")
        print("- dist/보험서류검증시스템.exe")
        print("- deployment/ (배포용 폴더)")
        print("- portable/ (포터블 버전)")
        print("- *.zip (최종 배포 파일)")
        
    except KeyboardInterrupt:
        print("\\n❌ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\\n❌ 예상치 못한 오류: {e}")

if __name__ == "__main__":
    main()
