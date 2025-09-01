
# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리
project_root = Path(SPECPATH)

block_cipher = None

# 메인 애플리케이션 분석
main_a = Analysis(
    ['run.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        ('src/*.py', 'src'),
        ('templates.json', '.'),
        ('README.md', '.'),
        ('requirements.txt', '.'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'PIL._tkinter_finder',
        'cv2',
        'numpy',
        'fitz',
        'pytesseract',
        'skimage',
        'skimage.metrics',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy.spatial.cKDTree',
        'scipy.sparse.csgraph._validation',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ROI 선택 도구 분석
roi_a = Analysis(
    ['src/roi_selector.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk', 
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.simpledialog',
        'PIL._tkinter_finder',
        'cv2',
        'numpy',
        'fitz',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# PDF 검증 도구 분석
validator_a = Analysis(
    ['src/pdf_validator_gui.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog', 
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'PIL._tkinter_finder',
        'cv2',
        'numpy',
        'fitz',
        'pytesseract',
        'skimage',
        'skimage.metrics',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 실행 파일 생성
main_pyz = PYZ(main_a.pure, main_a.zipped_data, cipher=block_cipher)
main_exe = EXE(
    main_pyz,
    main_a.scripts,
    main_a.binaries,
    main_a.zipfiles,
    main_a.datas,
    [],
    name='PDF_Validator_System',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI 애플리케이션이므로 콘솔 숨김
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
    version='version_info.txt' if os.path.exists('version_info.txt') else None,
)

roi_pyz = PYZ(roi_a.pure, roi_a.zipped_data, cipher=block_cipher)  
roi_exe = EXE(
    roi_pyz,
    roi_a.scripts,
    roi_a.binaries,
    roi_a.zipfiles,
    roi_a.datas,
    [],
    name='ROI_Selector',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
)

validator_pyz = PYZ(validator_a.pure, validator_a.zipped_data, cipher=block_cipher)
validator_exe = EXE(
    validator_pyz,
    validator_a.scripts, 
    validator_a.binaries,
    validator_a.zipfiles,
    validator_a.datas,
    [],
    name='PDF_Validator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
)
