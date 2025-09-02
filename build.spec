# -*- mode: python ; coding: utf-8 -*-

# PyInstaller build configuration file

block_cipher = None

a = Analysis(
    ['enhanced_launcher.py'],  # <-- 프로그램을 시작하는 메인 파이썬 파일
    pathex=[],
    binaries=[],
    datas=[
        ('src', 'src'),
        ('templates.json', '.'),
        ('vendor/tesseract', 'tesseract')  # <-- Tesseract 엔진을 통째로 포함
    ],
    hiddenimports=[
        'pytesseract',
        'skimage.metrics',
        'cv2',
        'fitz',
        'PIL'
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PDF_Validator_App',  # <-- 생성될 .exe 파일의 이름
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI 애플리케이션이므로 콘솔창(검은창)을 숨깁니다.
    icon=None,
)

# 최종적으로 모든 파일을 모으는 단계
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='release_build', # <-- 최종 결과물이 담길 폴더 이름
)