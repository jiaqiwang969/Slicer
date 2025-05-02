# Get root directory
get_property(_filepath TARGET "Qt5::Core" PROPERTY LOCATION_RELEASE)
get_filename_component(_dir ${_filepath} PATH)
if(APPLE)
  # "_dir" of the form "<qt_root_dir>/lib/QtCore.framework"
  set(qt_root_dir "${_dir}/../..")
else()
  if(DEFINED CMAKE_LIBRARY_ARCHITECTURE AND "${_dir}" MATCHES "${CMAKE_LIBRARY_ARCHITECTURE}$")
    # "_dir" of the form "<qt_root_dir>/lib/<arch>" (e.g "<qt_root_dir>/lib/x86_64-linux-gnu")
    set(qt_root_dir "${_dir}/../..")
  else()
    # "_dir" of the form "<qt_root_dir>/lib"
    set(qt_root_dir "${_dir}/..")
  endif()
endif()

# Sanity checks
set(expected_defined_vars
  Slicer_BUILD_I18N_SUPPORT
  Slicer_INSTALL_BIN_DIR
  )
foreach(var ${expected_defined_vars})
  if(NOT DEFINED ${var})
    message(FATAL_ERROR "Variable ${var} is not defined !")
  endif()
endforeach()

set(expected_existing_vars
  qt_root_dir
  )
foreach(var ${expected_existing_vars})
  if(NOT EXISTS "${${var}}")
    message(FATAL_ERROR "Variable ${var} is set to an inexistent directory or file ! [${${var}}]")
  endif()
endforeach()

set(Slicer_INSTALLED_QT_TOOLS)

if(Slicer_BUILD_I18N_SUPPORT)
  # Bundle Qt language tools with the application if internationalization is enabled.
  # These tools allow Slicer modules to update and process Qt translation (.ts) files
  # without requiring installation of Qt.
  list(APPEND Slicer_INSTALLED_QT_TOOLS
    lconvert
    lrelease
    lupdate
  )

  # Find qt tools
  find_program(QT_LINGUIST_EXECUTABLE linguist)
  find_program(QT_LRELEASE_EXECUTABLE lrelease)
  find_program(QT_LUPDATE_EXECUTABLE lupdate)
  find_program(QT_LCONVERT_EXECUTABLE lconvert)

  if(NOT QT_LCONVERT_EXECUTABLE)
    message(FATAL_ERROR "Qt tool lconvert not found in PATH. Please ensure qttools are installed and in PATH.")
  endif()
  if(NOT QT_LRELEASE_EXECUTABLE)
    message(FATAL_ERROR "Qt tool lrelease not found in PATH. Please ensure qttools are installed and in PATH.")
  endif()

  # Ensure subsequent calls refer to the found tools
  set(QT_LCONVERT_EXECUTABLE ${QT_LCONVERT_EXECUTABLE} CACHE FILEPATH "Path to Qt lconvert tool" FORCE)
  set(QT_LRELEASE_EXECUTABLE ${QT_LRELEASE_EXECUTABLE} CACHE FILEPATH "Path to Qt lrelease tool" FORCE)
  set(QT_LUPDATE_EXECUTABLE ${QT_LUPDATE_EXECUTABLE} CACHE FILEPATH "Path to Qt lupdate tool" FORCE)

endif()

foreach(tool IN LISTS Slicer_INSTALLED_QT_TOOLS)
  if (tool STREQUAL "lconvert")
    set(tool_executable ${QT_LCONVERT_EXECUTABLE})
  elseif (tool STREQUAL "lrelease")
    set(tool_executable ${QT_LRELEASE_EXECUTABLE})
  elseif (tool STREQUAL "lupdate")
    set(tool_executable ${QT_LUPDATE_EXECUTABLE})
  elseif (tool STREQUAL "linguist")
    set(tool_executable ${QT_LINGUIST_EXECUTABLE})
  else()
    message(FATAL_ERROR "Unknown Qt tool requested for installation: ${tool}")
  endif()

  if(NOT EXISTS "${tool_executable}")
    message(FATAL_ERROR "Qt tool ${tool} not found: ${tool_executable}")
  endif()
  install(PROGRAMS ${tool_executable}
    DESTINATION ${Slicer_INSTALL_BIN_DIR}
    COMPONENT Runtime
    )
  slicerStripInstalledLibrary(
    FILES "${Slicer_INSTALL_BIN_DIR}/${tool}"
    COMPONENT Runtime
    )
  if(APPLE)
    set(dollar "$")
    install(CODE
      "set(app ${Slicer_INSTALL_BIN_DIR}/${tool})
      set(appfilepath \"${dollar}ENV{DESTDIR}${dollar}{CMAKE_INSTALL_PREFIX}/${dollar}{app}\")
      message(\"CPack: - Adding rpath to ${dollar}{app}\")
      execute_process(COMMAND install_name_tool -add_rpath @loader_path/..  ${dollar}{appfilepath})"
      COMPONENT Runtime
      )
  endif()
endforeach()
