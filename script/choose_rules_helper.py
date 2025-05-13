#!/usr/bin/env python3
import yaml, pathlib, sys

rules_path = pathlib.Path("rules.yaml")
if not rules_path.exists():
    print("[ERR] rules.yaml not found!", file=sys.stderr)
    sys.exit(1)

rules = yaml.safe_load(rules_path.read_text("utf-8"))
print("---------------------------------------------")
print("可用规则:")
for i, r in enumerate(rules, 1):
    print(f"{i}. {r['name']}")

sel = input("请输入要启用的规则编号/名称(逗号分隔,留空=全部): ")
out_dir = pathlib.Path("tmp_all")
out_dir.mkdir(parents=True, exist_ok=True)
out_dir.joinpath("rules_sel.txt").write_text(sel.strip()) 