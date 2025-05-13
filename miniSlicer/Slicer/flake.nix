{
  description = "Development environment for VocalTractLab3D with specific dependencies";

  inputs = {
    # 主 Nixpkgs，用于获取构建工具和基础环境
    # nixpkgs.url = "github:NixOS/nixpkgs/nixos-23.11"; # 使用 23.11 稳定分支
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05"; # 使用 24.05 稳定分支

    # 添加 24.05 输入，专门用于 CGAL <= 移除
    # nixpkgs_24_05.url = "github:NixOS/nixpkgs/nixos-24.05";

    # 使用 Git URL 格式直接指定官方 21.05 分支，仅用于 wxWidgets 和 Eigen <= 移除
    # nixpkgs_21_05.url = "git+https://github.com/NixOS/nixpkgs.git?ref=nixos-21.05";

    # 使用 20.03 版本获取老版本的 Boost 1.71.0 <= 移除
    # nixpkgs_20_03.url = "git+https://github.com/NixOS/nixpkgs.git?ref=nixos-20.03";

    flake-utils.url = "github:numtide/flake-utils";

    # 添加 nixGL 输入
    nixgl.url = "github:nix-community/nixGL";
  };

  outputs = { self, nixpkgs, flake-utils, nixgl }: # 添加 nixgl 到输入参数
    flake-utils.lib.eachDefaultSystem (system:
      let
        # 定义使用的 nixpkgs 实例，添加 nixGL 的 overlay
        pkgs = import nixpkgs {
          inherit system;
          config = { allowUnfree = true; };
          overlays = [ nixgl.overlay ]; # 添加 nixGL 的 overlay
        };
        # pkgs_24_05 = import nixpkgs_24_05 { inherit system; config = { allowUnfree = true; }; }; # 用于 CGAL: 24.05 <= 移除
        # pkgs_21_05 = import nixpkgs_21_05 { inherit system; config = { allowUnfree = true; }; }; # 21.05 <= 移除
        # pkgs_20_03 = import nixpkgs_20_03 { inherit system; config = { allowUnfree = true; }; }; # 20.03 <= 移除

        # 导入自定义的 CGAL 包
        myCgal = pkgs.callPackage ./pkgs/cgal {
          # 从主 pkgs (24.05) 提供依赖
          boost = pkgs.boost;
          gmp = pkgs.gmp;
          mpfr = pkgs.mpfr;
          # cmake 会自动由 pkgs.callPackage 注入
          # stdenv 和 fetchurl 也会自动注入
        };

        # 自定义构建 jinja2-github 包
        myJinja2Github = pkgs.python3Packages.buildPythonPackage rec {
          pname = "jinja2-github";
          version = "0.1.1";
          format = "setuptools"; # 该包使用 setup.py

          src = pkgs.fetchurl { # 使用 fetchurl 直接下载
            url = "https://files.pythonhosted.org/packages/e6/ba/9012b1a96c56f217b64b9d84509fab3ca7bee46721035b7d090503e715ed/jinja2_github-0.1.1.tar.gz";
            hash = "sha256-DWuRJl1eKv+YFYzv121Utb/tAsF37UJkPvRftvpNAY8="; # 使用 Nix 报告的正确哈希
          };

          propagatedBuildInputs = [
            pkgs.python3Packages.jinja2
            pkgs.python3Packages.requests
            pkgs.python3Packages.pygithub
          ];

          # 如果需要，可以禁用检查阶段
          doCheck = false; # 禁用测试阶段以避免 pip 依赖问题

          meta = with pkgs.lib; {
            description = "Jinja2 extension for generating GitHub wiki/issue links";
            homepage = "https://github.com/kpfleming/jinja2-github";
            license = licenses.mit; # MIT 许可证
          };
        };
      in
      {
        devShells = {
          default = pkgs.mkShell {
            name = "vtl3d-env-custom-cgal"; # 更新名字以反映变化

            # 构建工具 - 来自 24.05
            nativeBuildInputs = [
              pkgs.pkg-config
              pkgs.gnumake
              pkgs.cmake
              pkgs.gcc    # 尝试使用 GCC 12
            ];

            # 依赖库 - 全部来自 24.05 (pkgs)，除了 CGAL
            buildInputs = [
              pkgs.wxGTK32      # WxWidgets (来自 24.05)
              pkgs.eigen        # Eigen (来自 24.05)
              pkgs.boost        # Boost (来自 24.05)
              # pkgs.cgal         # CGAL (来自 24.05) <= 替换为自定义版本
              myCgal            # 使用自定义编译的 CGAL
              pkgs.gmp          # GMP (来自 24.05, 也是 myCgal 的依赖)
              pkgs.mpfr         # MPFR (来自 24.05, 也是 myCgal 的依赖)
              pkgs.mesa         # OpenGL (Mesa) (来自 24.05)
              pkgs.freeglut     # GLUT (来自 24.05)
              pkgs.openal       # OpenAL (来自 24.05)

              # 添加额外的 OpenGL 依赖
              pkgs.libGL
              pkgs.libGLU
              pkgs.glew
              pkgs.xorg.libXi
              pkgs.xorg.libXmu
              pkgs.xorg.libXext
              pkgs.xorg.libX11
              pkgs.libglvnd      # OpenGL 加载器
              pkgs.libxkbcommon  # XKB 共享库

              # 添加 FFmpeg 及其相关库，用于支持 AVI 文件处理
              pkgs.ffmpeg_6      # 使用 FFmpeg 6.x 版本
              pkgs.ffmpeg_6.dev  # 开发头文件
              # 移除不安全的 libav 包
              pkgs.pkg-config    # 用于定位库 (注意：包名已从 pkgconfig 更改为 pkg-config)

              # 添加 Qt5 依赖
              pkgs.qt5Full       # Slicer 需要 Qt5
              pkgs.vulkan-loader # 尝试解决 nixGL 的 Vulkan 初始化问题
            ];

            # 使用主 nixpkgs 的 C++ 编译器和标准环境，但指定使用 C++14
            # packages = [ pkgs.gcc ]; # 这行似乎多余，因为 gcc 已经在 nativeBuildInputs 里了

            # 增强版 shellHook，明确设置所有关键环境变量
            shellHook = ''
              # 清除可能的缓存或冲突变量
              unset CGAL_DIR BOOST_ROOT CMAKE_PREFIX_PATH WXWIDGETS_CONFIG_EXECUTABLE GMP_INCLUDE_DIR GMP_LIBRARIES MPFR_INCLUDE_DIR MPFR_LIBRARIES GLUT_INCLUDE_DIR GLUT_glut_LIBRARY OPENAL_INCLUDE_DIR OPENAL_LIBRARY

              # 明确设置 CGAL 相关路径 - 使用自定义版本
              # export CGAL_DIR="${pkgs.cgal}/lib/cmake/CGAL" <= 替换
              export CGAL_DIR="${myCgal}/lib/cmake/CGAL"

              # 明确设置 Boost 相关路径 - 使用 24.05
              export BOOST_ROOT="${pkgs.boost}"
              export BOOST_INCLUDEDIR="${pkgs.boost.dev}/include"
              export BOOST_LIBRARYDIR="${pkgs.boost}/lib"

              # 确保 CMake 能够找到 wxWidgets - 使用 24.05
              export wxWidgets_CONFIG_EXECUTABLE="${pkgs.wxGTK32}/bin/wx-config"

              # 明确设置 FFmpeg 相关路径
              export FFMPEG_INCLUDE_DIR="${pkgs.ffmpeg_6.dev}/include"
              export FFMPEG_LIBRARIES="${pkgs.ffmpeg_6}/lib"
              export PKG_CONFIG_PATH="${pkgs.ffmpeg_6.dev}/lib/pkgconfig:$PKG_CONFIG_PATH"

              # 重要：添加路径到 CMAKE_PREFIX_PATH - 统一使用 pkgs (24.05)，除了 CGAL
              # export CMAKE_PREFIX_PATH="${pkgs.cgal}/lib/cmake/CGAL:${pkgs.boost}:${pkgs.wxGTK32}:${pkgs.eigen}:${pkgs.gmp}:${pkgs.mpfr}:${pkgs.freeglut}:${pkgs.openal}" <= 替换
              # export CMAKE_PREFIX_PATH="${myCgal}/lib/cmake/CGAL:${pkgs.boost}:${pkgs.wxGTK32}:${pkgs.eigen}:${pkgs.gmp}:${pkgs.mpfr}:${pkgs.freeglut}:${pkgs.openal}:${pkgs.libGL}:${pkgs.libGLU}:${pkgs.glew}:${pkgs.ffmpeg_6}"
              # 添加 Qt5 到 CMAKE_PREFIX_PATH
              export CMAKE_PREFIX_PATH="${myCgal}/lib/cmake/CGAL:${pkgs.boost}:${pkgs.wxGTK32}:${pkgs.eigen}:${pkgs.gmp}:${pkgs.mpfr}:${pkgs.freeglut}:${pkgs.openal}:${pkgs.libGL}:${pkgs.libGLU}:${pkgs.glew}:${pkgs.ffmpeg_6}:${pkgs.qt5Full}"

              # 明确设置 GMP 和 MPFR 的路径变量 - 来自 24.05
              export GMP_INCLUDE_DIR="${pkgs.gmp.dev}/include"
              export GMP_LIBRARIES="${pkgs.gmp}/lib/libgmp.so"
              export MPFR_INCLUDE_DIR="${pkgs.mpfr.dev}/include"
              export MPFR_LIBRARIES="${pkgs.mpfr}/lib/libmpfr.so"

              # 明确设置 GLUT 路径 - 来自 24.05
              export GLUT_INCLUDE_DIR="${pkgs.freeglut.dev}/include"
              export GLUT_glut_LIBRARY="${pkgs.freeglut}/lib/libglut.so"

              # 明确设置 OpenAL 路径 - 来自 24.05
              export OPENAL_INCLUDE_DIR="${pkgs.openal}/include"
              export OPENAL_LIBRARY="${pkgs.openal}/lib/libopenal.so"

              # 设置 OpenGL 环境变量
              export GL_INCLUDE_PATH="${pkgs.libGL.dev}/include:${pkgs.libGLU.dev}/include"
              export GL_LIBRARY_PATH="${pkgs.libGL}/lib:${pkgs.libGLU}/lib"
              export LD_LIBRARY_PATH="${pkgs.libGL}/lib:${pkgs.libGLU}/lib:${pkgs.glew}/lib:${pkgs.ffmpeg_6}/lib:$LD_LIBRARY_PATH"

              # 确保 X11 库可以被找到
              export LD_LIBRARY_PATH="${pkgs.xorg.libX11}/lib:${pkgs.xorg.libXext}/lib:${pkgs.xorg.libXi}/lib:${pkgs.xorg.libXmu}/lib:$LD_LIBRARY_PATH"

              # 设置 GLX 显示变量
              if [[ -z "$DISPLAY" ]]; then
                export DISPLAY=:0
              fi

              # 设置 XDG 相关环境变量
              export XDG_DATA_DIRS="${pkgs.gsettings-desktop-schemas}/share/gsettings-schemas/${pkgs.gsettings-desktop-schemas.name}:${pkgs.gtk3}/share/gsettings-schemas/${pkgs.gtk3.name}:$XDG_DATA_DIRS"

              # 设置 C++ 标准版本为 C++14
              #export CXXFLAGS="-std=c++14 $CXXFLAGS"
              export CMAKE_CXX_STANDARD=14
              export CMAKE_CXX_STANDARD_REQUIRED=ON
              export CMAKE_CXX_EXTENSIONS=OFF

              # 设置 CMake Policy
              export CMAKE_POLICY_DEFAULT_CMP0144=NEW
              export CMAKE_POLICY_DEFAULT_CMP0167=NEW
              export CMAKE_POLICY_DEFAULT_CMP0072=NEW

              # 添加 nixGL 运行函数
              run_with_nixgl() {
                # echo "运行: $@"
                echo "运行 (强制使用 XCB): $@" # 更新提示信息
                # nix run --override-input nixpkgs nixpkgs/nixos-24.05 --impure github:nix-community/nixGL -- "$@"
                QT_QPA_PLATFORM=xcb nix run --override-input nixpkgs nixpkgs/nixos-24.05 --impure github:nix-community/nixGL -- "$@" # 添加环境变量
              }

              # 创建 nixGL 命令别名
              alias nixGL='run_with_nixgl'

              echo "=== 环境变量设置 (Custom CGAL ${myCgal.version}) ===" # 更新标题
              echo "GCC 版本: $(${pkgs.gcc12}/bin/gcc --version | head -n1) (gcc12 from 24.05)"
              echo "Boost 版本: ${pkgs.boost.version} (from 24.05)"
              echo "WxWidgets 版本: $(${pkgs.wxGTK32}/bin/wx-config --version) (from 24.05)"
              # echo "CGAL 版本: ${pkgs.cgal.version} (from 24.05)" <= 替换
              echo "CGAL 版本: ${myCgal.version} (custom build)"
              echo "Eigen 版本: ${pkgs.eigen.version} (from 24.05)"
              echo "FFmpeg 版本: ${pkgs.ffmpeg_6.version} (from 24.05)"
              # echo "CGAL_DIR: $CGAL_DIR (from 24.05)" <= 替换
              echo "CGAL_DIR: $CGAL_DIR (custom build)"
              echo "BOOST_ROOT: $BOOST_ROOT (from 24.05)"
              echo "wxWidgets_CONFIG_EXECUTABLE: $wxWidgets_CONFIG_EXECUTABLE (from 24.05)"
              echo "Qt5 (Base) 版本: ${pkgs.qt5.qtbase.version} (from 24.05)"
              echo "CMAKE_PREFIX_PATH: $CMAKE_PREFIX_PATH"
              echo "OpenGL 库路径: $GL_LIBRARY_PATH"
              echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
              echo "======================================================="

              # 添加 nixGL 信息
              echo "nixGL 已通过 run_with_nixgl 函数和 nixGL 别名集成到环境中"
              echo "使用方法："
              echo "  nixGL ./geometry_viewer"
              echo "或者"
              echo "  run_with_nixgl ./geometry_viewer"
              echo "======================================================="

              # 提示用户如何清除 CMake 缓存
              echo -e "
如果 CMake 仍然有问题，请尝试清除 CMake 缓存："
              echo "  cd sources/build && rm -rf CMakeCache.txt CMakeFiles/ && cmake .. -DCMAKE_BUILD_TYPE=Release"
            '';
          };

          # 新增 Python 开发环境
          python = pkgs.mkShell {
            name = "vtl3d-python-env";

            # 包含 Python 解释器和所需库
            buildInputs = [
              pkgs.python3                 # 使用 24.05 的默认 Python3
              pkgs.python3Packages.matplotlib # 用于绘图
              pkgs.python3Packages.numpy   # 用于数值计算
              pkgs.python3Packages.trimesh # 用于处理三角网格
              pkgs.python3Packages.rtree   # 用于空间索引
              pkgs.python3Packages.pip      # 用于可选的包管理
              pkgs.python3Packages.cookiecutter
              #pkgs.python3Packages.jinja2-github
              myJinja2Github                 # 添加自定义的 jinja2-github 包
            ];

            shellHook = ''
              echo "=== 进入 Python 开发环境 ==="
              echo "Python 版本: $(python --version)"
              echo "Matplotlib 可用"
              echo "==========================="

              # 可以在这里添加 venv 创建/激活的逻辑，如果需要的话
              # 例如:
              # if [ ! -d ".venv" ]; then
              #   python -m venv .venv
              # fi
              # source .venv/bin/activate
            '';
          };
        };

        # 添加 packages 定义
        packages = {
          Slicer = pkgs.stdenv.mkDerivation rec {
            pname = "vtl3d-slicer"; # 包名
            version = "0.1";        # 版本号 (可以根据需要修改)


            # 源代码: 当前目录，过滤掉 .git 等
            src = pkgs.lib.cleanSource ./.;

            # 构建工具 (与 devShell 相同)
            nativeBuildInputs = [
              pkgs.pkg-config
              pkgs.gnumake
              pkgs.cmake
              pkgs.gcc12    # 确保使用与 devShell 一致的 GCC 版本
              pkgs.git      # 添加 Git 依赖
              pkgs.cacert   # 添加 CA 证书 (以防 curl 需要)
              pkgs.curl     # 添加 curl 用于下载
              pkgs.perl     # OpenSSL 配置需要 Perl
            ];

            # 依赖库 (与 devShell 相同)
            buildInputs = [
              pkgs.wxGTK32
              pkgs.eigen
              pkgs.boost
              myCgal
              pkgs.gmp
              pkgs.mpfr
              pkgs.mesa
              pkgs.libGLU
              pkgs.freeglut
              pkgs.openal
              pkgs.libGL
              pkgs.glew
              pkgs.xorg.libXi
              pkgs.xorg.libXmu
              pkgs.xorg.libXext
              pkgs.xorg.libX11
              pkgs.libglvnd
              pkgs.libxkbcommon
              pkgs.ffmpeg_6
              pkgs.ffmpeg_6.dev
              pkgs.qt5Full
              pkgs.vulkan-loader
            ];

            # CMake 配置标志
            cmakeFlags = [
              "-DCMAKE_BUILD_TYPE=Release"
              "-DSlicer_CMake_HTTPS_Supported:BOOL=TRUE" # 跳过 HTTPS 网络检查
              "-DSlicer_WC_LAST_CHANGED_DATE=1970-01-01" # 提供虚拟日期以避免错误
              # CMAKE_PREFIX_PATH 通常由 Nix 自动处理 buildInputs
              # 但如果需要，可以在这里添加额外的路径
              # 例如: "-DCGAL_DIR=${myCgal}/lib/cmake/CGAL"
              # 但最好让 CMake 通过 find_package 自动查找
            ];

            # 允许网络访问 (用于 ExternalProject 下载)
            __impure = true;

            # 构建阶段
            # Nix 会自动在 build/ 子目录下运行 CMake
            # configurePhase = ''
            #   runHook preConfigure
            #   cmake .. -DCMAKE_INSTALL_PREFIX=$out $cmakeFlags
            #   runHook postConfigure
            # '';

            # buildPhase = ''
            #   runHook preBuild
            #   make -j$NIX_BUILD_CORES
            #   runHook postBuild
            # '';

            # 安装阶段: 将构建好的可执行文件复制到 $out/bin
            # 假设主可执行文件位于 sources/build/geometry_viewer
            installPhase = ''
              runHook preInstall
              ls -all
              cd Slicer-build  # 假设内部构建目录名为 Slicer-build
              make install DESTDIR=$out
              runHook postInstall
            '';

            # 添加元信息
            meta = with pkgs.lib; {
              description = "VocalTractLab 3D Slicer Application";
              # homepage = "your-project-homepage"; # 替换为项目主页
              license = licenses.unfree; # 或其他合适的许可证
              platforms = platforms.linux; # 假设主要在 Linux 上开发
            };
          };

          # 默认包指向 Slicer
          default = self.packages.${system}.Slicer;

          # --- 修改：最小化 Slicer 构建 (现在包含 Python 支持) ---
          miniSlicer = pkgs.stdenv.mkDerivation rec {
            pname = "mini-slicer-template-config"; # Updated name reflecting source
            version = "0.1-template-config"; # Updated version

            # 源代码
            src = pkgs.lib.cleanSource ./.;

            # 构建系统依赖
            nativeBuildInputs = [
              pkgs.pkg-config
              pkgs.gnumake
              pkgs.cmake
              pkgs.gcc12
              pkgs.git
              pkgs.cacert
              pkgs.curl
              pkgs.perl
            ];

            # 运行和链接时依赖
            buildInputs = [
              # 核心 C++ 库
              pkgs.eigen
              pkgs.boost
              pkgs.zlib
              pkgs.libarchive

              # GUI 和可视化核心
              pkgs.qt5Full
              pkgs.mesa
              pkgs.libGLU
              pkgs.libGL
              pkgs.xorg.libXi
              pkgs.xorg.libXmu
              pkgs.xorg.libXext
              pkgs.xorg.libX11
              pkgs.libglvnd
              pkgs.libxkbcommon
              pkgs.vulkan-loader

              # XML/JSON 解析
              pkgs.libxml2
              # pkgs.rapidjson # Slicer SuperBuild 会构建

              # 图像格式 (基础)
              pkgs.libjpeg
              pkgs.libtiff
              pkgs.pngquant # 或 pkgs.libpng

              # Python 环境
              pkgs.python3
              pkgs.python3.pkgs.numpy

              # 新增：DICOM 支持
              pkgs.dcmtk
            ];

            # CMake 配置标志 - 基于 SlicerCustomAppTemplate 默认值
            cmakeFlags = [
              "-DCMAKE_BUILD_TYPE=Release"
              "-DSlicer_CMake_HTTPS_Supported:BOOL=TRUE"
              "-DSlicer_WC_LAST_CHANGED_DATE=1970-01-01"
              "-DBUILD_TESTING=ON" # 启用测试 (模板默认)

              # --- 功能开关 (匹配模板默认值) --- #
              "-DSlicer_USE_PYTHONQT:BOOL=ON"          # ON
              "-DSlicer_BUILD_DICOM_SUPPORT:BOOL=ON"     # ON
              "-DSlicer_USE_SimpleITK:BOOL=OFF"          # OFF
              # --- 明确指定使用 Nix 提供的 Python --- #
              "-DPython_EXECUTABLE:FILEPATH=${pkgs.python3}/bin/python3"
              "-DPython_INCLUDE_DIR:PATH=${pkgs.python3}/include/python${pkgs.python3.pythonVersion}"
              "-DPython_LIBRARY:FILEPATH=${pkgs.python3}/lib/libpython${pkgs.python3.pythonVersion}.so"
              "-DPython_NumPy_INCLUDE_DIR:PATH=${pkgs.python3.pkgs.numpy}/${pkgs.python3.sitePackages}/numpy/core/include"

              # --- 禁用非必需功能 --- #
              # CLI Support is ON implicitly by enabling modules below
              "-DSlicer_USE_TBB:BOOL=OFF"              # OFF (不在模板中，假定OFF)
              "-DSlicer_BUILD_EXTENSIONMANAGER_SUPPORT:BOOL=OFF" # OFF
              "-DSlicer_BUILD_APPLICATIONUPDATE_SUPPORT:BOOL=OFF" # OFF
              "-DSlicer_EXTENSION_SOURCE_DIRS:STRING=" # 清空，不构建模板的自定义模块
              "-DSlicer_BUILD_DIFFUSION_SUPPORT:BOOL=OFF"           # OFF
              "-DSlicer_BUILD_MULTIVOLUME_SUPPORT:BOOL=OFF"         # OFF
              "-DSlicer_BUILD_PARAMETERSERIALIZER_SUPPORT:BOOL=OFF" # OFF
              "-DSlicer_USE_QtTesting:BOOL=OFF"            # OFF

              # --- 远程模块 (匹配模板默认值，保留 vtkAddon) --- #
              "-DSlicer_BUILD_MultiVolumeExplorer:BOOL=OFF"
              "-DSlicer_BUILD_MultiVolumeImporter:BOOL=OFF"
              "-DSlicer_BUILD_SimpleFilters:BOOL=OFF"
              "-DSlicer_BUILD_BRAINSTOOLS:BOOL=OFF"
              "-DSlicer_BUILD_CompareVolumes:BOOL=OFF"
              "-DSlicer_BUILD_LandmarkRegistration:BOOL=OFF"
              "-DSlicer_BUILD_SurfaceToolbox:BOOL=OFF"

              # --- 内置模块启用/禁用 (完全匹配模板) --- #
              "-DSlicer_CLIMODULES_ENABLED:STRING=ResampleDTIVolume;ResampleScalarVectorDWIVolume"
              "-DSlicer_QTLOADABLEMODULES_ENABLED:STRING=" # 模板为空
              "-DSlicer_QTSCRIPTEDMODULES_ENABLED:STRING=" # 模板为空
              "-DSlicer_CLIMODULES_DISABLED:STRING=" # 模板为空
              "-DSlicer_QTLOADABLEMODULES_DISABLED:STRING=SceneViews;SlicerWelcome;ViewControllers"
              "-DSlicer_QTSCRIPTEDMODULES_DISABLED:STRING=DataProbe;DMRIInstall;Endoscopy;LabelStatistics;PerformanceTests;SampleData;VectorToScalarVolume"
            ];

            # 允许网络访问
            __impure = true;

            # 安装阶段
            installPhase = ''
              runHook preInstall
              cd Slicer-build
              make install DESTDIR=$out
              runHook postInstall
            '';

            # 元信息
            meta = with pkgs.lib; {
              description = "Slicer build configured based on SlicerCustomAppTemplate defaults"; # 更新描述
              homepage = "https://www.slicer.org/";
              license = licenses.bsd3;
              platforms = platforms.linux;
            };
          }; # --- miniSlicer 定义结束 ---
        };
      });
}
