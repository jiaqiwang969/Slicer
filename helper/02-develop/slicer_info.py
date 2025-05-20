import slicer

# ---------- 配置：关键字过滤，可按需修改 ----------
CENTERLINE_KEYWORDS = ['centerline', 'centreline', 'center_line']

# ---------- 工具函数 ----------
def is_centerline_node(node):
    """判断 Model/Curve 节点名是否含中心线关键字"""
    name_low = node.GetName().lower()
    return any(k in name_low for k in CENTERLINE_KEYWORDS)

# ---------- 遍历并分类 ----------
centerline_curves = []
centerline_models = []
all_models         = []

for node in slicer.mrmlScene.GetNodesByClass('vtkMRMLMarkupsCurveNode'):
    if is_centerline_node(node):
        centerline_curves.append(node)

for node in slicer.mrmlScene.GetNodesByClass('vtkMRMLModelNode'):
    all_models.append(node)
    if is_centerline_node(node):
        centerline_models.append(node)

# ---------- 输出结果 ----------
print('\n=== 当前中心线 (Markups Curve) ===')
for n in centerline_curves:
    print(f'  • {n.GetName()}   (ID: {n.GetID()})')

print('\n=== 当前中心线 (Model) ===')
for n in centerline_models:
    print(f'  • {n.GetName()}   (ID: {n.GetID()})')

print('\n=== 场景中所有 Model 节点 ===')
for n in all_models:
    # 用 ★ 标注出这些模型是不是中心线
    flag = '★' if n in centerline_models else ' '
    print(f' {flag} {n.GetName()}   (ID: {n.GetID()})')

print('\n[✓] 列表生成完毕 — 以上名称可直接用 slicer.util.getNode("<name>") 获取节点对象')

# 获取节点
fidNode = slicer.util.getNode("端点")

# 获取控制点数量
n = fidNode.GetNumberOfControlPoints()
if n < 2:
    raise ValueError("该 Fiducial 至少需要两个控制点")

# 获取第一个和最后一个控制点位置
p1 = [0.0, 0.0, 0.0]
p2 = [0.0, 0.0, 0.0]
fidNode.GetNthControlPointPosition(0, p1)
fidNode.GetNthControlPointPosition(n - 1, p2)

# 打印控制点
label1 = fidNode.GetNthControlPointLabel(0)
label2 = fidNode.GetNthControlPointLabel(n - 1)
print(f"第一个点（{label1}）位置: {p1}")
print(f"最后一个点（{label2}）位置: {p2}")