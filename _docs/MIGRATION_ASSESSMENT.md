# LawExec-OCR 迁移评估报告

> **目标环境**：麒麟系统 / Python 3.8 / 离线运行
> **评估日期**：2026-08-15
> **评估对象**：`/media/jisuo/Data/UDown/LawExec-OCR` v3.0
> **评估范围**：代码兼容性、依赖栈、系统依赖、离线可行性

---

## 🎯 一句话结论

> **可以迁移，但需要把 paddle 栈从 3.0 降级到 2.6（最后一个支持 Python 3.8 的分支），并修掉项目里 2 处历史遗留的破引用。**
> 离线打包体积约 **1.8 GB**，迁移工作量 **2.5–4 小时**。

---

## 📊 三维评估

### ① 麒麟系统 — ✅ 可行（先确认具体版本）

| 麒麟发行版 | glibc | 能否跑 paddle 2.6 | 能否跑 paddle 3.0 |
|------------|-------|-------------------|-------------------|
| **银河麒麟 V10 SP3+**（Ubuntu 22.04 内核）| 2.35 | ✅ | ✅ |
| **openKylin 1.0+**（Ubuntu 22.04 内核）| 2.35 | ✅ | ✅ |
| **统信 UOS 20**（Deepin 内核）| 2.28 | ✅ | ⚠️ 部分算子可能不可用 |
| **银河麒麟 V10 SP1/SP2**（CentOS 7 内核）| 2.17 | ⚠️ 需 `devtoolset-9` 升 glibc | ❌ |
| **中标麒麟 V7**（CentOS 7 内核）| 2.17 | ⚠️ 同上 | ❌ |

**判定**：
- 目标机若是 **SP3+ / openKylin / UOS20** → 三个目标全部通过
- 若是更老的 CentOS 7 内核版本 → 必须走 **paddle 2.6 + Python 3.8** 路线（其实也满足本题需求）

### ② Python 3.8 — ⚠️ 强制触发 paddle 栈降级

#### 当前装的（Py 3.12）vs Py 3.8 兼容性

| 包 | 实际版本 | 是否支持 Py 3.8 |
|----|----------|-----------------|
| paddlepaddle | 3.0.0 | ❌ 官方 3.0 仅支持 Py 3.9+ |
| paddleocr | 3.4.1 | ❌ 跟随 paddle 3.0 |
| paddlex | 3.4.3 | ❌ 跟随 paddle 3.0 |
| streamlit | 1.56.0 | ❌ 1.30+ 要求 Py 3.9+ |
| numpy | 2.4.4 | ❌ numpy 2.0+ 要求 Py 3.10+ |
| Pillow | 12.2.0 | ⚠️ Pillow 11+ 要求 Py 3.9+ |
| PyMuPDF | 1.27.2.3 | ✅ 支持 |
| opencv-python | 4.11.x | ✅ 支持 |
| python-Levenshtein | 未装 | ✅ 支持 |

#### 对 Py 3.8 友好的最高版本组合（建议锁定）

```text
paddlepaddle==2.6.2          # 最后一个支持 Py 3.8 的 paddle
paddleocr==2.8.0             # 跟随 paddle 2.6
paddlex==3.0.0               # 最后一个 3.x 支持 Py 3.8
streamlit==1.29.0            # 最后一个支持 Py 3.8
numpy==1.26.4                # 最后一个支持 Py 3.8
Pillow==10.4.0               # 最后一个支持 Py 3.8
opencv-python==4.10.0.84
PyMuPDF==1.24.10
python-Levenshtein==0.26.1
```

> 📌 注意：项目 `requirements.txt` 写的下限（`paddleocr>=2.7.0, paddlepaddle>=2.5.0`）允许这种降级，但当前实际安装的版本（3.x）已超出该下限——是开发期升级过头了。

### ③ 离线运行 — ✅ 可行，必须做"全量预热 + 路径固化"

#### 离线必须打包的内容

| 内容 | 体积 | 来源 |
|------|------|------|
| venv-ocr（依赖包，已装好）| 1.6 GB | `/media/jisuo/Data/UDown/LawExec-OCR/venv-ocr` |
| paddleocr 模型 | 210 MB | `~/.paddlex/official_models/` |
| 系统级 libreoffice | ~600 MB | 目标机 apt/dnf 装 |
| **应用层合计** | **~1.8 GB** | |

#### 模型清单（`~/.paddlex/official_models/`）

| 模型 | 大小 | 用途 |
|------|------|------|
| PP-OCRv5_server_det | 85 MB | 文本检测 |
| PP-OCRv5_server_rec | 82 MB | 文本识别 |
| UVDoc | 31 MB | 文档矫正 |
| PP-LCNet_x1_0_doc_ori | 6.6 MB | 文档方向分类 |
| PP-LCNet_x1_0_textline_ori | 6.6 MB | 文本行方向分类 |
| **合计** | **210 MB** | |

#### 离线模式必须做的三件事

1. **首次联网预热**让 `paddleocr` 把模型下载到 `~/.paddlex/official_models/` —— **本机已完成 ✅**
2. **设置离线环境变量**（避免 paddleocr 启动时回连服务器校验）：
   ```bash
   export PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True
   export HF_HUB_OFFLINE=1
   export TRANSFORMERS_OFFLINE=1
   ```
3. **`ocr_app.py` 顶部新增一行**（位于现有 `os.environ[...]` 区域）：
   ```python
   os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'
   ```

---

## 🐛 项目自身的两个隐藏 bug（迁移前必修）

### Bug 1：`engine/ocr_engine.py` 引用了不存在的路径

**文件**：`/media/jisuo/Data/UDown/LawExec-OCR/engine/ocr_engine.py:14-15`

```python
# 添加 Talomei OCR 源码路径
sys.path.insert(0, '/root/.openclaw/workspace-arkell/projects/ocr_gui/src')

from optimized_pipeline import OptimizedOCRPipeline   # ← 这模块在本机根本不存在
```

> ✅ **好消息**：`ocr_app.py`（主程序）**没有引用** `engine/ocr_engine.py`，实际 OCR 走的是 `paddleocr.PaddleOCR` 直调路径，主流程不受影响。
> ❌ **坏消息**：该文件**无法被加载**；迁移到新机器后若有任何代码意外 import 它就会崩。

**修复建议**：删除该文件（项目已走 `paddleocr` 主路径，不需要它），或重写为占位 stub。

### Bug 2：`test/` 下所有文件引用了不存在的 `optimized_pipeline`

| 受影响文件 | 引用行 |
|------------|--------|
| `test/debug_ocr_result.py` | `from optimized_pipeline import OptimizedOCRPipeline` |
| `test/debug_preprocess.py` | 同上 |
| `test/debug_single_page.py` | 仅 `from paddleocr import PaddleOCR`（可用）|
| `test/debug_single_page_v2.py` | 同上（可用）|
| `test/debug_ofd_structure.py` | 不依赖 paddle（可用）|

> 这些测试脚本在新机器上**永远跑不起来**。迁移前要么补回 `optimized_pipeline.py`，要么删除/注释这些测试文件。

---

## 🗺 迁移路径推荐（按工作量从小到大）

### 🟢 方案 A：最小改动路线（推荐）

| 步骤 | 操作 | 工时 |
|------|------|------|
| 1 | 目标机装 Python 3.8 + libreoffice | 0.5h |
| 2 | 在目标机新建 `venv-ocr`，`pip install` 锁定的旧版组合 | 1h（需联网一次，或离线 pip）|
| 3 | 拷贝 `~/.paddlex/`（210 MB）到目标机 | 0.1h |
| 4 | 拷贝项目源码（除 `engine/ocr_engine.py`、除 `test/` 全部）| 0.1h |
| 5 | `ocr_app.py` 顶部加一行 `os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK']='True'` | 0.05h |
| 6 | 启动测试：`./start.sh 8501` | 0.5h |
| **合计** | | **~2.5h** |

### 🟡 方案 B：完整清理路线（更稳）

| 步骤 | 操作 | 工时 |
|------|------|------|
| 1-5 | 同方案 A | 2.5h |
| 6 | 删 `engine/ocr_engine.py`（无用模块）| 0.1h |
| 7 | 删 `test/`（不可用测试）| 0.05h |
| 8 | 把 venv 路径固化到 `pyvenv.cfg`（确保 `home = /usr/bin` 仍指向麒麟的 python3.8）| 0.1h |
| 9 | 写一个 `install_offline.sh`：解压 → 链接 → 设置环境变量 | 0.5h |
| 10 | 跑回归测试（用项目里 sample PDF）| 1h |
| **合计** | | **~4h** |

---

## 📦 离线打包清单（执行时用）

### 需要打包的文件 / 目录

```
打包根目录：/media/jisuo/Data/UDown/LawExec-OCR-migration-bundle/
├── LawExec-OCR/                     # 项目源码（精简后）
│   ├── ocr_app.py
│   ├── start.sh                     # 已改相对路径
│   ├── start-daemon.sh              # 已改相对路径
│   ├── requirements.txt             # 改为锁定版本
│   └── .streamlit/
├── venv-ocr/                        # 整个 1.6 GB 虚拟环境
├── paddle_models/
│   └── .paddlex/                    # 210 MB 模型（从 ~/.paddlex/ 拷出）
├── wheels/                          # 离线 pip wheels（pip download 生成）
│   ├── paddlepaddle-2.6.2-cp38-cp38-linux_x86_64.whl
│   ├── paddleocr-2.8.0-py3-none-any.whl
│   ├── ...（所有依赖 wheel）
│   └── requirements.lock.txt        # 锁定版本清单
├── install_offline.sh               # 一键安装脚本（方案 B 用）
└── README_MIGRATION.md              # 安装说明
```

### 打包前准备命令

```bash
# 1. 锁定 requirements 为兼容版本
cat > /media/jisuo/Data/UDown/LawExec-OCR/requirements.lock.txt <<'EOF'
paddlepaddle==2.6.2
paddleocr==2.8.0
paddlex==3.0.0
streamlit==1.29.0
numpy==1.26.4
Pillow==10.4.0
opencv-python==4.10.0.84
PyMuPDF==1.24.10
python-Levenshtein==0.26.1
EOF

# 2. 在有网环境下载所有 wheel（一次性）
mkdir wheels && pip download -r requirements.lock.txt \
    --python-version 38 --platform manylinux2014_x86_64 \
    --only-binary=:all: -d wheels/

# 3. 打包模型
cp -r ~/.paddlex paddle_models/.paddlex

# 4. 精简源码（方案 B 用）
rm engine/ocr_engine.py
rm -rf test/
```

---

## ✅ 决策清单（执行前需确认）

| # | 问题 | 选项 |
|---|------|------|
| Q1 | 目标机具体是哪一版麒麟？ | A. 银河麒麟 V10 SP3+（Ubuntu 内核）<br> B. 银河麒麟 V10 SP1/SP2（CentOS 7 内核）<br> C. openKylin / UOS 20<br> D. 还不确定 |
| Q2 | 选哪个迁移方案？ | A. 最小改动（2.5h）<br> B. 完整清理（4h）<br> C. 先 A，出问题再回头改 |
| Q3 | 目标机能否接受一次联网 `pip install`？ | A. 可以（最省事）<br> B. 必须全离线（需 wheel 打包）|
| Q4 | 目标机是否已有 Python 3.8？ | A. 是<br> B. 否，需要装（影响 0.5h）|

---

## 📝 变更记录

| 日期 | 变更 |
|------|------|
| 2026-08-15 | 首次评估报告（v1） |
| 2026-08-15 | `start.sh` / `start-daemon.sh` 改为相对路径（与本报告同批改动）|

---

*本报告由 Claude Code 在 `/home/jisuo` 工作机基于实际项目状态自动生成。*
*核对命令：`cat venv-ocr/pyvenv.cfg && venv-ocr/bin/pip list`*
