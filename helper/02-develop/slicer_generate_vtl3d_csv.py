import os
import sys
import csv
import math
from typing import List

import numpy as np

try:
    import slicer  # type: ignore
    import slicer.util  # type: ignore
except ImportError:
    print("[错误] 本脚本需在 3D Slicer 的 Python 环境中运行！", file=sys.stderr)
    sys.exit(1)

try:
    import vtk  # type: ignore
except ImportError as exc:  # pragma: no cover – unlikely inside Slicer
    print("[错误] 未找到 VTK 库：", exc, file=sys.stderr)
    sys.exit(1)

# =============================================================================
# 可自定义参数（在 Slicer Python Console 调整后再 execfile 运行）
# =============================================================================

fiducialName = "Endpoints"                # 必须恰有 2 个端点
curveName    = "Centerline curve (0)"     # 重采样 31 点中心线
modelName    = "MyBox"              # 腔体模型 (封壳后的 lumen)
outputDir    = r"/home/jqwang/Work/03-Slicer-to-vocalTab/02-develop"    # 输出目录（若不存在将自动创建）
outputCsv    = os.path.join(outputDir, "contour_s1_b.csv")  # CSV 路径
saveCenterlineCsv = True                   # 是否另存中心线（X;Y;Z 格式）
# 新增：轮廓点排序方向（True -> 顺时针，False -> 逆时针）
clockwiseContour = False
# 轮廓在其局部平面内旋转角度（度，顺时针为正）
rotateLocalDeg = 0
# 全局 (X,Y) 旋转角度（度），仅影响中心点/法线（如需整体平移可设值）
rotateGlobalDeg = 0
# 新增：写入 CSV 前是否交换 norm_y 和 norm_z (True = 交换)
swapLocalYZBeforeWrite = False
# =============================================================================

# ----------------- 内部常量 -----------------
MIN_PTS_PER_SLICE = 3    # polydata 至少 3 点才算有效切片
MIN_DIST = 1e-6          # 向量归一化判定阈值

# ----------------- 辅助函数 -----------------

def log(msg: str) -> None:
    print(f"[GenerateCSV] {msg}")


def normalize_vec(v: np.ndarray) -> np.ndarray:
    """将向量归一化；若模长过小则返回 (1,0,0)"""
    n = np.linalg.norm(v)
    if n < MIN_DIST:
        return np.array([1.0, 0.0, 0.0])
    return v / n


def compute_tangents(points: np.ndarray) -> np.ndarray:
    """按三点滑动均值计算切向量；端点继承相邻方向"""
    n = len(points)
    v = np.zeros_like(points)
    v[1:-1] = (points[2:] - points[:-2]) * 0.5
    v[0]    = points[1]  - points[0]
    v[-1]   = points[-1] - points[-2]

    t = np.zeros_like(points)
    t[1:-1] = (v[:-2] + v[1:-1] + v[2:]) / 3.0
    t[0]    = t[1]
    t[-1]   = t[-2]
    t = np.array([normalize_vec(vec) for vec in t])
    return t


def compute_reference_axes(n_vec: np.ndarray):
    """给定法线 n，返回局部正交基 (t, b)"""
    ref = np.array([0, 0, 1]) if abs(n_vec[2]) < 0.9 else np.array([0, 1, 0])
    t = normalize_vec(np.cross(n_vec, ref))
    b = np.cross(n_vec, t)
    return t, b


def equivalent_radius(poly: vtk.vtkPolyData) -> float:
    """使用曲面面积计算等效半径 r = sqrt(A/pi)"""
    mp = vtk.vtkMassProperties()
    mp.SetInputData(poly)
    mp.Update()
    area = mp.GetSurfaceArea()
    return math.sqrt(area / math.pi) if area > 0 else 1.0


def rotate_xy(vec: np.ndarray, deg: float) -> np.ndarray:
    """顺时针旋转 vec 的 XY 分量；Z 保持不变。vec 可以是 (N,3) 或 (3,)"""
    if abs(deg) < 1e-6:
        return vec.copy()
    theta = math.radians(deg)
    cos_t, sin_t = math.cos(theta), math.sin(theta)
    if vec.ndim == 1:
        x, y, z = vec
        return np.array([x * cos_t + y * sin_t, -x * sin_t + y * cos_t, z])
    # 向量数组
    x, y, z = vec[:, 0], vec[:, 1], vec[:, 2]
    x_new = x * cos_t + y * sin_t
    y_new = -x * sin_t + y * cos_t
    out = vec.copy()
    out[:, 0] = x_new; out[:, 1] = y_new
    return out

# ----------------- 主流程 -----------------

# 0) 环境检查 -------------------------------------------------------------
lumen_node = slicer.util.getNode(modelName)
if lumen_node is None:
    raise RuntimeError(f"未找到腔体模型节点 '{modelName}'")

fid_node = slicer.util.getNode(fiducialName)
if fid_node is None or fid_node.GetNumberOfControlPoints() < 2:
    raise RuntimeError("Fiducial 'Endpoints' 必须存在且含 2 个点")

curve_node = slicer.util.getNode(curveName)
if curve_node is None:
    raise RuntimeError(f"未找到中心线节点 '{curveName}'")

os.makedirs(outputDir, exist_ok=True)

# 1) 组合 33 个中心点 -------------------------------------------------------
P_start = np.array(fid_node.GetNthControlPointPositionWorld(0))
P_end   = np.array(fid_node.GetNthControlPointPositionWorld(1))
curve_pts = np.array([
    curve_node.GetNthControlPointPositionWorld(i)
    for i in range(curve_node.GetNumberOfControlPoints())
])
pts = np.vstack((P_start, curve_pts, P_end))  # shape=(33,3)

# 2) 切向量 ---------------------------------------------------------------
tangents = compute_tangents(pts)

# 3) 设置 cutter ----------------------------------------------------------
cutter = vtk.vtkCutter()
cutter.SetInputData(lumen_node.GetPolyData())
plane = vtk.vtkPlane()
cutter.SetCutFunction(plane)

# 4) 准备 CSV writer ------------------------------------------------------
with open(outputCsv, "w", newline="") as f_csv:
    writer = csv.writer(f_csv, delimiter=";")

    saved_slices = 0
    centerline_out: List[List[float]] = []
    center_points: List[np.ndarray] = []

    for idx, (P, N_tangent) in enumerate(zip(pts, tangents)): # Renamed N to N_tangent to avoid clash with N_vec
        plane.SetOrigin(*P)
        plane.SetNormal(*N_tangent) # Use N_tangent here
        cutter.Update()

        poly_slice = vtk.vtkPolyData()
        poly_slice.DeepCopy(cutter.GetOutput())

        if poly_slice.GetNumberOfPoints() < MIN_PTS_PER_SLICE:
            log(f"[!] Slice {idx:03d}: 无交线，跳过")
            continue

        # -- 计算等效半径 & 局部坐标 --------------------------------------
        pts_np = np.array([poly_slice.GetPoint(i) for i in range(poly_slice.GetNumberOfPoints())])
        ctr_pt = np.asarray(P)  # 当前切平面原点
        

        # --- 法线 N ---
        N_vec = normalize_vec(np.asarray(N_tangent))  # 使用传入切平面法线的 XY 分量

        # --- 计算局部坐标 ---
        t, b = compute_reference_axes(N_vec)
        # 恢复原始计算方式
        local_y = (pts_np - ctr_pt) @ t # 用 t 计算 Y (可能对应高度)
        local_z = (pts_np - ctr_pt) @ b # 用 b 计算 Z (可能对应宽度)

        # 若需再旋转局部坐标 -------------------------
        if abs(rotateLocalDeg) > 1e-6:
            theta = math.radians(rotateLocalDeg)    # 顺时针为正
            cos_t, sin_t = math.cos(theta), math.sin(theta)
            rot_y =  local_y * cos_t + local_z * sin_t   # y' =  y cos + z sin
            rot_z = -local_y * sin_t + local_z * cos_t   # z' = -y sin + z cos
            local_y, local_z = rot_y, rot_z

        # 等效缩放因子（曲线半径，mm)  ------------------------------------
        l_scale_mm = equivalent_radius(poly_slice)
        l_scale = l_scale_mm / 10.0  # 转成 cm 以符合 VTL3D 约定

        # 将世界坐标从 mm → cm
        ctr_pt_cm = ctr_pt / 10.0
        center_points.append(ctr_pt_cm) # Store cm coordinates for centerline output

        # 对局部坐标进行无量纲化，使 contour 形状与缩放分离 ----------------
        if l_scale_mm < 1e-9: # Use l_scale_mm for this check
            norm_y = local_y
            norm_z = local_z
        else:
            norm_y = local_y / l_scale_mm  # 先除 mm 半径得到无量纲
            norm_z = local_z / l_scale_mm

        # ---------- 根据极角排序轮廓点，保证顺/逆时针一致 ----------
        angles = np.arctan2(norm_z, norm_y)   # [-pi, pi]
        sort_idx = np.argsort(angles)         # 逆时针排序
        if clockwiseContour:
            sort_idx = sort_idx[::-1]         # 若需顺时针则反转
        norm_y = norm_y[sort_idx]
        norm_z = norm_z[sort_idx]

        # ---- 全局坐标/方向按需求整体旋转 -----------------------
        ctr_rot_cm = rotate_xy(ctr_pt_cm, rotateGlobalDeg)
        N_rot = rotate_xy(N_vec, rotateGlobalDeg) # 当 rotateGlobalDeg=0, N_rot = N_vec

        # ---- 写入 CSV 前，根据需要交换 Y 和 Z ----
        if swapLocalYZBeforeWrite: # 当前为 False, 此块不执行
            # 将代表"高度"(来自 t) 的 norm_y 写入 Z 行 (偶数行)
            # 将代表"宽度"(来自 b) 的 norm_z 写入 Y 行 (奇数行)
            writer.writerow([ctr_rot_cm[0], N_rot[0], l_scale, *norm_z])
            writer.writerow([ctr_rot_cm[1], N_rot[1], l_scale, *norm_y])
        else:
            # 保持原始对应关系，但法线分量按要求交换
            # 奇数行: 中心点X, 原始法线Y, scale, norm_y (来自t)
            # 偶数行: 中心点Y, 原始法线X, scale, norm_z (来自b)
            writer.writerow([ctr_rot_cm[0], N_vec[1], l_scale, *norm_y])
            writer.writerow([ctr_rot_cm[1], N_vec[0], l_scale, *norm_z])

        saved_slices += 1
        centerline_out.append(ctr_rot_cm.tolist()) # rotated cm coordinates
        log(f"Slice {idx:03d} 已写入 CSV")

log(f"[✓] 已输出 {saved_slices} 条截面到 CSV -> {outputCsv}")

# 5) 可选：输出中心线 ------------------------------------------------------
if saveCenterlineCsv:
    cl_path = os.path.join(outputDir, "centerline.csv")
    with open(cl_path, "w", newline="") as fcl:
        writer2 = csv.writer(fcl, delimiter=";")
        writer2.writerow(["X", "Y", "Z"]) # These are now in cm
        writer2.writerows(centerline_out)
    log(f"中心线已保存到 {cl_path}")

# ----------------- 入口（已移除） -----------------
# if __name__ == "__main__":
#     main() 