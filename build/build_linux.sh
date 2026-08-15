#!/bin/bash
# ============================================
#  LawExec OCR - Linux 构建脚本
# ============================================
# 用途：在 Linux 上用 PyInstaller 打包成单目录可执行文件
# 输出：_platform/linux-x64/LawExec-OCR (约 520-580 MB)
# 用法：./build_linux.sh
# ============================================

set -e

# ---- 配置 ----
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_DIR="$ROOT_DIR/_app"
PLATFORM_DIR="$ROOT_DIR/_platform/linux-x64"
BUILD_DIR="$SCRIPT_DIR/.build_linux"
VENV_DIR="$BUILD_DIR/venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"
OUTPUT_NAME="LawExec-OCR"

echo "═══════════════════════════════════════════════════════"
echo "⚖️  LawExec OCR v3.0 - Linux 构建"
echo "═══════════════════════════════════════════════════════"
echo "📂 工程根: $ROOT_DIR"
echo "📂 应用源: $APP_DIR"
echo "📂 输出:   $PLATFORM_DIR"
echo

# ---- 1. 检查 Python ----
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "❌ 找不到 $PYTHON_BIN，请先安装 Python 3.9+"
    exit 1
fi
PY_VERSION=$("$PYTHON_BIN" --version 2>&1 | awk '{print $2}')
echo "✅ Python: $PY_VERSION"

# ---- 2. 准备构建目录 ----
mkdir -p "$BUILD_DIR"
echo "✅ 构建目录: $BUILD_DIR"

# ---- 3. 创建 venv ----
if [[ ! -d "$VENV_DIR" ]]; then
    echo "▶️  创建虚拟环境..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
echo "✅ venv: $VENV_DIR"

# ---- 4. 安装依赖 ----
echo "▶️  安装依赖..."
pip install --upgrade pip --quiet
pip install --quiet \
    rapidocr-onnxruntime \
    streamlit \
    opencv-python \
    PyMuPDF \
    Pillow \
    'numpy>=1.24,<2.0' \
    python-Levenshtein \
    pyinstaller
echo "✅ 依赖安装完成"

# ---- 5. 复制源文件到构建目录 ----
echo "▶️  准备源文件..."
cp "$APP_DIR/launcher.py" "$BUILD_DIR/"
cp "$APP_DIR/ocr_app.py" "$BUILD_DIR/"
cp "$APP_DIR/config.yaml" "$BUILD_DIR/"
mkdir -p "$BUILD_DIR/presets"
cp "$APP_DIR/presets/"*.yaml "$BUILD_DIR/presets/" 2>/dev/null || true
echo "✅ 源文件就绪"

# ---- 6. PyInstaller ----
echo "▶️  PyInstaller --onedir（首次约 60-90 秒）..."
cd "$BUILD_DIR"
pyinstaller --onedir \
    --name "$OUTPUT_NAME" \
    --collect-all rapidocr_onnxruntime \
    --collect-all streamlit \
    --add-data "ocr_app.py:." \
    --add-data "config.yaml:." \
    --add-data "presets:presets" \
    --hidden-import=streamlit.web.cli \
    --hidden-import=rapidocr_onnxruntime \
    --hidden-import=PIL.Image \
    --hidden-import=PIL.ImageEnhance \
    --hidden-import=PIL.ImageFilter \
    --hidden-import=PIL.ImageDraw \
    --hidden-import=PIL.ImageFont \
    --hidden-import=cv2 \
    --hidden-import=fitz \
    --hidden-import=numpy \
    --collect-submodules=PIL \
    --noconfirm \
    --log-level WARN \
    launcher.py

# ---- 7. 复制到 _platform/ ----
echo "▶️  部署到 _platform/linux-x64/..."
rm -rf "$PLATFORM_DIR"
mkdir -p "$PLATFORM_DIR"
cp -r "$BUILD_DIR/dist/$OUTPUT_NAME/"* "$PLATFORM_DIR/"
chmod +x "$PLATFORM_DIR/$OUTPUT_NAME"

# ---- 8. 输出统计 ----
SIZE=$(du -sh "$PLATFORM_DIR" | awk '{print $1}')
echo
echo "═══════════════════════════════════════════════════════"
echo "✅ 构建完成！"
echo "═══════════════════════════════════════════════════════"
echo "📂 产物: $PLATFORM_DIR"
echo "💾 大小: $SIZE"
echo "🚀 启动: $PLATFORM_DIR/$OUTPUT_NAME"
echo
echo "本地测试："
echo "  $PLATFORM_DIR/$OUTPUT_NAME"
echo "  浏览器打开 http://127.0.0.1:8501"
echo
