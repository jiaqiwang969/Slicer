# ****************************************************************************
# This file is part of VocalTractLab3D.
# Copyright (C) 2022, Peter Birkholz, Dresden, Germany
# www.vocaltractlab.de
# author: Peter Birkholz and Rémi Blandin
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# ****************************************************************************

# CMakeList.txt : CMake project for VocalTractLabGui, include source and define
# project specific logic here.
#
cmake_minimum_required(VERSION 3.8)

project("VTL3dGuiLib" LANGUAGES CXX)

# 生成共享库而非可执行
set(BUILD_SHARED_LIBS ON)

# Request the required wxWidgets libs
find_package(wxWidgets 3.1 COMPONENTS core base gl adv REQUIRED)

# Include the wxWidgets use file to initialize various settings
include(${wxWidgets_USE_FILE})

# Request Qt5 for logging and potential QWidget interaction (even if primarily wx)
find_package(Qt5 COMPONENTS Core Gui Widgets REQUIRED)

# Request the required CGAL lib
find_package(CGAL REQUIRED)

# Request the required Eigen lib
find_package(Eigen3 3.3 REQUIRED NO_MODULE)

if (MSVC)
  add_definitions(-D_USE_MATH_DEFINES -D_CRT_SECURE_NO_WARNINGS -DUNICODE -DwxUSE_UNICODE -D_WINDOWS -D__WXMSW__ -D_CRT_SECURE_NO_DEPRECATE -D_CRT_NONSTDC_NO_DEPRECATE -DNOMINMAX -DWIN32_LEAN_AND_MEAN -DNDEBUG -DCGAL_NO_GMP)
elseif(UNIX)
  add_definitions(-D_USE_MATH_DEFINES -D_CRT_SECURE_NO_WARNINGS -DWXUSINGDLL -DUNICODE -DwxUSE_UNICODE -D_CRT_SECURE_NO_DEPRECATE -D_CRT_NONSTDC_NO_DEPRECATE -DNDEBUG -DHAVE_OPENAL)
  find_package(OpenGL REQUIRED)
  find_package(GLUT REQUIRED)
  find_package(OpenAL REQUIRED)
endif()

# Collect source files
file(GLOB VTL3D_GUI_SRCS
  "Backend/*.h"
  "*.h"
  "Backend/*.cpp"
  "*.cpp"
  "VTL3dFactory.h"
  "VTL3dFactory.cpp"
  #"AreaFunctionWidget.cpp"
)

# List headers that require MOC processing (contain Q_OBJECT)
set(VTL3D_GUI_MOC_HDRS
  #AreaFunctionWidget.h
  # Add other .h files with Q_OBJECT here in the future if any
)

# Generate MOC files (output will be in VTL3D_GUI_MOC_SRCS variable)
qt5_wrap_cpp(VTL3D_GUI_MOC_SRCS ${VTL3D_GUI_MOC_HDRS})

# 无论后端如何，始终移除依赖 wxGLCanvas 的 VocalTractPicture.cpp，
# 以避免与我们为 wxQt 环境提供的 Stub 类重复定义。
list(REMOVE_ITEM VTL3D_GUI_SRCS ${CMAKE_CURRENT_SOURCE_DIR}/VocalTractPicture.cpp)

# 从源列表中移除独立可执行入口文件（如果存在）
list(REMOVE_ITEM VTL3D_GUI_SRCS ${CMAKE_CURRENT_SOURCE_DIR}/Application.cpp)

# 构建共享库
add_library(VTL3dGui SHARED 
  ${VTL3D_GUI_SRCS}
  ${VTL3D_GUI_MOC_SRCS} # Add MOC generated sources
)

# Public include directory for VTL3dGui target
# This allows parent CMake (VTL3dViewer) to find VTL3dFactory.h etc.
# Assuming VTL3dFactory.h is in the root of VTL3D_1.0 source directory
target_include_directories(VTL3dGui PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}> # For the build tree
  $<INSTALL_INTERFACE:include/VTL3dGui>          # For installation (if installed as a separate lib)
  # Add Qt include directories
  ${Qt5Core_INCLUDE_DIRS}
  ${Qt5Gui_INCLUDE_DIRS}
  ${Qt5Widgets_INCLUDE_DIRS}
)

# Link common Qt libraries. Mocced files might need QtCore at least.
set(QT_LINK_LIBS Qt5::Core Qt5::Gui Qt5::Widgets)

if (MSVC)
  target_link_libraries(VTL3dGui PRIVATE
    ${wxWidgets_LIBRARIES}
    CGAL::CGAL # Assumes CGAL provides an imported target
    Eigen3::Eigen # Assumes Eigen3 provides an imported target
    ${QT_LINK_LIBS}
  )
elseif(UNIX)
  target_link_libraries(VTL3dGui PRIVATE
    ${wxWidgets_LIBRARIES}
    CGAL::CGAL
    Eigen3::Eigen
    OpenGL::GL # Using imported target for OpenGL
    GLUT::GLUT # Using imported target for GLUT
    OpenAL::OpenAL # Using imported target for OpenAL
    ${QT_LINK_LIBS}
  )
endif()

# Install targets - keep for now, Slicer might expect certain structure
# Ensure install paths are relative and make sense if this module is part of a larger install
install(TARGETS VTL3dGui
  LIBRARY DESTINATION lib       # libVTL3dGui.so / VTL3dGui.dll
  ARCHIVE DESTINATION lib       # VTL3dGui.lib (Windows import library)
  RUNTIME DESTINATION bin       # VTL3dGui.dll (Windows, needs to be in PATH or next to exe)
  INCLUDES DESTINATION include/VTL3dGui # For installing public headers
)

# Install VTL3dFactory.h specifically if it's the main public header
# The target_include_directories should handle build-tree access
# install(FILES VTL3dFactory.h DESTINATION include/VTL3dGui) # Redundant if using INCLUDES in install(TARGETS...)
# install(FILES MainWindow.h DESTINATION include/VTL3dGui) # Only if MainWindow.h is also a public header

# Ensure VTL3dFactory.h is a public header if needed by VTL3dViewer widget
# This is handled by target_include_directories(VTL3dGui PUBLIC ...)
