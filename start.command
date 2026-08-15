#!/bin/bash
# ============================================
#  LawExec OCR v3.0 - macOS Portable Launcher
#  使用方法：双击本文件即可
# ============================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ---- 1. 优先检测 arm64 (M1+ Mac) ----
TARGET_ARM="$SCRIPT_DIR/_platform/macos-arm64/LawExec-OCR"
TARGET_X64="$SCRIPT_DIR/_platform/macos-x64/LawExec-OCR"

if [[ -f "$TARGET_ARM" ]]; then
    TARGET="$TARGET_ARM"
    ARCH="arm64 (M1+)"
elif [[ -f "$TARGET_X64" ]]; then
    TARGET="$TARGET_X64"
    ARCH="x64 (Intel)"
else
    # 用 GUI 弹窗报错
    osascript <<'AS' 2>/dev/null
display alert "未找到 macOS 二进制" message "请确认 U 盘目录完整：
    _platform/macos-arm64/LawExec-OCR
    _platform/macos-x64/LawExec-OCR

如果你的 U 盘是 Windows 版，请改在 Windows 上使用。" as critical buttons {"OK"}
AS
    read -p "按回车关闭..."
    exit 1
fi

# ---- 2. 首次运行检查：如果二进制被隔离（quarantine），引导用户跑设置脚本 ----
if xattr "$TARGET" 2>/dev/null | grep -q "com.apple.quarantine"; then
    INSTALL_SCRIPT="$SCRIPT_DIR/_platform/macos-arm64/_INSTALL_FIRST_TIME.command"
    if [[ -f "$INSTALL_SCRIPT" ]]; then
        osascript <<AS 2>/dev/null
display dialog "首次运行需要授权

macOS 默认会阻止未签名应用运行。
双击打开 '_platform/macos-arm64/_INSTALL_FIRST_TIME.command' 完成一次性设置（约 3 秒），之后本启动器即可正常使用。" buttons {"好"} default button 1 with title "LawExec OCR - 首次设置"
AS
        open "$INSTALL_SCRIPT"
        read -p "设置完成后按回车继续..."
    fi
fi

# ---- 3. 启动 ----
clear
echo "⚖️  LawExec OCR v3.0 - Portable Edition"
echo "📂 程序位置: $TARGET"
echo "🏗  架构: $ARCH"
echo "🌐 浏览器将自动打开 http://127.0.0.1:8501"
echo "⏹  关闭此窗口即可停止服务"
echo

open "http://127.0.0.1:8501"
exec "$TARGET"
