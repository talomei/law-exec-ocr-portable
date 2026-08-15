# 🪟 Win11 构建指南

> **目标**：在 Windows 11 上用 PyInstaller 打包 LawExec OCR
> **输出**：`_platform\windows-x64\LawExec-OCR.exe`（约 570 MB）
> **耗时**：首次 5-10 分钟（含下载依赖），后续 60-90 秒
> **难度**：🟢 简单，跟着复制粘贴即可

---

## 📋 前置准备（一次性，约 5 分钟）

### 1. 安装 Python 3.11（推荐）

下载地址：https://www.python.org/downloads/windows/

**关键：安装时务必勾选**：
- ☑️ **Add Python to PATH**（必须，否则命令行找不到 python）
- ☑️ **Use admin privileges when installing py.exe**

### 2. 验证 Python

打开 PowerShell 或 cmd：

```powershell
python --version
# 应输出：Python 3.11.x
pip --version
# 应输出：pip 24.x from ...
```

如果提示"找不到 python"，说明 PATH 没设好，重新安装并勾选 Add to PATH。

### 3. 准备项目目录

把整个 `LawExec-OCR-Portable` 目录拷到 Win11 上任意位置，例如：

```
D:\LawExec-OCR-Portable\
```

---

## 🚀 构建步骤（双击即可）

### 方法 A：双击 `build_windows.bat`（最简单）

1. 在 Windows 资源管理器中打开 `D:\LawExec-OCR-Portable\build\`
2. **双击 `build_windows.bat`**
3. 等待 5-10 分钟（首次含 pip 装包）
4. 完成后产物在 `_platform\windows-x64\` 下

### 方法 B：PowerShell 命令行（更可控）

```powershell
# 用管理员权限打开 PowerShell
cd D:\LawExec-OCR-Portable\build

# 第一次运行需绕过执行策略
powershell -ExecutionPolicy Bypass -File .\build_windows.ps1
```

---

## 🛠️ 常见问题排查

### Q1: "python 不是内部或外部命令"

**原因**：Python 没加到 PATH
**解决**：
```powershell
# 临时方案：用绝对路径
C:\Users\你的用户名\AppData\Local\Programs\Python\Python311\python.exe build_windows.ps1

# 永久方案：重新安装 Python 并勾选 Add to PATH
```

### Q2: "error: Microsoft Visual C++ 14.0 or greater is required"

**原因**：`python-Levenshtein` 需要 C 编译器
**解决**：编辑 `build_windows.ps1`，把 `python-Levenshtein` 从依赖列表里删掉

（这个包仅用于模糊去重，不影响核心 OCR。删除后仍能正常用。）

或者安装 Visual Studio Build Tools：https://visualstudio.microsoft.com/visual-cpp-build-tools/

### Q3: "PyMuPDF 安装失败"

**原因**：网络问题或 wheel 不兼容
**解决**：
```powershell
# 指定源
pip install PyMuPDF -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q4: 打包成功但启动报错 "ImportError: DLL load failed"

**原因**：PyInstaller 没把所有动态库打包
**解决**：在 `build_windows.ps1` 的 pyinstaller 命令末尾加：
```
--collect-all msvcrt
```

### Q5: 启动后浏览器没自动打开

**原因**：Windows 默认浏览器关联被改
**解决**：手动访问 http://127.0.0.1:8501

### Q6: Windows Defender 一直扫描

**解决**：
- 首次扫描 30-60 秒是正常的，耐心等
- 把 `_platform\windows-x64\` 加入 Defender 白名单
- 长期方案：申请 EV 代码签名（$300-500/年）

---

## ✅ 构建完成验证清单

构建成功后，检查以下项目：

| 检查项 | 通过条件 |
|--------|----------|
| 产物大小 | `_platform\windows-x64\LawExec-OCR.exe` 存在，> 15 MB |
| _internal/ 完整 | `_internal\streamlit\`、`_internal\rapidocr_onnxruntime\`、`_internal\PIL\` 都在 |
| 双击启动 | 双击 `start.bat`，cmd 窗口不闪退 |
| 端口监听 | `netstat -an \| findstr 8501` 看到 LISTENING |
| 浏览器访问 | http://127.0.0.1:8501 能看到 Streamlit 页面 |
| 上传测试 | 上传一个 PDF 能正常识别 |

### 快速验证命令

```powershell
# 1. 检查产物
dir _platform\windows-x64\LawExec-OCR.exe
dir _platform\windows-x64\_internal\streamlit
dir _platform\windows-x64\_internal\rapidocr_onnxruntime

# 2. 启动测试
cd ..
.\start.bat
# 另开一个 PowerShell 窗口：
netstat -an | findstr 8501
# 应看到：127.0.0.1:8501  LISTENING

# 3. HTTP 测试
curl http://127.0.0.1:8501/
# 应返回 HTML（HTTP 200）
```

---

## 📦 把产物放到 U 盘

构建完成后，把整个 `LawExec-OCR-Portable` 目录（573 MB → 1.1 GB 含三平台）拷到 U 盘：

```powershell
# 假设 U 盘是 E:
xcopy /E /H /K D:\LawExec-OCR-Portable E:\LawExec-OCR-Portable\
```

---

## ⏭️ 下一步

构建 Win 包后，回到 U 盘根目录双击 `start.bat`：
- 第一次 Windows SmartScreen 弹窗 → 选"更多信息" → "仍要运行"
- 浏览器自动打开 `http://127.0.0.1:8501`
- 上传 PDF 测试

---

## 🆘 仍有问题？

| 渠道 | 联系方式 |
|------|----------|
| 完整文档 | `_docs/USER_GUIDE.md` |
| 调研报告 | `_docs/PORTABLE_USB_TOOL_RESEARCH.md` |
| 迁移评估 | `_docs/MIGRATION_ASSESSMENT.md` |
| 启动脚本 | `build\build_windows.ps1`（可重跑）|

---

*📝 由 Claude Code 生成于 2026-08-15*
*🏷 适用版本：v3.0.0-portable*
