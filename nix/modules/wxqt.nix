{ lib, stdenv, fetchFromGitHub, cmake, ninja, pkg-config,
  qtbase, qttools, libGL, libGLU }:

stdenv.mkDerivation rec {
  pname   = "wxqt";
  version = "3.2.4";

  src = fetchFromGitHub {
    owner  = "wxWidgets";
    repo   = "wxWidgets";
    rev    = "v${version}";
    sha256 = "mYZWyT+JeO+1RUwm9pEqjTUrCJncnanbdOiM5+nJiTw="; # TODO: nix-prefetch-git
    fetchSubmodules = true;
  };

  nativeBuildInputs = [ cmake ninja pkg-config ];
  buildInputs      = [ qtbase qttools libGL libGLU ];

  dontWrapQtApps = true;

  cmakeFlags = [
    "-DwxBUILD_TOOLKIT=qt"
    "-DwxBUILD_QT=ON"
    "-DwxBUILD_SHARED=OFF"
    "-DwxBUILD_MONOLITHIC=OFF"
    "-DwxUSE_OPENGL=ON"
    "-DwxBUILD_COMPONENTS=core;base;gl"
    "-DwxENABLE_WEBVIEW=OFF"
    "-DwxENABLE_HTML=OFF"
    "-DwxUSE_STC=OFF"
  ];

  installPhase = ''
    mkdir -p $out/bin $out/lib $out/include
    # 头文件
    cp -r $src/include/* $out/include/

    # 库文件 + 配置目录
    cp -r lib/* $out/lib/

    # 查找并复制 wx-config
    cfg=$(find . -maxdepth 3 -name wx-config | head -n1 || true)
    if [ -n "$cfg" ]; then
      cp "$cfg" $out/bin/
    fi

    # 修正 wx-config 中的安装前缀，避免 "Directory '/build/source' no longer exists" 错误
    if [ -f $out/bin/wx-config ]; then
      substituteInPlace $out/bin/wx-config \
        --replace "/build/source/build" "$out" \
        --replace "/build/source" "$out"
      chmod +x $out/bin/wx-config
    fi
  '';

  meta = with lib; {
    description = "wxWidgets built with Qt backend (wxQt)";
    homepage    = "https://wxwidgets.org";
    license     = licenses.gpl3Plus;
    platforms   = platforms.linux ++ platforms.darwin;
  };
} 