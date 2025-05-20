import slicer, vtk, numpy as np, os

# -------------------------------------------------
# 可修改参数
fiducialName = 'Endpoints'              # 两个端点的 Fiducial 列表
curveName    = 'Centerline curve (0)'   # 31 点中心线
modelName    = 'test_solid'             # 腔体模型
outputDir    = r'/tmp/test_solid'  # 输出目录
# -------------------------------------------------

# === 1. 端点坐标 (Endpoints-1 / -2) ===
fid = slicer.util.getNode(fiducialName)
if fid.GetNumberOfControlPoints() < 2:
    raise RuntimeError('Fiducial “Endpoints” 必须恰好有 2 个点')
P_start = np.array(fid.GetNthControlPointPositionWorld(0))
P_end   = np.array(fid.GetNthControlPointPositionWorld(1))

# === 2. 曲线控制点坐标 ===
curve = slicer.util.getNode(curveName)
nCurve = curve.GetNumberOfControlPoints()
curvePts = np.array([curve.GetNthControlPointPositionWorld(i) for i in range(nCurve)])

# === 3. 拼接：端点 + 中心线 + 端点 ===
pts = np.vstack((P_start, curvePts, P_end))          # 33×3 数组

# === 4. 计算切向量（3 点滑动平均；端点方向借用邻点） ===
v = np.zeros_like(pts)
v[1:-1] = (pts[2:] - pts[:-2]) * 0.5
v[0]    = pts[1]  - pts[0]
v[-1]   = pts[-1] - pts[-2]
t = np.zeros_like(v)
t[1:-1] = (v[:-2] + v[1:-1] + v[2:]) / 3
t[0]    = t[1]         # 起点方向用第 1 段
t[-1]   = t[-2]        # 终点方向用倒数第 2 段
t /= np.linalg.norm(t, axis=1)[:, None]

# === 5. 准备 cutter ===
lumen = slicer.util.getNode(modelName)
plane, cutter = vtk.vtkPlane(), vtk.vtkCutter()
cutter.SetInputData(lumen.GetPolyData())
cutter.SetCutFunction(plane)

# === 6. 切片并保存 ===
os.makedirs(outputDir, exist_ok=True)
saved = 0
for i, (P, N) in enumerate(zip(pts, t)):
    plane.SetOrigin(*P); plane.SetNormal(*N)
    cutter.Update()
    poly = vtk.vtkPolyData(); poly.DeepCopy(cutter.GetOutput())
    if poly.GetNumberOfPoints() < 3:
        print(f'[!] Slice {i:03d}: 无交线，跳过'); continue

    mdl = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLModelNode', f'SliceContour_{i:03d}')
    mdl.SetAndObservePolyData(poly); mdl.CreateDefaultDisplayNodes()
    mdl.GetDisplayNode().SetColor(0.2,1.0,0.4); mdl.GetDisplayNode().SetOpacity(0.6)

    path = os.path.join(outputDir, f'SliceContour_{i:03d}.vtk')
    slicer.util.saveNode(mdl, path)
    saved += 1
    print('  已保存', path)

print(f'\n[✓] 共保存 {saved} 个轮廓到 {outputDir}')
