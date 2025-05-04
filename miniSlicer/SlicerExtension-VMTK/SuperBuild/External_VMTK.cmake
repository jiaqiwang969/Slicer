set(proj VMTK)

# Set dependency list
set(${proj}_DEPENDS "")
if(DEFINED Slicer_SOURCE_DIR)  # allow building as an extension bundled with Slicer
  list(APPEND ${proj}_DEPENDS
    ITK
    VTK
    )
endif()

# Include dependent projects if any
ExternalProject_Include_Dependencies(${proj} PROJECT_VAR proj)

if(${CMAKE_PROJECT_NAME}_USE_SYSTEM_${proj})
  message(FATAL_ERROR "Enabling ${CMAKE_PROJECT_NAME}_USE_SYSTEM_${proj} is not supported !")
endif()

# Sanity checks
if(DEFINED VMTK_DIR AND NOT EXISTS ${VMTK_DIR})
  message(FATAL_ERROR "VMTK_DIR [${VMTK_DIR}] variable is defined but corresponds to nonexistent directory")
endif()

if(NOT DEFINED ${proj}_DIR AND NOT ${CMAKE_PROJECT_NAME}_USE_SYSTEM_${proj})

  set(VMTK_USE_VTK9 ON)
  if(Slicer_VTK_VERSION_MAJOR VERSION_LESS "9")
    set(VMTK_USE_VTK9 OFF)
  endif()
  ExternalProject_Message(${proj} "VMTK_USE_VTK9:${VMTK_USE_VTK9}")

  set(EXTERNAL_PROJECT_OPTIONAL_CMAKE_CACHE_ARGS)
  if(VTK_WRAP_PYTHON)
    list(APPEND EXTERNAL_PROJECT_OPTIONAL_CMAKE_CACHE_ARGS
      -DPYTHON_EXECUTABLE:FILEPATH=${PYTHON_EXECUTABLE}
      -DPYTHON_INCLUDE_DIR:PATH=${PYTHON_INCLUDE_DIR}
      -DPYTHON_LIBRARY:FILEPATH=${PYTHON_LIBRARY}
      # Required by FindPython3 CMake module used by VTK
      -DPython3_ROOT_DIR:PATH=${Python3_ROOT_DIR}
      -DPython3_INCLUDE_DIR:PATH=${Python3_INCLUDE_DIR}
      -DPython3_LIBRARY:FILEPATH=${Python3_LIBRARY}
      -DPython3_LIBRARY_DEBUG:FILEPATH=${Python3_LIBRARY_DEBUG}
      -DPython3_LIBRARY_RELEASE:FILEPATH=${Python3_LIBRARY_RELEASE}
      -DPython3_EXECUTABLE:FILEPATH=${Python3_EXECUTABLE}
      )
  endif()

  ExternalProject_SetIfNotDefined(
    ${CMAKE_PROJECT_NAME}_${proj}_GIT_REPOSITORY
    "${EP_GIT_PROTOCOL}://github.com/jiaqiwang969/vmtk.git"
    QUIET
    )

  if(${Slicer_VERSION_MAJOR}.${Slicer_VERSION_MINOR} VERSION_GREATER_EQUAL 5.1)
    # Slicer >= 5.1 uses recent ITK-5.3RC version, which has BooleanStdVectorType
    # (see https://github.com/InsightSoftwareConsortium/ITK/commit/bc9ba8540f96c0fa4e9100b25b05eb812074a64e)
    set(DEFAULT_VMTK_TAG b122fc80e0de1fe3d46a6cc8ac56d72c9434cbf4)
  else()
    # Slicer < 5.1 uses older ITK-5.3RC version, which does not yet have BooleanStdVectorType
    set(DEFAULT_VMTK_TAG 30b0fdad5674d6f134e8a8b601bcef7917671b0a)
  endif()

  ExternalProject_SetIfNotDefined(
    ${CMAKE_PROJECT_NAME}_${proj}_GIT_TAG
    ${DEFAULT_VMTK_TAG}
    QUIET
    )

  set(EP_SOURCE_DIR ${CMAKE_BINARY_DIR}/${proj})
  set(EP_BINARY_DIR ${CMAKE_BINARY_DIR}/${proj}-build)
  set(Slicer_QTLOADABLEMODULES_LIB_DIR "lib/miniSlicer-5.9/qt-loadable-modules")
  set(Slicer_BINARY_INNER_SUBDIR Slicer-build)

  # --- BEGIN CMAKE DEBUG OUTPUT ---
  set(DEBUG_OUTPUT_FILE "$ENV{HOME}/vmtk_cmake_debug1.log")
  file(APPEND ${DEBUG_OUTPUT_FILE} "--- Debugging paths in External_VMTK.cmake (${CMAKE_CURRENT_LIST_FILE}) ---\n")
  # Using execute_process to get a timestamp reliably
  execute_process(COMMAND date OUTPUT_VARIABLE _CURRENT_DATETIME OUTPUT_STRIP_TRAILING_WHITESPACE)
  file(APPEND ${DEBUG_OUTPUT_FILE} "Timestamp: ${_CURRENT_DATETIME}\n")
  file(APPEND ${DEBUG_OUTPUT_FILE} "CMAKE_BINARY_DIR:             ${CMAKE_BINARY_DIR}\n")
  file(APPEND ${DEBUG_OUTPUT_FILE} "Slicer_BINARY_INNER_SUBDIR:   ${Slicer_BINARY_INNER_SUBDIR}\n")
  file(APPEND ${DEBUG_OUTPUT_FILE} "Slicer_QTLOADABLEMODULES_LIB_DIR: ${Slicer_QTLOADABLEMODULES_LIB_DIR}\n")
  set(CONSTRUCTED_LIBRARY_OUTPUT_PATH "${CMAKE_BINARY_DIR}/${Slicer_BINARY_INNER_SUBDIR}/${Slicer_QTLOADABLEMODULES_LIB_DIR}")
  file(APPEND ${DEBUG_OUTPUT_FILE} "Constructed Library Output Path: ${CONSTRUCTED_LIBRARY_OUTPUT_PATH}\n")
  # Add VMTK-specific install paths passed as arguments
  file(APPEND ${DEBUG_OUTPUT_FILE} "--- VMTK Install Path Arguments ---\n")
  file(APPEND ${DEBUG_OUTPUT_FILE} "Slicer_INSTALL_QTLOADABLEMODULES_PYTHON_LIB_DIR: ${Slicer_INSTALL_QTLOADABLEMODULES_PYTHON_LIB_DIR}\n")
  file(APPEND ${DEBUG_OUTPUT_FILE} "Slicer_INSTALL_QTLOADABLEMODULES_BIN_DIR:      ${Slicer_INSTALL_QTLOADABLEMODULES_BIN_DIR}\n")
  file(APPEND ${DEBUG_OUTPUT_FILE} "Slicer_INSTALL_QTLOADABLEMODULES_LIB_DIR:        ${Slicer_INSTALL_QTLOADABLEMODULES_LIB_DIR}\n")
  file(APPEND ${DEBUG_OUTPUT_FILE} "----------------------------------------------\n\n")
  message(STATUS "CMAKE DEBUG [External_VMTK]: Wrote path info to ${DEBUG_OUTPUT_FILE}")
  # --- END CMAKE DEBUG OUTPUT ---

  ExternalProject_Add(${proj}
    ${${proj}_EP_ARGS}
    GIT_REPOSITORY "${${CMAKE_PROJECT_NAME}_${proj}_GIT_REPOSITORY}"
    GIT_TAG "${${CMAKE_PROJECT_NAME}_${proj}_GIT_TAG}"
    SOURCE_DIR ${EP_SOURCE_DIR}
    BINARY_DIR ${EP_BINARY_DIR}
    CMAKE_CACHE_ARGS
      -DCMAKE_RUNTIME_OUTPUT_DIRECTORY:PATH=${CMAKE_BINARY_DIR}/${Slicer_BINARY_INNER_SUBDIR}/${Slicer_QTLOADABLEMODULES_LIB_DIR}
      -DCMAKE_LIBRARY_OUTPUT_DIRECTORY:PATH=${CMAKE_BINARY_DIR}/${Slicer_BINARY_INNER_SUBDIR}/${Slicer_QTLOADABLEMODULES_LIB_DIR}
      -DCMAKE_ARCHIVE_OUTPUT_DIRECTORY:PATH=${CMAKE_ARCHIVE_OUTPUT_DIRECTORY}
      -DBUILD_SHARED_LIBS:BOOL=ON
      -DBUILD_DOCUMENTATION:BOOL=OFF
      -DCMAKE_CXX_COMPILER:FILEPATH=${CMAKE_CXX_COMPILER}
      -DCMAKE_CXX_FLAGS:STRING=${ep_common_cxx_flags}
      -DCMAKE_C_COMPILER:FILEPATH=${CMAKE_C_COMPILER}
      -DCMAKE_C_FLAGS:STRING=${ep_common_c_flags}
      -DCMAKE_INSTALL_PREFIX:PATH=${CMAKE_CURRENT_BINARY_DIR}/SlicerVmtk-build
      # installation location for the pypes/scripts
      -DVMTK_INSTALL_BIN_DIR:PATH=${Slicer_INSTALL_QTLOADABLEMODULES_PYTHON_LIB_DIR}/pypes
      -DVMTK_MODULE_INSTALL_LIB_DIR:PATH=${Slicer_INSTALL_QTLOADABLEMODULES_PYTHON_LIB_DIR}/pypes
      -DVMTK_SCRIPTS_INSTALL_BIN_DIR:PATH=${Slicer_INSTALL_QTLOADABLEMODULES_PYTHON_LIB_DIR}/pypes
      -DVMTK_SCRIPTS_INSTALL_LIB_DIR:PATH=${Slicer_INSTALL_QTLOADABLEMODULES_PYTHON_LIB_DIR}/pypes
      -DPYPES_INSTALL_BIN_DIR:PATH=${Slicer_INSTALL_QTLOADABLEMODULES_PYTHON_LIB_DIR}/pypes
      -DPYPES_MODULE_INSTALL_LIB_DIR:PATH=${Slicer_INSTALL_QTLOADABLEMODULES_PYTHON_LIB_DIR}/pypes
      -DVMTK_CONTRIB_SCRIPTS_INSTALL_LIB_DIR:PATH=${Slicer_INSTALL_QTLOADABLEMODULES_PYTHON_LIB_DIR}/pypes
      -DVMTK_CONTRIB_SCRIPTS_INSTALL_BIN_DIR:PATH=${Slicer_INSTALL_QTLOADABLEMODULES_PYTHON_LIB_DIR}/pypes
      # installation location for all vtkvmtk stuff
      -DVTK_VMTK_INSTALL_BIN_DIR:PATH=${Slicer_INSTALL_QTLOADABLEMODULES_BIN_DIR}
      -DVTK_VMTK_INSTALL_LIB_DIR:PATH=${Slicer_INSTALL_QTLOADABLEMODULES_LIB_DIR}
      -DVTK_VMTK_MODULE_INSTALL_LIB_DIR:PATH=${Slicer_INSTALL_QTLOADABLEMODULES_LIB_DIR}
      -DVTK_VMTK_WRAP_PYTHON:BOOL=ON
      # we don't want superbuild since it will override our CMake settings
      -DVMTK_USE_SUPERBUILD:BOOL=OFF
      -DVMTK_CONTRIB_SCRIPTS:BOOL=ON
      -DVMTK_MINIMAL_INSTALL:BOOL=OFF
      -DVMTK_ENABLE_DISTRIBUTION:BOOL=OFF
      -DVMTK_WITH_LIBRARY_VERSION:BOOL=OFF
      # we want the vmtk scripts :)
      -DVMTK_SCRIPTS_ENABLED:BOOL=ON
      # we do not want cocoa, go away :)
      -DVTK_VMTK_USE_COCOA:BOOL=OFF
      # we use Slicer's VTK and ITK
      -DUSE_SYSTEM_VTK:BOOL=ON
      -DUSE_SYSTEM_ITK:BOOL=ON
      -DITK_DIR:PATH=${ITK_DIR}
      -DVTK_DIR:PATH=${VTK_DIR}
      # macOS
      -DCMAKE_INSTALL_NAME_TOOL:FILEPATH=${CMAKE_INSTALL_NAME_TOOL}
      -DCMAKE_MACOSX_RPATH:BOOL=0
      # Options
      -DVMTK_USE_VTK9:BOOL=${VMTK_USE_VTK9}
      ${EXTERNAL_PROJECT_OPTIONAL_CMAKE_CACHE_ARGS}
    DEPENDS
      ${${proj}_DEPENDS}
    )
  set(${proj}_DIR ${EP_BINARY_DIR})

  #-----------------------------------------------------------------------------
  # Launcher setting specific to build tree

  # NA

  #-----------------------------------------------------------------------------
  # Launcher setting specific to install tree

  # NA

else()
  ExternalProject_Add_Empty(${proj} DEPENDS ${${proj}_DEPENDS})
endif()

mark_as_superbuild(${proj}_DIR:PATH)
