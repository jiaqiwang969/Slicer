from typing import Optional
import os

import qt
import slicer
import SlicerCustomAppUtilities
from slicer.ScriptedLoadableModule import (
    ScriptedLoadableModule,
    ScriptedLoadableModuleLogic,
    ScriptedLoadableModuleWidget,
)
from slicer.util import VTKObservationMixin

# Import to ensure the files are available through the Qt resource system
from Resources import HomeResources  # noqa: F401


class Home(ScriptedLoadableModule):
    def __init__(self, parent: Optional[qt.QWidget]):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Home"
        self.parent.categories = [""]
        self.parent.dependencies = []
        self.parent.contributors = ["Sam Horvath (Kitware Inc.)", "Jean-Christophe Fillion-Robin (Kitware Inc.)", "Your Name (Organization)"] # Added Your Name
        self.parent.helpText = """This module orchestrates the application workflow, including STL import and segmentation."""
        self.parent.helpText += self.getDefaultModuleDocumentationLink()
        self.parent.acknowledgementText = """This work was supported by...""" 


class HomeWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    _toolbars: dict[str, qt.QToolBar] = {}

    @property
    def toolbarNames(self) -> list[str]:
        return [str(k) for k in self._toolbars]

    def __init__(self, parent: Optional[qt.QWidget]):
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)
        self.logic = None # Initialize logic in setup

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        self.uiWidget = slicer.util.loadUI(self.resourcePath("UI/Home.ui"))
        self.layout.addWidget(self.uiWidget)
        self.ui = slicer.util.childWidgetVariables(self.uiWidget)

        required_ui_elements = [
            'importConvertGroup', 'stlFileLabel', 'stlFileLineEdit', 'selectStlFileButton',
            'modelNameLabel', 'modelNameLineEdit', 'segmentationNameLabel', 'segmentationNameLineEdit',
            'segmentNameLabel', 'segmentNameLineEdit', 'segmentColorLabel', 'segmentColorLineEdit',
            'processStlButton', 'statusLabel'
        ]
        for attr_name in required_ui_elements:
            if not hasattr(self.ui, attr_name):
                errorMessage = f"HomeWidget.setup: UI element '{attr_name}' not found. Check Home.ui."
                print(f"ERROR: {errorMessage}")
                # For critical elements, you might want to disable the module or raise an error
                # setattr(self.ui, attr_name, None) # Avoids AttributeError but hides problem
        
        self.logic = HomeLogic(self.ui.statusLabel if hasattr(self.ui, 'statusLabel') else None)

        self.uiWidget.setPalette(slicer.util.mainWindow().style().standardPalette())
        self.modifyWindowUI()
        self.setCustomUIVisible(True)
        self.applyApplicationStyle()

        # Connect signals for UI elements from Home.ui
        if hasattr(self.ui, 'selectStlFileButton') and self.ui.selectStlFileButton:
            self.ui.selectStlFileButton.clicked.connect(self.onSelectStlFileClicked)
        if hasattr(self.ui, 'processStlButton') and self.ui.processStlButton:
            self.ui.processStlButton.clicked.connect(self.onProcessStlClicked)

    def cleanup(self):
        self.removeObservers()

    def setSlicerUIVisible(self, visible: bool):
        exemptToolbars = ["MainToolBar", "ViewToolBar", *self.toolbarNames]
        slicer.util.setDataProbeVisible(visible)
        slicer.util.setMenuBarsVisible(visible, ignore=exemptToolbars)
        slicer.util.setModuleHelpSectionVisible(visible)
        slicer.util.setModulePanelTitleVisible(visible)
        slicer.util.setPythonConsoleVisible(visible)
        slicer.util.setApplicationLogoVisible(visible)
        keepToolbars = [slicer.util.findChild(slicer.util.mainWindow(), tn) for tn in exemptToolbars if slicer.util.findChild(slicer.util.mainWindow(), tn)]
        slicer.util.setToolbarsVisible(visible, keepToolbars)

    def modifyWindowUI(self):
        self.initializeSettingsToolBar()

    def insertToolBar(self, beforeToolBarName: str, name: str, title: Optional[str] = None) -> qt.QToolBar:
        beforeToolBar = slicer.util.findChild(slicer.util.mainWindow(), beforeToolBarName)
        if title is None:
            title = name
        toolBar = qt.QToolBar(title)
        toolBar.name = name
        slicer.util.mainWindow().insertToolBar(beforeToolBar, toolBar)
        self._toolbars[name] = toolBar
        return toolBar

    def initializeSettingsToolBar(self):
        settingsToolBar = self.insertToolBar("MainToolBar", "SettingsToolBar", title="Settings")
        gearIcon = qt.QIcon(self.resourcePath("Icons/Gears.png"))
        self.settingsAction = settingsToolBar.addAction(gearIcon, "")
        self.settingsDialog = slicer.util.loadUI(self.resourcePath("UI/Settings.ui"))
        self.settingsUI = slicer.util.childWidgetVariables(self.settingsDialog)
        if hasattr(self.settingsUI, 'CustomUICheckBox'):
            self.settingsUI.CustomUICheckBox.toggled.connect(self.setCustomUIVisible)
        if hasattr(self.settingsUI, 'CustomStyleCheckBox'):
            self.settingsUI.CustomStyleCheckBox.toggled.connect(self.toggleStyle)
        self.settingsAction.triggered.connect(self.raiseSettings)

    def toggleStyle(self, visible: bool):
        if visible:
            self.applyApplicationStyle()
        else:
            slicer.app.styleSheet = ""

    def raiseSettings(self, _):
        self.settingsDialog.exec()

    def setCustomUIVisible(self, visible: bool):
        self.setSlicerUIVisible(not visible)

    def applyApplicationStyle(self):
        SlicerCustomAppUtilities.applyStyle([slicer.app], self.resourcePath("Home.qss"))
        self.styleThreeDWidget()
        self.styleSliceWidgets()

    def styleThreeDWidget(self):
        pass # Placeholder for 3D view styling

    def styleSliceWidgets(self):
        for name in slicer.app.layoutManager().sliceViewNames():
            sliceWidget = slicer.app.layoutManager().sliceWidget(name)
            # self.styleSliceWidget(sliceWidget) # Placeholder

    def onSelectStlFileClicked(self):
        if not (hasattr(self.ui, 'stlFileLineEdit') and self.ui.stlFileLineEdit):
            print("ERROR: stlFileLineEdit not found in UI.")
            return
        returnValue = qt.QFileDialog.getOpenFileName(self.parent, "选择 STL 文件", "", "STL Files (*.stl)")
        filePath = None
        if isinstance(returnValue, tuple):
            if len(returnValue) > 0: filePath = returnValue[0]
        elif isinstance(returnValue, str):
            filePath = returnValue
        if filePath:
            self.ui.stlFileLineEdit.setText(filePath)

    def onProcessStlClicked(self):
        ui_elements_to_check = [
            'stlFileLineEdit', 'modelNameLineEdit', 'segmentationNameLineEdit',
            'segmentNameLineEdit', 'segmentColorLineEdit', 'processStlButton'
        ]
        for elem_name in ui_elements_to_check:
            if not (hasattr(self.ui, elem_name) and getattr(self.ui, elem_name)):
                qt.QMessageBox.critical(self.parent, "内部错误", f"UI元素 '{elem_name}' 丢失，请检查UI定义。")
                return

        stlFilePath = self.ui.stlFileLineEdit.text
        modelName = self.ui.modelNameLineEdit.text
        segmentationName = self.ui.segmentationNameLineEdit.text
        segmentNameInSeg = self.ui.segmentNameLineEdit.text
        colorStr = self.ui.segmentColorLineEdit.text

        if not stlFilePath:
            qt.QMessageBox.warning(self.uiWidget, "输入错误", "请先选择一个 STL 文件。")
            return
        if not all([modelName, segmentationName, segmentNameInSeg, colorStr]):
            qt.QMessageBox.warning(self.uiWidget, "输入错误", "所有名称和颜色字段均不能为空。")
            return
        try:
            colorList = [float(c.strip()) for c in colorStr.split(',')]
            if len(colorList) != 3:
                raise ValueError("颜色格式应为 R,G,B (例如: 1.0,0.5,0.0)")
        except ValueError as e:
            qt.QMessageBox.warning(self.uiWidget, "输入错误", f"无效的颜色格式: {e}")
            return

        self.ui.processStlButton.enabled = False
        self.logic._updateStatus("开始处理 STL 文件...")
        slicer.app.processEvents()

        success, message = self.logic.importStlAndConvertToSegmentation(
            stlFilePath, modelName, segmentationName, segmentNameInSeg, colorList
        )
        self.logic._updateStatus(message)
        if success:
            qt.QMessageBox.information(self.uiWidget, "成功", message)
        else:
            qt.QMessageBox.critical(self.uiWidget, "失败", message)
        
        if hasattr(self.ui, 'processStlButton') and self.ui.processStlButton:
            self.ui.processStlButton.enabled = True
        slicer.app.processEvents()

class HomeLogic(ScriptedLoadableModuleLogic):
    def __init__(self, statusLabel: Optional[qt.QLabel] = None):
        ScriptedLoadableModuleLogic.__init__(self)
        self.statusLabel = statusLabel

    def _updateStatus(self, message: str):
        if self.statusLabel:
            self.statusLabel.text = f"状态: {message}"
        print(f"HomeLogic Status: {message}")

    def importStlAndConvertToSegmentation(self, stl_file_path: str, desired_model_name: str,
                                          segmentation_node_name: str, segment_name_in_segmentation: str,
                                          segment_color: list[float]):
        self._updateStatus(f"开始导入 STL: {stl_file_path} (模型名: {desired_model_name})")
        slicer.app.processEvents()

        loaded_model_node = None
        raw_load_result_for_debug = None
        try:
            if not os.path.exists(stl_file_path):
                raise FileNotFoundError(f"STL 文件未找到: {stl_file_path}")

            raw_load_result_for_debug = slicer.util.loadModel(stl_file_path, returnNode=True)
            if isinstance(raw_load_result_for_debug, slicer.vtkMRMLNode):
                loaded_model_node = raw_load_result_for_debug
            elif isinstance(raw_load_result_for_debug, tuple) and len(raw_load_result_for_debug) > 0:
                if isinstance(raw_load_result_for_debug[0], slicer.vtkMRMLNode):
                    loaded_model_node = raw_load_result_for_debug[0]
                elif len(raw_load_result_for_debug) > 1 and isinstance(raw_load_result_for_debug[0], bool) and \
                     raw_load_result_for_debug[0] is True and isinstance(raw_load_result_for_debug[1], slicer.vtkMRMLNode):
                    loaded_model_node = raw_load_result_for_debug[1]
            
            if not loaded_model_node:
                raise RuntimeError(f"slicer.util.loadModel 未能返回有效节点。Raw: {raw_load_result_for_debug}")
            
            initial_model_name = loaded_model_node.GetName()
            self._updateStatus(f"STL 已加载为 '{initial_model_name}'. ID: {loaded_model_node.GetID()}")

            if initial_model_name != desired_model_name:
                existing_node = slicer.mrmlScene.GetFirstNodeByName(desired_model_name)
                if existing_node and existing_node.GetID() != loaded_model_node.GetID():
                    self._updateStatus(f"删除已存在的同名节点: {desired_model_name}")
                    slicer.mrmlScene.RemoveNode(existing_node)
                loaded_model_node.SetName(desired_model_name)
                self._updateStatus(f"模型已重命名为: {loaded_model_node.GetName()}")
            
            final_model_name = loaded_model_node.GetName()
            self._updateStatus(f"开始将模型 '{final_model_name}' 转换为分割 '{segmentation_node_name}'...")
            slicer.app.processEvents()

            existing_segmentation_node = slicer.mrmlScene.GetFirstNodeByName(segmentation_node_name)
            if existing_segmentation_node:
                self._updateStatus(f"分割节点 '{segmentation_node_name}' 已存在，将删除旧节点。")
                slicer.mrmlScene.RemoveNode(existing_segmentation_node)

            segmentation_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode", segmentation_node_name)
            if not segmentation_node:
                raise RuntimeError(f"创建 vtkMRMLSegmentationNode '{segmentation_node_name}' 失败。")
            segmentation_node.CreateDefaultDisplayNodes()
            
            segment_id = segmentation_node.GetSegmentation().AddEmptySegment(segment_name_in_segmentation)
            if not segment_id:
                raise RuntimeError(f"未能向 '{segmentation_node_name}' 添加 Segment '{segment_name_in_segmentation}'.")

            success_import_to_seg = slicer.modules.segmentations.logic().ImportModelToSegmentationNode(loaded_model_node, segmentation_node, segment_id)
            if not success_import_to_seg:
                if slicer.mrmlScene.IsNodePresent(segmentation_node):
                    slicer.mrmlScene.RemoveNode(segmentation_node) # Cleanup partially created segmentation
                raise RuntimeError(f"从模型 '{final_model_name}' 导入到 Segment '{segment_name_in_segmentation}' 失败。")
            
            segment = segmentation_node.GetSegmentation().GetSegment(segment_id)
            if segment:
                segment.SetColor(segment_color)
            else:
                self._updateStatus(f"警告: 未能获取 Segment '{segment_id}' 来设置颜色。")

            if hasattr(loaded_model_node, "GetDisplayNode") and loaded_model_node.GetDisplayNode():
                 loaded_model_node.GetDisplayNode().SetVisibility(False) # Hide original model
            
            self._updateStatus(f"模型 '{final_model_name}' 已成功转换为分割 '{segmentation_node_name}'.")
            slicer.util.resetSliceViews()
            slicer.util.resetThreeDViews()
            layoutManager = slicer.app.layoutManager()
            if layoutManager and layoutManager.threeDWidget(0):
                layoutManager.threeDWidget(0).threeDView().resetFocalPoint()

            return True, f"处理成功: STL '{stl_file_path}' 已导入并转换为分割 '{segmentation_node_name}'."

        except Exception as e:
            error_msg = f"处理失败: {type(e).__name__} - {e}. STL: '{stl_file_path}'. Raw load: {raw_load_result_for_debug}"
            self._updateStatus(error_msg)
            # Basic cleanup: if model was loaded but process failed, remove the loaded model if it wasn't the intended final model or if it's now orphaned.
            if loaded_model_node and isinstance(loaded_model_node, slicer.vtkMRMLNode) and slicer.mrmlScene.IsNodePresent(loaded_model_node):
                 # Heuristic: if error occurred during segmentation, the model might be fine but user might want it gone.
                 # Or if the name is still the initial name and not desired_model_name.
                 # For simplicity now, we remove it if an error occurred after it was confirmed loaded.
                 self._updateStatus(f"错误后清理: 移除节点 '{loaded_model_node.GetName()}'.")
                 slicer.mrmlScene.RemoveNode(loaded_model_node)
            return False, error_msg 