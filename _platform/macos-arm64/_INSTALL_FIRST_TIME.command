#!/bin/bash
# =============================================================
#  LawExec OCR - macOS 首次设置脚本（A1 稳如老狗版）
# =============================================================
# 用途：递归移除 macOS 隔离属性（com.apple.quarantine），
#       让 _platform/macos-arm64/LawExec-OCR 能直接双击启动。
#
# 特性：
#   ✅ 自动定位（不依赖 U 盘挂载点具体名字）
#   ✅ 处理任何文件路径（含空格、中文）
#   ✅ GUI 引导弹窗 + 通知
#   ✅ 可重复运行（幂等）
#   ✅ 同时设置所有 .command 文件可执行权限
#   ✅ 自身被隔离时自动先解自己
# =============================================================

set -e

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ─────────── 0. 自解隔离（如果脚本本身被隔离） ───────────
SCRIPT_FILE="$0"
if xattr "$SCRIPT_FILE" 2>/dev/null | grep -q "com.apple.quarantine"; then
    echo -e "${YELLOW}⚠️  本脚本自身被隔离，先自解...${NC}"
    xattr -d com.apple.quarantine "$SCRIPT_FILE" 2>/dev/null || true
fi

# ─────────── 1. 引导弹窗 ───────────
RESULT=$(osascript <<'AS' 2>/dev/null
display dialog "LawExec OCR 首次设置

将自动处理 macOS 隔离属性，整个过程约 3 秒。

点击「好」继续。" buttons {"取消", "好"} default button 2
AS
)
if [[ $? -ne 0 ]] || [[ "$RESULT" == *"返回:取消"* ]]; then
    echo -e "${YELLOW}已取消${NC}"
    exit 0
fi

# ─────────── 2. 定位脚本所在目录 ───────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo -e "${BLUE}📂 脚本位置: $SCRIPT_DIR${NC}"

# ─────────── 3. 递归找所有 .app / 主可执行文件 ───────────
echo -e "${BLUE}🔍 扫描 .app bundle 和可执行文件...${NC}"

APP_PATHS=()
while IFS= read -r -d '' app; do
    APP_PATHS+=("$app")
done < <(find "$SCRIPT_DIR" -maxdepth 4 -name "*.app" -print0 2>/dev/null)

EXEC_PATHS=()
while IFS= read -r -d '' exe; do
    EXEC_PATHS+=("$exe")
done < <(find "$SCRIPT_DIR" -maxdepth 3 -type f \( -name "LawExec-OCR" -o -name "LawExec-OCR.bin" \) -print0 2>/dev/null)

LIB_PATHS=()
while IFS= read -r -d '' lib; do
    LIB_PATHS+=("$lib")
done < <(find "$SCRIPT_DIR" -maxdepth 4 -type f \( -name "*.dylib" -o -name "*.so" \) -print0 2>/dev/null)

TOTAL_COUNT=$((${#APP_PATHS[@]} + ${#EXEC_PATHS[@]} + ${#LIB_PATHS[@]}))

if [[ $TOTAL_COUNT -eq 0 ]]; then
    osascript -e 'display alert "未找到目标文件" message "请确认 U 盘结构完整：
    _platform/macos-arm64/LawExec-OCR
    _platform/macos-arm64/LawExec-OCR.app

当前扫描路径：'"$SCRIPT_DIR"'" as critical buttons {"OK"}' 2>/dev/null
    echo -e "${RED}❌ 未找到目标文件${NC}"
    read -p "按回车关闭..."
    exit 1
fi

echo -e "${GREEN}找到:${NC}"
[[ ${#APP_PATHS[@]} -gt 0 ]]  && echo -e "  📦 .app: ${#APP_PATHS[@]} 个"
[[ ${#EXEC_PATHS[@]} -gt 0 ]] && echo -e "  ⚙️  可执行: ${#EXEC_PATHS[@]} 个"
[[ ${#LIB_PATHS[@]} -gt 0 ]]  && echo -e "  📚 动态库: ${#LIB_PATHS[@]} 个"

# ─────────── 4. 递归移除隔离属性 ───────────
SUCCESS=0
FAILED=0
PROCESSED=()

remove_quarantine() {
    local target="$1"
    if xattr -dr com.apple.quarantine "$target" 2>/dev/null; then
        SUCCESS=$((SUCCESS + 1))
        PROCESSED+=("✅ $target")
    else
        FAILED=$((FAILED + 1))
        PROCESSED+=("❌ $target")
    fi
}

echo -e "\n${YELLOW}🔓 移除 com.apple.quarantine...${NC}"
for app in "${APP_PATHS[@]}";  do remove_quarantine "$app"; done
for exe in "${EXEC_PATHS[@]}"; do remove_quarantine "$exe"; done
for lib in "${LIB_PATHS[@]}";  do remove_quarantine "$lib"; done

# ─────────── 5. 设置 .command 文件可执行 ───────────
COMMAND_FILES=()
while IFS= read -r -d '' cf; do
    chmod +x "$cf" 2>/dev/null && COMMAND_FILES+=("$cf")
done < <(find "$SCRIPT_DIR" -maxdepth 4 -name "*.command" -print0 2>/dev/null)

# 同时把根目录的 start.command 也设可执行
ROOT_CMD="$(cd "$SCRIPT_DIR/../.." && pwd)/start.command"
[[ -f "$ROOT_CMD" ]] && chmod +x "$ROOT_CMD"

# ─────────── 6. 验证（复查一次） ───────────
echo -e "\n${BLUE}🔍 验证（应返回空）：${NC}"
REMAINING=0
for path in "${APP_PATHS[@]}" "${EXEC_PATHS[@]}" "${LIB_PATHS[@]}"; do
    if xattr "$path" 2>/dev/null | grep -q "com.apple.quarantine"; then
        echo -e "  ${RED}⚠️  $path 仍有隔离属性${NC}"
        REMAINING=$((REMAINING + 1))
    fi
done

if [[ $REMAINING -eq 0 ]]; then
    echo -e "  ${GREEN}✅ 全部清理干净${NC}"
fi

# ─────────── 7. 总结 ───────────
SUMMARY="处理完成 ✅

成功: $SUCCESS 个
失败: $FAILED 个
.command 文件: ${#COMMAND_FILES[@]} 个已设可执行

现在可以关闭此窗口，回到 U 盘根目录双击 start.command 启动应用。"

echo -e "\n${GREEN}════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 全部完成！${NC}"
echo -e "${GREEN}════════════════════════════════════${NC}"
echo -e "$SUMMARY"

osascript -e "display notification \"成功: $SUCCESS / 失败: $FAILED\" with title \"LawExec OCR 设置完成\"" 2>/dev/null
osascript -e "display dialog \"$SUMMARY\" buttons {\"好\"} default button 1 with title \"LawExec OCR - 设置完成\"" 2>/dev/null

exit 0
