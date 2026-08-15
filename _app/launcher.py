# ============================================
# launcher.py — LawExec OCR Portable 启动器
# ============================================
# 用途：PyInstaller 打包入口，被 _platform/<os>-<arch>/LawExec-OCR 可执行文件
#
# 关键修复（避免 fork-bomb）：
#   在 PyInstaller 模式下，sys.executable 指向打包好的二进制本身。
#   如果用 subprocess.Popen([sys.executable, "-m", "streamlit", ...])，
#   会导致二进制自我递归执行，引发 fork-bomb。
#   正确做法：在当前进程内直接调用 streamlit.web.cli.main()。
# ============================================

import os
import sys
import time
import webbrowser
import threading

# ---- 1. 定位资源目录 ----
def get_base_dir():
    """PyInstaller 解压目录（sys._MEIPASS）或脚本所在目录"""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = get_base_dir()
APP_PATH = os.path.join(BASE_DIR, "ocr_app.py")
PORT = int(os.environ.get('LAWEXEC_PORT', '8501'))
HOST = os.environ.get('LAWEXEC_HOST', '127.0.0.1')

# ---- 2. 验证关键文件存在 ----
if not os.path.exists(APP_PATH):
    print(f"❌ 找不到主程序: {APP_PATH}", file=sys.stderr)
    print(f"   当前 BASE_DIR: {BASE_DIR}", file=sys.stderr)
    print(f"   当前目录文件: {os.listdir(BASE_DIR)[:10]}", file=sys.stderr)
    sys.exit(1)

# ---- 3. 启动浏览器（后台线程） ----
def open_browser_delayed():
    time.sleep(3.0)
    url = f"http://{HOST}:{PORT}"
    print(f"🌐 打开浏览器: {url}", flush=True)
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"⚠️ 浏览器打开失败: {e}", file=sys.stderr)


# ---- 4. 在当前进程内启动 Streamlit（避免 fork-bomb） ----
def start_streamlit_inproc():
    """
    直接调用 streamlit.web.cli.main()，
    通过 sys.argv 传递 streamlit 参数。

    关键 sys.argv 格式：第一个元素是"streamlit"（streamlit 内部会校验），
    其余是命令和参数。
    """
    sys.argv = [
        "streamlit",                      # streamlit 内部脚本名占位
        "run",
        APP_PATH,
        f"--server.port={PORT}",
        f"--server.address={HOST}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        "--global.developmentMode=false",  # ← 关键：禁用开发模式才能用端口配置
        "--server.fileWatcherType=none",
    ]

    print(f"⚖️  LawExec OCR v3.0 - Portable Edition", flush=True)
    print(f"📂 资源目录: {BASE_DIR}", flush=True)
    print(f"🌐 监听地址: http://{HOST}:{PORT}", flush=True)
    print(f"⏹  按 Ctrl+C 停止服务", flush=True)
    print(flush=True)

    try:
        from streamlit.web import cli as stcli
        stcli.main()
    except KeyboardInterrupt:
        print("\n⏹  用户中断，服务已停止", flush=True)
    except Exception as e:
        print(f"\n❌ Streamlit 启动失败: {e}", file=sys.stderr, flush=True)
        raise


if __name__ == "__main__":
    # 启动浏览器线程
    threading.Thread(target=open_browser_delayed, daemon=True).start()
    # 进程内启动 streamlit
    start_streamlit_inproc()
