[![CI (Build)](https://github.com/Slicer/Slicer/actions/workflows/ci.yml/badge.svg)](https://github.com/Slicer/Slicer/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/Slicer/Slicer/badge)](https://securityscorecards.dev/viewer/?uri=github.com/Slicer/Slicer)

Slicer, or 3D Slicer, is a free, open source software package for visualization and
image analysis.

3D Slicer is natively designed to be available on multiple platforms,
including Windows, Linux and macOS.

Build instructions for all platforms are available on the Slicer wiki:
- https://slicer.readthedocs.io/en/latest/developer_guide/build_instructions/index.html

For Slicer community announcements and support, visit:
- https://discourse.slicer.org

For documentation, tutorials, and more information, please see:
- https://www.slicer.org

See License.txt for information on using and contributing.



-L
打印每个 derivation 的名字和阶段（例如 [1/12] Building Slicer）
--show-trace
出错时显示详细堆栈信息，便于定位 flake/module/nix 代码问题
--verbose
打印 Nix 本身的调试输出（如 fetcher 日志）
--keep-going
即使某个包构建失败，也尝试构建其他 derivation
--print-build-logs
构建失败后打印详细 build logs（否则默认隐藏）
NIX_BUILD_LOG=1
启用日志输出环境变量，让所有构建步骤保留日志并可查看

