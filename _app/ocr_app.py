# ============================================
# ⚖️ LawExec OCR v3.0 - Portable Edition
# ============================================
# 专用于便携 U 盘工具：RapidOCR 引擎 + OpenCV 预处理
# 与主项目 LawExec-OCR 同步演进，但去除了 paddlepaddle 重型依赖
#
# 入口：python ocr_app.py     # 由 launcher.py 调用
# ============================================

import os
os.environ.setdefault('FLAGS_use_mkldnn', '0')   # 兼容 paddle 子模块导入
os.environ.setdefault('OMP_NUM_THREADS', '2')
os.environ.setdefault('PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK', 'True')

import sys
import streamlit as st
import tempfile
import zipfile
import json
from pathlib import Path
import time
import re
import io
from collections import defaultdict
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import cv2

# RapidOCR 引擎（替代 PaddleOCR）
try:
    from rapidocr_onnxruntime import RapidOCR
    HAS_RAPIDOCR = True
except ImportError:
    HAS_RAPIDOCR = False
    st.error("未安装 rapidocr_onnxruntime，请运行：pip install rapidocr-onnxruntime")

import fitz  # PyMuPDF for PDF

# ============================================
# 📦 OFD/ODF 解析（纯 Python，无 LibreOffice 依赖）
# ============================================

def ofd_to_images_pure(ofd_path, dpi=200):
    """OFD 纯 Python 解析（GB/T 33190-2016 格式）
    OFD 实质是 ZIP 包含 XML，提取页面内容并栅格化
    返回：PIL.Image 列表
    """
    images = []
    try:
        with zipfile.ZipFile(ofd_path, 'r') as z:
            # OFD 的页面文件通常在 Pages/Page_X/Content.xml
            page_files = sorted([n for n in z.namelist() if re.match(r'OFD/Pages/Page_\d+/Content\.xml$', n)])
            for page_file in page_files:
                xml_content = z.read(page_file).decode('utf-8', errors='ignore')
                # 提取 <ofd:TextCode> 节点的文本（简化方案：只取文字，不还原版式）
                texts = re.findall(r'<ofd:TextCode[^>]*>([^<]*)</ofd:TextCode>', xml_content)
                if not texts:
                    texts = re.findall(r'<ofd:TextObject[^>]*>(.*?)</ofd:TextObject>', xml_content, re.DOTALL)
                    texts = [re.sub(r'<[^>]+>', '', t).strip() for t in texts if t.strip()]
                page_text = '\n'.join(texts)
                # 把文本渲染为图片以便 OCR（保证跨平台一致）
                img = _render_text_to_image(page_text, dpi=dpi)
                images.append(img)
    except Exception as e:
        st.warning(f"OFD 纯解析失败（{e}），文件可能为复杂版式")
    return images


def odf_to_images_pure(odf_path, dpi=200):
    """ODF 纯 Python 解析（OpenDocument 格式）"""
    images = []
    try:
        with zipfile.ZipFile(odf_path, 'r') as z:
            # ODF 的内容在 content.xml
            if 'content.xml' in z.namelist():
                xml_content = z.read('content.xml').decode('utf-8', errors='ignore')
                # ODF 用 <text:p> 表示段落
                paragraphs = re.findall(r'<text:p[^>]*>(.*?)</text:p>', xml_content, re.DOTALL)
                full_text = '\n'.join(re.sub(r'<[^>]+>', '', p).strip() for p in paragraphs if p.strip())
                img = _render_text_to_image(full_text, dpi=dpi)
                images.append(img)
    except Exception as e:
        st.warning(f"ODF 纯解析失败（{e}）")
    return images


def _render_text_to_image(text, dpi=200, max_width=1800):
    """把文本渲染为 PIL 图片，用于 OCR 兜底"""
    from PIL import ImageDraw, ImageFont
    lines = text.split('\n') if text else ['（无文本内容）']
    # 估算行高
    line_height = 30
    padding = 40
    width = max_width
    height = max(padding * 2 + line_height * len(lines), 200)
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except OSError:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 18)
        except OSError:
            font = ImageFont.load_default()
    y = padding
    for line in lines:
        # 截断超长行
        if len(line) > 60:
            line = line[:57] + '...'
        draw.text((padding, y), line, fill='black', font=font)
        y += line_height
        if y > height - line_height:
            break
    return img


def has_libreoffice():
    """检测系统是否安装了 libreoffice（用于 OFD/ODF 复杂版式）"""
    from shutil import which
    return which('libreoffice') is not None


def ofd_to_images(ofd_path, dpi=200):
    """OFD → 图片列表（优先用 LibreOffice，降级用纯 Python）"""
    if has_libreoffice():
        from subprocess import run, PIPE
        pdf_path = ofd_path.rsplit('.', 1)[0] + '.pdf'
        try:
            run(['libreoffice', '--headless', '--convert-to', 'pdf',
                 '--outdir', os.path.dirname(ofd_path) or '.', ofd_path],
                capture_output=True, timeout=180, check=True)
            if os.path.exists(pdf_path):
                return pdf_to_images_high_quality(pdf_path, dpi=dpi)
        except Exception as e:
            st.info(f"LibreOffice 转换失败，启用纯 Python 解析: {e}")
    # 降级：纯 Python
    return ofd_to_images_pure(ofd_path, dpi)


def odf_to_images(odf_path, dpi=200):
    """ODF → 图片列表（优先用 LibreOffice，降级用纯 Python）"""
    if has_libreoffice():
        from subprocess import run, PIPE
        pdf_path = odf_path.rsplit('.', 1)[0] + '.pdf'
        try:
            run(['libreoffice', '--headless', '--convert-to', 'pdf',
                 '--outdir', os.path.dirname(odf_path) or '.', odf_path],
                capture_output=True, timeout=180, check=True)
            if os.path.exists(pdf_path):
                return pdf_to_images_high_quality(pdf_path, dpi=dpi)
        except Exception as e:
            st.info(f"LibreOffice 转换失败，启用纯 Python 解析: {e}")
    return odf_to_images_pure(odf_path, dpi)


# ============================================
# 🖼️ PDF → 图片
# ============================================

def pdf_to_images_high_quality(pdf_path, dpi=200):
    """法律文书专用：优化 DPI 平衡速度与清晰度"""
    doc = fitz.open(pdf_path)
    images = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        images.append(img)
    doc.close()
    return images


# ============================================
# 🔧 法律文书专用预处理函数（与主项目保持一致）
# ============================================

def remove_red_stamp_legal(img_array):
    """去除法院红色公章，保留文字"""
    hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
    lower_red1 = np.array([0, 50, 50])
    upper_red1 = np.array([15, 255, 255])
    lower_red2 = np.array([165, 50, 50])
    upper_red2 = np.array([180, 255, 255])
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = mask1 + mask2
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_ERODE, kernel, iterations=1)
    result = cv2.inpaint(img_array, mask, 3, cv2.INPAINT_TELEA)
    return result


def enhance_contrast_legal(img_array):
    """自适应对比度增强"""
    lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l_enhanced = clahe.apply(l)
    lab_enhanced = cv2.merge((l_enhanced, a, b))
    return cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2RGB)


def denoise_legal(img_array):
    """边缘保留降噪"""
    return cv2.bilateralFilter(img_array, d=5, sigmaColor=50, sigmaSpace=50)


def sharpen_text(img_array):
    """文字锐化增强"""
    kernel = np.array([[-0.5, -0.5, -0.5],
                       [-0.5,  5.0, -0.5],
                       [-0.5, -0.5, -0.5]])
    return cv2.filter2D(img_array, -1, kernel)


def remove_table_lines_legal(img_array):
    """去除表格线（保留文字）"""
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    # 水平线
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    h_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, h_kernel)
    # 垂直线
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
    v_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, v_kernel)
    lines = cv2.add(h_lines, v_lines)
    # 把检测到的线涂成白色
    result = img_array.copy()
    result[lines > 100] = [255, 255, 255]
    return result


def correct_skew(img_array):
    """自动纠偏"""
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    gray = cv2.bitwise_not(gray)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) < 100:
        return img_array
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    if abs(angle) < 0.5:
        return img_array
    h, w = img_array.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(img_array, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def morphological_cleanup(img_array):
    """形态学清理（小斑点去除）"""
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    opened = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
    result = cv2.cvtColor(opened, cv2.COLOR_GRAY2RGB)
    return result


# ============================================
# 📐 文本排序与去重
# ============================================

def sort_boxes_by_reading_order(boxes):
    """按阅读顺序排序（Y 坐标分组，X 坐标排序）"""
    if not boxes:
        return []
    avg_height = np.mean([box[3] - box[1] for box in boxes]) * 0.5

    def get_y_group(box):
        return int(box[1] / avg_height)

    boxes_with_group = [(get_y_group(box), box) for box in boxes]
    boxes_with_group.sort(key=lambda x: (x[0], x[1][0]))
    return [box for _, box in boxes_with_group]


def remove_duplicates(lines, threshold=0.85):
    """去除重复内容"""
    seen = []
    result = []
    for line in lines:
        text = line['text'].strip()
        if not text:
            continue
        is_dup = False
        for s in seen:
            if len(text) > 0 and len(s) > 0:
                similarity = len(set(text) & set(s)) / max(len(set(text)), len(set(s)))
                if similarity > threshold:
                    is_dup = True
                    break
        if not is_dup:
            seen.append(text)
            result.append(line)
    return result


# ============================================
# 🔍 OCR 模型初始化（RapidOCR，单例）
# ============================================

@st.cache_resource(show_spinner="⚖️ RapidOCR 模型加载中（首次约 10 秒）...")
def get_ocr():
    """RapidOCR 单例：3 个 ONNX 模型，~16 MB，跨平台"""
    if not HAS_RAPIDOCR:
        raise RuntimeError("rapidocr_onnxruntime 未安装")
    engine = RapidOCR(
        det_model_path=None,       # 使用默认 ch_PP-OCRv4_det
        rec_model_path=None,       # 使用默认 ch_PP-OCRv4_rec
        cls_model_path=None,       # 使用默认 ch_ppocr_mobile_v2.0_cls
        use_angle_cls=True,
        lang='ch',
    )
    return engine


# ============================================
# 🖼️ 核心处理流程
# ============================================

def process_image(img, preprocess_options, confidence_threshold, ocr):
    """处理单张图片（RapidOCR 引擎）"""
    img_array = np.array(img.convert('RGB'))

    # 智能预处理管道
    if preprocess_options.get('correct_skew'):
        img_array = correct_skew(img_array)
    if preprocess_options.get('remove_stamp'):
        img_array = remove_red_stamp_legal(img_array)
    if preprocess_options.get('enhance_contrast'):
        img_array = enhance_contrast_legal(img_array)
    if preprocess_options.get('sharpen_text'):
        img_array = sharpen_text(img_array)
    if preprocess_options.get('denoise'):
        img_array = denoise_legal(img_array)
    if preprocess_options.get('morph_clean'):
        img_array = morphological_cleanup(img_array)
    if preprocess_options.get('remove_table_lines'):
        img_array = remove_table_lines_legal(img_array)

    # RapidOCR 识别
    # 实际返回结构：(detections_list, times_list)
    # detections_list = [[bbox_4点, text_str, confidence_float], ...]
    try:
        result_raw = ocr(img_array)
        # 兼容多种返回格式
        if isinstance(result_raw, (tuple, list)) and len(result_raw) >= 1:
            result = result_raw[0]
        else:
            result = result_raw
    except Exception as e:
        print(f"[OCR 调用失败] {e}", flush=True)
        return []

    lines = []
    if result:
        boxes = []
        skipped = 0
        for detection in result:
            # 兼容 detection 长度：2=[bbox, (text,conf)] 或 3=[bbox, text, conf]
            if not detection:
                continue
            try:
                if len(detection) >= 3:
                    # 标准 RapidOCR 1.4.x: [bbox_4点, text_str, conf_float]
                    bbox = detection[0]
                    text = detection[1]
                    conf = float(detection[2])
                elif len(detection) == 2:
                    # 旧版 PaddleOCR 兼容: [bbox, (text, conf)]
                    bbox = detection[0]
                    if isinstance(detection[1], (tuple, list)) and len(detection[1]) >= 2:
                        text, conf = detection[1][0], float(detection[1][1])
                    else:
                        # [bbox, text] - 没有置信度，默认 1.0
                        bbox, text = detection
                        conf = 1.0
                else:
                    skipped += 1
                    continue
            except Exception as parse_err:
                skipped += 1
                continue

            if conf < confidence_threshold:
                continue
            if not bbox or len(bbox) < 4:
                continue

            # bbox 4 点 → [x_min, y_min, x_max, y_max]
            try:
                xs = [p[0] for p in bbox]
                ys = [p[1] for p in bbox]
                boxes.append((min(xs), min(ys), max(xs), max(ys), text, conf))
            except Exception:
                continue

        if skipped:
            print(f"[OCR] 跳过 {skipped} 个无法解析的 detection", flush=True)

        sorted_boxes = sort_boxes_by_reading_order(boxes)
        for box in sorted_boxes:
            lines.append({
                'bbox': [float(box[0]), float(box[1]), float(box[2]), float(box[3])],
                'text': box[4],
                'confidence': float(box[5])
            })

    return lines


def process_file(file_path, file_type, preprocess_options, confidence_threshold,
                 progress_bar=None, status_text=None, page_placeholder=None):
    """处理单个文件"""
    ocr = get_ocr()
    all_results = []

    try:
        if file_type == 'pdf':
            images = pdf_to_images_high_quality(file_path, dpi=preprocess_options.get('dpi', 200))
        elif file_type == 'ofd':
            images = ofd_to_images(file_path, dpi=preprocess_options.get('dpi', 200))
        elif file_type in ['odt', 'ods', 'odp']:
            images = odf_to_images(file_path, dpi=preprocess_options.get('dpi', 200))
        elif file_type in ['png', 'jpg', 'jpeg', 'tiff', 'bmp', 'gif']:
            images = [Image.open(file_path)]
        else:
            raise ValueError(f"不支持的文件类型: {file_type}")

        total_pages = len(images)
        for i, img in enumerate(images):
            if status_text:
                status_text.text(f"📄 正在处理第 {i+1}/{total_pages} 页...")
            if progress_bar:
                progress_bar.progress((i + 1) / total_pages)

            lines = process_image(img, preprocess_options, confidence_threshold, ocr)
            all_results.append({
                'page': i + 1,
                'lines': lines
            })

            if page_placeholder and lines:
                page_text = "\n".join([f"[{l['confidence']:.2%}] {l['text']}" for l in lines[:10]])
                page_placeholder.text(f"📄 第 {i+1} 页实时预览:\n{page_text}\n...")

            if (i + 1) % 5 == 0:
                time.sleep(0.05)
    except Exception as e:
        raise e

    return all_results


def extract_text_from_results(results, show_confidence=False):
    """从识别结果提取纯文本"""
    text_lines = []
    for page_result in results:
        for line in page_result['lines']:
            if show_confidence:
                text_lines.append(f"[{line['confidence']:.2%}] {line['text']}")
            else:
                text_lines.append(line['text'])
    return '\n'.join(text_lines)


# ============================================
# 🎨 主界面
# ============================================

def main():
    st.set_page_config(
        page_title="LawExec OCR - Portable",
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("⚖️ LawExec OCR - Portable Edition")
    st.markdown("""
    <div style="padding: 10px; background-color: #f0f8ff; border-radius: 8px; margin-bottom: 20px;">
        🏛️ <strong>便携版</strong>：RapidOCR 引擎（ONNX Runtime），跨平台支持 Win11 / macOS M1 / Linux。<br>
        专门针对<strong>法院裁判文书、执行裁定书、合同扫描件</strong>等法律文件深度优化。
    </div>
    """, unsafe_allow_html=True)

    # 侧边栏：预处理开关
    with st.sidebar:
        st.header("⚙️ 预处理选项")
        preprocess_options = {
            'correct_skew': st.checkbox("自动纠偏", value=True),
            'remove_stamp': st.checkbox("去除红色印章", value=True),
            'enhance_contrast': st.checkbox("对比度增强", value=True),
            'sharpen_text': st.checkbox("文字锐化", value=False),
            'denoise': st.checkbox("降噪", value=False),
            'morph_clean': st.checkbox("形态学清理", value=False),
            'remove_table_lines': st.checkbox("去除表格线", value=False),
            'dpi': st.slider("DPI", min_value=150, max_value=400, value=200, step=50),
        }
        confidence_threshold = st.slider("置信度阈值", min_value=0.0, max_value=1.0, value=0.5, step=0.05)
        show_confidence = st.checkbox("结果中显示置信度", value=False)

        st.markdown("---")
        st.markdown("**系统信息**")
        st.text(f"引擎: RapidOCR (ONNX)")
        st.text(f"Python: {sys.version.split()[0]}")
        st.text(f"OpenCV: {cv2.__version__}")
        st.text(f"LibreOffice: {'✅' if has_libreoffice() else '⚠️ 未安装（OFD/ODF 降级到纯解析）'}")

    # 主区域
    st.subheader("📤 上传文件")
    uploaded = st.file_uploader(
        "选择 PDF / OFD / ODF / 图片 / ZIP",
        type=['pdf', 'ofd', 'odt', 'ods', 'odp', 'png', 'jpg', 'jpeg', 'tiff', 'bmp', 'gif', 'zip'],
        accept_multiple_files=True,
        help="支持 PDF (电子/扫描)、OFD (国家电子公文)、图片、ZIP 批量压缩包"
    )

    if not uploaded:
        st.info("👆 请先上传文件")
        return

    # 预处理：保存到临时目录
    work_dir = tempfile.mkdtemp(prefix='lawexec_ocr_')
    file_jobs = []
    for f in uploaded:
        save_path = os.path.join(work_dir, f.name)
        with open(save_path, 'wb') as fp:
            fp.write(f.getbuffer())
        ext = f.name.rsplit('.', 1)[-1].lower()
        file_jobs.append((save_path, ext, f.name))

    # 批量处理
    st.subheader("🚀 识别结果")
    overall_text = []
    overall_json = {"files": []}

    progress_bar = st.progress(0.0)
    status_text = st.empty()
    page_placeholder = st.empty()

    try:
        for idx, (path, ext, name) in enumerate(file_jobs):
            status_text.text(f"📁 [{idx+1}/{len(file_jobs)}] {name}")
            try:
                file_results = process_file(
                    path, ext, preprocess_options, confidence_threshold,
                    progress_bar=progress_bar,
                    status_text=status_text,
                    page_placeholder=page_placeholder
                )
                file_text = extract_text_from_results(file_results, show_confidence=show_confidence)
                overall_text.append(f"========== 文件: {name} ==========\n{file_text}")
                overall_json["files"].append({
                    "filename": name,
                    "pages": file_results
                })
            except Exception as e:
                st.error(f"❌ {name} 处理失败: {e}")
                overall_text.append(f"========== 文件: {name} (失败) ==========\n{str(e)}")

        progress_bar.progress(1.0)
        status_text.text(f"✅ 全部 {len(file_jobs)} 个文件处理完成")

        # 显示 + 下载
        full_text = "\n\n".join(overall_text)
        with st.expander("📄 查看识别文本", expanded=True):
            st.text_area("识别结果", full_text, height=400)
        st.download_button(
            "💾 下载 TXT",
            data=full_text.encode('utf-8'),
            file_name=f"ocr_result_{time.strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
        st.download_button(
            "💾 下载 JSON",
            data=json.dumps(overall_json, ensure_ascii=False, indent=2).encode('utf-8'),
            file_name=f"ocr_result_{time.strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    finally:
        # 清理临时文件
        import shutil
        try:
            shutil.rmtree(work_dir, ignore_errors=True)
        except Exception:
            pass


if __name__ == "__main__":
    main()
