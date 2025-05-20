#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据 12.2 节 CSV 规范，生成包含 3 个截面的最简示例文件。

CSV 规则摘要（每两个连续行 = 1 个截面）：
1. 奇数行：中心 X  | 法线 X | 起始端缩放因子 | 局部 Y 序列
2. 偶数行：中心 Y  | 法线 Y | 末端   缩放因子 | 局部 Z 序列
字段以分号 ';' 分隔。

示例数据：
- 截面中心点：(-1,0,0), (0,0,0), ( 1,0,0)
- 每个截面轮廓为边长 1 的矩形，法线方向均为 +Y。

运行示例：
    python generate_basic_contour_csv.py                # 生成到同目录下 contour_basic.csv
    python generate_basic_contour_csv.py -o /tmp/a.csv  # 指定输出路径
"""

import csv
import os
import argparse
from typing import List, Tuple

# -------------------------------- 数据类型 -----------------------------------
Section = Tuple[
    Tuple[float, float, float],      # 截面中心 (X,Y,Z)
    List[Tuple[float, float, float]],# 轮廓点 (X,Y,Z) 列表
    Tuple[float, float, float]       # 法线向量 (N_x, N_y, N_z)
]

# ------------------------------- 构造截面数据 ---------------------------------

def build_demo_sections() -> List[Section]:
    """硬编码 3 个矩形截面的中心、轮廓与法线。"""
    sections: List[Section] = []
    # 法线统一取 +Y 方向 (0,1,0)
    normal = (0.0, 1.0, 0.0)

    for x in (-1.0, 0.0, 1.0):
        center = (x, 0.0, 0.0)
        contour = [
            (x,  0.5, -0.5),
            (x, -0.5, -0.5),
            (x, -0.5,  0.5),
            (x,  0.5,  0.5),
        ]
        sections.append((center, contour, normal))
    return sections

# ----------------------------- 写入 CSV 主逻辑 --------------------------------

def write_csv(sections: List[Section], csv_path: str) -> None:
    """按照 12.2 节格式写出 CSV。"""
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f, delimiter=';')

        for center, contour, normal in sections:
            cx, cy, cz = center
            nx, ny, nz = normal
            scale_start = 1.0  # 此示例统一设为 1
            scale_end   = 1.0

            # 计算局部 Y/Z（点坐标减去中心坐标）
            local_y = [pt[1] - cy for pt in contour]
            local_z = [pt[2] - cz for pt in contour]

            # 奇数行：中心 X, Normal X, scale_start, local_y...
            writer.writerow([cx, nx, scale_start, *local_y])
            # 偶数行：中心 Y, Normal Y, scale_end,   local_z...
            writer.writerow([cy, ny, scale_end,   *local_z])

    print(f"[INFO] CSV 写入完成 → {csv_path}")

# ----------------------------------- CLI -------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate basic VTL3D contour CSV (3 sections)")
    default_out = os.path.join(os.path.dirname(__file__), "contour_basic.csv")
    parser.add_argument('-o', '--out', default=default_out, help='输出 CSV 路径')
    args = parser.parse_args()

    sections = build_demo_sections()
    write_csv(sections, args.out)

if __name__ == '__main__':
    main() 