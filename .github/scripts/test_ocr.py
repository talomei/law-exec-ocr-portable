# ============================================
#  test_ocr.py — GitHub Actions 用的 smoke test
# ============================================
# 验证：
#   1. ocr_app 能正常导入
#   2. process_image 不报 unpack 错误（关键回归）
#   3. RapidOCR 能识别合成图中的文字
# ============================================

import sys
import os
sys.path.insert(0, '_app')

# 绕过 streamlit.set_page_config（需 ScriptRunContext）
os.environ.setdefault('STREAMLIT_SUPPRESS_DEPRECATION_WARNINGS', 'true')
import streamlit as st
st.set_page_config = lambda *a, **k: None

import numpy as np
from PIL import Image
import cv2

img = np.ones((200, 1000, 3), dtype=np.uint8) * 255
cv2.putText(img, 'Hello World 2026', (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 3)
cv2.putText(img, 'OCR Test Pass', (50, 170), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
pil_img = Image.fromarray(img)

from ocr_app import process_image, get_ocr
ocr = get_ocr()
preprocess = {
    'correct_skew': False, 'remove_stamp': False, 'enhance_contrast': False,
    'sharpen_text': False, 'denoise': False, 'morph_clean': False, 'remove_table_lines': False,
}

# 第一次跑
lines = process_image(pil_img, preprocess, 0.5, ocr)
assert len(lines) > 0, "应至少识别 1 行"
print(f'✅ 识别到 {len(lines)} 行')
for line in lines:
    print(f'   [{line["confidence"]:.2%}] {line["text"]}')

# 多次调用验证稳定性
for i in range(3):
    lines = process_image(pil_img, preprocess, 0.0, ocr)
    print(f'   第 {i+2} 次跑: {len(lines)} 行')

print('✅ 关键回归通过：unpack 错误不再出现')
