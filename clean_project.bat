@echo off
chcp 65001 > nul
title Clean Project Files

echo.
echo ========================================
echo   Clean Unnecessary Files
echo ========================================
echo.

cd /d "%~dp0"

echo Removing unnecessary batch files and scripts...

REM Delete unnecessary files
del /q build_for_windows.py 2>nul
del /q build_portable.bat 2>nul
del /q build_release.spec 2>nul
del /q check_environment.bat 2>nul
del /q clean_for_deployment.py 2>nul
del /q create_portable.py 2>nul
del /q create_zip_package.py 2>nul
del /q deploy_windows.bat 2>nul
del /q fix_environment.py 2>nul
del /q fresh_deploy.bat 2>nul
del /q fresh_start.bat 2>nul
del /q fresh_start.py 2>nul
del /q install_pyinstaller.bat 2>nul
del /q make_distribution.bat 2>nul
del /q one_click_setup.bat 2>nul
del /q quick_build.py 2>nul
del /q rebuild_environment.bat 2>nul
del /q setup_dependencies.bat 2>nul
del /q simple_build.py 2>nul
del /q simple_deploy.bat 2>nul
del /q build.spec 2>nul
del /q insurance_main.spec 2>nul
del /q pdf_validator.spec 2>nul
del /q run.spec 2>nul
del /q 보험서류검증시스템.spec 2>nul
del /q cleanup.py 2>nul
del /q cleanup_project.py 2>nul

REM Clean build directories
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "deployment" rmdir /s /q deployment
if exist "portable" rmdir /s /q portable
if exist "temp_build" rmdir /s /q temp_build

echo.
echo [SUCCESS] Project cleaned!
echo.
echo Remaining files:
echo ✅ setup_dev.bat (dev environment setup)
echo ✅ build_user_release.bat (user deployment)
echo ✅ create_release.bat (GitHub release)
echo.
echo Now you have a clean project!

REM Delete this cleanup file too
timeout /t 2 >nul
del "%~f0"
