# miniSlicer for VTL3D Integration

本仓库旨在将 VTL3d 有限元分析软件深度集成到定制的 3D Slicer 版本 (miniSlicer) 中。
当前主要工作集中在**第二阶段：通过 C++ Loadable Module (`VTL3dViewer`) 嵌入 VTL3d 的原生 wxWidgets GUI**。

## 当前状态 (Phase 2 - Part 1: Module Skeleton)

我们已经成功完成了以下工作：

1.  **VTL3d GUI 作为共享库 (`libVTL3dGui.so`)**:
    *   VTL3d 的 wxWidgets GUI 部分已编译为一个独立的共享库。
    *   该库通过 `VTL3dFactory.cpp` 暴露了工厂函数 `CreateVTL3dMainWindow(QWidget* parent)`，用于创建并返回 VTL3d 主窗口的 QWidget 封装。
    *   相关的构建逻辑位于 `miniSlicer/Slicer/Modules/Loadable/VTL3dViewer/VTL3D_1.0/CMakeLists.txt`。

2.  **Slicer Loadable Module `VTL3dViewer` 骨架**:
    *   创建了名为 `VTL3dViewer` 的 C++ Loadable Module，其源码位于 `miniSlicer/Slicer/Modules/Loadable/VTL3dViewer/`。
    *   `VTL3D_1.0` (包含 `libVTL3dGui.so` 的构建) 已作为 `VTL3dViewer` 模块的一个子项目，在其 `CMakeLists.txt` 中通过 `add_subdirectory(VTL3D_1.0)` 进行构建。
    *   `VTL3dViewer` 模块的 CMake 配置 (`miniSlicer/Slicer/Modules/Loadable/VTL3dViewer/CMakeLists.txt`) 负责构建模块自身并链接到 `libVTL3dGui.so`。
    *   模块的 C++ 骨架代码 (`qSlicerVTL3dViewerModule.h/cxx`, `qSlicerVTL3dViewerModuleWidget.h/cxx`, `vtkSlicerVTL3dViewerModuleLogic.h/cxx`) 已按照 Slicer 规范进行了修正，解决了编译和链接问题。

3.  **集成与构建流程**:
    *   `VTL3dViewer` 模块已添加到 `miniSlicer/Slicer/Modules/Loadable/CMakeLists.txt` 中，作为 Slicer 内置模块进行统一构建。
    *   顶层的 `miniSlicer/CMakeLists.txt` 不再直接管理 `VTL3D_1.0` 的构建，此任务已下放给 `VTL3dViewer` 模块。
    *   整个 `miniSlicer` 项目（包含 `VTL3dViewer` 及其子项目 `VTL3D_1.0`）已能在 Nix 环境下成功编译。

**简而言之，`VTL3dViewer` 模块的C++框架已经搭建完毕并可以成功编译，其依赖的 `libVTL3dGui.so` 也作为其一部分正确构建和链接。**

## 下一步核心任务 (Phase 2 - Part 2: GUI Embedding)

接下来的工作重点是在 `qSlicerVTL3dViewerModuleWidget` 中实现 VTL3d GUI 的实际嵌入：

1.  **动态加载 `libVTL3dGui.so`**:
    *   在 `qSlicerVTL3dViewerModuleWidget::setup()` 方法 (位于 `miniSlicer/Slicer/Modules/Loadable/VTL3dViewer/qSlicerVTL3dViewerModuleWidget.cxx`) 中。
    *   确定 `libVTL3dGui.so` 在构建树和安装树中的相对或绝对路径。
        *   构建树中，它可能位于 `.../build-mini/Slicer-build/Modules/Loadable/VTL3dViewer/VTL3D_1.0/bin` (Windows DLL) 或 `.../build-mini/Slicer-build/Modules/Loadable/VTL3dViewer/VTL3D_1.0/lib` (Linux .so)。更可靠地，它可以是相对于 `libqSlicerVTL3dViewerModule.so` 的路径。
    *   使用 `QLibrary` 类加载该共享库。

2.  **解析工厂函数符号**:
    *   从加载的 `QLibrary` 实例中解析出 `CreateVTL3dMainWindow` 函数的地址。
    *   定义正确的函数指针类型 `typedef QWidget* (*CreateVTL3dMainWindowFunc)(QWidget* parent);`。

3.  **调用工厂函数并嵌入 GUI**:
    *   调用解析得到的 `CreateVTL3dMainWindowFunc` 函数，将 `qSlicerVTL3dViewerModuleWidget` 实例 (`this`) 或其一个子 `QWidget` 作为父窗口指针传递给它。
    *   获取返回的 `QWidget*` (它包装了 VTL3d 的 wxWidgets 主窗口)。
    *   将这个返回的 `QWidget*` 添加到 `qSlicerVTL3dViewerModuleWidget` 的布局中，替换掉当前的占位符 `QLabel`。

4.  **库生命周期管理**:
    *   考虑将 `QLibrary` 对象作为 `qSlicerVTL3dViewerModuleWidgetPrivate` 的成员变量，以确保 `libVTL3dGui.so` 在 `VTL3dViewer` 模块界面存在期间保持加载状态，在 Widget 销毁时自动卸载。

5.  **错误处理与用户反馈**:
    *   为库加载失败、符号解析失败或工厂函数返回空等情况提供明确的错误提示 (例如，使用 `QMessageBox`)。

## 编译与测试步骤 (当前阶段)

在进行下一步开发前，确保当前模块骨架能稳定编译：

1.  **确保顶层 `miniSlicer/CMakeLists.txt` 中已移除对旧 `VTL3D_1.0` 路径的 `add_subdirectory` 调用。**
2.  **清理构建目录 (强烈建议)**:
    ```bash
    rm -rf ./build/build-mini
    ```
3.  **重新配置 CMake (使用 nix 环境)**:
    ```bash
    nix develop
    configure_slicer_mini ./miniSlicer ./build/build-mini ./build/install-mini
    ```
4.  **构建项目**:
    ```bash
    cd ./build/build-mini && make -j$(nproc)
    ```

完成 GUI 嵌入后，后续可进一步开发 Slicer 场景与嵌入的 VTL3d GUI 之间的数据交互功能。
