# LawExec OCR Portable - 用户指南

> **版本**：v3.0.0-portable
> **评估日期**：2026-08-15
> **目标**：让 LawExec OCR 在 U 盘上即插即用

---

## 📖 一句话使用

| 平台 | 操作 |
|------|------|
| **Windows 11** | 插上 U 盘 → 双击 `start.bat` |
| **macOS (M1+)** | 插上 U 盘 → 双击 `_INSTALL_FIRST_TIME.command`（仅首次）→ 双击 `start.command` |
| **macOS (Intel)** | 同上，脚本自动检测 |
| **Linux** | 终端运行 `./start.sh` |

---

## 🪟 Windows 11 详细步骤

### 首次使用

1. 插入 U 盘
2. 在 U 盘根目录双击 **`start.bat`**
3. Windows SmartScreen 弹出警告（仅首次）：
   - 点击 **"更多信息"**
   - 点击 **"仍要运行"**
4. 等待 5-10 秒，浏览器自动打开 `http://127.0.0.1:8501`
5. Windows Defender 首次扫描约 30-60 秒（仅首次）

### 后续使用

- 直接双击 `start.bat` 即可
- 关闭启动窗口即可停止服务

### 常见问题

| 问题 | 解决 |
|------|------|
| 双击 .bat 闪退 | 右键 → "以管理员身份运行" |
| 浏览器没自动打开 | 手动访问 http://127.0.0.1:8501 |
| 端口 8501 被占用 | 编辑 start.bat，把 8501 改成 8502 等 |

---

## 🍎 macOS 详细步骤

### 首次使用（关键步骤）

macOS 默认会阻止"未签名应用"运行，需要一次性授权：

**步骤 1**：双击 `start.command`
- 系统弹出 "无法打开，因为无法验证开发者"

**步骤 2**：取消弹窗，去 `_platform/macos-arm64/` 目录
- 双击 **`_INSTALL_FIRST_TIME.command`**（A1 稳如老狗版）
  - 或 `_QUICK_FIX.command`（A2 极简版，给懂行的用）
- 按提示点"好"
- 约 3 秒后弹出"设置完成"

**步骤 3**：回到 U 盘根目录，双击 `start.command`
- 浏览器自动打开
- ✅ 之后每次直接双击 `start.command` 即可

### ⚠️ 关键提示

- **不要拖走 .app 到 Applications**：直接双击运行即可
- **如果换了 Mac 用**：需要在新 Mac 上重跑 `_INSTALL_FIRST_TIME.command`
- **如果 U 盘内容更新了**：重跑一次设置脚本

### 常见问题

| 问题 | 解决 |
|------|------|
| 设置脚本提示"未找到目标文件" | 确认 U 盘结构完整，路径含中文/空格不影响 |
| 双击 .app 还是被拦截 | 终端跑 `xattr -dr com.apple.quarantine /Volumes/你的U盘/_platform/macos-arm64/` |
| 浏览器没自动打开 | 手动访问 http://127.0.0.1:8501 |
| 启动很慢 | 首次需要解压 PyInstaller 资源（10-20 秒），之后秒启 |

### macOS Sequoia (15) / Tahoe (26+) 特殊说明

Apple 在新版本中进一步收紧了 Gatekeeper，但 `xattr -d` 命令仍然有效。如果遇到"无法打开，即使已移除隔离属性"：

```bash
# 临时方案：禁用 Gatekeeper（仅当前会话）
sudo spctl --master-disable

# 永久方案：申请 Apple Developer ID 签名（$99/年）
# 详见 _docs/PORTABLE_USB_TOOL_RESEARCH.md
```

---

## 🐧 Linux 详细步骤

### 源码模式（推荐用于开发）

```bash
cd /media/你的U盘/LawExec-OCR-Portable/_app
pip install -r requirements-portable.txt
python3 -m streamlit run ocr_app.py
```

### 打包模式（需要先在 Linux 上 PyInstaller 构建）

```bash
cd /media/你的U盘/LawExec-OCR-Portable
./start.sh
```

---

## 📁 目录结构说明

```
LawExec-OCR-Portable/
├── start.bat                 ← Windows 启动器
├── start.command             ← macOS 启动器
├── start.sh                  ← Linux/macOS CLI 启动器
├── README.txt                ← 一句话使用说明
│
├── _platform/                ← 各平台二进制（按需填充）
│   ├── windows-x64/
│   ├── macos-arm64/
│   │   ├── _INSTALL_FIRST_TIME.command   ← macOS 首次设置
│   │   └── _QUICK_FIX.command           ← macOS 极简修复
│   ├── macos-x64/
│   └── linux-x64/
│
├── _app/                     ← 应用源码（可读可改）
│   ├── ocr_app.py            ← 主程序（RapidOCR 版）
│   ├── launcher.py           ← PyInstaller 入口
│   ├── config.yaml           ← 配置
│   └── presets/
│       └── legal_doc.yaml    ← 法律文书预设
│
├── _docs/                    ← 文档
│   ├── USER_GUIDE.md         ← 本文件
│   ├── PORTABLE_USB_TOOL_RESEARCH.md
│   └── MIGRATION_ASSESSMENT.md
│
├── _test_samples/            ← 测试样本
│
├── build/                    ← 构建脚本（供开发者用）
│   ├── build_linux.sh
│   ├── build_macos.sh
│   └── build_windows.ps1
│
└── _logs/                    ← 运行日志
```

---

## 🔧 高级配置

### 修改端口

环境变量：

```bash
# Windows (PowerShell)
$env:LAWEXEC_PORT=8502; .\start.bat

# macOS / Linux
LAWEXEC_PORT=8502 ./start.sh
```

### 修改文件大小上限

编辑 `_app/ocr_app.py` 第 484 行：

```python
config.toml 里 maxUploadSize = 500  # 改为 1000 = 1GB
```

### 关闭 LibreOffice 提示

OFD/ODF 处理会优先用 LibreOffice（如系统已装），未装时降级到纯 Python。如果想强制用纯 Python：

```python
# 编辑 _app/ocr_app.py，注释掉 has_libreoffice() 检查
```

---

## 📊 性能参考

### 启动时间

| 平台 | 首次 | 后续 |
|------|------|------|
| Windows 11 | 8-15 秒（含 Defender 扫描）| 3-5 秒 |
| macOS M1 | 5-8 秒 | 2-3 秒 |
| Linux | 3-5 秒 | 1-2 秒 |

### OCR 速度

- 单页 A4 PDF（200 DPI）：约 1-2 秒
- 单页扫描件（300 DPI）：约 2-4 秒
- 100 页批量 PDF：约 3-5 分钟

### 置信度参考

| 文档类型 | 典型置信度 |
|----------|-----------|
| 电子 PDF | 0.95-0.99 |
| 高清扫描 | 0.85-0.95 |
| 模糊/低分辨率 | 0.60-0.85 |
| 印章覆盖区域 | 0.50-0.80（取决于预处理）|

---

## 🆘 获取帮助

| 渠道 | 链接 |
|------|------|
| 项目主页 | `/media/jisuo/Data/UDown/LawExec-OCR/` |
| 迁移评估 | `_docs/MIGRATION_ASSESSMENT.md` |
| 便携化调研 | `_docs/PORTABLE_USB_TOOL_RESEARCH.md` |
| 源码 | `_app/ocr_app.py` |
| 日志 | `_logs/` |

---

## 📝 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 3.0.0-portable | 2026-08-15 | 首次发布便携版（RapidOCR 引擎） |

---

*LawExec OCR v3.0 Portable Edition - 让法律 OCR 走到 U 盘里*
