@echo off
REM ============================================
REM  LawExec OCR - Windows 构建脚本（双击运行）
REM ============================================
REM 自动调用 PowerShell 跑 build_windows.ps1

chcp 65001 >nul
setlocal

set "SCRIPT_DIR=%~dp0"
set "PS_SCRIPT=%SCRIPT_DIR%build_windows.ps1"

if not exist "%PS_SCRIPT%" (
    echo [ERROR] 找不到 %PS_SCRIPT%
    pause
    exit /b 1
)

echo.
echo ⚖️  LawExec OCR v3.0 - Windows 构建
echo    自动调用 PowerShell 脚本...
echo.

powershell -ExecutionPolicy Bypass -File "%PS_SCRIPT%" %*

if errorlevel 1 (
    echo.
    echo [ERROR] 构建失败！查看上方错误信息
) else (
    echo.
    echo [OK] 构建完成！产物在 _platform\windows-x64\
)
pause
