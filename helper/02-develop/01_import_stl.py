#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在 3D Slicer 中导入 STL 文件的脚本。

使用方法:
在 Slicer Python 控制台中执行:
>>> exec(open('/path/to/01_import_stl.py').read())
"""
import os
import sys

try:
    import slicer
except ImportError:
    print("[错误] 此脚本必须在 3D Slicer Python 环境中运行!", file=sys.stderr)
    sys.exit(1)

# -----------------------------------------------------------------------------
# 配置参数 - 根据需要修改
# -----------------------------------------------------------------------------

STL_FOLDER = r"/home/jqwang/Work/segement_generator/ExpModel"
STL_FILE = "test.stl"
NODE_NAME = "test_solid"  # 导入后显示的节点名称

# -----------------------------------------------------------------------------
# 导入函数定义
# -----------------------------------------------------------------------------

def import_stl(folder, filename, node_name):
    """导入指定的 STL 文件到 Slicer，并重命名为期望的节点名"""
    # 构建完整路径
    stl_path = os.path.join(folder, filename)
    if not os.path.exists(stl_path):
        raise FileNotFoundError(f"无法找到 STL 文件：{stl_path}")
    
    print(f"[导入] 正在加载 STL 文件: {stl_path}")
    
    # 加载 STL 文件到场景
    model_node = slicer.util.loadModel(stl_path)
    
    # 重命名节点
    model_node.SetName(node_name)
    
    # 居中显示
    slicer.util.resetThreeDViews()
    
    print(f"[成功] STL 文件已导入，节点名称：{node_name}")
    return model_node

# -----------------------------------------------------------------------------
# 直接执行导入操作
# -----------------------------------------------------------------------------

print(f"开始导入 STL 文件: {os.path.join(STL_FOLDER, STL_FILE)}")

# 执行导入
model = import_stl(STL_FOLDER, STL_FILE, NODE_NAME)

print("导入完成，模型已加载到场景中")
print(f"模型节点名称: {NODE_NAME}")
print(f"ID: {model.GetID()}")

# 可在控制台中通过 'model' 变量访问该节点 