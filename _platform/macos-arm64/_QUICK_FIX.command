#!/bin/bash
# =============================================================
#  LawExec OCR - macOS 一键修复（A2 极简 5 行版）
# =============================================================
# 适用：用户已经知道自己在干嘛，只需要快速解决问题
# 用法：双击运行即可
# =============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
osascript -e 'display notification "正在移除隔离属性..." with title "LawExec OCR"' 2>/dev/null
xattr -dr com.apple.quarantine "$SCRIPT_DIR" 2>/dev/null
chmod +x "$SCRIPT_DIR"/*.command "$SCRIPT_DIR"/*/*.command 2>/dev/null
osascript -e 'display dialog "✅ 完成！现在可以双击 start.command 启动了。" buttons {"好"} default button 1' 2>/dev/null
