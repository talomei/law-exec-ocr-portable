# ============================================
#  LawExec OCR - Windows 构建脚本
# ============================================
# 用途：在 Windows 11 上用 PyInstaller 打包
# 输出：_platform\windows-x64\LawExec-OCR.exe (约 520-580 MB)
# 用法：powershell -ExecutionPolicy Bypass -File build_windows.ps1
# 备选：双击 build_windows.bat（自动调用本脚本）
# ============================================

# PowerShell 默认输出编码是 GBK/Windows-1252，会导致 emoji 乱码
# 强制设为 UTF-8（PowerShell 5.1+）
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

$ErrorActionPreference = "Stop"

# ---- 配置 ----
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
$AppDir = Join-Path $RootDir "_app"
$PlatformDir = Join-Path $RootDir "_platform\windows-x64"
$BuildDir = Join-Path $ScriptDir ".build_windows"
$VenvDir = Join-Path $BuildDir "venv"
$PythonBin = $env:PYTHON_BIN
if (-not $PythonBin) { $PythonBin = "python" }
$OutputName = "LawExec-OCR"

Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "⚖️  LawExec OCR v3.0 - Windows 构建" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "📂 工程根: $RootDir"
Write-Host "📂 应用源: $AppDir"
Write-Host "📂 输出:   $PlatformDir"
Write-Host ""

# ---- 1. 检查 Python ----
try {
    $pyVersion = & $PythonBin --version 2>&1
    Write-Host "✅ Python: $pyVersion"
} catch {
    Write-Host "❌ 找不到 $PythonBin，请先安装 Python 3.9+（勾选 Add to PATH）" -ForegroundColor Red
    exit 1
}

# ---- 2. 准备构建目录 ----
New-Item -ItemType Directory -Force -Path $BuildDir | Out-Null

# ---- 3. 创建 venv ----
if (-not (Test-Path $VenvDir)) {
    Write-Host "▶️  创建虚拟环境..."
    & $PythonBin -m venv $VenvDir
}
$activateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
. $activateScript
Write-Host "✅ venv: $VenvDir"

# ---- 4. 安装依赖 ----
Write-Host "▶️  安装依赖..."
python -m pip install --upgrade pip --quiet
python -m pip install --quiet `
    rapidocr-onnxruntime `
    streamlit `
    opencv-python `
    PyMuPDF `
    Pillow `
    'numpy>=1.24,<2.0' `
    python-Levenshtein `
    pyinstaller
Write-Host "✅ 依赖安装完成"

# ---- 5. 复制源文件 ----
Write-Host "▶️  准备源文件..."
Copy-Item -Path (Join-Path $AppDir "launcher.py") -Destination $BuildDir
Copy-Item -Path (Join-Path $AppDir "ocr_app.py") -Destination $BuildDir
Copy-Item -Path (Join-Path $AppDir "config.yaml") -Destination $BuildDir
New-Item -ItemType Directory -Force -Path (Join-Path $BuildDir "presets") | Out-Null
Get-ChildItem (Join-Path $AppDir "presets") -Filter "*.yaml" | ForEach-Object {
    Copy-Item $_.FullName (Join-Path $BuildDir "presets")
}

# ---- 6. PyInstaller ----
Write-Host "▶️  PyInstaller --onedir（首次约 60-120 秒）..."
Push-Location $BuildDir
pyinstaller --onedir `
    --name $OutputName `
    --collect-all rapidocr_onnxruntime `
    --collect-all streamlit `
    --add-data "ocr_app.py;." `
    --add-data "config.yaml;." `
    --add-data "presets;presets" `
    --hidden-import=streamlit.web.cli `
    --hidden-import=rapidocr_onnxruntime `
    --hidden-import=PIL.Image `
    --hidden-import=PIL.ImageEnhance `
    --hidden-import=PIL.ImageFilter `
    --hidden-import=PIL.ImageDraw `
    --hidden-import=PIL.ImageFont `
    --hidden-import=cv2 `
    --hidden-import=fitz `
    --hidden-import=numpy `
    --collect-submodules=PIL `
    --noconfirm `
    --log-level WARN `
    launcher.py
Pop-Location

# ---- 7. 部署到 _platform/ ----
Write-Host "▶️  部署到 $PlatformDir ..."
if (Test-Path $PlatformDir) { Remove-Item $PlatformDir -Recurse -Force }
New-Item -ItemType Directory -Force -Path $PlatformDir | Out-Null
Copy-Item -Path (Join-Path $BuildDir "dist\$OutputName\*") -Destination $PlatformDir -Recurse -Force

# ---- 8. 统计 ----
$size = (Get-ChildItem $PlatformDir -Recurse | Measure-Object Length -Sum).Sum / 1MB
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "✅ 构建完成！" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "📂 产物: $PlatformDir"
Write-Host "💾 大小: $([math]::Round($size, 0)) MB"
Write-Host ""
Write-Host "⚠️  Windows 首次运行："
Write-Host "   1. 双击 start.bat"
Write-Host "   2. SmartScreen 提示 → 更多信息 → 仍要运行"
Write-Host "   3. 等待 5-10 秒（首次含 Defender 扫描）"
Write-Host ""
