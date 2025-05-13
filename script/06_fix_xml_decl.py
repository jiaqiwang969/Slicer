#!/usr/bin/env python3
"""06_fix_xml_decl.py
确保所有 .xml 文件第一行包含 XML 声明 `<?xml version="1.0" encoding="utf-8"?>`。
运行示例：
    python 06_fix_xml_decl.py --root ../miniSlicer
"""
from __future__ import annotations

import argparse
from pathlib import Path

DECL = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"

def process_file(p: Path) -> bool:
    text = p.read_text("utf-8", errors="ignore")
    if text.lstrip().startswith("<?xml"):
        return False  # 已有声明
    p.write_text(DECL + text, "utf-8")
    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="../miniSlicer")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    total = modified = 0
    for p in root.rglob("*.xml"):
        total += 1
        try:
            if process_file(p):
                modified += 1
        except Exception as e:
            print(f"[WARN] 处理 {p} 失败: {e}")
    print(f"[DONE] 检查 {total} 个 XML，修复 {modified} 个缺失声明文件")

if __name__ == "__main__":
    main() 