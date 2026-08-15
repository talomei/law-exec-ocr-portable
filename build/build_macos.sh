#!/bin/bash
# ============================================
#  LawExec OCR - macOS 构建脚本
# ============================================
# 用途：在 macOS 上用 PyInstaller 打包
# 输出：_platform/macos-arm64/ 或 macos-x64/ (约 520-580 MB)
# 用法：./build_macos.sh [arm64|x64]
#      默认 arm64（M1+ Mac）
# ============================================

set -e

# ---- 参数 ----
TARGET_ARCH="${1:-arm64}"
if [[ "$TARGET_ARCH" != "arm64" && "$TARGET_ARCH" != "x64" ]]; then
    echo "❌ 架构参数错误：$TARGET_ARCH（仅支持 arm64 或 x64）"
    exit 1
fi

# ---- 路径 ----
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_DIR="$ROOT_DIR/_app"
PLATFORM_DIR="$ROOT_DIR/_platform/macos-$TARGET_ARCH"
BUILD_DIR="$SCRIPT_DIR/.build_macos_$TARGET_ARCH"
VENV_DIR="$BUILD_DIR/venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"
OUTPUT_NAME="LawExec-OCR"

echo "═══════════════════════════════════════════════════════"
echo "⚖️  LawExec OCR v3.0 - macOS 构建"
echo "═══════════════════════════════════════════════════════"
echo "🏗  目标架构: $TARGET_ARCH"
echo "📂 工程根:   $ROOT_DIR"
echo "📂 输出:     $PLATFORM_DIR"
echo

# ---- 1. macOS 检查 ----
if [[ "$(uname)" != "Darwin" ]]; then
    echo "❌ 此脚本必须在 macOS 上运行！"
    echo "   跨平台编译需要 OSXCROSS 或在本机虚拟机构建。"
    exit 1
fi

# ---- 2. 检查 Python ----
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "❌ 找不到 $PYTHON_BIN"
    echo "   推荐: brew install python@3.11"
    exit 1
fi
PY_VERSION=$("$PYTHON_BIN" --version 2>&1 | awk '{print $2}')
echo "✅ Python: $PY_VERSION"

# ---- 3. 准备构建目录 ----
mkdir -p "$BUILD_DIR"

# ---- 4. 创建 venv ----
if [[ ! -d "$VENV_DIR" ]]; then
    echo "▶️  创建虚拟环境..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
echo "✅ venv: $VENV_DIR"

# ---- 5. 安装依赖 ----
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

# ---- 6. 复制源文件 ----
echo "▶️  准备源文件..."
cp "$APP_DIR/launcher.py" "$BUILD_DIR/"
cp "$APP_DIR/ocr_app.py" "$BUILD_DIR/"
cp "$APP_DIR/config.yaml" "$BUILD_DIR/"
mkdir -p "$BUILD_DIR/presets"
cp "$APP_DIR/presets/"*.yaml "$BUILD_DIR/presets/" 2>/dev/null || true

# ---- 7. PyInstaller ----
echo "▶️  PyInstaller --onedir --target-arch=$TARGET_ARCH（首次约 60-120 秒）..."
cd "$BUILD_DIR"
TARGET_ARCH_FLAG=""
if [[ "$TARGET_ARCH" == "arm64" ]]; then
    TARGET_ARCH_FLAG="--target-arch=arm64"
elif [[ "$TARGET_ARCH" == "x64" ]]; then
    TARGET_ARCH_FLAG="--target-arch=x86_64"
fi

pyinstaller --onedir \
    --name "$OUTPUT_NAME" \
    $TARGET_ARCH_FLAG \
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

# ---- 8. 复制到 _platform/ ----
echo "▶️  部署到 _platform/macos-$TARGET_ARCH/..."
rm -rf "$PLATFORM_DIR"
mkdir -p "$PLATFORM_DIR"
cp -r "$BUILD_DIR/dist/$OUTPUT_NAME/"* "$PLATFORM_DIR/"
chmod +x "$PLATFORM_DIR/$OUTPUT_NAME"

# ---- 9. 复制 macOS 设置脚本（如果还没在） ----
cp "$SCRIPT_DIR/../_platform/macos-arm64/_INSTALL_FIRST_TIME.command" "$PLATFORM_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR/../_platform/macos-arm64/_QUICK_FIX.command" "$PLATFORM_DIR/" 2>/dev/null || true
chmod +x "$PLATFORM_DIR"/*.command 2>/dev/null || true

# ---- 10. 统计 ----
SIZE=$(du -sh "$PLATFORM_DIR" | awk '{print $1}')
echo
echo "═══════════════════════════════════════════════════════"
echo "✅ 构建完成！"
echo "═══════════════════════════════════════════════════════"
echo "📂 产物: $PLATFORM_DIR"
echo "💾 大小: $SIZE"
echo
echo "⚠️  macOS 首次使用需要移除隔离属性："
echo "   xattr -dr com.apple.quarantine $PLATFORM_DIR"
echo
echo "   或双击 _INSTALL_FIRST_TIME.command 引导用户操作"
echo
