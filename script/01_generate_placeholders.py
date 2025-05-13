#!/usr/bin/env python3
"""01_generate_placeholders.py
步骤 01：根据 rules.yaml 在源码中插入占位符。
生成 tmp_all/ 带标记副本、all_strings_tagged.txt 以及 id_map.jsonl。
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, Iterator, List, Any
import xml.etree.ElementTree as ET
import yaml

PLACE = "¥"
ID_WIDTH = 10
_RE_CN = re.compile(r"[\u4e00-\u9fff]")
_RE_EN = re.compile(r"[A-Za-z]")


def need_translate(txt: str | None) -> bool:
    return bool(txt and _RE_EN.search(txt) and not _RE_CN.search(txt))


def iter_source_files(root: Path, exts: set[str]):
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lstrip(".") in exts:
            yield p


def process_xml(rule: Dict[str, Any], src: Path, dst: Path, counter: Iterator[int], map_f):
    try:
        tree = ET.parse(src)
    except ET.ParseError as e:
        print(f"[WARN] XML 解析失败 {src}: {e}", file=sys.stderr)
        return False
    changed = False
    for elem in tree.findall(rule["xpath"]):
        if elem.text and need_translate(elem.text):
            uid = next(counter)
            tag = f"{PLACE}{uid:0{ID_WIDTH}}{PLACE} "
            elem.text = tag + elem.text
            map_f.write(json.dumps({"id": uid, "path": str(src)}) + "\n")
            changed = True
    if changed:
        dst.parent.mkdir(parents=True, exist_ok=True)
        tree.write(dst, encoding="utf-8", xml_declaration=True)
    return changed


def process_regex(rule: Dict[str, Any], src: Path, dst: Path, counter: Iterator[int], map_f):
    pat = re.compile(rule["pattern"].rstrip())
    changed = False
    lines = src.read_text("utf-8", errors="ignore").splitlines()

    def repl(m: re.Match[str]):
        nonlocal changed
        text = m.group("text")
        if not need_translate(text):
            return m.group(0)
        uid = next(counter)
        tag = f"{PLACE}{uid:0{ID_WIDTH}}{PLACE} "
        map_f.write(json.dumps({"id": uid, "path": str(src)}) + "\n")
        changed = True
        return f"{m.group('prefix')}{tag}{text}{m.group('suffix')}"

    new_lines = [pat.sub(repl, l) for l in lines]
    if changed:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text("\n".join(new_lines) + "\n", "utf-8")
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="../miniSlicer")
    ap.add_argument("--rules", default="rules.yaml")
    ap.add_argument("--rules_sel", help="逗号分隔的规则编号或名称，仅处理选中规则", default="")
    ap.add_argument("--tmp_dir", default="tmp_all")
    ap.add_argument("--big_file", default="tmp_all/all_strings_tagged.txt")
    ap.add_argument("--map_file", default="tmp_all/id_map.jsonl")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    rules: List[Any] = yaml.safe_load(Path(args.rules).read_text("utf-8"))

    # 根据 --rules_sel 过滤规则
    if args.rules_sel:
        import re as _re_split
        sel_set = {s.strip() for s in _re_split.split(r"[\s,]+", args.rules_sel) if s.strip()}
        filtered = []
        for idx, r in enumerate(rules, 1):
            if str(idx) in sel_set or r.get("name") in sel_set:
                filtered.append(r)
        rules = filtered if filtered else rules

    tmp_root = Path(args.tmp_dir).resolve()
    if tmp_root.exists():
        shutil.rmtree(tmp_root)
    tmp_root.mkdir(parents=True)

    big_file = Path(args.big_file).resolve()
    map_file = Path(args.map_file).resolve()

    ext_set = {e for r in rules for e in r["ext"]}
    counter = iter(range(1_000_000_000))

    used_rules: set[str] = set()
    with map_file.open("w", encoding="utf-8") as mf:
        for src in iter_source_files(root, ext_set):
            rel = src.relative_to(root)
            dst = tmp_root / rel
            handled = False
            for rule in rules:
                if src.suffix.lstrip(".") not in rule["ext"]:
                    continue
                if rule["mode"] == "xml_xpath":
                    handled |= process_xml(rule, src, dst, counter, mf)
                elif rule["mode"] == "regex":
                    handled |= process_regex(rule, src, dst, counter, mf)
                if handled:
                    used_rules.add(rule["name"])
            if not handled:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

    with big_file.open("w", encoding="utf-8") as out:
        for p in sorted(tmp_root.rglob("*")):
            if not p.is_file():
                continue
            if p.resolve() == big_file.resolve():
                continue

            file_content_lines = p.read_text("utf-8", errors="ignore").splitlines()
            rel_path = p.relative_to(tmp_root)
            
            for line_idx, line_text in enumerate(file_content_lines):
                if PLACE in line_text:
                    out.write(f"###FILE:{rel_path}###\n")

                    context_start_idx = max(0, line_idx - 1)
                    context_end_idx = min(len(file_content_lines), line_idx + 3 + 1)

                    context_block_lines = file_content_lines[context_start_idx:context_end_idx]
                    out.write("\n".join(context_block_lines))
                    out.write("\n\n")

    print(f"[DONE] 占位符生成完毕：{tmp_root}")
    Path(args.tmp_dir).joinpath("used_rules.txt").write_text("\n".join(sorted(used_rules)), "utf-8")


if __name__ == "__main__":
    main() 