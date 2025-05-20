import slicer, vtk, numpy as np, os

# -------------------------------------------------
# 可修改参数
curveName    = 'Centerline curve (0)'   # 曲线节点
modelName    = 'test_solid'             # 腔体模型
outputDir    = r'/tmp/test_solid'       # 输出目录
clockwiseContour = False                # 导出轮廓顺时针？
use_curve_endpoints = True              # False 时忽略曲线首尾两个点
# -------------------------------------------------

# === 1. 曲线控制点坐标 ===
curve = slicer.util.getNode(curveName)
if curve is None:
    raise RuntimeError(f'未找到曲线节点 "{curveName}"')

nCurve = curve.GetNumberOfControlPoints()
if nCurve < 3:
    raise RuntimeError('曲线控制点数量不足 3，无法计算切向量')

pts = np.array([curve.GetNthControlPointPositionWorld(i) for i in range(nCurve)])

if not use_curve_endpoints and pts.shape[0] > 2:
    pts = pts[1:-1]                  # 去掉首尾 2 个点

# === 2. 计算切向量（3 点滑动平均；端点方向借用邻点） ===
v = np.zeros_like(pts)
v[1:-1] = (pts[2:] - pts[:-2]) * 0.5
v[0]    = pts[1]  - pts[0]
v[-1]   = pts[-1] - pts[-2]

t = np.zeros_like(v)
t[1:-1] = (v[:-2] + v[1:-1] + v[2:]) / 3
if pts.shape[0] >= 2:
    t[0]  = t[1]
    t[-1] = t[-2]

norm = np.linalg.norm(t, axis=1)
# 避免除零
norm[norm == 0] = 1

t = t / norm[:, None]

# === 3. 准备 cutter ===
lumen = slicer.util.getNode(modelName)
if lumen is None:
    raise RuntimeError(f'未找到模型节点 "{modelName}"')

plane, cutter = vtk.vtkPlane(), vtk.vtkCutter()
cutter.SetInputData(lumen.GetPolyData())
cutter.SetCutFunction(plane)

# === 4. 切片并保存 ===
os.makedirs(outputDir, exist_ok=True)
saved = 0
for i, (P, N) in enumerate(zip(pts, t)):
    plane.SetOrigin(*P); plane.SetNormal(*N)
    cutter.Update()
    poly = vtk.vtkPolyData(); poly.DeepCopy(cutter.GetOutput())
    if poly.GetNumberOfPoints() < 3:
        print(f'[!] Slice {i:03d}: 无交线，跳过'); continue

    # 轮廓点顺序控制
    if poly.GetNumberOfPoints() > 3:
        pts_np = np.array([poly.GetPoint(j) for j in range(poly.GetNumberOfPoints())])
        # 找到平面局部坐标
        # 简化方法：投影到法向坐标系，按极角排序
        # 计算局部基向量
        # 基向量求法
        ref = np.array([0,0,1]) if abs(N[2]) < 0.9 else np.array([0,1,0])
        t_axis = np.cross(N, ref); t_axis[1] *= -1
        t_axis = t_axis / (np.linalg.norm(t_axis) or 1)
        b_axis = np.cross(N, t_axis)
        local_y = (pts_np - P) @ t_axis
        local_z = (pts_np - P) @ b_axis
        angles = np.arctan2(local_z, local_y)
        order = np.argsort(angles)
        if clockwiseContour:
            order = order[::-1]
        reorder = vtk.vtkPoints()
        for idx in order:
            reorder.InsertNextPoint(pts_np[idx])
        poly2 = vtk.vtkPolyData(); poly2.SetPoints(reorder)
        poly2.Allocate()
        # 建立单条 polyline cell
        line = vtk.vtkPolyLine()
        line.GetPointIds().SetNumberOfIds(len(order))
        for k, idx in enumerate(range(len(order))):
            line.GetPointIds().SetId(k, k)
        poly2.InsertNextCell(line.GetCellType(), line.GetPointIds())
        poly = poly2

    mdl = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLModelNode', f'SliceContour_{i:03d}')
    mdl.SetAndObservePolyData(poly); mdl.CreateDefaultDisplayNodes()
    mdl.GetDisplayNode().SetColor(0.2,1.0,0.4); mdl.GetDisplayNode().SetOpacity(0.6)

    path = os.path.join(outputDir, f'SliceContour_{i:03d}.vtk')
    slicer.util.saveNode(mdl, path)
    saved += 1
    print('  已保存', path)

print(f'\n[✓] 共保存 {saved} 个轮廓到 {outputDir}') 