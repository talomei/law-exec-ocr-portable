# 📦 LawExec-OCR-Portable 交付清单

> **构建日期**：2026-08-15
> **版本**：v3.0.0-portable
> **目标**：U 盘即插即用，Win11 / macOS M1+ / Linux 跨平台

---

## ✅ 已完成

### 1. 目录结构

```
/media/jisuo/Data/UDown/LawExec-OCR-Portable/     ← 总 573 MB
├── start.bat                                      ← Windows 启动器
├── start.command                                  ← macOS 启动器
├── start.sh                                       ← Linux/macOS CLI
├── README.txt                                     ← 一句话使用
├── requirements-portable.txt                      ← 精简依赖清单
│
├── _app/                                          ← 44 KB 源码（可读可改）
│   ├── ocr_app.py                                 ← RapidOCR 主程序（556 行）
│   ├── launcher.py                                ← PyInstaller 入口（已修 fork-bug）
│   ├── config.yaml
│   ├── requirements-portable.txt
│   └── presets/legal_doc.yaml
│
├── _platform/
│   ├── linux-x64/                                 ← 573 MB ✅ 已构建并验证
│   │   ├── LawExec-OCR                            ← ELF 可执行
│   │   └── _internal/                             ← Python + RapidOCR + Streamlit
│   ├── macos-arm64/                               ← 12 KB（含设置脚本，待构建）
│   │   ├── _INSTALL_FIRST_TIME.command            ← A1 稳如老狗版
│   │   └── _QUICK_FIX.command                     ← A2 极简 5 行版
│   ├── macos-x64/                                 ← 待构建
│   └── windows-x64/                               ← 待构建
│
├── _docs/                                         ← 36 KB
│   ├── USER_GUIDE.md
│   ├── PORTABLE_USB_TOOL_RESEARCH.md
│   └── MIGRATION_ASSESSMENT.md
│
├── build/                                         ← 各平台构建脚本
│   ├── build_linux.sh
│   ├── build_macos.sh
│   └── build_windows.ps1
│
├── _logs/                                         ← 运行日志（空）
└── _test_samples/                                 ← 测试样本（空，预留）
```

### 2. 实测验证（Linux x64 平台）

| 测试项 | 结果 |
|--------|------|
| PyInstaller --onedir 构建 | ✅ 574 MB / ~60s |
| 二进制启动进程数 | ✅ 单进程（无 fork-bomb）|
| 端口 8501 监听 | ✅ 正常 |
| HTTP 200 响应 | ✅ 1.7ms |
| Streamlit 渲染 | ✅ 3 个 streamlit 资源引用 |
| fork-bug 修复 | ✅ 用 `streamlit.web.cli.main()` 进程内调用 |
| Pillow 子模块 | ✅ `--collect-submodules=PIL` 解决 |

### 3. macOS A1/A2 设置脚本

- **A1 `_INSTALL_FIRST_TIME.command`**（149 行）：
  - 自动定位、递归去隔离、GUI 弹窗、可重复运行
  - 一次设置 → 后续所有 .command / .app 可用
- **A2 `_QUICK_FIX.command`**（13 行）：极简 5 行版，给懂行的用

---

## ⏳ 待办（在 Win/Mac 上完成构建）

| 平台 | 任务 | 工作量 | 工具 |
|------|------|--------|------|
| **macOS M1+** | 在 Mac 上跑 `build_macos.sh` | 5 分钟 | 需 Mac 本机或 GitHub Actions runner |
| **macOS Intel** | 在 Mac 上跑 `build_macos.sh x64` | 5 分钟 | 同上 |
| **Windows 11** | 在 Win 上跑 `build_windows.ps1` | 5 分钟 | 需 Win11 真机或 GitHub Actions |

### 推荐：用 GitHub Actions 自动化

`build/` 目录里的三个脚本可以直接接到 GitHub Actions matrix build：

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]
    include:
      - os: macos-latest
        arch: arm64
      - os: macos-13   # Intel
        arch: x64
```

跑一次即可获得三个平台的产物，免去在每台真机操作。

---

## 📊 体积预算

| 平台 | 二进制大小 | 加上 docs/启动器 | 占 U 盘空间 |
|------|-----------|------------------|-------------|
| Linux x64（已构建）| 573 MB | +1 MB | 574 MB |
| Windows x64（预估）| ~570 MB | +1 MB | ~571 MB |
| macOS arm64（预估）| ~520 MB | +12 KB（含设置脚本）| ~520 MB |
| macOS x64（预估）| ~540 MB | +12 KB | ~540 MB |
| **三平台合计** | | | **~1.6 GB** |
| **仅 Win+Mac 双平台** | | | **~1.1 GB** |

> 8 GB U 盘即可放 Win+Mac 双平台（剩余 6 GB 可放测试样本/日志）。
> 16 GB U 盘更宽裕。

---

## 🧪 验证清单

### 在 Linux 上 ✅（已完成）

```bash
./_platform/linux-x64/LawExec-OCR
# 浏览器打开 http://127.0.0.1:8501
# 上传一个 PDF 测试
```

### 在 macOS M1 上（待验证）

```bash
# 1. 第一次：双击 _INSTALL_FIRST_TIME.command
# 2. 然后双击 start.command
# 3. 浏览器自动打开
```

### 在 Windows 11 上（待验证）

```bat
REM 1. 双击 start.bat
REM 2. SmartScreen 提示 → 更多信息 → 仍要运行
REM 3. 浏览器自动打开
```

---

## 🐛 已知问题 & 解决方案

| 问题 | 临时方案 | 根本解决 |
|------|----------|----------|
| macOS 首次被 Gatekeeper 拦截 | 跑 `_INSTALL_FIRST_TIME.command` | Apple Developer ID 签名（$99/年）|
| Windows SmartScreen 警告 | 点"更多信息 → 仍要运行" | EV 代码签名证书（$300-500/年）|
| Defender 首次扫描 30-60 秒 | 等待 | 加白名单 |
| PIL 子模块缺失 | `--collect-submodules=PIL` 已加 | 长期监控 PyInstaller hook 变化 |
| `fitz` API 弃用警告 | 不影响功能 | 升级到 `import pymupdf`（下版本）|
| 16 GB 装不下三平台 | 砍掉 Intel Mac | 升级 32 GB U 盘 |

---

## 📋 后续路线图

| 阶段 | 内容 | 优先级 |
|------|------|--------|
| **v3.0.1** | 修复 fitz 弃用警告（改 pymupdf）| P2 |
| **v3.1.0** | 接入 Apple Developer ID 自动签名 | P1 |
| **v3.2.0** | 接入 GitHub Actions 自动三平台构建 | P1 |
| **v4.0.0** | 加入 OFD 复杂版式还原（不只抽文字）| P3 |
| **v4.1.0** | 接入更大模型（PP-OCRv5）| P3 |

---

## 📞 联系与反馈

- **项目主页**：`/media/jisuo/Data/UDown/LawExec-OCR/`
- **便携版根**：`/media/jisuo/Data/UDown/LawExec-OCR-Portable/`
- **问题反馈**：在原项目 README.md 提 issue

---

*📦 由 Claude Code 在本机构建并验证*
*🕐 构建时间：2026-08-15 17:23*
*✅ 验证状态：Linux x64 单进程、端口监听、HTTP 200 全通过*
