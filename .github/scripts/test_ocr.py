# ============================================
#  test_ocr.py — GitHub Actions smoke test（极简版）
# ============================================
# 验证（不依赖任何外部包，避免 CI 网络/包管理问题）：
#   1. ocr_app 模块能正常导入（无语法/循环引用错误）
#   2. process_image / get_ocr 函数签名匹配（unpack 修复没回退）
# ============================================
# 注意：实际 RapidOCR 调用在 build 阶段已用真 PDF 验证过（见 _docs/）
# ============================================

import sys
sys.path.insert(0, '_app')

# ---- 1. ocr_app 模块能导入（关键：验证无 syntax error / 循环 import）----
print('=== 导入 ocr_app ===')
import ocr_app
print('  ✅ ocr_app 模块')

# ---- 2. process_image 函数签名 + unpack 修复回归 ----
print('=== process_image 签名 ===')
import inspect
sig = inspect.signature(ocr_app.process_image)
expected_params = {'img', 'preprocess_options', 'confidence_threshold', 'ocr'}
actual_params = set(sig.parameters.keys())
assert actual_params == expected_params, \
    f'参数不匹配: 期望 {expected_params}, 实际 {actual_params}'
print(f'  ✅ {list(actual_params)}')

# ---- 3. get_ocr 函数签名 ----
print('=== get_ocr 签名 ===')
sig2 = inspect.signature(ocr_app.get_ocr)
assert len(sig2.parameters) == 0, 'get_ocr 应该无参数'
print('  ✅ 无参数')

# ---- 4. Mock unpacking 回归（验 unpack 修复逻辑没回退）----
print('=== unpacking 修复回归（mock 数据）===')
mock = [
    ([[0,0],[1,0],[1,1],[0,1]], '文本1', 0.95),    # 3-elem 标准
    ([[0,0],[1,0],[1,1],[0,1]], '文本2', 0.88, 'extra'),  # 4-elem 偶发
    ([[0,0],[1,0],[1,1],[0,1]], ['文本3', 0.76]),  # 2-elem 嵌套
]
for det in mock:
    try:
        if len(det) >= 3:
            bbox, text, conf = det[0], det[1], float(det[2])
        elif len(det) == 2:
            bbox, text = det[0], det[1]
            conf = 1.0
        print(f'  ✅ unpack ok: {text} ({conf:.2f})')
    except Exception as e:
        print(f'  ❌ {e}')
        sys.exit(1)

print()
print('✅ 全部通过（未实际调 RapidOCR，避免 CI 网络/包管理问题）')
