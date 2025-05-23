cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(SlicerVMTK)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/vmtk/SlicerExtension-VMTK")
set(EXTENSION_CATEGORY "Vascular Modeling Toolkit")
set(EXTENSION_CONTRIBUTORS "Daniel Haehn (Boston Childrens Hospital), Luca Antiga (Orobix), Steve Pieper (Isomics), Jean-Christophe Fillion-Robin (Kitware)")
set(EXTENSION_DESCRIPTION "Vascular Modeling Toolkit for vessel tree segmentation and centerline extraction.")
set(EXTENSION_STATUS "Beta")
set(EXTENSION_ICONURL "https://www.nitrc.org/project/screenshot.php?group_id=196&screenshot_id=269")
set(EXTENSION_SCREENSHOTURLS "https://www.nitrc.org/project/screenshot.php?group_id=196&screenshot_id=126 https://www.nitrc.org/project/screenshot.php?group_id=196&screenshot_id=227 https://www.nitrc.org/project/screenshot.php?group_id=196&screenshot_id=228 https://www.nitrc.org/project/screenshot.php?group_id=196&screenshot_id=229")
set(EXTENSION_DEPENDS "ExtraMarkups")
set(EXTENSION_LICENSE_FILE ${Slicer_LICENSE_FILE})
set(EXTENSION_README_FILE ${Slicer_README_FILE})
set(EXTENSION_BUILD_SUBDIRECTORY inner-build)

set(SUPERBUILD_TOPLEVEL_PROJECT inner)

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
# include(${Slicer_USE_FILE}) # Comment out: Not needed/valid when included directly in Slicer build via add_subdirectory.
# mark_as_superbuild(Slicer_DIR) # Comment out: Not needed/valid when included directly in Slicer build via add_subdirectory.

find_package(Git REQUIRED)
# mark_as_superbuild(GIT_EXECUTABLE) # Comment out: Superbuild specific macro, likely not needed here.

option(SlicerVMTK_USE_ExtraMarkups
  "This needs to be disabled if ExtraMarkups Slicer extension is unavailable" ON)

# find_package(ExtraMarkups REQUIRED) # Comment out: ExtraMarkups is built alongside VMTK within the Slicer build process, treat as internal target not external package.

#-----------------------------------------------------------------------------
# SuperBuild setup - ONLY run if building standalone, NOT when integrated into Slicer
if(NOT DEFINED Slicer_SOURCE_DIR) # Heuristic: Slicer_SOURCE_DIR is usually defined when built within Slicer

  option(${EXTENSION_NAME}_SUPERBUILD "Build ${EXTENSION_NAME} and the projects it depends on." ON)
  mark_as_advanced(${EXTENSION_NAME}_SUPERBUILD)
  if(${EXTENSION_NAME}_SUPERBUILD)
    message(STATUS "SlicerVMTK: Running in Standalone SuperBuild mode.")
    include("${CMAKE_CURRENT_SOURCE_DIR}/SuperBuild.cmake")
    return() # Exit early if we handled the SuperBuild
  endif()

else() # We ARE being built as part of Slicer
  message(STATUS "SlicerVMTK: Detected integration into Slicer build. Skipping own SuperBuild logic.")
  # Ensure the SUPERBUILD option is OFF in this context, just in case
  # This might be redundant now but provides clarity.
  set(${EXTENSION_NAME}_SUPERBUILD OFF)
endif()
#-----------------------------------------------------------------------------

# This part should now execute correctly when integrated
find_package(VMTK REQUIRED)

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(VesselnessFiltering)
add_subdirectory(LevelSetSegmentation)
if(${Slicer_VERSION_MAJOR}.${Slicer_VERSION_MINOR} VERSION_GREATER_EQUAL 4.11)
  # New-generation centerline computation - only available for recent Slicer versions
  add_subdirectory(ExtractCenterline)
else()
  add_subdirectory(CenterlineComputation)
endif()
add_subdirectory(QuickArterySegmentation)
add_subdirectory(GuidedArterySegmentation)
add_subdirectory(GuidedVeinSegmentation)
add_subdirectory(StenosisMeasurement1D)
add_subdirectory(StenosisMeasurement2D)
add_subdirectory(BranchClipper)
add_subdirectory(ArterialCalcificationPreProcessor)
add_subdirectory(CenterlineDisassembly)
add_subdirectory(ClipVessel)
if(SlicerVMTK_USE_ExtraMarkups)
  add_subdirectory(CrossSectionAnalysis)
  add_subdirectory(StenosisMeasurement3D)
  add_subdirectory(EditCenterline)
endif()

#-----------------------------------------------------------------------------
set(EXTENSION_CPACK_INSTALL_CMAKE_PROJECTS)
if(NOT APPLE)
  list(APPEND EXTENSION_CPACK_INSTALL_CMAKE_PROJECTS "${VMTK_DIR};VMTK;RuntimeLibraries;/")
endif()
list(APPEND EXTENSION_CPACK_INSTALL_CMAKE_PROJECTS "${VMTK_DIR};VMTK;PythonRuntimeLibraries;/")
list(APPEND EXTENSION_CPACK_INSTALL_CMAKE_PROJECTS "${VMTK_DIR};VMTK;RuntimeExecutables;/")
set(${EXTENSION_NAME}_CPACK_INSTALL_CMAKE_PROJECTS "${EXTENSION_CPACK_INSTALL_CMAKE_PROJECTS}" CACHE STRING "List of external projects to install" FORCE)

#-----------------------------------------------------------------------------
list(APPEND CPACK_INSTALL_CMAKE_PROJECTS "${CMAKE_BINARY_DIR};${EXTENSION_NAME};ALL;/")
list(APPEND CPACK_INSTALL_CMAKE_PROJECTS "${${EXTENSION_NAME}_CPACK_INSTALL_CMAKE_PROJECTS}")

# Explicitly set EXTENSION_NAME before including SlicerExtensionCPack.cmake
# to ensure it's defined in the correct scope for the script.
set(EXTENSION_NAME SlicerVMTK)

include(${Slicer_EXTENSION_GENERATE_CONFIG})


include(${Slicer_EXTENSION_CPACK})
