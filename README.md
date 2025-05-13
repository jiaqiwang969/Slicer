# miniSlicer for VTL3D

本仓库用于在 Nix 环境下构建、开发与本地化定制 3D Slicer（miniSlicer）。

## TODO

1. 确认已编译或下载的 **VTL3d** 可执行文件能够在命令行生成所需 CSV 结果。
2. 在 `miniSlicer/Modules/Scripted/` 新建目录 `VTL3dBridge/`。
3. 创建 `VTL3dBridge/CMakeLists.txt`，并确保该模块被 Slicer 主项目识别与编译。
4. 编写 `VTL3dBridge.py`，实现 `ScriptedLoadableModule`、`Widget`、`Logic` 三个类。
5. 在 Widget 中添加：
   - `ctkPathLineEdit`：选择 **VTL3d 可执行文件**路径（默认自动探测）。
   - `ctkPathLineEdit`：选择 **CSV 输出目录**。
   - `qt.QPushButton`：**Run VTL3d**。
6. 在 Logic 中：
   - 使用 `subprocess.run()` 调用 VTL3d，可选 `--csv <outDir>` 参数。
   - 阻塞等待进程结束并验证 CSV 文件是否生成。
7. 解析生成的 CSV：
   - 创建 `vtkMRMLTableNode`，将数据列填充到表格。
   - 使用 `slicer.modules.tables.logic().AddDefaultTableView()` 自动展示结果。
8. 为可能的异常（可执行文件不存在、CSV 缺失、解析错误）提供消息框反馈。
9. 利用 `QSettings` 记忆用户上次选择的路径。
10. 编译／运行 miniSlicer，验证按钮流程在 Linux/macOS 环境成功执行并显示结果表。
11. 更新本 `README.md`，记录使用步骤与演示 GIF，提交 PR。

## 下一阶段：深度嵌入 VTL3d 原生 GUI

以下工作可并行推进，完成后即可在 miniSlicer 内直接显示 VTL3d 的 wxWidgets 界面。

1. **编译 wxQt**  
   已在 `nix/shells.nix` 的 `wxqtDrv` 实现，`nix develop` 即可获取依赖环境。

2. **将 VTL3d GUI 打包为共享库**  
   - 在 `miniSlicer/VTL3D_1.0` CMake 中改用 `add_library(VTL3dGui SHARED …)`；  
   - 去除主循环，仅保留 UI，暴露 `extern "C" QWidget* CreateVTL3dMainWindow(QWidget* parent=nullptr);`;  
   - 对应 derivation 写在 `nix/modules/vtl3d-gui.nix`，产物为 `libVTL3dGui.so`。

3. **创建 C++ Loadable 模块 `VTL3dViewer`**  
   使用 ExtensionWizard 模板，Widget 内通过 `QLibrary` 动态加载 `libVTL3dGui.so`，调用工厂函数并用 `QWidget::createWindowContainer()` 嵌入。

4. **集成至 flake**  
   - 在 `flake.nix` 的 `packages` 输出 `wxqt`、`vtl3dGui`;  
   - 在 `devShells.default.buildInputs` 加入 `vtl3dGui` 便于调试。

5. **验证与调试**  
   - `patchelf --print-rpath libVTL3dGui.so` 确认 RPATH 含 wxQt 路径；  
   - 若界面空白，检查 `wx-config` 是否指向 Qt 版本；  
   - macOS 需为嵌入窗口调用 `setAttribute(Qt::WA_NativeWindow)` 以避免渲染黑屏。

> 完成以上步骤后，即可在 miniSlicer 中打开 "VTL3dViewer" 模块并直接操作 VTL3d 原生界面，后续可继续桥接 MRML 事件与数据。

为了确认 **wxQt+OpenGL** 组件与 **VTL3d GUI** 在本机环境中能够以共享库形式正确编译、链接并被 Slicer SuperBuild 识别，我们进行了一次最小复现的"干净构建"实验。它相当于

1. 先单独把 `VTL3D_1.0` 目录当成普通 CMake 项目编译，确保 `libVTL3dGui.so` 本身没有缺头文件或库缺失；
2. 再把 miniSlicer 整个 SuperBuild 跑到只编译 `VTL3dGui` 目标，验证它与 Slicer 其他第三方依赖（VTK、Qt、ITK 等）共存，且能被安装到输出树；

这样一来就证明：
• wxWidgets 的 Qt 后端和 OpenGL 组件参数设置正确；
• 我们移除执行入口 (`Application.cpp`) 后，`libVTL3dGui.so` 作为纯 UI 库可被其他模块安全加载；
• 后续只需写一个 Loadable 模块动态加载此库，即可在 Slicer 内嵌 VTL3d 原生界面。

### 本地编译验证（已通过）

```bash
# 1) 进入 nix 开发环境（aarch64）
$ nix develop

# 2) 独立构建 VTL3dGui
$ rm -rf build-vtl && mkdir build-vtl
$ cmake -S miniSlicer/VTL3D_1.0 -B build-vtl -DCMAKE_BUILD_TYPE=Release
$ cmake --build build-vtl -j$(nproc)
# → 生成 build-vtl/libVTL3dGui.so 且包含 CreateVTL3dMainWindow 符号

# 3) 在 miniSlicer SuperBuild 内编译
$ rm -rf build-mini && mkdir build-mini
$ cmake -S miniSlicer -B build-mini -DCMAKE_BUILD_TYPE=Release
$ cmake --build build-mini --target VTL3dGui -j$(nproc)
$ find build-mini -name libVTL3dGui.so | head
build-mini/VTL3D_1.0/libVTL3dGui.so  # ✅ 库成功集成
```

上述流程在 aarch64-linux 平台已验证通过，确保 wxQt OpenGL 组件齐全并无符号冲突，可作为后续 Loadable 模块开发的基础。

## TODO

<!--
- [ ] 在 CI 中启用 `impure-derivations`：于 `nix build` / `nix develop` / Garnix 配置里追加 `--extra-experimental-features impure-derivations`，以允许外网下载与 `ExternalProject` 步骤。
- [ ] 完成 UI 与帮助文档的全面中文化校对；解决残留占位符与专业术语一致性。
- [ ] 集成 VocalTractLab 3D 的有限元（FEM）求解模块，支持声学场与组织动力学仿真。
- [ ] 构建并验证复杂声道（多分支管道）模型的加载、网格划分与后处理流程。
- [ ] 在 x86_64 Linux 环境下完成基础与扩展示例 CI；后续补充 Windows、macOS (x86_64 / arm64) 的交叉构建或 GitHub Actions matrix 测试。
- [ ] 引入 CUDA / ROCm 条件编译选项，评估 GPU 加速 FEM 计算可行性。
- [ ] 优化 Nix derivation 产物体积，使用 `stripDebug` 与 `patchelf --shrink-rpath` 等策略，降低二进制发布大小。
- [ ] 发布 Cachix 二进制缓存，减少 CI 构建时间。
- [ ] 撰写用户手册与开发者文档，整理模块接口与插件示例。
-->

<!--
## TODO

- [ ] …（添加更多待办） 
--> 