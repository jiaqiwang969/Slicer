// ****************************************************************************
// Stub version of VocalTractPicture used when compiling with wxQt backend.
// It avoids using wxGLCanvas/OpenGL to prevent crashes.
// ****************************************************************************
#pragma once

#include <wx/wx.h>

class VocalTractPictureStub : public wxPanel
{
public:
  enum RenderMode { RM_NONE, RM_3DSOLID, RM_3DWIRE, RM_2D };

  // Directly公开与原类同名成员，以便其他源文件无需改动即可访问
  bool showControlPoints {true};
  bool showCenterLine {false};
  bool isRoughCenterLine {false};
  bool showCutVectors {false};
  bool showEmaPoints {false};
  bool renderBothSides {true};
  RenderMode renderMode {RM_NONE};
  bool showPalatogramDivision {false};
  bool showPoster {false};
  bool posterEditing {false};
  bool showTongueCrossSections {false};
  bool crossSectionWithTongue {false};
  int  selectedControlPoint {-1};
  double cutPlanePos_cm {0.0};

  VocalTractPictureStub(wxWindow* parent)
    : wxPanel(parent, wxID_ANY)
  {
    this->SetBackgroundColour(*wxLIGHT_GREY);
  }

  // 提供与原类兼容的空实现接口，若后面有调用可逐步补充
  void Refresh() {}
  void Update() {}
  void SetMinSize(const wxSize& size) { wxPanel::SetMinSize(size); }

  // 与 OpenGL 版本兼容的接口占位实现
  bool loadPoster(const wxString&) { return false; }
  void currentPictureToPoster() {}

  bool exportTractWireframeSVG(const wxString&, int) { return false; }
  bool exportCrossSectionSVG(const wxString&) { return false; }
  bool saveImageBmp(const wxString&) { return false; }
};

using VocalTractPicture = VocalTractPictureStub; 