"""
VTL3dBridge
===========
一个最小化 ScriptedLoadableModule，用于在 miniSlicer 中调用外部 VTL3d 可执行文件，
并将其生成的 CSV 结果导入到 Slicer 中以表格形式展示。

• 依赖：外部 VTL3d 可执行文件能够通过命令行生成 CSV 文件。
• 使用方法：
  1. 在模块界面中设置 VTL3d 可执行文件路径与 CSV 输出目录；
  2. 点击【Run VTL3d】按钮；
  3. 计算完成后，CSV 会自动导入并显示在 Table 视图中。
"""

import csv
import glob
import logging
import os
import subprocess
import time

import qt
import ctk
import slicer
import vtk
from slicer.ScriptedLoadableModule import (
    ScriptedLoadableModule,
    ScriptedLoadableModuleWidget,
    ScriptedLoadableModuleLogic,
)


# ----------------------------------------------------------------------------
class VTL3dBridge(ScriptedLoadableModule):
    """模块元数据。"""

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "VTL3dBridge"
        self.parent.categories = ["VTL3d"]
        self.parent.contributors = ["miniSlicer team"]
        self.parent.helpText = (
            "使用外部 VTL3d 可执行文件完成计算，并自动导入其 CSV 结果。"
        )
        self.parent.acknowledgementText = "基于 3D Slicer Scripted 模块模板修改。"


# ----------------------------------------------------------------------------
class VTL3dBridgeWidget(ScriptedLoadableModuleWidget):
    """模块界面。"""

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        self.logic = VTL3dBridgeLogic()

        settings = qt.QSettings()

        # 界面布局 ------------------------------------------------------------
        mainCollapsible = ctk.ctkCollapsibleButton()
        mainCollapsible.text = "VTL3d 设置"
        self.layout.addWidget(mainCollapsible)

        formLayout = qt.QFormLayout(mainCollapsible)

        # VTL3d 可执行文件路径
        self.exePathWidget = ctk.ctkPathLineEdit()
        defaultExe = settings.value("VTL3dBridge/exePath", "")
        self.exePathWidget.currentPath = defaultExe
        formLayout.addRow("VTL3d 可执行文件:", self.exePathWidget)

        # CSV 文件路径（导入剖面）
        self.csvPathWidget = ctk.ctkPathLineEdit()
        defaultCsv = settings.value("VTL3dBridge/csvPath", "")
        self.csvPathWidget.currentPath = defaultCsv
        formLayout.addRow("CSV 文件:", self.csvPathWidget)

        # Executable 输出目录（可选，若需要写文件）
        self.outDirWidget = ctk.ctkPathLineEdit()
        self.outDirWidget.filters = ctk.ctkPathLineEdit.Dirs
        defaultOutDir = settings.value("VTL3dBridge/outDir", qt.QDir.homePath())
        self.outDirWidget.currentPath = defaultOutDir
        formLayout.addRow("CSV 输出目录:", self.outDirWidget)

        # 按钮布局
        btnLayout = qt.QHBoxLayout()
        self.launchButton = qt.QPushButton("Launch VTL3d (nixGL)")
        self.importButton = qt.QPushButton("Import CSV")
        btnLayout.addWidget(self.launchButton)
        btnLayout.addWidget(self.importButton)
        formLayout.addRow(btnLayout)

        self.launchButton.connect("clicked()", self.onLaunch)
        self.importButton.connect("clicked()", self.onImportCsv)

        # 日志输出
        self.logOutput = qt.QPlainTextEdit()
        self.logOutput.setReadOnly(True)
        formLayout.addRow(self.logOutput)

        self.layout.addStretch(1)

    # --------------------------------------------------------------------
    def onLaunch(self):
        """使用 nixGL 启动 VTL3d GUI。"""
        exePath = self.exePathWidget.currentPath
        if not os.path.isfile(exePath):
            slicer.util.errorDisplay("VTL3d 可执行文件路径无效！")
            return

        # 保存设置
        qt.QSettings().setValue("VTL3dBridge/exePath", exePath)

        try:
            self.log("通过 nixGL 启动 VTL3d…")
            subprocess.Popen(["nixGL", exePath])
        except FileNotFoundError:
            slicer.util.errorDisplay("未找到 nixGL，请确认已安装并在 PATH 中！")
        except Exception as e:
            slicer.util.errorDisplay(f"启动失败: {e}")
            logging.exception(e)

    # --------------------------------------------------------------------
    def onImportCsv(self):
        """导入用户指定的 CSV 文件到表格视图。"""
        csvPath = self.csvPathWidget.currentPath
        if not os.path.isfile(csvPath):
            # 若路径为空，则弹出文件对话框
            csvPath, _ = qt.QFileDialog.getOpenFileName(
                self.parentWidget(), "选择 CSV 文件", qt.QDir.homePath(), "CSV (*.csv)"
            )
            if not csvPath:
                return
            self.csvPathWidget.currentPath = csvPath

        # 保存路径
        qt.QSettings().setValue("VTL3dBridge/csvPath", csvPath)

        try:
            self.logic.importCsv(csvPath)
            self.log(f"已导入 {csvPath}")
        except Exception as e:
            slicer.util.errorDisplay(f"CSV 导入失败: {e}")
            logging.exception(e)

    # --------------------------------------------------------------------
    def log(self, text):
        self.logOutput.appendPlainText(text)
        logging.info(text)


# ----------------------------------------------------------------------------
class VTL3dBridgeLogic(ScriptedLoadableModuleLogic):
    """处理核心逻辑，如 CSV 解析。"""

    def importCsv(self, csvPath):
        tableNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode", os.path.basename(csvPath))

        with open(csvPath, newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)

        if not rows:
            raise RuntimeError("CSV 文件为空！")

        # 假设第一行是表头或数据？这里直接按列填充
        cols = list(zip(*rows))
        for colIdx, colData in enumerate(cols):
            array = vtk.vtkDoubleArray()
            array.SetName(f"Col{colIdx}")
            for value in colData:
                try:
                    array.InsertNextValue(float(value))
                except ValueError:
                    # 如果无法转换则填 0
                    array.InsertNextValue(0.0)
            tableNode.AddColumn(array)

        # 显示 Table
        slicer.modules.tables.logic().AddDefaultTableView(tableNode) 