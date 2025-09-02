"""
간단한 PyInstaller 빌드 스크립트
가상환경 문제 우회용
"""

import os
import sys
import subprocess
from pathlib import Path

def simple_build():
    """간단한 빌드 실행"""
    project_root = Path(__file__).parent
    
    print("🔨 간단한 빌드 시작...")
    print(f"📁 작업 디렉토리: {project_root}")
    
    # 가상환경 Python 직접 사용
    venv_python = project_root / "venv" / "Scripts" / "python.exe"
    
    if venv_python.exists():
        python_exe = str(venv_python)
        print(f"✅ 가상환경 Python 사용: {python_exe}")
    else:
        python_exe = sys.executable
        print(f"⚠️ 시스템 Python 사용: {python_exe}")
    
    try:
        # 단순한 PyInstaller 명령
        cmd = [
            python_exe, "-m", "PyInstaller",
            "--onefile",
            "--windowed",
            "--name", "보험서류검증시스템",
            "--distpath", "dist",
            "--workpath", "build",
            "--add-data", "templates;templates",
            "--add-data", "src;src",
            "enhanced_launcher.py"
        ]
        
        print("실행 명령어:")
        print(" ".join(cmd))
        print()
        
        # 실행
        result = subprocess.run(cmd, cwd=project_root)
        
        if result.returncode == 0:
            exe_file = project_root / "dist" / "보험서류검증시스템.exe"
            if exe_file.exists():
                file_size = exe_file.stat().st_size / (1024 * 1024)
                print(f"✅ 빌드 성공!")
                print(f"📁 실행파일: {exe_file}")
                print(f"📊 크기: {file_size:.1f} MB")
                return True
        
        print("❌ 빌드 실패")
        return False
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

if __name__ == "__main__":
    if simple_build():
        print("\n🎉 빌드 완료! 이제 'python create_zip_package.py'를 실행하세요.")
    else:
        print("\n❌ 빌드 실패. 오류를 확인하고 다시 시도하세요.")
