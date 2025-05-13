# miniSlicer for VTL3D

本仓库用于在 Nix 环境下构建、开发与本地化定制 3D Slicer（miniSlicer）。

## TODO

- [ ] 在 CI 中启用 `impure-derivations`：于 `nix build` / `nix develop` / Garnix 配置里追加 `--extra-experimental-features impure-derivations`，以允许外网下载与 `ExternalProject` 步骤。
- [ ] 完成 UI 与帮助文档的全面中文化校对；解决残留占位符与专业术语一致性。
- [ ] 集成 VocalTractLab 3D 的有限元（FEM）求解模块，支持声学场与组织动力学仿真。
- [ ] 构建并验证复杂声道（多分支管道）模型的加载、网格划分与后处理流程。
- [ ] 在 x86_64 Linux 环境下完成基础与扩展示例 CI；后续补充 Windows、macOS (x86_64 / arm64) 的交叉构建或 GitHub Actions matrix 测试。
- [ ] 引入 CUDA / ROCm 条件编译选项，评估 GPU 加速 FEM 计算可行性。
- [ ] 优化 Nix derivation 产物体积，使用 `stripDebug` 与 `patchelf --shrink-rpath` 等策略，降低二进制发布大小。
- [ ] 发布 Cachix 二进制缓存，减少 CI 构建时间。
- [ ] 撰写用户手册与开发者文档，整理模块接口与插件示例。

## TODO

- [ ] …（添加更多待办） 