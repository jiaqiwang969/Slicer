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
import csv  # For contour export
import numpy as np  # Numerical computations

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
        # 新增：保存 Markups 小部件以便在 cleanup 中调用 exit()
        self.markupsModuleWidget = None

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
            centerlineLayout = qt.QVBoxLayout(centerlinePage)
            centerlineLayout.setContentsMargins(0, 0, 0, 0)

            # 尝试通过 Slicer API 获取 ExtractCenterline 模块小部件（新实例优先）
            centerlineModuleWidgetInstance = None # Python 模块实例或 C++ QWidget
            try:
                centerlineModuleWidgetInstance = slicer.util.getNewModuleWidget('ExtractCenterline')
            except Exception as e_new:
                print(f"INFO: getNewModuleWidget('ExtractCenterline') 失败: {type(e_new).__name__}: {e_new}，尝试回退至 getModuleWidget().")
                centerlineModuleWidgetInstance = slicer.util.getModuleWidget('ExtractCenterline')

            if centerlineModuleWidgetInstance is None:
                raise RuntimeError("获取 ExtractCenterline 模块 GUI 失败，返回 None。")

            # 对于脚本模块, .parent 是实际的 QWidget
            if hasattr(centerlineModuleWidgetInstance, 'parent') and centerlineModuleWidgetInstance.parent is not None:
                widget_to_add = centerlineModuleWidgetInstance.parent
                widget_to_add.setParent(centerlinePage) # 确保父级
                centerlineLayout.addWidget(widget_to_add)
                widget_to_add.show()
                print(f"DEBUG: ExtractCenterline.parent (type: {type(widget_to_add).__name__}) added to layout.")
            elif isinstance(centerlineModuleWidgetInstance, qt.QWidget):
                 # 回退：如果脚本模块实例本身就是 QWidget (不常见但以防万一)
                centerlineModuleWidgetInstance.setParent(centerlinePage)
                centerlineLayout.addWidget(centerlineModuleWidgetInstance)
                centerlineModuleWidgetInstance.show()
                print(f"DEBUG: ExtractCenterline (widgetInstance itself, type: {type(centerlineModuleWidgetInstance).__name__}) added to layout.")
            else:
                raise TypeError(f"无法从 ExtractCenterline (type: {type(centerlineModuleWidgetInstance).__name__}) 获取可添加到布局的 QWidget")

        except Exception as e:
            centerlineLayout = qt.QVBoxLayout(centerlinePage)
            errLab = qt.QLabel(f"无法加载原始 ExtractCenterlineWidget: {type(e).__name__} - {e}")
            errLab.setWordWrap(True)
            centerlineLayout.addWidget(errLab)
            import traceback; traceback.print_exc()

        self.mainTabWidget.addTab(centerlinePage, "中心线提取")

        # --- 新建 "中心线编辑" 页签，复用原生 Markups 模块 GUI ---
        sectionPage = qt.QWidget()
        sectionLayout = qt.QVBoxLayout(sectionPage)
        sectionLayout.setContentsMargins(0, 0, 0, 0)
        sectionLayout.setSpacing(0)
        try:
            # 优先尝试创建一个新的 Markups 模块小部件实例，避免影响主模块面板
            try:
                markupsModuleWidgetInstance = slicer.util.getNewModuleWidget('Markups')
            except Exception as e_new:
                print(f"INFO: getNewModuleWidget('Markups') failed with {type(e_new).__name__}: {e_new}. 尝试退回至 getModuleWidget().")
                markupsModuleWidgetInstance = slicer.util.getModuleWidget('Markups')

            if markupsModuleWidgetInstance is None:
                raise RuntimeError("从 Slicer 获取 Markups 模块小部件失败，返回 None。")

            # 对于 C++ 模块 (如 qSlicerMarkupsModuleWidget), slicer.util 返回的实例本身
            # 在 C++ 层面是 QWidget。我们直接传递它给 addWidget。
            # Python 的 isinstance(obj, qt.QWidget) 对这些封装类可能返回 False。
            try:
                markupsModuleWidgetInstance.setParent(sectionPage) # 确保父级
                sectionLayout.addWidget(markupsModuleWidgetInstance)
                markupsModuleWidgetInstance.show()
                print(f"DEBUG: Markups widget (type: {type(markupsModuleWidgetInstance).__name__}) successfully added to layout and shown.")
                # >>>>>>> 新增：正确初始化 Markups 小部件，使其内部面板处于激活状态 <<<<<<<
                try:
                    # 设置 MRML 场景
                    if hasattr(markupsModuleWidgetInstance, "setMRMLScene"):
                        markupsModuleWidgetInstance.setMRMLScene(slicer.mrmlScene)
                    # 调用 enter()，模拟 Slicer 切换到该模块时的流程
                    if hasattr(markupsModuleWidgetInstance, "enter"):
                        markupsModuleWidgetInstance.enter()
                except Exception as e_init_mk:
                    print(f"WARNING: 初始化 Markups 小部件时调用 setMRMLScene/enter 失败: {type(e_init_mk).__name__}: {e_init_mk}")
                # 保存引用，便于后续 cleanup 调用 exit()
                self.markupsModuleWidget = markupsModuleWidgetInstance
            except Exception as e_add_markups:
                print(f"ERROR: Failed to add/show Markups widget. Type: {type(markupsModuleWidgetInstance).__name__}. Error: {e_add_markups}")
                # 如果 addWidget 失败 (例如，因为类型不匹配导致 ValueError)，则会在这里捕获
                # 并可以显示占位符
                errLab = qt.QLabel(f"无法嵌入 Markups 模块界面: {type(e_add_markups).__name__}")
                errLab.setWordWrap(True)
                sectionLayout.addWidget(errLab)

        except Exception as e:
            errLab = qt.QLabel(f"无法加载 Markups 模块小部件: {type(e).__name__} - {e}")
            errLab.setWordWrap(True)
            sectionLayout.addWidget(errLab)
            import traceback; traceback.print_exc()

        self.mainTabWidget.addTab(sectionPage, "中心线编辑")

        # ---------- 构建 剖面提取 UI ----------
        profilePage = qt.QWidget()
        profileLayout = qt.QVBoxLayout(profilePage)
        profileLayout.setContentsMargins(0, 0, 0, 0)
        profileLayout.setSpacing(0)

        # 输入节点选择
        inputGroup = qt.QGroupBox("输入数据")
        inputForm = qt.QFormLayout(inputGroup)

        self.profile_modelCombo = slicer.qMRMLNodeComboBox()
        self.profile_modelCombo.nodeTypes = ["vtkMRMLModelNode"]
        self.profile_modelCombo.selectNodeUponCreation = True
        self.profile_modelCombo.addEnabled = False
        self.profile_modelCombo.removeEnabled = False
        self.profile_modelCombo.renameEnabled = False
        self.profile_modelCombo.noneEnabled = False
        self.profile_modelCombo.setMRMLScene(slicer.mrmlScene)

        self.profile_curveCombo = slicer.qMRMLNodeComboBox()
        self.profile_curveCombo.nodeTypes = ["vtkMRMLMarkupsCurveNode"]
        self.profile_curveCombo.selectNodeUponCreation = True
        self.profile_curveCombo.addEnabled = False
        self.profile_curveCombo.removeEnabled = False
        self.profile_curveCombo.renameEnabled = False
        self.profile_curveCombo.noneEnabled = False
        self.profile_curveCombo.setMRMLScene(slicer.mrmlScene)

        self.profile_endpointsCombo = slicer.qMRMLNodeComboBox()
        self.profile_endpointsCombo.nodeTypes = ["vtkMRMLMarkupsFiducialNode"]
        self.profile_endpointsCombo.selectNodeUponCreation = True
        self.profile_endpointsCombo.addEnabled = False
        self.profile_endpointsCombo.removeEnabled = False
        self.profile_endpointsCombo.renameEnabled = False
        self.profile_endpointsCombo.noneEnabled = True
        self.profile_endpointsCombo.setMRMLScene(slicer.mrmlScene)

        inputForm.addRow("模型:", self.profile_modelCombo)
        inputForm.addRow("中心线曲线:", self.profile_curveCombo)
        inputForm.addRow("端点 Fiducial:", self.profile_endpointsCombo)

        # 输出设置
        outputGroup = qt.QGroupBox("输出设置")
        outputForm = qt.QFormLayout(outputGroup)

        pathLayout = qt.QHBoxLayout()
        self.profile_outputDirLine = qt.QLineEdit()
        browseBtn = qt.QPushButton("浏览…")
        pathLayout.addWidget(self.profile_outputDirLine)
        pathLayout.addWidget(browseBtn)

        self.profile_csvNameLine = qt.QLineEdit("contour_auto.csv")

        outputForm.addRow("文件夹:", pathLayout)
        outputForm.addRow("CSV 文件名:", self.profile_csvNameLine)

        # 选项
        optionsGroup = qt.QGroupBox("选项")
        optionsLayout = qt.QVBoxLayout(optionsGroup)
        self.profile_clockwiseCheck = qt.QCheckBox("顺时针轮廓排序")
        self.profile_useCmCheck = qt.QCheckBox("输出 cm 单位 (mm→cm)")
        self.profile_scaleRadiusCheck = qt.QCheckBox("按等效半径归一化")
        self.profile_useCmCheck.setChecked(True)
        self.profile_scaleRadiusCheck.setChecked(True)
        optionsLayout.addWidget(self.profile_clockwiseCheck)
        optionsLayout.addWidget(self.profile_useCmCheck)
        optionsLayout.addWidget(self.profile_scaleRadiusCheck)

        # 执行按钮 & 状态
        runLayout = qt.QHBoxLayout()
        self.btn_generateVtk = qt.QPushButton("生成 VTK")
        self.btn_vtk2curve = qt.QPushButton("VTK → ClosedCurve")
        self.btn_curve2csv = qt.QPushButton("ClosedCurve → CSV")
        self.btn_vtk2curve.enabled = False
        self.btn_curve2csv.enabled = False
        self.profile_statusLabel = qt.QLabel()
        runLayout.addWidget(self.btn_generateVtk)
        runLayout.addWidget(self.btn_vtk2curve)
        runLayout.addWidget(self.btn_curve2csv)
        runLayout.addWidget(self.profile_statusLabel, 1)

        # 组装到主布局
        profileLayout.addWidget(inputGroup)
        profileLayout.addWidget(outputGroup)
        profileLayout.addWidget(optionsGroup)
        profileLayout.addLayout(runLayout)
        profileLayout.addStretch(1)

        self.mainTabWidget.addTab(profilePage, "剖面提取")

        # 连接信号
        browseBtn.clicked.connect(self.onBrowseProfileOutputDir)
        self.btn_generateVtk.clicked.connect(self.onGenerateVtks)
        self.btn_vtk2curve.clicked.connect(self.onVtkToCurves)
        self.btn_curve2csv.clicked.connect(self.onCurvesToCsv)

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
        # 如果嵌入的 Markups 小部件存在，则调用其 exit() 进行清理
        if hasattr(self, "markupsModuleWidget") and self.markupsModuleWidget is not None:
            try:
                if hasattr(self.markupsModuleWidget, "exit"):
                    self.markupsModuleWidget.exit()
            except Exception as e_exit_mk:
                print(f"WARNING: 调用 Markups 小部件 exit() 时发生异常: {type(e_exit_mk).__name__}: {e_exit_mk}")
        # 调用父类 cleanup（当前为空实现，留作兼容）
        try:
            ScriptedLoadableModuleWidget.cleanup(self)
        except Exception:
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

    def onBrowseProfileOutputDir(self):
        dirPath = qt.QFileDialog.getExistingDirectory(self.parent, "选择输出文件夹")
        if dirPath:
            self.profile_outputDirLine.setText(dirPath)

    def onGenerateVtks(self):
        """第一步：根据用户输入切割模型并将轮廓直接保存为 .vtk 文件。

        不创建 ClosedCurve，仅在场景中生成中间 ModelNode（便于可视化），
        同时把每个轮廓保存为 VTK PolyData 文件，供第二步转换为 ClosedCurve。
        """

        import numpy as _np  # 局部引用，避免与模块顶层命名冲突

        # ---- 0. 基本校验 ----
        modelNode = self.profile_modelCombo.currentNode()
        curveNode = self.profile_curveCombo.currentNode()
        endpointsNode = self.profile_endpointsCombo.currentNode()

        if modelNode is None or curveNode is None:
            slicer.util.errorDisplay("请先选择有效的模型节点和中心线曲线节点！")
            return

        outputDir = self.profile_outputDirLine.text.strip()
        if not outputDir:
            slicer.util.errorDisplay("请指定输出文件夹！")
            return

        os.makedirs(outputDir, exist_ok=True)

        clockwiseContour = self.profile_clockwiseCheck.isChecked()
        # 是否使用端点：若端点节点存在且点数≥2，则采用 UI 复选框（目前默认总使用）
        use_curve_endpoints = True
        if endpointsNode is None or endpointsNode.GetNumberOfControlPoints() < 2:
            use_curve_endpoints = True  # 如果没有额外端点节点，则使用曲线自身端点

        # ---- 1. 获取曲线控制点 ----
        nCurve = curveNode.GetNumberOfControlPoints()
        if nCurve < 3:
            slicer.util.errorDisplay("中心线控制点不足 3，无法计算切向量！")
            return

        pts = _np.array([curveNode.GetNthControlPointPositionWorld(i) for i in range(nCurve)])

        if not use_curve_endpoints and pts.shape[0] > 2:
            pts = pts[1:-1]

        # 如果 endpointsNode 提供两端点并且启用端点，则在曲线点前后补充
        if endpointsNode and endpointsNode.GetNumberOfControlPoints() >= 2 and use_curve_endpoints:
            start_pt = _np.array(endpointsNode.GetNthControlPointPositionWorld(0))
            end_pt = _np.array(endpointsNode.GetNthControlPointPositionWorld(1))
            pts = _np.vstack([start_pt, pts, end_pt])

        # ---- 2. 计算切向量 ----
        v = _np.zeros_like(pts)
        if len(pts) >= 3:
            v[1:-1] = (pts[2:] - pts[:-2]) * 0.5
        v[0] = pts[1] - pts[0]
        v[-1] = pts[-1] - pts[-2]

        t = _np.zeros_like(v)
        if len(pts) >= 3:
            t[1:-1] = (v[:-2] + v[1:-1] + v[2:]) / 3
        if len(pts) >= 2:
            t[0] = t[1]
            t[-1] = t[-2]

        norm = _np.linalg.norm(t, axis=1)
        norm[norm == 0] = 1
        t = t / norm[:, None]

        # ---- 3. cutter 设置 ----
        plane = vtk.vtkPlane()
        cutter = vtk.vtkCutter()
        cutter.SetInputData(modelNode.GetPolyData())
        cutter.SetCutFunction(plane)

        # ---- 4. 循环切割并保存 ----
        saved = 0
        for i, (P, N) in enumerate(zip(pts, t)):
            plane.SetOrigin(*P); plane.SetNormal(*N)
            cutter.Update()

            poly = vtk.vtkPolyData(); poly.DeepCopy(cutter.GetOutput())
            if poly.GetNumberOfPoints() < 3:
                slicer.util.logMessage(f"[!] Slice {i:03d}: 无交线，跳过")
                continue

            # 若点数>3，则根据极角排序保证顺序一致性
            if poly.GetNumberOfPoints() > 3:
                pts_np = _np.array([poly.GetPoint(j) for j in range(poly.GetNumberOfPoints())])

                # 生成局部基
                ref = _np.array([0, 0, 1]) if abs(N[2]) < 0.9 else _np.array([0, 1, 0])
                t_axis = _np.cross(N, ref); t_axis[1] *= -1
                t_axis = t_axis / (_np.linalg.norm(t_axis) or 1)
                b_axis = _np.cross(N, t_axis)

                local_y = (pts_np - P) @ t_axis
                local_z = (pts_np - P) @ b_axis
                angles = _np.arctan2(local_z, local_y)
                order = _np.argsort(angles)
                if clockwiseContour:
                    order = order[::-1]

                # 重新构建 PolyData
                reorder_pts = vtk.vtkPoints()
                for idx in order:
                    reorder_pts.InsertNextPoint(pts_np[idx])

                poly2 = vtk.vtkPolyData(); poly2.SetPoints(reorder_pts)
                poly2.Allocate()
                line = vtk.vtkPolyLine()
                line.GetPointIds().SetNumberOfIds(len(order))
                for k in range(len(order)):
                    line.GetPointIds().SetId(k, k)
                poly2.InsertNextCell(line.GetCellType(), line.GetPointIds())
                poly = poly2

            # 在场景中创建可视化模型节点
            mdl_name = f"SliceContour_{i:03d}"
            mdl = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLModelNode', mdl_name)
            mdl.SetAndObservePolyData(poly)
            mdl.CreateDefaultDisplayNodes()
            if mdl.GetDisplayNode():
                mdl.GetDisplayNode().SetColor(0.2, 1.0, 0.4)
                mdl.GetDisplayNode().SetOpacity(0.6)

            # 保存 .vtk 文件
            out_path = os.path.join(outputDir, f"{mdl_name}.vtk")
            try:
                slicer.util.saveNode(mdl, out_path)
                saved += 1
            except Exception as _e:
                slicer.util.logMessage(f"保存 {out_path} 失败: {_e}")

        msg = f"共保存 {saved} 个 VTK 轮廓到 {outputDir}" if saved else "未能生成任何 VTK 轮廓。"

        self.profile_statusLabel.setText(msg)
        slicer.app.processEvents()

        # 缓存参数供后续使用（即使没保存成功，也缓存，便于调试）
        self._profile_cache = {
            "modelNode": modelNode,
            "curveNode": curveNode,
            "endpointsNode": endpointsNode,
            "useEndpoints": use_curve_endpoints,
            "outputDir": outputDir,
            "clockwise": clockwiseContour,
            "useCm": self.profile_useCmCheck.isChecked(),
            "scaleByRadius": self.profile_scaleRadiusCheck.isChecked(),
        }

        # 更新按钮状态
        self.btn_vtk2curve.enabled = saved > 0
        self.btn_curve2csv.enabled = False  # 需等待第二步完成
        if saved == 0:
            slicer.util.errorDisplay(msg)
        else:
            slicer.util.infoDisplay(msg)

    def onVtkToCurves(self):
        """第二步：把由 onGenerateVtks 生成的 `SliceContour_###` 模型转为 ClosedCurve。

        处理流程：
        1. 收集名称匹配 "SliceContour_###" 的 `vtkMRMLModelNode`，按编号升序排序。
        2. 对每个节点读取 PolyData 点序列，依次添加到新建 `vtkMRMLMarkupsClosedCurveNode`。
        3. 设置基本显示属性，命名保持编号一致，如 `SliceCurve_###`。
        4. 统计并在 UI 中反馈，若成功至少 1 条即启用 CSV 导出按钮。
        """

        import re

        # ---- 1. 收集并排序 ----
        pattern = re.compile(r"^SliceContour_(\d{3,})$", re.IGNORECASE)
        model_nodes = []
        for node in slicer.util.getNodesByClass("vtkMRMLModelNode"):
            name = node.GetName() or ""
            m = pattern.match(name)
            if m:
                idx = int(m.group(1))
                model_nodes.append((idx, node))

        if not model_nodes:
            slicer.util.infoDisplay("未找到任何 SliceContour_### VTK 模型，无法转换！")
            self.btn_curve2csv.enabled = False
            return

        # 根据编号排序
        model_nodes.sort(key=lambda x: x[0])

        # ---- 2. 转换 ----
        created = 0
        # 在整个批量过程中暂停视图渲染，末尾自动恢复
        with slicer.util.RenderBlocker():
            for idx, mdl in model_nodes:
                pd = mdl.GetPolyData()
                if pd is None or pd.GetNumberOfPoints() < 3:
                    continue

                # 已存在对应 ClosedCurve 则跳过
                existing = slicer.mrmlScene.GetFirstNodeByName(f"SliceCurve_{idx:03d}")
                if existing and isinstance(existing, slicer.vtkMRMLMarkupsClosedCurveNode):
                    continue

                curveNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsClosedCurveNode', f"SliceCurve_{idx:03d}")
                curveNode.CreateDefaultDisplayNodes()
                disp = curveNode.GetDisplayNode()
                if disp:
                    disp.SetColor(1.0, 0.8, 0.2)
                    disp.SetOpacity(0.8)
                    # 缩小控制点与线宽
                    try:
                        if hasattr(disp, "SetGlyphScale"):
                            disp.SetGlyphScale(0.5)
                        if hasattr(disp, "SetLineThickness"):
                            disp.SetLineThickness(0.5)
                    except Exception as _e_disp:
                        slicer.util.logMessage(f"设置 ClosedCurve 显示属性时发生异常: {_e_disp}")

                # 批量添加控制点，使用 NodeModify 上下文抑制多次 Modified 事件
                with slicer.util.NodeModify(curveNode):
                    for i in range(pd.GetNumberOfPoints()):
                        curveNode.AddControlPointWorld(pd.GetPoint(i))

                created += 1

        # ---- 3. 结果反馈 ----
        msg = f"已创建 {created} 条 ClosedCurve" if created else "所有轮廓已存在，无需转换。"
        self.profile_statusLabel.setText(msg)
        slicer.app.processEvents()

        # ---- 4. 按钮状态 ----
        self.btn_curve2csv.enabled = created > 0
        if created > 0:
            slicer.util.infoDisplay(msg)
        else:
            slicer.util.infoDisplay(msg)

    def onCurvesToCsv(self):
        """第三步：遍历 SliceCurve_### ClosedCurve 节点并导出 CSV。

        不再重新切割模型，直接使用用户（可能已编辑）的 ClosedCurve 数据。
        CSV 格式与前两步保持一致：两行/截面，包含中心点、参考轴、缩放因子及轮廓点投影坐标。
        """

        import re, csv as _csv, numpy as _np, math, vtk

        if not hasattr(self, "_profile_cache"):
            slicer.util.errorDisplay("请先执行前两步生成并转换截面！")
            return

        params = self._profile_cache

        outputDir = params["outputDir"]
        csvName = self.profile_csvNameLine.text.strip() or "contour_auto.csv"

        clockwise = params["clockwise"]
        useCm = params["useCm"]
        scaleByRadius = params["scaleByRadius"]

        # ---- 1. 收集曲线 ----
        pattern = re.compile(r"^SliceCurve_(\d{3,})$", re.IGNORECASE)
        curve_nodes = []
        for node in slicer.util.getNodesByClass("vtkMRMLMarkupsClosedCurveNode"):
            m = pattern.match(node.GetName() or "")
            if m:
                idx = int(m.group(1))
                curve_nodes.append((idx, node))

        if not curve_nodes:
            slicer.util.errorDisplay("未找到任何 SliceCurve_### 曲线，无法导出！")
            return

        curve_nodes.sort(key=lambda x: x[0])

        os.makedirs(outputDir, exist_ok=True)
        outputCsvPath = os.path.join(outputDir, csvName)

        saved = 0
        centerline_out = []

        with open(outputCsvPath, "w", newline="") as f_csv:
            writer = _csv.writer(f_csv, delimiter=";")

            for idx, curveNode in curve_nodes:
                n_pts = curveNode.GetNumberOfControlPoints()
                if n_pts < 3:
                    continue

                pts_np = _np.array([curveNode.GetNthControlPointPositionWorld(i) for i in range(n_pts)])

                # ---- 2. 计算平面法向 (PCA) ----
                pts_centered = pts_np - pts_np.mean(axis=0)
                cov = _np.cov(pts_centered.T)
                eig_vals, eig_vecs = _np.linalg.eigh(cov)
                N = eig_vecs[:, 0]            # 最小特征值对应向量
                N = N / (_np.linalg.norm(N) or 1)

                # ---- 3. 参考轴 t_axis, b_axis ----
                ref = _np.array([0, 0, 1]) if abs(N[2]) < 0.9 else _np.array([0, 1, 0])
                t_axis = _np.cross(N, ref); t_axis[1] *= -1
                t_axis = t_axis / (_np.linalg.norm(t_axis) or 1)
                b_axis = _np.cross(N, t_axis)

                # ---- 4. 投影（保持 ClosedCurve 原有点顺序） ----
                local_y_ord = (pts_np - pts_np.mean(axis=0)) @ t_axis
                local_z_ord = (pts_np - pts_np.mean(axis=0)) @ b_axis

                # ---- 5. 计算缩放因子 ----
                scale_val = 1.0
                if scaleByRadius:
                    # 计算投影后多边形面积 (shoelace)
                    x2d, y2d = local_y_ord, local_z_ord
                    area2d = 0.5 * abs(_np.dot(x2d, _np.roll(y2d, -1)) - _np.dot(y2d, _np.roll(x2d, -1)))
                    r_mm = math.sqrt(area2d / math.pi) if area2d > 0 else 1.0
                    if r_mm > 1e-6:
                        local_y_ord /= r_mm
                        local_z_ord /= r_mm
                    scale_val = r_mm / (10.0 if useCm else 1.0)

                # ---- 6. 导出 ----
                centroid = pts_np.mean(axis=0)
                P_out = centroid / 10.0 if useCm else centroid.copy()

                writer.writerow([P_out[0], t_axis[0], scale_val, *_np.round(local_y_ord, 6)])
                writer.writerow([P_out[1], t_axis[1], scale_val, *_np.round(local_z_ord, 6)])

                saved += 1
                centerline_out.append(P_out.tolist())

        # 额外保存中心点序列
        cl_path = os.path.join(outputDir, "centerline_from_curves.csv")
        with open(cl_path, "w", newline="") as fcl:
            w = _csv.writer(fcl, delimiter=";")
            w.writerow(["X", "Y", "Z"])
            w.writerows(centerline_out)

        msg = f"已导出 {saved} 条曲线到 {outputCsvPath}" if saved else "CSV 导出失败，未处理曲线。"

        self.profile_statusLabel.setText(msg)
        slicer.app.processEvents()

        if saved:
            slicer.util.infoDisplay(msg)
        else:
            slicer.util.errorDisplay(msg)

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

    def extractContoursToCsv(self, modelNode, curveNode, endpointsNode, useEndpoints, outputDir, csvName, clockwise, useCm, scaleByRadius, saveVtk):
        """Extract contour slices along centerline and save to CSV.

        Parameters
        ----------
        modelNode : vtkMRMLModelNode
            Closed lumen model to be cut.
        curveNode : vtkMRMLMarkupsCurveNode
            Centerline curve (control points serve as section centers).
        endpointsNode : vtkMRMLMarkupsFiducialNode | None
            Two-point fiducial defining explicit endpoints (optional).
        useEndpoints : bool
            If True, prepend/append the endpoints to centerline list.
        outputDir : str
            Directory to save CSV.
        csvName : str
            File name of CSV.
        clockwise, useCm, scaleByRadius : bool
            Export options, see UI.

        Returns
        -------
        (bool, str)
            Success flag and message.
        """
        try:
            # Validate nodes
            if modelNode is None or curveNode is None:
                return False, "模型或中心线节点为空。"

            # Obtain vtkPolyData from model or segmentation
            if isinstance(modelNode, slicer.vtkMRMLSegmentationNode):
                segIds = vtk.vtkStringArray()
                modelNode.GetSegmentation().GetSegmentIDs(segIds)
                if segIds.GetNumberOfValues() == 0:
                    return False, "分割节点中没有 Segment。"
                segId = segIds.GetValue(0)

                # 确保存在闭合曲面
                polyData = vtk.vtkPolyData()
                success = modelNode.GetClosedSurfaceRepresentation(segId, polyData)
                if (not success) or polyData.GetNumberOfPoints() == 0:
                    return False, "无法从分割节点获取有效闭合曲面表示。"
            else:
                polyData = modelNode.GetPolyData()
            if polyData is None or polyData.GetNumberOfPoints() == 0:
                return False, "模型 PolyData 无效或为空。"

            numCurvePts = curveNode.GetNumberOfControlPoints()
            if numCurvePts < 3:
                return False, "中心线控制点不足 3 个。"

            # Build points list (numpy Nx3)
            pts_list = []

            if useEndpoints and endpointsNode is not None and endpointsNode.GetNumberOfControlPoints() >= 2:
                pts_list.append(np.array(endpointsNode.GetNthControlPointPositionWorld(0)))

            # curve control points
            for i in range(numCurvePts):
                pts_list.append(np.array(curveNode.GetNthControlPointPositionWorld(i)))

            if useEndpoints and endpointsNode is not None and endpointsNode.GetNumberOfControlPoints() >= 2:
                pts_list.append(np.array(endpointsNode.GetNthControlPointPositionWorld(1)))

            pts = np.vstack(pts_list)

            if pts.shape[0] < 3:
                return False, "截面点数不足 3，无法计算切向量。"

            # Helper functions
            EPS = 1e-6

            def normalize(v):
                n = np.linalg.norm(v)
                return v / n if n > EPS else np.array([1.0, 0.0, 0.0])

            # Compute tangents (3-point moving average)
            v = np.zeros_like(pts)
            v[1:-1] = (pts[2:] - pts[:-2]) * 0.5
            v[0] = pts[1] - pts[0]
            v[-1] = pts[-1] - pts[-2]

            t = np.zeros_like(pts)
            t[1:-1] = (v[:-2] + v[1:-1] + v[2:]) / 3.0
            t[0] = t[1]
            t[-1] = t[-2]
            tangents = np.array([normalize(vec) for vec in t])

            # Prepare cutter
            plane = vtk.vtkPlane()
            cutter = vtk.vtkCutter()
            cutter.SetInputData(polyData)
            cutter.SetCutFunction(plane)

            # Utils
            def compute_reference_axes(n_vec):
                ref = np.array([0, 0, 1]) if abs(n_vec[2]) < 0.9 else np.array([0, 1, 0])
                t_axis = normalize(np.cross(n_vec, ref) * np.array([1, -1, 1]))
                b_axis = np.cross(n_vec, t_axis)
                return t_axis, b_axis

            def equivalent_radius(pd):
                tf = vtk.vtkTriangleFilter()
                tf.SetInputData(pd)
                tf.Update()
                mp = vtk.vtkMassProperties()
                mp.SetInputConnection(tf.GetOutputPort())
                mp.Update()
                area = mp.GetSurfaceArea()
                return math.sqrt(area / math.pi) if area > 0 else 1.0

            # Ensure output directory
            os.makedirs(outputDir, exist_ok=True)
            outputCsv = os.path.join(outputDir, csvName)

            saved = 0
            centerline_out = []

            with open(outputCsv, 'w', newline='') as f_csv:
                writer = csv.writer(f_csv, delimiter=';')

                for idx, (P, N) in enumerate(zip(pts, tangents)):
                    plane.SetOrigin(*P)
                    plane.SetNormal(*N)
                    cutter.Update()

                    slicePoly = vtk.vtkPolyData()
                    slicePoly.DeepCopy(cutter.GetOutput())

                    if slicePoly.GetNumberOfPoints() < 3:
                        self._updateStatus(f"Slice {idx:03d}: 无交线，跳过")
                        continue

                    pts_np = np.array([slicePoly.GetPoint(i) for i in range(slicePoly.GetNumberOfPoints())])

                    N_vec = normalize(N)
                    t_axis, b_axis = compute_reference_axes(N_vec)

                    local_y = (pts_np - P) @ t_axis
                    local_z = (pts_np - P) @ b_axis

                    # Optional scaling
                    if scaleByRadius:
                        r_mm = equivalent_radius(slicePoly)
                        if r_mm > EPS:
                            local_y /= r_mm
                            local_z /= r_mm
                    scale_val = 1.0 if not scaleByRadius else equivalent_radius(slicePoly) / (10.0 if useCm else 1.0)

                    # Sort by angle
                    angles = np.arctan2(local_z, local_y)
                    sort_idx = np.argsort(angles)
                    if clockwise:
                        sort_idx = sort_idx[::-1]
                    local_y = local_y[sort_idx]
                    local_z = local_z[sort_idx]

                    # Unit conversion
                    P_out = P / 10.0 if useCm else P.copy()

                    writer.writerow([P_out[0], t_axis[1], scale_val, *local_y])
                    writer.writerow([P_out[1], t_axis[0], scale_val, *local_z])

                    # --- 可视化并可选保存 VTK ---
                    if saveVtk:
                        # 使用 Markups ClosedCurve 以便后续交互编辑
                        curveNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsClosedCurveNode', f'SliceCurve_{idx:03d}')
                        curveNode.CreateDefaultDisplayNodes()
                        disp = curveNode.GetDisplayNode()
                        if disp:
                            disp.SetColor(0.2, 1.0, 0.4)
                            disp.SetOpacity(0.6)

                        # 添加控制点（保持顺序）
                        ordered_pts = pts_np[sort_idx]
                        for pt in ordered_pts:
                            curveNode.AddControlPointWorld(pt.tolist())

                        # 可选保存为 .mrk.json 文件
                        jsonPath = os.path.join(outputDir, f'SliceCurve_{idx:03d}.mrk.json')
                        try:
                            slicer.util.saveNode(curveNode, jsonPath)
                        except Exception:
                            pass

                    saved += 1
                    centerline_out.append(P_out.tolist())

            if saved == 0:
                return False, "未能生成任何截面，CSV 未创建。"

            self._updateStatus(f"共写入 {saved} 条截面 → {outputCsv}")

            # 额外保存中心线
            cl_path = os.path.join(outputDir, 'centerline.csv')
            with open(cl_path, 'w', newline='') as fcl:
                w = csv.writer(fcl, delimiter=';')
                w.writerow(['X', 'Y', 'Z'])
                w.writerows(centerline_out)

            return True, f"剖面提取完成，{saved} 条截面已保存到 {outputCsv}"

        except Exception as e:
            import traceback, io
            tb = io.StringIO()
            traceback.print_exc(file=tb)
            self._updateStatus(tb.getvalue())
            return False, f"剖面提取失败: {type(e).__name__}: {e}"

    pass

