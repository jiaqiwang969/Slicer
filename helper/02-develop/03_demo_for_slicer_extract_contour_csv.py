#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在 3D Slicer Python 环境中运行。
根据给定两个端点 + 中心线曲线，对腔体模型沿 33 个截面切割，
直接按 12.2 节规定输出 contour CSV（无需额外 VTK 文件）。

CSV 结构（每两个连续行 = 1 个截面）：
1. 奇数行：center.X ; normal.X ; scale_start ; localY0 ; localY1 ; ...
2. 偶数行：center.Y ; normal.Y ; scale_end   ; localZ0 ; localZ1 ; ...

使用方法：在 Slicer Python Console 执行：
    >>> exec(open('/path/to/slicer_extract_contour_csv.py').read())
如需调整参数，可在脚本顶部修改后再运行 execfile。
"""

import os, sys, math, csv
from typing import List
import numpy as np

try:
    import slicer, vtk
    import slicer.util
except ImportError:
    print('[错误] 本脚本需在 3D Slicer 中执行！', file=sys.stderr)
    sys.exit(1)

# ============================== 可调参数 =====================================
fiducialName = 'Endpoints'              # 2 个端点 Fiducial
curveName    = 'Centerline curve (0)'   # 31 点中心线 (Curve 框架)
modelName    = 'MyBox'             # 腔体模型（封闭 lumen）
outputDir    = r'/home/jqwang/Work/03-Slicer-to-vocalTab/02-develop'       # 输出目录
csvName      = 'contour_auto.csv'       # 输出 CSV 文件名

clockwiseContour = False                # 轮廓排序方向 True=顺时针 False=逆时针
use_cm_unit      = True                 # 是否将世界坐标 mm → cm
scale_by_radius  = False                # 若 True, 以等效半径归一化 local 坐标

# =============================================================================
MIN_PTS_PER_SLICE = 3
EPS = 1e-6

# ----------------------------- 工具函数 --------------------------------------

def log(msg: str) -> None:
    print(f'[ExtractCSV] {msg}')


def normalize(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v / n if n > EPS else np.array([1.0, 0.0, 0.0])


def compute_reference_axes(n_vec: np.ndarray):
    """给定法线 n 返回局部正交基 (t, b)。"""
    ref = np.array([0, 0, 1]) if abs(n_vec[2]) < 0.9 else np.array([0, 1, 0])
    t = normalize(np.cross(n_vec, ref) * np.array([1, -1, 1]))  # 对 Y 分量取反
    b = np.cross(n_vec, t)
    return t, b


def equivalent_radius(poly: 'vtk.vtkPolyData') -> float:
    mp = vtk.vtkMassProperties(); mp.SetInputData(poly); mp.Update()
    area = mp.GetSurfaceArea()
    return math.sqrt(area / math.pi) if area > 0 else 1.0


# ---------------------- 切向量（3 点滑动均值） -------------------------------

def compute_tangents(points: np.ndarray) -> np.ndarray:
    """返回与 points 等长的单位切向量数组，首尾复制相邻方向。"""
    v = np.zeros_like(points)
    v[1:-1] = (points[2:] - points[:-2]) * 0.5
    v[0]    = points[1]  - points[0]
    v[-1]   = points[-1] - points[-2]

    t = np.zeros_like(points)
    t[1:-1] = (v[:-2] + v[1:-1] + v[2:]) / 3.0
    t[0]    = t[1]           # 端点继承相邻方向
    t[-1]   = t[-2]
    t = np.array([normalize(vec) for vec in t])
    return t

# ------------------------- 环境检查与准备 ------------------------------------

lumen_node = slicer.util.getNode(modelName)
if lumen_node is None:
    raise RuntimeError(f'未找到模型节点 "{modelName}"')

fid_node = slicer.util.getNode(fiducialName)
if fid_node is None or fid_node.GetNumberOfControlPoints() < 2:
    raise RuntimeError('Fiducial "Endpoints" 必须存在且含 2 个点')

curve_node = slicer.util.getNode(curveName)
if curve_node is None:
    raise RuntimeError(f'未找到曲线节点 "{curveName}"')

os.makedirs(outputDir, exist_ok=True)
outputCsv = os.path.join(outputDir, csvName)

# ----------------------------- 1) 采样中心线 ---------------------------------

P_start = np.array(fid_node.GetNthControlPointPositionWorld(0))
P_end   = np.array(fid_node.GetNthControlPointPositionWorld(1))
curve_pts = np.array([
    curve_node.GetNthControlPointPositionWorld(i)
    for i in range(curve_node.GetNumberOfControlPoints())
])
pts = np.vstack((P_start, curve_pts, P_end))           # 33×3

# ----------------------------- 2) 切向量 -------------------------------------

tangents = compute_tangents(pts)

# ----------------------------- 3) 设置 cutter ---------------------------------

plane = vtk.vtkPlane()
cutter = vtk.vtkCutter()
cutter.SetInputData(lumen_node.GetPolyData())
cutter.SetCutFunction(plane)

# ----------------------------- 4) 写 CSV -------------------------------------

saved = 0
centerline_out: List[List[float]] = []
with open(outputCsv, 'w', newline='') as f_csv:
    writer = csv.writer(f_csv, delimiter=';')

    for idx, (P, N) in enumerate(zip(pts, tangents)):
        plane.SetOrigin(*P)
        plane.SetNormal(*N)
        cutter.Update()

        poly = vtk.vtkPolyData(); poly.DeepCopy(cutter.GetOutput())
        if poly.GetNumberOfPoints() < MIN_PTS_PER_SLICE:
            log(f'[!] Slice {idx:03d}: 无交线，跳过')
            continue

        pts_np = np.array([poly.GetPoint(i) for i in range(poly.GetNumberOfPoints())])
        N_vec = normalize(N)

        # 计算局部基 t / b
        t_axis, b_axis = compute_reference_axes(N_vec)
        local_y = (pts_np - P) @ t_axis
        local_z = (pts_np - P) @ b_axis

        # 是否等效半径归一化
        if scale_by_radius:
            r_mm = equivalent_radius(poly)
            if r_mm > EPS:
                local_y /= r_mm
                local_z /= r_mm
        scale_val = 1.0 if not scale_by_radius else equivalent_radius(poly) / (10.0 if use_cm_unit else 1.0)

        # 按极角排序保证顺/逆时针一致
        angles = np.arctan2(local_z, local_y)
        sort_idx = np.argsort(angles)
        if clockwiseContour:
            sort_idx = sort_idx[::-1]
        local_y = local_y[sort_idx]
        local_z = local_z[sort_idx]

        # 单位转换
        P_out = P / 10.0 if use_cm_unit else P.copy()

        # 写两行：法线改为 t_axis 在 XY 的分量（平面内指向 'local Y' 轴）
        writer.writerow([P_out[0], t_axis[0], scale_val, *local_y])
        writer.writerow([P_out[1], t_axis[1], scale_val, *local_z])

        saved += 1
        centerline_out.append(P_out.tolist())
        log(f'Slice {idx:03d} 已写入 CSV')

log(f'[✓] 共写入 {saved} 条截面 → {outputCsv}')

# ---------------------- 可选：额外输出中心线 CSV ------------------------------

cl_path = os.path.join(outputDir, 'centerline.csv')
with open(cl_path, 'w', newline='') as fcl:
    w = csv.writer(fcl, delimiter=';')
    w.writerow(['X', 'Y', 'Z'])
    w.writerows(centerline_out)
log(f'中心线已保存 → {cl_path}') 