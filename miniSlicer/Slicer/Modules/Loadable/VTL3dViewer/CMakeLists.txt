cmake_minimum_required(VERSION 3.16)

# Ensure Slicer loadable module macros are available
# Note: Might be redundant if already included by parent, but usually safe to keep.
include(SlicerMacroBuildLoadableModule)

# -----------------------------------------------------------------------------
# Build the VTL3d GUI library (libVTL3dGui.so) from the VTL3D_1.0 subdirectory first.
# This makes the "VTL3dGui" target available for linking.
add_subdirectory(VTL3D_1.0)

# -----------------------------------------------------------------------------
set(MODULE_NAME VTL3dViewer)
string(TOUPPER ${MODULE_NAME} MODULE_NAME_UPPER)

# -----------------------------------------------------------------------------
# Sources for the VTL3dViewer Slicer module itself
set(MODULE_SRCS
  qSlicer${MODULE_NAME}Module.cxx
  qSlicer${MODULE_NAME}Module.h
  qSlicer${MODULE_NAME}ModuleWidget.cxx
  qSlicer${MODULE_NAME}ModuleWidget.h
  vtkSlicer${MODULE_NAME}ModuleLogic.cxx
  vtkSlicer${MODULE_NAME}ModuleLogic.h
  )

# -----------------------------------------------------------------------------
# Explicitly list headers that require MOC processing (contain Q_OBJECT)
set(MODULE_MOC_SRCS
  qSlicer${MODULE_NAME}Module.h
  qSlicer${MODULE_NAME}ModuleWidget.h
  )

# -----------------------------------------------------------------------------
# Export directive for qSlicer... classes (e.g., qSlicerVTL3dViewerModule)
set(MODULE_EXPORT_DIRECTIVE "Q_SLICER_QTMODULES_${MODULE_NAME_UPPER}_EXPORT")

# -----------------------------------------------------------------------------
# Ensure Slicer's export header template for Qt modules is defined.
# Slicer_SOURCE_DIR should be correctly set by the parent Slicer CMakeLists.txt
if(NOT DEFINED Slicer_EXPORT_HEADER_TEMPLATE AND DEFINED Slicer_SOURCE_DIR)
  set(Slicer_EXPORT_HEADER_TEMPLATE "${Slicer_SOURCE_DIR}/CMake/qSlicerExport.h.in" CACHE INTERNAL "")
endif()

# -----------------------------------------------------------------------------
# Specify target libraries for the VTL3dViewer module.
# VTL3dGui is built from the VTL3D_1.0 subdirectory.
# Slicer core libraries (CTK, VTK, ITK, Qt etc.) are linked implicitly 
# by slicerMacroBuildLoadableModule via Slicer_GUI_LIBRARY.
set(MODULE_TARGET_LIBRARIES VTL3dGui)

# -----------------------------------------------------------------------------
# Build the Slicer Loadable Module
slicerMacroBuildLoadableModule(
  NAME ${MODULE_NAME}
  EXPORT_DIRECTIVE ${MODULE_EXPORT_DIRECTIVE}
  SRCS ${MODULE_SRCS}
  MOC_SRCS ${MODULE_MOC_SRCS}
  TARGET_LIBRARIES ${MODULE_TARGET_LIBRARIES}
  # MOC_SRCS, UI_SRCS, RESOURCES can be added here if the VTL3dViewer module
  # itself has Qt UI files or additional resources beyond the VTL3dGui library.
  ) 