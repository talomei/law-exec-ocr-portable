# GitHub Actions - Portable 自动构建

> **目的**：一次 push，自动产出 Win11 + macOS M1/Intel + Linux x64 三平台便携包

## 📊 任务矩阵

| 平台 | Runner | 产物 | 大小 | 用时 |
|------|--------|------|------|------|
| **Windows 11 x64** | windows-latest | `LawExec-OCR-windows-x64.zip` | ~570 MB | 5-8 min |
| **macOS M1+ ARM64** | macos-latest | `LawExec-OCR-macos-arm64.zip` | ~520 MB | 6-10 min |
| **macOS Intel x64** | macos-13 | `LawExec-OCR-macos-x64.zip` | ~540 MB | 6-10 min |
| **Linux x64** | ubuntu-latest | `LawExec-OCR-linux-x64.zip` | ~570 MB | 4-6 min |

## 🚀 使用方法

### 1. 把项目推到 GitHub

```bash
cd /media/jisuo/Data/UDown/LawExec-OCR-Portable
git init
git add .
git commit -m "Initial: LawExec OCR Portable v3.0"
git remote add origin https://github.com/你的用户名/law-exec-ocr-portable.git
git push -u origin main
```

### 2. 触发构建

#### 方式 A：自动触发（push 到 main）
```bash
git push origin main
# → Actions 自动跑三平台
# → Artifacts 可在 Actions 页面下载（保留 14 天）
```

#### 方式 B：手动触发
1. 进 GitHub 仓库 → **Actions** → **Build Portable** → **Run workflow**
2. 选 "上传构建产物" → 点 **Run**

#### 方式 C：发 Release（推荐生产用）
```bash
git tag v3.0.0
git push origin v3.0.0
# → 自动跑构建 + 发 GitHub Release
# → Release 永久保留
```

## 💰 费用

- **公开仓库**：GitHub 无限免费 minutes
- **私有仓库**：每月 2000 分钟免费
  - 三平台一次构建约 25 分钟
  - 月度预算可跑 80 次构建

## 🔧 自定义

### 加新平台
编辑 `.github/workflows/build-portable.yml` 的 `matrix.include` 块。

### 只跑某个平台
进 Actions → Run workflow → 通过 `inputs.platform` 过滤（需小改 workflow）

### 加速构建
- 加 `--cache-from` 缓存 pip 包
- 用 `actions/cache@v4` 缓存 PyInstaller bootloader

## 📥 下载产物

### 通过 Actions Artifacts
1. 进 GitHub 仓库 → **Actions** → 选 build run
2. 滚到页面底部 **Artifacts** 区
3. 下载 `LawExec-OCR-{platform}.zip`

### 通过 Release
1. 进 GitHub 仓库 → **Releases**（右侧栏）
2. 找版本号 → 点进去
3. 在 **Assets** 下下载对应平台

---

*由 Claude Code 生成的 GitHub Actions 模板*
