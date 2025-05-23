cmake_minimum_required(VERSION 3.16.3)

# Enable C++14
if(NOT DEFINED CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set (EP_GIT_PROTOCOL "https")

# Slicer sources
include(FetchContent)
if(NOT DEFINED slicersources_SOURCE_DIR)
  message(STATUS "Downloading Slicer sources using FetchContent...")
  # Download Slicer sources and set variables slicersources_SOURCE_DIR and slicersources_BINARY_DIR
  FetchContent_Populate(slicersources
    GIT_REPOSITORY ${EP_GIT_PROTOCOL}://github.com/jiaqiwang969/Slicer
    GIT_TAG        2c286e4661bdcfc2dc28b429cbe0bb447cd66473
    GIT_PROGRESS   1
    )
else()
  message(STATUS "Using local Slicer sources from: ${slicersources_SOURCE_DIR}")
  set(slicersources_BINARY_DIR ${CMAKE_CURRENT_BINARY_DIR}/slicersources-subbuild)
endif()

# macOS initialization
set(CMAKE_MODULE_PATH ${slicersources_SOURCE_DIR}/CMake ${CMAKE_MODULE_PATH})
include(SlicerInitializeOSXVariables)

project(miniSlicer)

# Configure Application
set(Slicer_APPLICATIONS_DIR ${CMAKE_CURRENT_SOURCE_DIR}/Applications)
set(Slicer_MAIN_PROJECT "miniSlicerApp")

# Set organization
set(Slicer_ORGANIZATION_DOMAIN "kitware.com")
set(Slicer_ORGANIZATION_NAME   "Kitware, Inc.")

# Default home and favorite modules
set(Slicer_DEFAULT_HOME_MODULE "Home")
set(Slicer_DEFAULT_FAVORITE_MODULES "Data, Volumes, Models, Transforms, Markups, SegmentEditor")

# Configure SuperBuild
set(SUPERBUILD_TOPLEVEL_PROJECT Slicer)
set(EXTERNAL_PROJECT_ADDITIONAL_DIR "${CMAKE_CURRENT_SOURCE_DIR}/SuperBuild")
include(ExternalProjectDependency)

# Additional Slicer dependencies looked up in EXTERNAL_PROJECT_ADDITIONAL_DIR
set(Slicer_ADDITIONAL_DEPENDENCIES
  )

#  Enable listed remote modules from ITK
set(Slicer_ITK_ADDITIONAL_MODULES
  )

if(NOT CMAKE_CONFIGURATION_TYPES)
  set(Slicer_DEFAULT_BUILD_TYPE "Release")
endif()
include(SlicerInitializeBuildType)
include(SlicerInitializeReleaseType)

# Set application bundle identifier for macOS
if(APPLE)
  set(Slicer_MACOSX_BUNDLE_GUI_IDENTIFIER "com.kitware.minislicer")
endif()

# Installation folder and admin account requirement for Windows
if(WIN32)
  # Note: To avoid escaping issue, make sure to use forward slash when setting
  #       "Slicer_CPACK_NSIS_INSTALL_ROOT". It is replaced by "\\\\" in SlicerCPack.
  set(Slicer_CPACK_NSIS_INSTALL_REQUIRES_ADMIN_ACCOUNT ON)
  if(Slicer_CPACK_NSIS_INSTALL_REQUIRES_ADMIN_ACCOUNT)
    # User has administrative privileges, therefore we can install to shared folder
    # "C:\Program Files" or "C:\Program Files (x86)".
    if(CMAKE_CL_64)
      set(Slicer_CPACK_NSIS_INSTALL_ROOT "$PROGRAMFILES64")
    else()
      set(Slicer_CPACK_NSIS_INSTALL_ROOT "$PROGRAMFILES")
    endif()
  else()
    # We do not require administrative privileges, therefore we install to user folder
    # "C:\Users\<username>\AppData\Local".
    set(Slicer_CPACK_NSIS_INSTALL_ROOT "$LOCALAPPDATA/${Slicer_ORGANIZATION_NAME}")
  endif()
endif()

# Slicer options
option(BUILD_TESTING                            "Build application test suite"                        ON)
option(Slicer_BUILD_APPLICATIONUPDATE_SUPPORT   "Build application update support"                    OFF)
option(Slicer_BUILD_DOCUMENTATION               "Build documentation (Doxygen, sphinx, ...)"          OFF)
if(WIN32)
  option(Slicer_BUILD_WIN32_CONSOLE_LAUNCHER    "Build ${PROJECT_NAME} launcher executable as a console app on windows (displays console at application start)" OFF)
  option(Slicer_BUILD_WIN32_CONSOLE             "Build application executable as a console app (allows capturing and piping console output)" ON)
endif()

option(Slicer_BUILD_DICOM_SUPPORT               "Build application with DICOM support"                ON)
option(Slicer_BUILD_DIFFUSION_SUPPORT           "Build application with Diffusion support"            OFF)
option(Slicer_BUILD_EXTENSIONMANAGER_SUPPORT    "Build application with ExtensionManager support"     OFF)
option(Slicer_BUILD_MULTIVOLUME_SUPPORT         "Build application with MultiVolume support"          OFF)
option(Slicer_BUILD_PARAMETERSERIALIZER_SUPPORT "Build application with parameter serializer support" OFF)
option(Slicer_USE_PYTHONQT                      "Build application with Python support"               ON)
option(Slicer_USE_QtTesting                     "Build application with QtTesting support"            OFF)
option(Slicer_USE_SimpleITK                     "Build application with SimpleITK support"            OFF)
option(Slicer_USE_VMTK                          "Build Slicer with VMTK support"                      ON)

option(Slicer_BUILD_BRAINSTOOLS                 "Build application with BRAINSTools module"           OFF)
option(Slicer_BUILD_DataStore                   "Build application with DataStore module"             OFF)
option(Slicer_BUILD_CompareVolumes              "Build application with ChangeTrackerPy module"       OFF)
option(Slicer_BUILD_LandmarkRegistration        "Build application with LandmarkRegistration module"  OFF)
option(Slicer_BUILD_SurfaceToolbox              "Build application with SurfaceToolbox module"        OFF)

# Enable Slicer built-in modules
set(Slicer_CLIMODULES_ENABLED
  ResampleDTIVolume             # Needed by ResampleScalarVectorDWIVolume
  ResampleScalarVectorDWIVolume # Depends on DiffusionApplications, needed by CropVolume
  )
set(Slicer_QTLOADABLEMODULES_ENABLED
  )
set(Slicer_QTSCRIPTEDMODULES_ENABLED
  )

# Disable Slicer built-in modules
set(Slicer_CLIMODULES_DISABLED
  )
set(Slicer_QTLOADABLEMODULES_DISABLED
  SceneViews
  SlicerWelcome
  ViewControllers
  )
set(Slicer_QTSCRIPTEDMODULES_DISABLED
  DataProbe
  DMRIInstall
  Endoscopy
  LabelStatistics
  PerformanceTests
  #SampleData
  VectorToScalarVolume
  WebServer
  # DICOM       # Re-enable core DICOM module
  # DICOMPlugin # Re-enable DICOM plugin framework
  # DICOMLib    # Re-enable core DICOM library to fix ModuleNotFoundError

  )

# Enable/Disable Slicer custom modules: To create a new module, use the SlicerExtensionWizard.
set(Slicer_EXTENSION_SOURCE_DIRS
  #${miniSlicer_SOURCE_DIR}/Modules/CLI/MyCLIModule
  #${miniSlicer_SOURCE_DIR}/Modules/Loadable/MyLoadableModule
  ${miniSlicer_SOURCE_DIR}/Modules/Scripted/Home
  ${miniSlicer_SOURCE_DIR}/Modules/Scripted/VTL3dBridge
  )

# --- Build VTL3d GUI library -------------------------------------------------
#add_subdirectory(${miniSlicer_SOURCE_DIR}/VTL3D_1.0)
# ---------------------------------------------------------------------------

# --- Add SlicerExtraMarkups Extension Source Directory ---
set(EXTRAMARKUPS_EXTENSION_SRC_REL "SlicerExtraMarkups")
get_filename_component(EXTRAMARKUPS_SOURCE_DIR ${EXTRAMARKUPS_EXTENSION_SRC_REL} ABSOLUTE BASE_DIR ${CMAKE_CURRENT_SOURCE_DIR})
if(EXISTS "${EXTRAMARKUPS_SOURCE_DIR}/CMakeLists.txt")
  message(STATUS "Adding SlicerExtraMarkups extension source directory to Slicer build: ${EXTRAMARKUPS_SOURCE_DIR}")
  list(APPEND Slicer_EXTENSION_SOURCE_DIRS ${EXTRAMARKUPS_SOURCE_DIR})
else()
  message(WARNING "SlicerExtraMarkups extension source directory not found at expected location: ${EXTRAMARKUPS_SOURCE_DIR}. Build might fail.")
endif()
# --- End Add SlicerExtraMarkups Extension ---



# --- Add SlicerVMTK Extension Source Directory ---
# Calculate path relative to this CMakeLists.txt
set(VMTK_EXTENSION_SRC_REL "SlicerExtension-VMTK") 
get_filename_component(VMTK_EXTENSION_SOURCE_DIR ${VMTK_EXTENSION_SRC_REL} ABSOLUTE BASE_DIR ${CMAKE_CURRENT_SOURCE_DIR})

if(EXISTS "${VMTK_EXTENSION_SOURCE_DIR}/CMakeLists.txt")
  message(STATUS "Adding SlicerVMTK extension source directory to Slicer build: ${VMTK_EXTENSION_SOURCE_DIR}")
  list(APPEND Slicer_EXTENSION_SOURCE_DIRS ${VMTK_EXTENSION_SOURCE_DIR})
else()
  message(WARNING "SlicerVMTK extension source directory not found at expected location: ${VMTK_EXTENSION_SOURCE_DIR}. VMTK modules will not be built.")
endif()
# --- End Add SlicerVMTK Extension ---

# --- Add Slicer-SurfaceWrapSolidify Extension Source Directory ---
set(SURFACEWRAPSOUDIFY_EXTENSION_SRC_REL "Slicer-SurfaceWrapSolidify")
get_filename_component(SURFACEWRAPSOUDIFY_SOURCE_DIR ${SURFACEWRAPSOUDIFY_EXTENSION_SRC_REL} ABSOLUTE BASE_DIR ${CMAKE_CURRENT_SOURCE_DIR})
if(EXISTS "${SURFACEWRAPSOUDIFY_SOURCE_DIR}/CMakeLists.txt")
  message(STATUS "Adding Slicer-SurfaceWrapSolidify extension source directory to Slicer build: ${SURFACEWRAPSOUDIFY_SOURCE_DIR}")
  list(APPEND Slicer_EXTENSION_SOURCE_DIRS ${SURFACEWRAPSOUDIFY_SOURCE_DIR})
else()
  message(WARNING "Slicer-SurfaceWrapSolidify extension source directory not found at expected location: ${SURFACEWRAPSOUDIFY_SOURCE_DIR}. Build might fail.")
endif()
# --- End Add Slicer-SurfaceWrapSolidify Extension ---

# --- Add LanguageTools Extension Source Directory ---
set(LANGUAGETOOLS_EXTENSION_SRC_REL "LanguageTools")
get_filename_component(LANGUAGETOOLS_SOURCE_DIR ${LANGUAGETOOLS_EXTENSION_SRC_REL} ABSOLUTE BASE_DIR ${CMAKE_CURRENT_SOURCE_DIR})
if(EXISTS "${LANGUAGETOOLS_SOURCE_DIR}/CMakeLists.txt")
  message(STATUS "Adding LanguageTools extension source directory to Slicer build: ${LANGUAGETOOLS_SOURCE_DIR}")
  list(APPEND Slicer_EXTENSION_SOURCE_DIRS ${LANGUAGETOOLS_SOURCE_DIR})
else()
  message(WARNING "LanguageTools extension source directory not found at expected location: ${LANGUAGETOOLS_SOURCE_DIR}. Build might fail.")
endif()
# --- End Add LanguageTools Extension ---

# --- Add SlicerSurfaceToolbox Extension Source Directory ---
set(SURFACETOOLBOX_EXTENSION_SRC_REL "SlicerSurfaceToolbox")
get_filename_component(SURFACETOOLBOX_SOURCE_DIR ${SURFACETOOLBOX_EXTENSION_SRC_REL} ABSOLUTE BASE_DIR ${CMAKE_CURRENT_SOURCE_DIR})
if(EXISTS "${SURFACETOOLBOX_SOURCE_DIR}/CMakeLists.txt")
  message(STATUS "Adding SlicerSurfaceToolbox extension source directory to Slicer build: ${SURFACETOOLBOX_SOURCE_DIR}")
  list(APPEND Slicer_EXTENSION_SOURCE_DIRS ${SURFACETOOLBOX_SOURCE_DIR})
else()
  message(WARNING "SlicerSurfaceToolbox extension source directory not found at expected location: ${SURFACETOOLBOX_SOURCE_DIR}. Build might fail.")
endif()
# --- End Add SlicerSurfaceToolbox Extension ---

# Add remote extension source directories

# SlicerCustomAppUtilities
set(extension_name "SlicerCustomAppUtilities")
set(${extension_name}_SOURCE_DIR "${CMAKE_BINARY_DIR}/${extension_name}")
FetchContent_Populate(${extension_name}
  SOURCE_DIR     ${${extension_name}_SOURCE_DIR}
  GIT_REPOSITORY ${EP_GIT_PROTOCOL}://github.com/KitwareMedical/SlicerCustomAppUtilities.git
  GIT_TAG        1d984a2c9143e2617ff1ffa9d86c51e07dc6321e
  GIT_PROGRESS   1
  QUIET
  )
message(STATUS "Remote - ${extension_name} [OK]")
list(APPEND Slicer_EXTENSION_SOURCE_DIRS ${${extension_name}_SOURCE_DIR}/Modules/Scripted/SlicerCustomAppUtilities)

# SlicerOpenIGTLink
#set(extension_name "SlicerOpenIGTLink")
#set(${extension_name}_SOURCE_DIR "${CMAKE_BINARY_DIR}/${extension_name}")
#FetchContent_Populate(${extension_name}
#  SOURCE_DIR     ${${extension_name}_SOURCE_DIR}
#  GIT_REPOSITORY ${EP_GIT_PROTOCOL}://github.com/openigtlink/SlicerOpenIGTLink.git
#  GIT_TAG        2b92f7b1ffe02403109b671f28424e8770e902a0
#  GIT_PROGRESS   1
#  QUIET
#  )
#message(STATUS "Remote - ${extension_name} [OK]")
#list(APPEND Slicer_EXTENSION_SOURCE_DIRS ${${extension_name}_SOURCE_DIR})


# Add Slicer sources
add_subdirectory(${slicersources_SOURCE_DIR} ${slicersources_BINARY_DIR})