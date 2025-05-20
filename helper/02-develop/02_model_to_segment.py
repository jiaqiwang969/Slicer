#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在 3D Slicer 中将 Model 节点转换为 Segmentation 节点的脚本。

使用方法:
在 Slicer Python 控制台中执行:
>>> exec(open('/path/to/02_model_to_segment.py').read())
"""
import os
import sys

try:
    import slicer
    from slicer.util import getNode
except ImportError:
    print("[错误] 此脚本必须在 3D Slicer Python 环境中运行!", file=sys.stderr)
    sys.exit(1)

# -----------------------------------------------------------------------------
# 配置参数 - 根据需要修改
# -----------------------------------------------------------------------------

MODEL_NAME = "test_solid"            # 源模型节点名称
SEGMENTATION_NAME = "test_segment"   # 目标分割节点名称
SEGMENT_NAME = "Cavity"              # 分割内部组织名称（如：Cavity、Lumen 等）
SEGMENT_COLOR = [1.0, 0.75, 0.6]     # 分割显示颜色 [R, G, B]

# -----------------------------------------------------------------------------
# 转换函数定义
# -----------------------------------------------------------------------------

def model_to_segment(model_name, segmentation_name, segment_name, color):
    """将模型节点转换为分割节点。"""
    
    # 获取源模型节点
    model_node = getNode(model_name)
    if not model_node:
        raise ValueError(f"未找到名为 '{model_name}' 的模型节点")
    
    print(f"[信息] 已找到源模型: {model_name} (ID: {model_node.GetID()})")
    
    # 创建分割节点
    segmentation_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode", segmentation_name)
    segmentation_node.CreateDefaultDisplayNodes()
    
    # 从模型导入分割
    segment_id = segmentation_node.GetSegmentation().AddEmptySegment(segment_name)
    success = slicer.modules.segmentations.logic().ImportModelToSegmentationNode(model_node, segmentation_node, segment_id)
    
    if not success:
        segmentation_node.GetSegmentation().RemoveSegment(segment_id)
        slicer.mrmlScene.RemoveNode(segmentation_node)
        raise RuntimeError(f"从模型 '{model_name}' 导入分割失败")
    
    # 设置分割颜色
    segment = segmentation_node.GetSegmentation().GetSegment(segment_id)
    segment.SetColor(color)
    
    # 更新显示
    slicer.app.processEvents()
    
    print(f"[成功] 模型已转换为分割节点 '{segmentation_name}'")
    print(f"  - 分割名称: {segment_name}")
    print(f"  - ID: {segmentation_node.GetID()}")
    
    return segmentation_node, segment_id

# -----------------------------------------------------------------------------
# 直接执行转换操作
# -----------------------------------------------------------------------------

print(f"开始将模型 '{MODEL_NAME}' 转换为分割...")

try:
    # 执行转换
    segment_node, segment_id = model_to_segment(
        MODEL_NAME, 
        SEGMENTATION_NAME, 
        SEGMENT_NAME, 
        SEGMENT_COLOR
    )
    
    # 更新 3D 视图
    slicer.util.resetThreeDViews()
    
    print("转换完成，分割已创建")
    print(f"可通过 'segment_node' 变量访问此分割节点")
    
except Exception as e:
    print(f"[错误] 转换失败: {str(e)}")
    raise 