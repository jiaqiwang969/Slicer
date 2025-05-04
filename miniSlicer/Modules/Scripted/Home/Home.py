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

# Import to ensure the files are available through the Qt resource system
from Resources import HomeResources  # noqa: F401


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

    def setup(self):
        """Called when the application opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer)
        self.uiWidget = slicer.util.loadUI(self.resourcePath("UI/Home.ui"))
        self.layout.addWidget(self.uiWidget)
        self.ui = slicer.util.childWidgetVariables(self.uiWidget)

        # Get references to relevant underlying modules
        # NA

        # --- Get UI elements defined in Home.ui ---
        # Assuming 'loadMRHeadButton' and 'statusLabel' are defined in Home.ui
        if not hasattr(self.ui, 'loadMRHeadButton'):
            print("WARNING: loadMRHeadButton not found in UI definition!")
            self.ui.loadMRHeadButton = None # Avoid errors later
        if not hasattr(self.ui, 'statusLabel'):
            print("WARNING: statusLabel not found in UI definition!")
            self.ui.statusLabel = None # Avoid errors later

        # Create logic class
        self.logic = HomeLogic(self.ui.statusLabel) # Pass label for status updates

        # Dark palette does not propagate on its own
        # See https://github.com/KitwareMedical/SlicerCustomAppTemplate/issues/72
        self.uiWidget.setPalette(slicer.util.mainWindow().style().standardPalette())

        # Remove unneeded UI elements
        self.modifyWindowUI()
        self.setCustomUIVisible(True)

        # Apply style
        self.applyApplicationStyle()

        # --- Add Hello World Button --- 
        self.helloButton = qt.QPushButton("Say Hello to wjq")
        # Add the button to the main layout of the loaded UI widget
        # Assuming the top-level widget in Home.ui has a layout accessible via self.uiWidget.layout()
        # If Home.ui has a specific named layout (e.g., 'verticalLayout'), use that instead:
        # e.g., self.ui.verticalLayout.addWidget(self.helloButton)
        if self.uiWidget.layout() is not None:
            self.uiWidget.layout().addWidget(self.helloButton)
        else:
            # Fallback: Create a new layout if none exists (less likely for a loaded UI)
            fallbackLayout = qt.QVBoxLayout(self.uiWidget)
            fallbackLayout.addWidget(self.helloButton)
            print("HomeWidget: Added Hello button to a fallback layout.")

        self.helloButton.clicked.connect(self.onHelloButtonClicked)
        # --- End Hello World Button ---

        # --- Connect signals for UI elements from Home.ui ---
        if self.ui.loadMRHeadButton:
            self.ui.loadMRHeadButton.clicked.connect(self.onLoadMRHeadClicked)
        # --- End Connect signals ---

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

    # --- Slot for Hello World Button --- 
    def onHelloButtonClicked(self):
        """Called when the 'Say Hello' button is clicked."""
        qt.QMessageBox.information(self.uiWidget, "Greeting", "Hello World from miniSlicer!")
    # --- End Slot --- 

    # --- Slot for Load MRHead Button --- 
    def onLoadMRHeadClicked(self):
        """Called when the 'Load MRHead Data' button is clicked."""
        # Prevent double-clicks or clicks while loading
        if self.ui.loadMRHeadButton:
            self.ui.loadMRHeadButton.enabled = False
        # Run loading in logic, re-enable button when done (via status update perhaps)
        self.logic.loadMRHeadData()
        # Consider enabling the button after a short delay or via a signal from logic if loading is long
        # For simplicity here, we re-enable immediately after triggering logic
        if self.ui.loadMRHeadButton:
             self.ui.loadMRHeadButton.enabled = True
    # --- End Slot ---


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
            self.statusLabel.text = f"Status: {message}"
        print(f"HomeLogic Status: {message}") # Also print to console

    def loadMRHeadData(self):
        """Loads the MRHead sample data."""
        self._updateStatus("Loading MRHead data...")
        slicer.app.processEvents() # Allow UI to update status before potentially blocking operation
        try:
            sampleDataLogic = slicer.modules.sampledata.logic()
            # Ensure SampleData module is available
            if not sampleDataLogic:
                raise RuntimeError("SampleData module logic not found.")
            
            mrHeadVolumeNode = sampleDataLogic.downloadMRHead()
            if mrHeadVolumeNode:
                self._updateStatus("MRHead data loaded successfully.")
                # Optional: Center the 3D view on the loaded volume
                slicer.app.layoutManager().resetThreeDViews()
                threeDView = slicer.app.layoutManager().threeDWidget(0).threeDView()
                threeDView.resetFocalPoint()
            else:
                # Check if node already exists (downloadMRHead might return None if already present)
                existingNode = slicer.mrmlScene.GetFirstNodeByName("MRHead")
                if existingNode:
                    self._updateStatus("MRHead data already loaded.")
                else:
                    self._updateStatus("Failed to load MRHead data (download failed?).")
        except Exception as e:
            self._updateStatus(f"Error loading MRHead data: {e}")
            slicer.util.errorDisplay(f"Failed to load MRHead data: {e}")
        finally:
             slicer.app.processEvents() # Allow UI to update after loading attempt

    pass
