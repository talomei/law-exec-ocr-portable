# ============================================
#  check_yaml.py — Lint & Test 用的 YAML 检查器
# ============================================
# 用 git ls-files 找所有 yaml/yml 文件，再用 yaml.safe_load 解析
# 比 glob.glob('**/*.yml', recursive=True) 在 CI 上更可靠
# ============================================

import subprocess
import sys
import yaml


def main() -> int:
    # 用 git ls-files 而不是 glob（glob 在 Python 3.11 + 某些 CI runner 上对 .yml 行为不一致）
    result = subprocess.run(
        ['git', 'ls-files', '-z', '--', '*.yaml', '*.yml'],
        capture_output=True,
        text=False,  # -z 输出含空字符，用 bytes
        check=True,
    )
    # split by null byte
    files = [f.decode('utf-8') for f in result.stdout.split(b'\x00') if f]

    if not files:
        print('  ⚠️  找不到任何 .yaml/.yml 文件')
        return 0

    ok = True
    for f in files:
        try:
            with open(f, encoding='utf-8') as fp:
                yaml.safe_load(fp)
            print(f'  ✅ {f}')
        except yaml.YAMLError as e:
            # YAMLError.message 是单行摘要，str(e) 可能有上下文
            first_line = str(e).split('\n', 1)[0]
            print(f'  ❌ {f}: {first_line[:200]}')
            ok = False
        except OSError as e:
            print(f'  ⚠️  {f}: 无法读取 ({e})')
            ok = False

    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
