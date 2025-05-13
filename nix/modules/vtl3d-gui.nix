{ lib, stdenv, cmake, ninja, pkg-config,
  eigen, boost, cgal, wxqt,
  src }:

stdenv.mkDerivation rec {
  pname   = "VTL3dGui";
  version = "1.0";

  inherit src;

  nativeBuildInputs = [ cmake ninja pkg-config ];
  buildInputs      = [ wxqt eigen boost cgal ];

  dontWrapQtApps = true;

  cmakeFlags = [
    "-DwxWidgets_CONFIG_EXECUTABLE=${wxqt}/bin/wx-config"
    "-DBUILD_SHARED_LIBS=ON"
  ];

  # 采用 default installPhase (make install)

  meta = with lib; {
    description = "VTL3d GUI library built with wxQt backend";
    license     = licenses.gpl3Plus;
  };
} 