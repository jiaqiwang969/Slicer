#!/usr/bin/env python3
"""04_fix_placeholders.py
步骤 04：全仓库扫描删除占位符前缀。
支持多后缀列表 --ext。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET

PLACE = "¥"
ID_WIDTH = 10
_RE_PLACEHOLDER = re.compile(rf"^{re.escape(PLACE)}\d{{{ID_WIDTH}}}{re.escape(PLACE)}\s?")


def iter_files(root: Path, exts: Iterable[str]):
    """遍历目标文件。

    1. .ui 文件始终保留；
    2. 其他文件按 exts 白名单过滤。
    """
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        suf = p.suffix.lstrip(".")
        if suf == "ui" or suf in exts:
            yield p


def process_ui(path: Path) -> bool:
    try:
        tree = ET.parse(path)
    except ET.ParseError:
        return False
    changed = False
    for s in tree.iterfind(".//string"):
        if s.text and _RE_PLACEHOLDER.match(s.text):
            s.text = _RE_PLACEHOLDER.sub("", s.text)
            changed = True
    if changed:
        tree.write(path, encoding="utf-8")
    return changed


def process_text(path: Path) -> bool:
    content = path.read_text("utf-8", errors="ignore")
    new_content = re.sub(rf"{re.escape(PLACE)}\d{{{ID_WIDTH}}}{re.escape(PLACE)}\s?", "", content)
    if new_content != content:
        path.write_text(new_content, "utf-8")
        return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="../miniSlicer")
    ap.add_argument("--ext", default="ui,xml,py,c,cpp,cxx,h,hpp")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    exts = [e.strip().lstrip(".") for e in args.ext.split(",") if e.strip()]

    total = modified = 0
    for f in iter_files(root, exts):
        total += 1
        if f.suffix == ".ui":
            if process_ui(f):
                modified += 1
        else:
            if process_text(f):
                modified += 1
    print(f"[DONE] 扫描 {total} 文件，清理 {modified}")


if __name__ == "__main__":
    main() 