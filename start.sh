#!/bin/bash
# ============================================
#  LawExec OCR v3.0 - Linux/macOS CLI Launcher
#  使用方法：./start.sh
#  适用：开发测试 / Linux 服务器
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PORT="${LAWEXEC_PORT:-8501}"
HOST="${LAWEXEC_HOST:-127.0.0.1}"

echo "⚖️  LawExec OCR v3.0 - Portable Edition (Linux/macOS)"
echo "📂 工作目录: $SCRIPT_DIR/_app"
echo "🌐 监听地址: http://$HOST:$PORT"
echo

# ---- 检测模式：优先二进制，降级到 venv ----
if [[ -f "$SCRIPT_DIR/_platform/linux-x64/LawExec-OCR" ]]; then
    echo "▶️  使用打包好的二进制"
    exec "$SCRIPT_DIR/_platform/linux-x64/LawExec-OCR"
fi

if [[ -f "$SCRIPT_DIR/_app/ocr_app.py" ]]; then
    echo "▶️  使用源码模式（需先装 pip 依赖）"
    cd "$SCRIPT_DIR/_app"
    exec python3 -m streamlit run ocr_app.py \
        --server.port "$PORT" \
        --server.address "$HOST" \
        --server.headless true \
        --browser.gatherUsageStats false \
        --global.developmentMode false
fi

echo "❌ 找不到任何可执行入口"
echo "   期望: $SCRIPT_DIR/_platform/linux-x64/LawExec-OCR"
echo "   或:   $SCRIPT_DIR/_app/ocr_app.py"
exit 1
