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