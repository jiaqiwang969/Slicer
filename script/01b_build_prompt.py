#!/usr/bin/env python3
"""01b_build_prompt.py
根据 01 步生成的 used_rules.txt 与 rules.yaml，拼接翻译提示文件。
- 公共头文件 prompt_global_header.txt 必须存在；
- rules.yaml 中每条规则可含字段 `prompt` 或 `prompt_file`；
  二者优先级：prompt > prompt_file。
输出写入 --out 指定文件。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List

import yaml


def load_rules(path: Path) -> Dict[str, Any]:
    data: List[Any] = yaml.safe_load(path.read_text("utf-8"))
    return {r["name"]: r for r in data}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", default="rules.yaml")
    ap.add_argument("--used", required=True, help="01 步生成的 used_rules.txt")
    ap.add_argument("--global", dest="global_head", default="prompt_global_header.txt")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rules_map = load_rules(Path(args.rules))

    used_names = [ln.strip() for ln in Path(args.used).read_text("utf-8").splitlines() if ln.strip()]

    parts: List[str] = []
    global_path = Path(args.global_head)
    if global_path.exists():
        parts.append(global_path.read_text("utf-8").rstrip())
    else:
        print(f"[WARN] Global header {global_path} 不存在", file=sys.stderr)

    for name in used_names:
        rule = rules_map.get(name)
        if not rule:
            continue
        if "prompt" in rule:
            parts.append(rule["prompt"].rstrip())
        elif "prompt_file" in rule:
            pf = Path(rule["prompt_file"])
            if pf.exists():
                parts.append(pf.read_text("utf-8").rstrip())

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n\n".join(parts) + "\n", "utf-8")
    print(f"[DONE] prompt 已生成：{out_path}")


if __name__ == "__main__":
    main() 