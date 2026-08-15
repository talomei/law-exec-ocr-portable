@echo off
chcp 65001 >nul
setlocal

REM ============================================
REM  LawExec OCR v3.0 - Windows Portable Launcher
REM ============================================

set "SCRIPT_DIR=%~dp0"
set "TARGET=%SCRIPT_DIR%_platform\windows-x64\LawExec-OCR.exe"

echo.
echo ============================================
echo   ⚖️  LawExec OCR v3.0 - Portable Edition
echo ============================================
echo.

if not exist "%TARGET%" (
    echo [ERROR] 找不到程序: %TARGET%
    echo.
    echo 请确认 U 盘目录完整，特别是 _platform\windows-x64\ 子目录。
    echo 如果这是 macOS 或 Linux 的 U 盘，请改用对应平台。
    echo.
    pause
    exit /b 1
)

echo [INFO]  启动程序: %TARGET%
echo [INFO]  浏览器将自动打开 http://127.0.0.1:8501
echo [INFO]  关闭此窗口即可停止服务
echo.

REM 先打开浏览器（避免 streamlit 子进程阻塞 cmd）
start "" "http://127.0.0.1:8501"

REM 启动主程序
"%TARGET%"

REM 退出时清理
echo.
echo [INFO]  服务已停止
pause
