#ifndef VTL3DFACORY_H
#define VTL3DFACORY_H

// Forward declaration for QWidget to avoid full Qt header include if not necessary
// for the function signature itself. Full include will be in .cpp or consumer.
#if defined(__cplusplus)
class QWidget;
#else
typedef struct QWidget QWidget; // C-compatible way for type safety
#endif

#ifdef __cplusplus
extern "C" {
#endif

// Export/Import macro
#if defined(_WIN32) || defined(_WIN64)
  #ifdef VTL3DGUI_DLL_EXPORTS // This should be defined by the VTL3dGui library project when building the DLL
    #define VTL3D_GUI_EXPORT __declspec(dllexport)
  #else
    #define VTL3D_GUI_EXPORT __declspec(dllimport)
  #endif
#elif (defined(__GNUC__) && __GNUC__ >= 4) || defined(__clang__)
  #define VTL3D_GUI_EXPORT __attribute__((visibility("default")))
#else
  #define VTL3D_GUI_EXPORT
#endif

// Factory function declaration
// The signature depends on whether wxWidgets is compiled with Qt support (__WXQT__)
#ifdef __WXQT__
VTL3D_GUI_EXPORT QWidget* CreateVTL3dMainWindow(QWidget* parent);
#else
// If not __WXQT__, the return type and parent type might be different (e.g., void* or a wxWindow pointer)
// For Slicer integration, __WXQT__ is the target scenario.
VTL3D_GUI_EXPORT void* CreateVTL3dMainWindow(void* parent_as_qwidget_handle_or_similar);
#endif

#ifdef __cplusplus
} // extern "C"
#endif

#endif // VTL3DFACORY_H 