from typing import Optional

import qt
import slicer
import SlicerCustomAppUtilities
from slicer.ScriptedLoadableModule import (
    ScriptedLoadableModule,
    ScriptedLoadableModuleLogic,
    ScriptedLoadableModuleWidget,
)
from slicer.util import VTKObservationMixin
import os
import vtk # Added for vtk.vtkBoundingBox
import math # Added for math.sin, math.radians
import sys

# Attempt to import the specific Slicer module that provides the Segment Editor Widget bindings
try:
    import qSlicerSegmentationsModuleWidgetsPythonQt
    slicer_segment_editor_widget_class = qSlicerSegmentationsModuleWidgetsPythonQt.qMRMLSegmentEditorWidget
    print("DEBUG: Successfully imported qSlicerSegmentationsModuleWidgetsPythonQt and got qMRMLSegmentEditorWidget class.")
except ImportError:
    print("ERROR: Could not import qSlicerSegmentationsModuleWidgetsPythonQt. Segment Editor cannot be created.")
    slicer_segment_editor_widget_class = None
except AttributeError:
    print("ERROR: qSlicerSegmentationsModuleWidgetsPythonQt imported, but qMRMLSegmentEditorWidget not found within it.")
    slicer_segment_editor_widget_class = None

# Import to ensure the files are available through the Qt resource system
from Resources import HomeResources  # noqa: F401

# Segment Editor widget class - ensure it's imported if not already available
if slicer_segment_editor_widget_class is None:
    try:
        import qSlicerSegmentationsModuleWidgetsPythonQt
        slicer_segment_editor_widget_class = qSlicerSegmentationsModuleWidgetsPythonQt.qMRMLSegmentEditorWidget
    except ImportError:
        print("WARNING: Unable to import qSlicerSegmentationsModuleWidgetsPythonQt on second attempt. Segment Editor features will be disabled.")
        slicer_segment_editor_widget_class = None

# Data module widget class (for Subject Hierarchy / Data module)
try:
    import qSlicerDataModuleWidgetsPythonQt
    slicer_data_widget_class = qSlicerDataModuleWidgetsPythonQt.qSlicerDataModuleWidget
except Exception:
    slicer_data_widget_class = None  # Fallback if bindings not available


class Home(ScriptedLoadableModule):
    """The home module allows to orchestrate and style the overall application workflow.

    It is a "special" module in the sense that its role is to customize the application and
    coordinate a workflow between other "regular" modules.

    Associated widget and logic are not intended to be initialized multiple times.
    """

    def __init__(self, parent: Optional[qt.QWidget]):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Home"
        self.parent.categories = [""]
        self.parent.dependencies = []
        self.parent.contributors = ["Sam Horvath (Kitware Inc.)", "Jean-Christophe Fillion-Robin (Kitware Inc.)"]
        self.parent.helpText = """This module orchestrates and styles the overall application workflow."""
        self.parent.helpText += self.getDefaultModuleDocumentationLink()
        self.parent.acknowledgementText = """..."""  # replace with organization, grant and thanks.


class HomeWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    @property
    def toolbarNames(self) -> list[str]:
        return [str(k) for k in self._toolbars]

    _toolbars: dict[str, qt.QToolBar] = {}

    def __init__(self, parent: Optional[qt.QWidget]):
        """Called when the application opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)
        self.segmentEditorNode = None
        self.segmentEditorWidget = None # Initialize members

    def setup(self):
        """Called when the application opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)

        # --- Create main tab widget ---
        self.uiWidget = slicer.util.loadUI(self.resourcePath("UI/Home.ui"))
        # Capture child widgets before we build other tabs (we will need importStlGroup etc.)
        self.ui = slicer.util.childWidgetVariables(self.uiWidget)

        self.mainTabWidget = qt.QTabWidget()
        self.mainTabWidget.setTabPosition(qt.QTabWidget.North)

        # Prepare a container page for Data tab (regardless of which data view implementation we use)
        dataPage = qt.QWidget()
        dataPageLayout = qt.QVBoxLayout(dataPage)
        dataPageLayout.setContentsMargins(4, 4, 4, 4)
        dataPageLayout.setSpacing(4)

        contentWidget = None

        if slicer_data_widget_class:
            try:
                contentWidget = slicer_data_widget_class()
                contentWidget.setMRMLScene(slicer.mrmlScene)
            except Exception:
                contentWidget = None

        if contentWidget is None:
            try:
                import qSlicerSubjectHierarchyModuleWidgetsPythonQt as _shW
                SubjectHierarchyTreeView = _shW.qMRMLSubjectHierarchyTreeView
                contentWidget = SubjectHierarchyTreeView()
                contentWidget.setMRMLScene(slicer.mrmlScene)
            except Exception:
                contentWidget = None

        if contentWidget:
            dataPageLayout.addWidget(contentWidget, 1)  # stretch 1 so it expands

        # ---- 工具组 ----
        toolGroup = qt.QGroupBox("模型工具")
        toolLayout = qt.QVBoxLayout(toolGroup)

        if hasattr(self.ui, 'importStlGroup'):
            self.ui.importStlGroup.setParent(toolGroup)
            toolLayout.addWidget(self.ui.importStlGroup)
        if hasattr(self.ui, 'resetViewsToFitModelsButton'):
            self.ui.resetViewsToFitModelsButton.setParent(toolGroup)
            toolLayout.addWidget(self.ui.resetViewsToFitModelsButton)

        dataPageLayout.addWidget(toolGroup, 0)

        self.mainTabWidget.addTab(dataPage, "模型导入")
        data_tab_added = True

        # Finally, add 声腔提取 tab (always added last so 模型导入 is on the left)
        self.mainTabWidget.addTab(self.uiWidget, "声腔提取")

        # --- 新建 "中心线提取" 页签，直接实例化原始 ExtractCenterlineWidget ---
        centerlinePage = qt.QWidget()
        # Create tab container with its own logic
        try:
            from ExtractCenterline import ExtractCenterlineWidget
            centerlineLayout = qt.QVBoxLayout(centerlinePage)
            centerlineLayout.setContentsMargins(0, 0, 0, 0)
            # 实例化原始模块小部件并嵌入
            ecWidget = ExtractCenterlineWidget(centerlinePage)
            ecWidget.setup()  # 调用其 setup 构建完整 GUI
            centerlineLayout.addWidget(ecWidget)
        except Exception as e:
            centerlineLayout = qt.QVBoxLayout(centerlinePage)
            errLab = qt.QLabel(f"无法加载原始 ExtractCenterlineWidget: {type(e).__name__} - {e}")
            errLab.setWordWrap(True)
            centerlineLayout.addWidget(errLab)
            import traceback; traceback.print_exc()

        self.mainTabWidget.addTab(centerlinePage, "中心线提取")

        self.layout.addWidget(self.mainTabWidget)

        print("DEBUG: Attributes in self.ui after childWidgetVariables:")
        if self.ui:
            for attr_name in dir(self.ui):
                if not attr_name.startswith("__") and not callable(getattr(self.ui, attr_name)):
                    widget_instance = getattr(self.ui, attr_name)
                    if isinstance(widget_instance, qt.QObject):
                        print(f"  - {attr_name} (ObjectName: {widget_instance.objectName}, Type: {type(widget_instance).__name__})")
                    else:
                        print(f"  - {attr_name} (Type: {type(widget_instance).__name__})")
        else:
            print("DEBUG: self.ui object is None or empty.")

        required_ui_elements = [
            'importStlGroup', 'stlFileLabel', 'stlFileLineEdit', 'selectStlFileButton',
            'modelNameLabel', 'modelNameLineEdit', 'processStlButton',
            'resetViewsToFitModelsButton',
            'segmentEditorDisplayGroupBox', # We need the group box. Its layout is defined in the UI.
            'statusLabel'
        ]
        for attr_name in required_ui_elements:
            if not hasattr(self.ui, attr_name):
                errorMessage = f"HomeWidget.setup: UI element '{attr_name}' not found. Check Home.ui."
                print(f"ERROR: {errorMessage}")
        
        self.logic = HomeLogic(self.ui.statusLabel if hasattr(self.ui, 'statusLabel') else None)
        self.uiWidget.setPalette(slicer.util.mainWindow().style().standardPalette())
        self.modifyWindowUI()
        self.setCustomUIVisible(True)
        self.applyApplicationStyle()

        # Connect signals for existing UI elements (STL import, ResetViews)
        if hasattr(self.ui, 'selectStlFileButton'):
            self.ui.selectStlFileButton.clicked.connect(self.onSelectStlFileClicked)
        if hasattr(self.ui, 'processStlButton'):
            self.ui.processStlButton.clicked.connect(self.onProcessStlClicked)
        if hasattr(self.ui, 'resetViewsToFitModelsButton'):
            self.ui.resetViewsToFitModelsButton.clicked.connect(self.onResetViewsToFitModelsClicked)

        # --- Segment Editor Setup ---
        # Get/Create Segment Editor Parameter Node
        parameterNodeSingletonTag = "EditorHomeParameterNode"
        self.segmentEditorNode = slicer.mrmlScene.GetSingletonNode(parameterNodeSingletonTag, "vtkMRMLSegmentEditorNode")
        if not self.segmentEditorNode:
            self.segmentEditorNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentEditorNode", parameterNodeSingletonTag)
            self.segmentEditorNode.SetSingletonTag(parameterNodeSingletonTag)
        
        if self.segmentEditorNode:
            try:
                self.segmentEditorNode.SetMaskMode(slicer.vtkMRMLSegmentationNode.EditAllowedEverywhere)
                self.segmentEditorNode.SetOverwriteMode(slicer.vtkMRMLSegmentEditorNode.OverwriteAllSegments)
            except AttributeError as e:
                print(f"ERROR setting SegmentEditorNode modes (EditAllowedEverywhere/OverwriteAllSegments): {e}. Using default integer values.")
                self.segmentEditorNode.SetMaskMode(0) # Fallback for EditAllowedEverywhere
                self.segmentEditorNode.SetOverwriteMode(0) # Fallback for OverwriteAllSegments

        # Instantiate qMRMLSegmentEditorWidget using the correctly imported class
        if slicer_segment_editor_widget_class and self.segmentEditorNode:
            try:
                print(f"DEBUG: Attempting to instantiate Segment Editor Widget using: {slicer_segment_editor_widget_class}")
                self.segmentEditorWidget = slicer_segment_editor_widget_class() # No parent here yet
                
                if self.segmentEditorWidget:
                    print(f"DEBUG: Successfully instantiated Segment Editor Widget. ObjectName: {self.segmentEditorWidget.objectName}")
                    self.segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
                    self.segmentEditorWidget.setMRMLSegmentEditorNode(self.segmentEditorNode)
                    print("DEBUG: MRMLScene and SegmentEditorNode set for the editor widget.")

                    # Add it to our Home.ui layout
                    segment_editor_groupbox = getattr(self.ui, 'segmentEditorDisplayGroupBox', None)
                    if segment_editor_groupbox:
                        target_layout = segment_editor_groupbox.layout() # This is the QVBoxLayout named segmentEditorLayout in the .ui
                        if target_layout and isinstance(target_layout, qt.QLayout):
                            print(f"DEBUG: Found layout '{target_layout.objectName}' in segmentEditorDisplayGroupBox. Adding editor widget.")
                            target_layout.addWidget(self.segmentEditorWidget)
                            # Parentage should be handled by addWidget, but explicitly setting size policy is good.
                            self.segmentEditorWidget.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
                            self.segmentEditorWidget.setVisible(True)
                            print("DEBUG: Segment Editor Widget added to layout and made visible.")
                        else:
                            # 如果在 UI 中未能获取到布局，则在运行时创建一个新的垂直布局并添加到 groupBox
                            print(f"INFO: segmentEditorDisplayGroupBox.layout() is {type(target_layout).__name__ if target_layout else 'None'}. Programmatically creating and setting QVBoxLayout for it.")
                            new_layout = qt.QVBoxLayout(segment_editor_groupbox)
                            new_layout.setObjectName("segmentEditorLayout_auto")
                            new_layout.addWidget(self.segmentEditorWidget)
                            self.segmentEditorWidget.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
                            self.segmentEditorWidget.setVisible(True)
                            print("DEBUG: 运行时创建布局并成功嵌入 Segment Editor Widget。")
                    else:
                        print("ERROR: segmentEditorDisplayGroupBox not found in self.ui, cannot embed editor widget.")
                        self.segmentEditorWidget = None # Failed to place it
                else:
                    print("ERROR: Instantiation of Segment Editor Widget returned None.")
            except Exception as e:
                print(f"ERROR: Exception during qSlicerSegmentEditorWidget instantiation or setup: {e}")
                self.segmentEditorWidget = None
        else:
            if not slicer_segment_editor_widget_class:
                print("ERROR: Segment Editor Widget class (slicer_segment_editor_widget_class) not available for instantiation.")
            if not self.segmentEditorNode:
                print("ERROR: self.segmentEditorNode is None, cannot configure editor widget.")
        # --- End Segment Editor Setup ---

        # --- Register Custom Segment Editor Effects ---
        self.registerWrapSolidifyEffect()

        # Configure sourceModelNodeComboBox (this was for ModelToSeg)
        if hasattr(self.ui, 'sourceModelNodeComboBox') and self.ui.sourceModelNodeComboBox:
            self.ui.sourceModelNodeComboBox.nodeTypes = ["vtkMRMLModelNode"]
            self.ui.sourceModelNodeComboBox.setMRMLScene(slicer.mrmlScene)
            self.ui.sourceModelNodeComboBox.selectNodeUponCreation = True
            self.ui.sourceModelNodeComboBox.addEnabled = False
            self.ui.sourceModelNodeComboBox.removeEnabled = False
            self.ui.sourceModelNodeComboBox.editEnabled = False
            self.ui.sourceModelNodeComboBox.renameEnabled = False
            self.ui.sourceModelNodeComboBox.noneEnabled = True 
            self.ui.sourceModelNodeComboBox.showHidden = False
            self.ui.sourceModelNodeComboBox.showChildNodeTypes = False

        # --- 不再需要运行时 reparent（已在 dataPageCreation 中完成） ---

    def cleanup(self):
        """Called when the application closes and the module widget is destroyed."""
        pass

    def setSlicerUIVisible(self, visible: bool):
        exemptToolbars = [
            "MainToolBar",
            "ViewToolBar",
            *self.toolbarNames,
        ]
        slicer.util.setDataProbeVisible(visible)
        slicer.util.setMenuBarsVisible(visible, ignore=exemptToolbars)
        slicer.util.setModuleHelpSectionVisible(visible)
        slicer.util.setModulePanelTitleVisible(visible)
        slicer.util.setPythonConsoleVisible(visible)
        slicer.util.setApplicationLogoVisible(visible)
        keepToolbars = [slicer.util.findChild(slicer.util.mainWindow(), toolbarName) for toolbarName in exemptToolbars]
        slicer.util.setToolbarsVisible(visible, keepToolbars)

    def modifyWindowUI(self):
        """Customize the entire user interface to resemble the custom application"""
        # Custom toolbars
        self.initializeSettingsToolBar()

    def insertToolBar(self, beforeToolBarName: str, name: str, title: Optional[str] = None) -> qt.QToolBar:
        """Helper method to insert a new toolbar between existing ones"""
        beforeToolBar = slicer.util.findChild(slicer.util.mainWindow(), beforeToolBarName)

        if title is None:
            title = name

        toolBar = qt.QToolBar(title)
        toolBar.name = name
        slicer.util.mainWindow().insertToolBar(beforeToolBar, toolBar)

        self._toolbars[name] = toolBar

        return toolBar

    def initializeSettingsToolBar(self):
        """Create toolbar and dialog for app settings"""
        settingsToolBar = self.insertToolBar("MainToolBar", "SettingsToolBar", title="Settings")

        gearIcon = qt.QIcon(self.resourcePath("Icons/Gears.png"))
        self.settingsAction = settingsToolBar.addAction(gearIcon, "")

        # Settings dialog
        self.settingsDialog = slicer.util.loadUI(self.resourcePath("UI/Settings.ui"))
        self.settingsUI = slicer.util.childWidgetVariables(self.settingsDialog)
        self.settingsUI.CustomUICheckBox.toggled.connect(self.setCustomUIVisible)
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
        viewNode = slicer.app.layoutManager().threeDWidget(0).mrmlViewNode()  # noqa: F841
        # viewNode.SetBackgroundColor(0.0, 0.0, 0.0)
        # viewNode.SetBackgroundColor2(0.0, 0.0, 0.0)
        # viewNode.SetBoxVisible(False)
        # viewNode.SetAxisLabelsVisible(False)
        # viewNode.SetOrientationMarkerType(slicer.vtkMRMLViewNode.OrientationMarkerTypeAxes)

    def styleSliceWidgets(self):
        for name in slicer.app.layoutManager().sliceViewNames():
            sliceWidget = slicer.app.layoutManager().sliceWidget(name)
            self.styleSliceWidget(sliceWidget)

    def styleSliceWidget(self, sliceWidget: slicer.qMRMLSliceWidget):
        controller = sliceWidget.sliceController()  # noqa: F841
        # controller.sliceViewLabel = ""
        # slicer.util.findChild(sliceWidget, "PinButton").visible = False
        # slicer.util.findChild(sliceWidget, "ViewLabel").visible = False
        # slicer.util.findChild(sliceWidget, "FitToWindowToolButton").visible = False
        # slicer.util.findChild(sliceWidget, "SliceOffsetSlider").spinBoxVisible = False

    # --- Slots for STL Import and Conversion ---
    def onSelectStlFileClicked(self):
        """Opens a file dialog to select an STL file."""
        returnValue = qt.QFileDialog.getOpenFileName(self.parent, "选择 STL 文件", "", "STL Files (*.stl)")
        
        filePath = None
        if isinstance(returnValue, tuple):
            if len(returnValue) > 0:
                filePath = returnValue[0]
        elif isinstance(returnValue, str):
            filePath = returnValue
        
        if filePath and hasattr(self.ui, 'stlFileLineEdit') and self.ui.stlFileLineEdit:
            self.ui.stlFileLineEdit.setText(filePath)

    def onProcessStlClicked(self):
        """Handles the STL import and conversion process."""
        if not (hasattr(self.ui, 'stlFileLineEdit') and self.ui.stlFileLineEdit and \
                hasattr(self.ui, 'modelNameLineEdit') and self.ui.modelNameLineEdit and \
                hasattr(self.ui, 'processStlButton') and self.ui.processStlButton):
            print("ERROR: HomeWidget.onProcessStlClicked: Required UI elements for processing are missing.")
            qt.QMessageBox.critical(self.parent, "内部错误", "处理所需的UI元素丢失，请检查UI定义。")
            return

        stlFilePath = self.ui.stlFileLineEdit.text
        modelName = self.ui.modelNameLineEdit.text

        if not stlFilePath:
            qt.QMessageBox.warning(self.uiWidget, "输入错误", "请先选择一个 STL 文件。")
            return

        if not modelName:
            qt.QMessageBox.warning(self.uiWidget, "输入错误", "模型名称不能为空。")
            return

        self.ui.processStlButton.enabled = False
        self.logic._updateStatus("开始导入 STL 文件...")
        slicer.app.processEvents()

        imported_node, message = self.logic.importStlModel(
            stlFilePath,
            modelName
        )

        self.logic._updateStatus(message)

        if imported_node:
            qt.QMessageBox.information(self.uiWidget, "成功", message)
        else:
            qt.QMessageBox.critical(self.uiWidget, "失败", message)

        if hasattr(self.ui, 'processStlButton') and self.ui.processStlButton: # Check again before enabling
            self.ui.processStlButton.enabled = True
        slicer.app.processEvents()
    # --- End Slots for STL Import and Conversion ---

    # --- Slot for Resetting Views to Fit Models ---
    def onResetViewsToFitModelsClicked(self):
        """Resets all views to fit the currently visible models in the scene."""
        self.logic._updateStatus("正在重置视图以适应模型...")
        slicer.app.processEvents() # Allow UI to update status
        
        self.logic.resetViewsToFitAllModels()
        
        self.logic._updateStatus("视图已重置。")
        slicer.app.processEvents()
    # --- End Slot for Resetting Views to Fit Models ---

    def registerWrapSolidifyEffect(self):
        """Registers the Wrap Solidify effect for the Segment Editor."""
        try:
            print("DEBUG: 开始注册 'Wrap Solidify' Segment Editor 效果...")
            import qSlicerSegmentationsEditorEffectsPythonQt as qSlicerSegmentationsEditorEffects
            effectFactory = qSlicerSegmentationsEditorEffects.qSlicerSegmentEditorEffectFactory.instance()
            print(f"DEBUG: 已获取 SegmentEditorEffectFactory 实例: {effectFactory}")

            # 计算效果脚本可能所在的路径
            moduleDir = os.path.dirname(slicer.util.modulePath(self.moduleName))
            primaryDir = os.path.join(moduleDir, "Resources", "SegmentEditorEffects", "WrapSolidify")
            primaryPath = os.path.join(primaryDir, "SegmentEditorEffect.py")
            print(f"DEBUG: 主要查找路径: {primaryPath}")

            effectPath = primaryPath
            if not os.path.exists(effectPath):
                fallbackDir = os.path.join(moduleDir, "Resources", "WrapSolidify")
                fallbackPath = os.path.join(fallbackDir, "SegmentEditorEffect.py")
                print(f"DEBUG: 主要路径不存在，尝试备用路径: {fallbackPath}")
                if os.path.exists(fallbackPath):
                    effectPath = fallbackPath
                else:
                    # 进一步尝试通过已安装的 SegmentEditorWrapSolidifyLib 包来定位脚本
                    try:
                        import importlib
                        wrap_lib_spec = importlib.util.find_spec("SegmentEditorWrapSolidifyLib")
                        if wrap_lib_spec and wrap_lib_spec.origin:
                            candidate_lib_dir = os.path.dirname(wrap_lib_spec.origin)
                            candidate_effect_path = os.path.join(candidate_lib_dir, "SegmentEditorEffect.py")
                            print(f"DEBUG: 尝试通过 SegmentEditorWrapSolidifyLib 定位脚本: {candidate_effect_path}")
                            if os.path.exists(candidate_effect_path):
                                effectPath = candidate_effect_path
                            else:
                                print("DEBUG: 通过 SegmentEditorWrapSolidifyLib 仍未找到脚本。")
                        else:
                            print("DEBUG: 未检测到 SegmentEditorWrapSolidifyLib 模块规格，跳过此途径。")
                    except Exception as e_lib:
                        print(f"DEBUG: 通过 importlib 检测 SegmentEditorWrapSolidifyLib 失败: {e_lib}")

                    # 如果仍未找到，放弃注册
                    if not os.path.exists(effectPath):
                        print("WARNING: 未找到 'Wrap Solidify' 脚本文件，放弃注册。")
                        return

            # 检查是否已注册（遍历 registeredEffects 列表）
            already_registered = False
            try:
                for eff in effectFactory.registeredEffects():
                    if eff and hasattr(eff, "name") and eff.name == "Wrap Solidify":
                        already_registered = True
                        break
            except Exception as e_check:
                print(f"DEBUG: 检测已注册效果时异常: {e_check}. 将忽略并尝试直接注册。")

            if already_registered:
                print("INFO: 'Wrap Solidify' 效果已在工厂中注册，跳过重复注册。")
                return

            # 执行脚本注册
            instance = qSlicerSegmentationsEditorEffects.qSlicerSegmentEditorScriptedEffect(None)
            instance.setPythonSource(effectPath.replace('\\', '/'))
            instance.self().register()
            print(f"INFO: 成功从 {effectPath} 注册 'Wrap Solidify' 效果。")

            # 如果本模块已嵌入 SegmentEditorWidget，则刷新其效果列表以立即显示新效果
            try:
                if hasattr(self, "segmentEditorWidget") and self.segmentEditorWidget:
                    print("DEBUG: 调用 segmentEditorWidget.updateEffectList() 以刷新效果按钮。")
                    self.segmentEditorWidget.updateEffectList()
            except Exception as e_upd:
                print(f"WARNING: 更新 SegmentEditorWidget 效果列表时出错: {e_upd}")
        except ImportError as e:
            print(f"ERROR: 导入 SegmentEditor 效果绑定失败: {e}")
        except Exception as e:
            print(f"ERROR: 注册 'Wrap Solidify' 效果时发生异常: {type(e).__name__} - {e}")


class HomeLogic(ScriptedLoadableModuleLogic):
    """
    Implements underlying logic for the Home module.
    Handles data loading and updates status.
    """
    def __init__(self, statusLabel: Optional[qt.QLabel] = None):
        ScriptedLoadableModuleLogic.__init__(self)
        self.statusLabel = statusLabel

    def _updateStatus(self, message: str):
        """Helper to update the status label if it exists."""
        if self.statusLabel:
            self.statusLabel.text = f"状态: {message}"
        print(f"HomeLogic Status: {message}") # Also print to console

    def importStlModel(self, stl_file_path: str, desired_node_name: str):
        """
        Imports an STL file and renames the resulting model node to desired_node_name.
        Returns (vtkMRMLNode, str): The imported model node (or None on failure) and a status message.
        """
        self._updateStatus(f"开始导入 STL 文件: {stl_file_path} (期望名称: {desired_node_name})")
        slicer.app.processEvents()

        loaded_node = None # This will hold the successfully extracted MRML node
        raw_load_result_for_debug = None # For detailed error messages

        try:
            if not os.path.exists(stl_file_path):
                raise FileNotFoundError(f"STL 文件未找到: {stl_file_path}")

            self._updateStatus(f"调用 slicer.util.loadModel for {stl_file_path}...")
            raw_load_result_for_debug = slicer.util.loadModel(stl_file_path, returnNode=True)
            
            # --- Robustly extract the MRML node from loadModel result ---
            if isinstance(raw_load_result_for_debug, slicer.vtkMRMLNode): # Check if it's a direct MRML node
                loaded_node = raw_load_result_for_debug
            elif isinstance(raw_load_result_for_debug, tuple) and len(raw_load_result_for_debug) > 0:
                # If it's a tuple, check its elements
                if isinstance(raw_load_result_for_debug[0], slicer.vtkMRMLNode): # Is the first element a node?
                    loaded_node = raw_load_result_for_debug[0]
                elif len(raw_load_result_for_debug) > 1 and \
                     isinstance(raw_load_result_for_debug[0], bool) and \
                     raw_load_result_for_debug[0] is True and \
                     isinstance(raw_load_result_for_debug[1], slicer.vtkMRMLNode): # Is it (True, node_object)?
                    loaded_node = raw_load_result_for_debug[1]
            # --- End of robust extraction ---
            
            if not loaded_node: # If no valid node was extracted
                raise RuntimeError(f"slicer.util.loadModel 未能返回有效的节点对象。Raw load result: {raw_load_result_for_debug}")
            
            initial_name = loaded_node.GetName()
            self._updateStatus(f"STL 文件已初步加载。初始节点名称: '{initial_name}', ID: {loaded_node.GetID()}")

            # Step 2: Handle the desired node name.
            if initial_name == desired_node_name:
                self._updateStatus(f"初始名称 '{initial_name}' 与期望名称 '{desired_node_name}' 相同。无需额外重命名步骤。")
            else:
                # Use GetFirstNodeByName to avoid exception if node doesn't exist
                existing_node_with_desired_name = slicer.mrmlScene.GetFirstNodeByName(desired_node_name)
                if existing_node_with_desired_name and existing_node_with_desired_name.GetID() != loaded_node.GetID():
                    self._updateStatus(f"节点 '{desired_node_name}' 已被另一节点占用。正在删除旧节点 (ID: {existing_node_with_desired_name.GetID()})...")
                    slicer.mrmlScene.RemoveNode(existing_node_with_desired_name)
                elif existing_node_with_desired_name and existing_node_with_desired_name.GetID() == loaded_node.GetID():
                    self._updateStatus(f"注意: 刚加载的节点 ('{initial_name}') 已是或已变为 '{desired_node_name}'。")

                self._updateStatus(f"尝试将节点 '{initial_name}' 重命名为 '{desired_node_name}'...")
                loaded_node.SetName(desired_node_name)
                
                final_name = loaded_node.GetName()
                self._updateStatus(f"节点已重命名。最终名称: '{final_name}'")
                if final_name != desired_node_name:
                    self._updateStatus(f"注意: 最终节点名称 '{final_name}' 与期望的 '{desired_node_name}' 不同 (可能由于名称冲突自动调整)。")

            slicer.app.processEvents()

            slicer.util.resetSliceViews()
            layoutManager = slicer.app.layoutManager()
            if layoutManager:
                for threeDViewIndex in range(layoutManager.threeDViewCount):
                    threeDWidget = layoutManager.threeDWidget(threeDViewIndex)
                    if threeDWidget:
                        threeDView = threeDWidget.threeDView()
                        threeDView.resetFocalPoint()
            
            return loaded_node, f"STL 文件 '{stl_file_path}' 已成功导入为 '{loaded_node.GetName()}'."

        except Exception as e:
            error_msg = f"导入 STL 文件 '{stl_file_path}' (目标名: '{desired_node_name}') 失败: {type(e).__name__} - {e}. Raw load result was: {raw_load_result_for_debug}"
            self._updateStatus(error_msg)
            
            # Cleanup attempt: only if loaded_node was successfully extracted as a valid MRML node earlier
            if loaded_node and isinstance(loaded_node, slicer.vtkMRMLNode) and slicer.mrmlScene.IsNodePresent(loaded_node):
                self._updateStatus(f"发生错误后，尝试移除此函数调用处理的节点 '{loaded_node.GetName()}' (ID: {loaded_node.GetID()})...")
                slicer.mrmlScene.RemoveNode(loaded_node)
            elif not isinstance(loaded_node, slicer.vtkMRMLNode) and loaded_node is not None:
                 self._updateStatus(f"错误处理：先前提取的 loaded_node 不是有效的 MRML 节点 (类型: {type(loaded_node).__name__})，无法按预期清理。")
            
            return None, error_msg

    def resetViewsToFitAllModels(self):
        """Resets 3D and slice views to fit all currently visible model nodes in the scene."""
        
        modelNodes = slicer.util.getNodesByClass('vtkMRMLModelNode')
        visibleModelNodes = []
        for node in modelNodes:
            displayNode = node.GetDisplayNode()
            if displayNode and displayNode.GetVisibility():
                visibleModelNodes.append(node)
        
        if not visibleModelNodes:
            self._updateStatus("场景中没有可见的模型节点来调整视图。")
            # qt.QMessageBox.information(slicer.util.mainWindow(), "视图重置", "场景中没有可见的模型节点。")
            return

        # Calculate combined bounds of visible model nodes
        allNodesBounds = vtk.vtkBoundingBox() # Use vtk.vtkBoundingBox
        for node in visibleModelNodes:
            nodeBoundsArray = [0.0] * 6
            node.GetRASBounds(nodeBoundsArray) # Get bounds in RAS (world) coordinates
            if nodeBoundsArray[0] <= nodeBoundsArray[1]: # Check if bounds are valid (xmin <= xmax)
                allNodesBounds.AddBounds(nodeBoundsArray)

        if not allNodesBounds.IsValid():
            self._updateStatus("无法计算可见模型的有效边界框。")
            return
        
        finalBoundsArray = [0.0] * 6
        allNodesBounds.GetBounds(finalBoundsArray)

        # Fit 3D views to these specific bounds
        layoutManager = slicer.app.layoutManager()

        if layoutManager:
            for threeDViewIndex in range(layoutManager.threeDViewCount):
                threeDWidget = layoutManager.threeDWidget(threeDViewIndex)
                if threeDWidget:
                    threeDView = threeDWidget.threeDView()
                    viewNode = threeDView.mrmlViewNode()
                    if viewNode:
                        cameraNode = slicer.modules.cameras.logic().GetViewActiveCameraNode(viewNode)
                        if cameraNode:
                            self._updateStatus(f"正在调整3D视图 {threeDViewIndex} (相机: {cameraNode.GetName()}) 以适应边界: {finalBoundsArray}")
                            
                            # Get vtkCamera directly from cameraNode
                            vtk_camera = cameraNode.GetCamera()
                            if not vtk_camera:
                                self._updateStatus(f"无法从相机节点 {cameraNode.GetName()} 获取vtkCamera对象。跳过此视图。")
                                continue

                            # Calculate center of the bounds
                            center_x = (finalBoundsArray[0] + finalBoundsArray[1]) / 2.0
                            center_y = (finalBoundsArray[2] + finalBoundsArray[3]) / 2.0
                            center_z = (finalBoundsArray[4] + finalBoundsArray[5]) / 2.0
                            bounds_center = [center_x, center_y, center_z]

                            # Calculate radius of the bounding sphere for the bounds
                            width = finalBoundsArray[1] - finalBoundsArray[0]
                            height = finalBoundsArray[3] - finalBoundsArray[2]
                            depth = finalBoundsArray[5] - finalBoundsArray[4]
                            # Max length of the bounding box diagonal, or simply max dimension for a looser fit
                            # radius = math.sqrt(width*width + height*height + depth*depth) * 0.5
                            # Let's use a simpler radius based on the largest dimension to ensure it fits
                            # or use half of the largest extent of the bounding box as the radius
                            bounds_radius = max(width, height, depth) / 2.0
                            if bounds_radius == 0: # Avoid division by zero if bounds are degenerate
                                bounds_radius = 1.0 # Default small radius

                            # Get current camera properties
                            view_angle_deg = vtk_camera.GetViewAngle()
                            view_angle_rad = math.radians(view_angle_deg)
                            
                            # Calculate new distance from focal point to camera position
                            # distance = radius / sin(half_view_angle)
                            if math.sin(view_angle_rad / 2.0) > 1e-6: # Avoid division by zero for tiny angles
                                new_distance = bounds_radius / math.sin(view_angle_rad / 2.0)
                            else:
                                new_distance = bounds_radius * 5 # Fallback if angle is too small, pull back further
                            
                            if vtk_camera.GetParallelProjection():
                                # For parallel projection, adjust parallel scale
                                # Parallel scale is half of the viewport height in world coordinates.
                                # We want the largest dimension of the bounds to fit.
                                vtk_camera.SetParallelScale(max(height, width) / 2.0) # A common approach
                                # Or more precisely, if fitting to bounds_radius in the view angle context:
                                # vtk_camera.SetParallelScale(bounds_radius)
                            else:
                                # For perspective projection, set the distance
                                # The new_distance calculation is for perspective.
                                pass # new_distance will be used below

                            # Get view plane normal (direction from focal point to camera)
                            view_plane_normal = list(vtk_camera.GetViewPlaneNormal())
                            
                            # Set new focal point
                            cameraNode.SetFocalPoint(bounds_center)

                            # Calculate new camera position
                            new_camera_position = [
                                bounds_center[0] - view_plane_normal[0] * new_distance,
                                bounds_center[1] - view_plane_normal[1] * new_distance,
                                bounds_center[2] - view_plane_normal[2] * new_distance
                            ]
                            cameraNode.SetPosition(new_camera_position)
                            
                            # Optionally, re-orthogonalize view up if needed, though SetPosition/FocalPoint often handles this
                            # vtk_camera.OrthogonalizeViewUp()
                            # cameraNode.SetViewUp(vtk_camera.GetViewUp()) # Update MRML node if vtkCamera was changed directly

                            cameraNode.ResetClippingRange() # Important after changing position/focal point
                            threeDView.forceRender()
                        else:
                            self._updateStatus(f"无法获取3D视图 {threeDViewIndex} 的相机节点。尝试使用 resetFocalPoint。")
                            threeDView.resetFocalPoint() # Fallback
                    else:
                        self._updateStatus(f"无法获取3D视图 {threeDViewIndex} 的视图节点。尝试使用 resetFocalPoint。")
                        threeDView.resetFocalPoint() # Fallback
            self._updateStatus("3D视图已尝试适应模型边界。")
        else:
            self._updateStatus("无法获取布局管理器用于调整3D视图。")

        # Fit Slice views to these specific bounds
        sliceViewNames = ["Red", "Yellow", "Green"] # Standard Slicer slice view names
        if layoutManager:
            boundsCenterRAS = [
                (finalBoundsArray[0] + finalBoundsArray[1]) / 2.0,
                (finalBoundsArray[2] + finalBoundsArray[3]) / 2.0,
                (finalBoundsArray[4] + finalBoundsArray[5]) / 2.0
            ]
            boundsWidthRAS = finalBoundsArray[1] - finalBoundsArray[0]
            boundsHeightRAS = finalBoundsArray[3] - finalBoundsArray[2]
            boundsDepthRAS = finalBoundsArray[5] - finalBoundsArray[4]

            for viewName in sliceViewNames:
                sliceWidget = layoutManager.sliceWidget(viewName)
                if sliceWidget:
                    sliceLogic = sliceWidget.sliceLogic()
                    if sliceLogic:
                        sliceNode = sliceLogic.GetSliceNode()
                        if sliceNode and isinstance(sliceNode, slicer.vtkMRMLSliceNode):
                            self._updateStatus(f"正在调整切片视图 '{viewName}' 以适应边界...")
                            
                            # 1. Get the SliceToRAS matrix
                            sliceToRAS = sliceNode.GetSliceToRAS()

                            # 2. Set the translation part of SliceToRAS to boundsCenterRAS
                            # This makes boundsCenterRAS the origin of the slice plane in RAS
                            for i in range(3):
                                sliceToRAS.SetElement(i, 3, boundsCenterRAS[i])
                            
                            # It might be necessary to also ensure the slice offsets are zero if we directly set origin this way,
                            # as JumpSlice works by adjusting offsets. Let's set them to zero for clarity.
                            sliceNode.SetSliceOffset(0.0) 

                            # Apply the modified matrix back to the slice node if it's a copy (usually not needed for GetSliceToRAS directly)
                            # However, it's safer to trigger an update after modifying matrix elements even if it's a direct pointer.
                            # sliceNode.SetSliceToRAS(sliceToRAS) # This would be if GetSliceToRAS returned a copy.
                                                        # For now, direct modification and UpdateMatrices should suffice.

                            # 3. Adjust Field of View (same logic as before)
                            currentFOVx, currentFOVy, currentFOVz = sliceNode.GetFieldOfView()
                            orientation = sliceNode.GetOrientationString()

                            # Get the dimensions of the slice view widget in pixels
                            sliceViewWidget = sliceWidget.sliceView() # qMRMLSliceView
                            viewWidthPx = sliceViewWidget.width
                            viewHeightPx = sliceViewWidget.height

                            candidateFOVx, candidateFOVy = 1.0, 1.0 # Default to 1mm if unknown

                            if orientation == "Axial":
                                candidateFOVx = boundsWidthRAS
                                candidateFOVy = boundsHeightRAS
                            elif orientation == "Sagittal":
                                candidateFOVx = boundsHeightRAS 
                                candidateFOVy = boundsDepthRAS  
                            elif orientation == "Coronal":
                                candidateFOVx = boundsWidthRAS  
                                candidateFOVy = boundsDepthRAS  
                            else: 
                                sorted_dims = sorted([boundsWidthRAS, boundsHeightRAS, boundsDepthRAS], reverse=True)
                                candidateFOVx = sorted_dims[0]
                                candidateFOVy = sorted_dims[1]
                            
                            # Ensure candidate FOVs are not zero or negative
                            candidateFOVx = max(candidateFOVx, 1.0)
                            candidateFOVy = max(candidateFOVy, 1.0)

                            finalFOVx, finalFOVy = candidateFOVx, candidateFOVy

                            if viewWidthPx > 0 and viewHeightPx > 0:
                                scaleX = candidateFOVx / viewWidthPx
                                scaleY = candidateFOVy / viewHeightPx
                                
                                finalScale = max(scaleX, scaleY)
                                
                                finalFOVx = finalScale * viewWidthPx
                                finalFOVy = finalScale * viewHeightPx
                            else:
                                self._updateStatus(f"警告: 无法获取切片视图 '{viewName}' 的有效像素尺寸。FOV可能未按比例调整。")
                                # Use candidates directly if pixel dimensions are not available

                            sliceNode.SetFieldOfView(finalFOVx, finalFOVy, currentFOVz) # Keep original Z FOV (thickness)
                            sliceNode.UpdateMatrices() # Ensure matrix changes are propagated
                            # The slice view should update automatically after SliceNode properties are changed and UpdateMatrices is called.

                        else:
                            self._updateStatus(f"无法获取切片视图 '{viewName}' 的有效 SliceNode。")
                    else:
                        self._updateStatus(f"无法获取切片视图 '{viewName}' 的 SliceLogic。")
                else:
                    self._updateStatus(f"无法获取切片小部件 '{viewName}'。")
            self._updateStatus("切片视图已尝试适应模型边界。")
        else:
            self._updateStatus("无法获取布局管理器用于调整切片视图。")

        slicer.app.processEvents() # Ensure UI updates after view changes

    pass
