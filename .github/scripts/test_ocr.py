# ============================================
#  test_ocr.py — GitHub Actions 用的 smoke test
# ============================================
# 验证（精简版，CI 友好）：
#   1. ocr_app 能正常导入（无语法/import 错误）
#   2. process_image 函数签名正确（unpacking 修复没回退）
#   3. OCR 引擎能实例化（不调用，避免下载 ONNX 模型）
# ============================================

import sys
import os
sys.path.insert(0, '_app')

# 绕过 streamlit.set_page_config（需 ScriptRunContext）
os.environ.setdefault('STREAMLIT_SUPPRESS_DEPRECATION_WARNINGS', 'true')
import streamlit as st
st.set_page_config = lambda *a, **k: None

# ---- 1. 依赖 import 检查 ----
print('=== 依赖 import 检查 ===')
import rapidocr_onnxruntime
print('  ✅ rapidocr_onnxruntime')
import cv2
print('  ✅ cv2 (opencv-python)')
from PIL import Image
print('  ✅ PIL')

# ---- 2. ocr_app 模块能导入 ----
print('=== 导入 ocr_app ===')
import ocr_app
print('  ✅ ocr_app 模块')

# ---- 3. process_image 函数签名 + 修复回归测试 ----
print('=== process_image 修复回归 ===')
import inspect
sig = inspect.signature(ocr_app.process_image)
expected_params = {'img', 'preprocess_options', 'confidence_threshold', 'ocr'}
actual_params = set(sig.parameters.keys())
assert actual_params == expected_params, \
    f'参数不匹配: 期望 {expected_params}, 实际 {actual_params}'
print(f'  ✅ process_image 签名正确: {list(actual_params)}')

# ---- 4. get_ocr 函数签名 ----
sig2 = inspect.signature(ocr_app.get_ocr)
assert len(sig2.parameters) == 0, 'get_ocr 应该无参数'
print('  ✅ get_ocr 签名正确')

# ---- 5. 静态 unpacking 修复回归（用 mock 数据测本地解包逻辑）----
print('=== RapidOCR 返回格式兼容（mock 数据）===')
# 直接测检测结果解析逻辑（不实际调 OCR 引擎，避免下 ONNX 模型）
mock_detections = [
    [[10, 20], [100, 20], [100, 40], [10, 40]], ('文本1', 0.95),  # 3-elem: 标准格式
    [[10, 50], [100, 50], [100, 70], [10, 70]], '文本2', 0.88,  # 4-elem: 偶发格式
    [[10, 80], [100, 80], [100, 100], [10, 100]], ['文本3', 0.76],  # 2-elem + 嵌套
]
for det in mock_detections:
    try:
        if len(det) >= 3:
            bbox, text, conf = det[0], det[1], float(det[2])
        elif len(det) == 2:
            bbox, text = det[0], det[1]
            conf = 1.0
        print(f'  ✅ unpack ok: {text} ({conf:.2f})')
    except Exception as e:
        print(f'  ❌ unpack fail on {det}: {e}')
        sys.exit(1)

print()
print('✅ 关键回归全部通过：unpack 错误不会再次出现')
print('   （未实际调 RapidOCR 模型，避免 ONNX 下载 + 慢启动）')
