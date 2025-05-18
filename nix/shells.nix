# This file defines the development shells.
# It expects pkgs, myCgal, myJinja2Github, and lib to be passed in.
{ pkgs, myCgal, myJinja2Github, lib }:
let
    wxqtDrv = pkgs.callPackage ./modules/wxqt.nix {
      qtbase = pkgs.qt5.qtbase;
      qttools = pkgs.qt5.qttools;
      libGL   = pkgs.libGL;
      libGLU  = pkgs.libGLU;
    };

  defaultShell = pkgs.mkShell {
    name = "vtl3d-env-custom-cgal";

    nativeBuildInputs = [
      pkgs.pkg-config
      pkgs.gnumake
      pkgs.cmake
      pkgs.gcc    # Using GCC from pkgs (currently 24.05)
      pkgs.git    # Add git for ExternalProject/FetchContent
      pkgs.ccache  # <--- 添加 ccache
      pkgs.gdb     # 调试器
    ];

    buildInputs = [
      wxqtDrv
      pkgs.eigen
      pkgs.boost
      myCgal            # Custom CGAL
      pkgs.gmp
      pkgs.mpfr
      pkgs.mesa
      pkgs.freeglut
      pkgs.openal
      pkgs.libGL
      pkgs.libGLU
      pkgs.glew
      pkgs.xorg.libXi
      pkgs.xorg.libXmu
      pkgs.xorg.libXext
      pkgs.xorg.libX11
      pkgs.libglvnd
      pkgs.libxkbcommon
      pkgs.ffmpeg_6
      pkgs.ffmpeg_6.dev
      pkgs.qt5Full       # Slicer needs Qt5
      pkgs.vulkan-loader
      pkgs.libxml2
    ];

    shellHook = ''
      # --- ccache 配置 (Simpler Method) ---
      export CCACHE_DIR="''${XDG_CACHE_HOME:-$HOME/.cache}/ccache-nix" # 指定缓存目录 (可选)
      # Ensure wxqt and ccache binaries appear early in PATH
      export PATH="${wxqtDrv}/bin:${pkgs.ccache}/bin:$PATH"
      # Remove explicit CC/CXX overrides and CMake launcher settings
      # Let ccache wrapper handle the compiler interception via PATH
      # ------------------------------------

      # Clear potential conflicting variables
      unset CGAL_DIR BOOST_ROOT CMAKE_PREFIX_PATH WXWIDGETS_CONFIG_EXECUTABLE GMP_INCLUDE_DIR GMP_LIBRARIES MPFR_INCLUDE_DIR MPFR_LIBRARIES GLUT_INCLUDE_DIR GLUT_glut_LIBRARY OPENAL_INCLUDE_DIR OPENAL_LIBRARY
      # Unset compiler variables in case they were set previously
      unset CC CXX CMAKE_C_COMPILER_LAUNCHER CMAKE_CXX_COMPILER_LAUNCHER

      # Set CGAL paths (custom)
      export CGAL_DIR="${myCgal}/lib/cmake/CGAL"

      # Set Boost paths
      export BOOST_ROOT="${pkgs.boost}"
      export BOOST_INCLUDEDIR="${pkgs.boost.dev}/include"
      export BOOST_LIBRARYDIR="${pkgs.boost}/lib"

      # Set WxWidgets config path
      export wxWidgets_CONFIG_EXECUTABLE="${wxqtDrv}/bin/wx-config"

      # Set FFmpeg paths
      export FFMPEG_INCLUDE_DIR="${pkgs.ffmpeg_6.dev}/include"
      export FFMPEG_LIBRARIES="${pkgs.ffmpeg_6}/lib"
      export PKG_CONFIG_PATH="${pkgs.ffmpeg_6.dev}/lib/pkgconfig:$PKG_CONFIG_PATH"

      # Set CMAKE_PREFIX_PATH including custom CGAL and Qt5
      export CMAKE_PREFIX_PATH="${myCgal}/lib/cmake/CGAL:${pkgs.boost}:${wxqtDrv}:${pkgs.eigen}:${pkgs.gmp}:${pkgs.mpfr}:${pkgs.freeglut}:${pkgs.openal}:${pkgs.libGL}:${pkgs.libGLU}:${pkgs.glew}:${pkgs.ffmpeg_6}:${pkgs.qt5Full}"

      # Set GMP and MPFR paths
      export GMP_INCLUDE_DIR="${pkgs.gmp.dev}/include"
      export GMP_LIBRARIES="${pkgs.gmp}/lib/libgmp.so"
      export MPFR_INCLUDE_DIR="${pkgs.mpfr.dev}/include"
      export MPFR_LIBRARIES="${pkgs.mpfr}/lib/libmpfr.so"

      # Set GLUT paths
      export GLUT_INCLUDE_DIR="${pkgs.freeglut.dev}/include"
      export GLUT_glut_LIBRARY="${pkgs.freeglut}/lib/libglut.so"

      # Set OpenAL paths
      export OPENAL_INCLUDE_DIR="${pkgs.openal}/include"
      export OPENAL_LIBRARY="${pkgs.openal}/lib/libopenal.so"

      # Set OpenGL environment variables
      export GL_INCLUDE_PATH="${pkgs.libGL.dev}/include:${pkgs.libGLU.dev}/include"
      export GL_LIBRARY_PATH="${pkgs.libGL}/lib:${pkgs.libGLU}/lib"
      export LD_LIBRARY_PATH="${pkgs.libGL}/lib:${pkgs.libGLU}/lib:${pkgs.glew}/lib:${pkgs.ffmpeg_6}/lib:$LD_LIBRARY_PATH"

      # Ensure X11 libraries can be found
      export LD_LIBRARY_PATH="${pkgs.xorg.libX11}/lib:${pkgs.xorg.libXext}/lib:${pkgs.xorg.libXi}/lib:${pkgs.xorg.libXmu}/lib:$LD_LIBRARY_PATH"

      # Add gcc runtime libraries (libstdc++ etc.) so wrapped binaries like PythonSlicer can start
      stdcpp_path="$(${pkgs.gcc}/bin/gcc -print-file-name=libstdc++.so)"
      if [[ -n "$stdcpp_path" && -f "$stdcpp_path" ]]; then
        export LD_LIBRARY_PATH="$(dirname "$stdcpp_path"):$LD_LIBRARY_PATH"
      fi

      # Set display variable if not set
      if [[ -z "$DISPLAY" ]]; then
        export DISPLAY=:0
      fi

      # Set XDG Data Dirs for GSettings schemas
      export XDG_DATA_DIRS="${pkgs.gsettings-desktop-schemas}/share/gsettings-schemas/${pkgs.gsettings-desktop-schemas.name}:${pkgs.gtk3}/share/gsettings-schemas/${pkgs.gtk3.name}:$XDG_DATA_DIRS"

      # Set C++ standard to C++14 via CMake variables
      export CMAKE_CXX_STANDARD=14
      export CMAKE_CXX_STANDARD_REQUIRED=ON
      export CMAKE_CXX_EXTENSIONS=OFF

      # Set CMake Policies
      export CMAKE_POLICY_DEFAULT_CMP0144=NEW
      export CMAKE_POLICY_DEFAULT_CMP0167=NEW
      export CMAKE_POLICY_DEFAULT_CMP0072=NEW

      # nixGL runner function with forced XCB platform for Qt
      run_with_nixgl() {
        echo "Running (forcing XCB): $@"
        QT_QPA_PLATFORM=xcb nix run --override-input nixpkgs nixpkgs/nixos-24.05 --impure github:nix-community/nixGL -- "$@"
      }
      alias nixGL='run_with_nixgl'

      # --- CMake Helper Functions ---
      configure_slicer_full() {
        local source_dir="''${1:-.}"
        local build_dir="''${2:-./build-slicer-full}"
        local install_prefix="''${3:-$build_dir/install}"

        echo "Configuring Slicer (Full)..."
        echo "Source Dir: $source_dir"
        echo "Build Dir:  $build_dir"
        echo "Install Prefix: $install_prefix"

        mkdir -p "$build_dir"
        cmake -S "$source_dir" -B "$build_dir" \
          -DCMAKE_INSTALL_PREFIX="$install_prefix" \
          -DCMAKE_BUILD_TYPE=Release \
          -DSlicer_CMake_HTTPS_Supported:BOOL=TRUE \
          -DSlicer_WC_LAST_CHANGED_DATE=1970-01-01
          # Add other Slicer full build flags here

        echo "Configuration complete. cd '$build_dir' and run 'make -j$(nproc)' or 'make install'."
      }

      configure_slicer_mini() {
        local source_dir="''${1:-.}"
        local build_dir="''${2:-./build-slicer-mini}"
        local install_prefix="''${3:-$build_dir/install}"
        # Resolve source_dir to an absolute path relative to PWD
        # Check if readlink exists, otherwise use python alternative for wider compatibility
        local absolute_source_dir
        if command -v readlink &> /dev/null; then
            absolute_source_dir="$(readlink -f "$source_dir")"
        elif command -v python &> /dev/null; then
            absolute_source_dir="$(python -c "import os, sys; print(os.path.abspath(sys.argv[1]))" "$source_dir")"
        else
            echo "Error: Cannot resolve absolute path. Need 'readlink' or 'python'." >&2
            return 1
        fi
        local slicer_source_path="$absolute_source_dir/Slicer" # Path to the Slicer subdirectory

        echo "Configuring Slicer (Minimal)..."
        echo "Source Dir: $absolute_source_dir"
        echo "Build Dir:  $build_dir"
        echo "Install Prefix: $install_prefix"
        # Adjust Extension Dir calculation to use absolute path
        local extension_source_dir="$absolute_source_dir/Modules/Scripted/Home" # Assuming Home module location
        echo "Extension Dir: $extension_source_dir"

        mkdir -p "$build_dir"
        # Use absolute paths for -S and -Dslicersources_SOURCE_DIR
        cmake -S "$absolute_source_dir" -B "$build_dir" \
          -DCMAKE_INSTALL_PREFIX="$install_prefix" \
          -DCMAKE_BUILD_TYPE=Release \
          -DSlicer_CMake_HTTPS_Supported:BOOL=TRUE \
          -DSlicer_WC_LAST_CHANGED_DATE=1970-01-01 \
          -Dslicersources_SOURCE_DIR:PATH="$slicer_source_path" # Use absolute Slicer source path

        echo "Configuration complete. cd '$build_dir' and run 'make -j$(nproc)' or 'make install'."
      }
      # --- End CMake Helper Functions ---ss

      echo "=== Environment Summary (Custom CGAL ${myCgal.version}) ==="
      echo "GCC Version: $(${pkgs.gcc}/bin/gcc --version | head -n1)"
      echo "Boost Version: ${pkgs.boost.version}"
      echo "WxWidgets (Qt) Version: $(${wxqtDrv}/bin/wx-config --version)"
      echo "CGAL Version: ${myCgal.version} (custom build)"
      echo "Eigen Version: ${pkgs.eigen.version}"
      echo "FFmpeg Version: ${pkgs.ffmpeg_6.version}"
      echo "Qt5 (Base) Version: ${pkgs.qt5.qtbase.version}"
      echo "CGAL_DIR: $CGAL_DIR (custom build)"
      echo "BOOST_ROOT: $BOOST_ROOT"
      echo "wxWidgets_CONFIG_EXECUTABLE: $wxWidgets_CONFIG_EXECUTABLE"
      echo "CMAKE_PREFIX_PATH: $CMAKE_PREFIX_PATH"
      echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
      echo "======================================================="
      echo "nixGL Integration: Use 'nixGL <command>' or 'run_with_nixgl <command>' (Forces QT_QPA_PLATFORM=xcb)"
      echo "======================================================="
      echo -e "
CMake Helper Usage (run from project root):
  configure_slicer_mini ./miniSlicer ./build/build-mini ./build/install-mini
  cd ./build/build-mini && make -j$(nproc)
  or
  configure_slicer_full ./miniSlicer/Slicer ./build/build-full ./build/install-full
  cd ./build/build-full && make -j$(nproc)
"
      echo "Compiler cache (ccache) enabled."
      echo "CCACHE_DIR: $CCACHE_DIR"

      if [ -f .env ]; then
        set -a
        . ./.env
        set +a
      fi
    '';
  };

  # Python development shell
  python = pkgs.mkShell {
    name = "vtl3d-python-env";

    buildInputs = [
      pkgs.python3                 # Default Python 3 from pkgs
      pkgs.python3Packages.matplotlib
      pkgs.python3Packages.numpy
      pkgs.python3Packages.trimesh
      pkgs.python3Packages.rtree
      pkgs.python3Packages.openai          # Add OpenAI Python SDK
      pkgs.python3Packages.aiofiles
      pkgs.python3Packages.pip
      pkgs.python3Packages.cookiecutter
      myJinja2Github             # Custom jinja2-github
      pkgs.libxml2
      pkgs.python3Packages.pyyaml  # ← 新增
    ];

    shellHook = ''
      echo "=== Python Development Environment ==="
      python --version
      # 动态列出安装的包名称（忽略版本号）
      if command -v pip &>/dev/null; then
        pkg_list=$(pip list --format=columns | tail -n +3 | awk '{print $1}' | paste -sd', ' -)
        echo "Available packages: $pkg_list"
      fi
      echo "===================================="

      if [ -f .env ]; then
        set -a
        . ./.env
        set +a
      fi
    '';
  };

  # Shell for VTL3D (wxGTK GTK3 backend)
  miniVTL3D = pkgs.mkShell {
    name = "vtl3d-wxgtk-env";

    nativeBuildInputs = [
      pkgs.pkg-config pkgs.gnumake pkgs.cmake pkgs.gcc pkgs.git pkgs.ccache
      pkgs.gdb  # 调试器
    ];

    buildInputs = [
      pkgs.wxGTK32 pkgs.eigen pkgs.boost myCgal pkgs.gmp pkgs.mpfr pkgs.mesa
      pkgs.freeglut pkgs.openal pkgs.libGL pkgs.libGLU pkgs.glew pkgs.xorg.libXi
      pkgs.xorg.libXmu pkgs.xorg.libXext pkgs.xorg.libX11 pkgs.libglvnd
      pkgs.libxkbcommon pkgs.ffmpeg_6 pkgs.ffmpeg_6.dev pkgs.qt5Full
      pkgs.vulkan-loader pkgs.libxml2
    ];

    shellHook = ''
      # --- ccache 配置 ---
      export CCACHE_DIR="''${XDG_CACHE_HOME:-$HOME/.cache}/ccache-nix"
      export PATH="${pkgs.wxGTK32}/bin:${pkgs.ccache}/bin:$PATH"

      # 清理变量
      unset CGAL_DIR BOOST_ROOT CMAKE_PREFIX_PATH WXWIDGETS_CONFIG_EXECUTABLE
      unset GMP_INCLUDE_DIR GMP_LIBRARIES MPFR_INCLUDE_DIR MPFR_LIBRARIES
      unset GLUT_INCLUDE_DIR GLUT_glut_LIBRARY OPENAL_INCLUDE_DIR OPENAL_LIBRARY
      unset CC CXX CMAKE_C_COMPILER_LAUNCHER CMAKE_CXX_COMPILER_LAUNCHER

      # 基础路径
      export CGAL_DIR="${myCgal}/lib/cmake/CGAL"
      export BOOST_ROOT="${pkgs.boost}"
      export BOOST_INCLUDEDIR="${pkgs.boost.dev}/include"
      export BOOST_LIBRARYDIR="${pkgs.boost}/lib"
      export wxWidgets_CONFIG_EXECUTABLE="${pkgs.wxGTK32}/bin/wx-config"

      export FFMPEG_INCLUDE_DIR="${pkgs.ffmpeg_6.dev}/include"
      export FFMPEG_LIBRARIES="${pkgs.ffmpeg_6}/lib"
      export PKG_CONFIG_PATH="${pkgs.ffmpeg_6.dev}/lib/pkgconfig:$PKG_CONFIG_PATH"

      export CMAKE_PREFIX_PATH="${myCgal}/lib/cmake/CGAL:${pkgs.boost}:${pkgs.wxGTK32}:${pkgs.eigen}:${pkgs.gmp}:${pkgs.mpfr}:${pkgs.freeglut}:${pkgs.openal}:${pkgs.libGL}:${pkgs.libGLU}:${pkgs.glew}:${pkgs.ffmpeg_6}:${pkgs.qt5Full}"

      export GMP_INCLUDE_DIR="${pkgs.gmp.dev}/include"
      export GMP_LIBRARIES="${pkgs.gmp}/lib/libgmp.so"
      export MPFR_INCLUDE_DIR="${pkgs.mpfr.dev}/include"
      export MPFR_LIBRARIES="${pkgs.mpfr}/lib/libmpfr.so"

      export GLUT_INCLUDE_DIR="${pkgs.freeglut.dev}/include"
      export GLUT_glut_LIBRARY="${pkgs.freeglut}/lib/libglut.so"

      export OPENAL_INCLUDE_DIR="${pkgs.openal}/include"
      export OPENAL_LIBRARY="${pkgs.openal}/lib/libopenal.so"

      export GL_INCLUDE_PATH="${pkgs.libGL.dev}/include:${pkgs.libGLU.dev}/include"
      export GL_LIBRARY_PATH="${pkgs.libGL}/lib:${pkgs.libGLU}/lib"
      export LD_LIBRARY_PATH="${pkgs.libGL}/lib:${pkgs.libGLU}/lib:${pkgs.glew}/lib:${pkgs.ffmpeg_6}/lib:$LD_LIBRARY_PATH"
      export LD_LIBRARY_PATH="${pkgs.xorg.libX11}/lib:${pkgs.xorg.libXext}/lib:${pkgs.xorg.libXi}/lib:${pkgs.xorg.libXmu}/lib:$LD_LIBRARY_PATH"

      stdcpp_path="$(${pkgs.gcc}/bin/gcc -print-file-name=libstdc++.so)"
      if [[ -n "$stdcpp_path" && -f "$stdcpp_path" ]]; then
        export LD_LIBRARY_PATH="$(dirname "$stdcpp_path"):$LD_LIBRARY_PATH"
      fi

      [[ -z "$DISPLAY" ]] && export DISPLAY=:0

      export XDG_DATA_DIRS="${pkgs.gsettings-desktop-schemas}/share/gsettings-schemas/${pkgs.gsettings-desktop-schemas.name}:${pkgs.gtk3}/share/gsettings-schemas/${pkgs.gtk3.name}:$XDG_DATA_DIRS"

      export CMAKE_CXX_STANDARD=14
      export CMAKE_CXX_STANDARD_REQUIRED=ON
      export CMAKE_CXX_EXTENSIONS=OFF

      export CMAKE_POLICY_DEFAULT_CMP0144=NEW
      export CMAKE_POLICY_DEFAULT_CMP0167=NEW
      export CMAKE_POLICY_DEFAULT_CMP0072=NEW

      run_with_nixgl() {
        echo "Running (forcing XCB): $@"
        QT_QPA_PLATFORM=xcb nix run --override-input nixpkgs nixpkgs/nixos-24.05 --impure github:nix-community/nixGL -- "$@"
      }
      alias nixGL='run_with_nixgl'

      # --- VTL3D build aliases ---
      alias make_vtl='(echo "执行 make_vtl" && cd miniVTL3D/sources && mkdir -p build && cd build && cmake .. && make -j$(nproc))'
      alias remake_vtl='(echo "执行 remake_vtl" && cd miniVTL3D/sources/build && make -j$(nproc))'
      alias clean_vtl='(echo "执行 clean_vtl: 正在删除 miniVTL3D/sources/build..." && rm -rf miniVTL3D/sources/build && echo "clean_vtl 已完成.")'

      # --- Debug 版本构建 & gdb 运行 ---
      alias make_vtl_debug='(echo "执行 make_vtl_debug: 以 Debug 模式重新配置并编译..." && cd miniVTL3D/sources && rm -rf build_debug && mkdir -p build_debug && cd build_debug && cmake -DCMAKE_BUILD_TYPE=Debug .. && make -j$(nproc) && echo "make_vtl_debug 已完成. 可执行在 miniVTL3D/sources/build_debug/VocalTractLab")'

      alias run_vtl_gdb='(echo "启动 gdb (Debug build)" && cd miniVTL3D/sources/build_debug && ulimit -c unlimited && gdb ./VocalTractLab)'

      echo ""
      echo "======================================================="
      echo "        VocalTractLab3D 开发环境        "
      echo "======================================================="
      echo "Nix Shell 环境已激活."
      echo ""
      echo "--- 构建 VocalTractLab3D (本项目) ---"
      echo "  假设您当前位于 VocalTractLab3D 项目根目录 (例如, /home/jqwang/Work/01-Vocal3D)."
      echo "  主 CMakeLists.txt 文件预期位于子目录如 'miniVTL3D/sources/' 下."
      echo ""
      echo "  1. 进入 VTL3D 源码目录:"
      echo "     cd miniVTL3D/sources"
      echo "  2. 创建并进入构建目录:"
      echo "     mkdir -p build && cd build"
      echo "  3. 使用 CMake 配置项目:"
      echo "     cmake .."
      echo "  4. 编译项目:"
      echo "     make -j$(nproc)  # 或直接使用 'make'"
      echo ""
      echo "--- 本项目自定义构建别名 ---"
      echo "  'make_vtl': 进入 miniVTL3D/sources/build, 配置 (cmake ..) 并构建项目."
      echo "  'remake_vtl': 进入 miniVTL3D/sources/build 并运行 'make -j$(nproc)' (不清理,不重新配置)."
      echo "  'clean_vtl': 删除 miniVTL3D/sources/build 目录."
      echo "  'make_vtl_debug': 以 Debug 模式重新配置并编译 (build_debug)。"
      echo "  'run_vtl_gdb': 在 build_debug 目录下用 gdb 启动 VocalTractLab。"
      echo ""
      echo "=== VTL3D build environment ready ==="
    '';
  };

in
{
  default = defaultShell;
  miniSlicer = defaultShell;
  miniVTL3D = miniVTL3D;
  python = python;
}
