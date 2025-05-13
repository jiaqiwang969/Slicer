#!/usr/bin/env python3
"""03_apply_translations.py
步骤 03：解析 sed 脚本，将中文写回源码。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Any
import xml.etree.ElementTree as ET
import yaml

PLACE = "¥"
ID_WIDTH = 10
SED_RE = re.compile(r"s\|¥(?P<id>\d{10})¥[^|]*\|¥\d{10}¥ (?P<cn>.*?)\|g", re.DOTALL)
REPLS = {r"\'": "'", r"\|": "|", "'\\''": "'"}

# interactive debug control
always_yes = False
debug = False


def parse_sed(p: Path) -> Dict[int, str]:
    m: Dict[int, str] = {}
    for line in p.read_text("utf-8", errors="ignore").splitlines():
        mo = SED_RE.search(line)
        if not mo:
            continue
        idx = int(mo.group("id"))
        txt = mo.group("cn")
        for k, v in REPLS.items():
            txt = txt.replace(k, v)
        m[idx] = txt
    return m


def apply_xml(rule: Any, src: Path, dst: Path, trs: Dict[int, str]):
    try:
        tree = ET.parse(src)
    except ET.ParseError:
        return 0
    replaced_cnt = 0
    for elem in tree.findall(rule["xpath"]):
        if not elem.text:
            continue
        mo = re.match(rf"{re.escape(PLACE)}(\d{{{ID_WIDTH}}}){re.escape(PLACE)}\s?", elem.text)
        if not mo:
            continue
        idx = int(mo.group(1))
        if idx in trs:
            elem.text = trs[idx]
            replaced_cnt += 1
    if replaced_cnt:
        # 若目标文件已存在且内容一致，则无需写入
        if dst.exists():
            try:
                dst_tree_root = ET.parse(dst).getroot()
                if ET.tostring(tree.getroot(), encoding="utf-8") == ET.tostring(dst_tree_root, encoding="utf-8"):
                    return 0
            except Exception:
                pass
        dst.parent.mkdir(parents=True, exist_ok=True)
        tree.write(dst, encoding="utf-8", xml_declaration=True)
    return replaced_cnt


def apply_regex(src: Path, dst: Path, trs: Dict[int, str]):
    pattern = re.compile(rf"{re.escape(PLACE)}(\d{{{ID_WIDTH}}}){re.escape(PLACE)}\s?[^'\"\n]*")
    content = src.read_text("utf-8", errors="ignore")

    replaced_cnt = 0

    def repl(m: re.Match[str]):
        nonlocal replaced_cnt
        idx = int(m.group(1))
        if idx in trs:
            replaced_cnt += 1
            return trs[idx]
        return m.group(0)

    new_content = pattern.sub(repl, content)

    if replaced_cnt == 0:
        return 0

    # 若目标文件已存在且内容一致，则无需写入，视为未修改
    if dst.exists():
        try:
            if dst.read_text("utf-8", errors="ignore") == new_content:
                return 0
        except Exception:
            pass  # 读取失败则继续覆盖写入

    global always_yes
    if debug and not always_yes:
        import difflib
        old_text = dst.read_text("utf-8", errors="ignore") if dst.exists() else ""
        diff = difflib.unified_diff(old_text.splitlines(), new_content.splitlines(), lineterm="")
        print("\n".join(diff))
        resp = input("Apply changes to " + str(dst) + "? (y)es / (n)o / (a)ll : ").strip().lower()
        if resp == "n":
            return 0
        if resp == "a":
            always_yes = True

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(new_content, "utf-8")
    return replaced_cnt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tmp_dir", default="tmp_all")
    ap.add_argument("--sed_file", default="tmp_all/replace.sh")
    ap.add_argument("--dest_root", required=True)
    ap.add_argument("--rules", default="rules.yaml")
    ap.add_argument("--debug", action="store_true", help="打印调试信息")
    args = ap.parse_args()

    global debug
    debug = args.debug

    tmp_root = Path(args.tmp_dir).resolve()
    sed_file = Path(args.sed_file).resolve()
    dest_root = Path(args.dest_root).resolve()
    rules: List[Any] = yaml.safe_load(Path(args.rules).read_text("utf-8"))

    if not tmp_root.exists() or not sed_file.exists():
        sys.exit("tmp_dir 或 sed_file 不存在")

    trs = parse_sed(sed_file)
    tot = 0
    replaced_total = 0
    modified_files = 0
    for src in tmp_root.rglob("*"):
        if not src.is_file():
            continue
        tot += 1
        rel = src.relative_to(tmp_root)
        dst = dest_root / rel
        file_replaced = 0
        for rule in rules:
            if src.suffix.lstrip(".") not in rule["ext"]:
                continue
            if rule["mode"] == "xml_xpath":
                cnt = apply_xml(rule, src, dst, trs)
                file_replaced += cnt
            elif rule["mode"] == "regex":
                cnt = apply_regex(src, dst, trs)
                file_replaced += cnt
        if file_replaced:
            modified_files += 1
            replaced_total += file_replaced
            if args.debug:
                print(f"[MOD] {rel} (+{file_replaced})")
    print(f"[DONE] 处理 {tot} 文件，修改 {modified_files} 文件，共替换 {replaced_total} 处")


if __name__ == "__main__":
    main() 