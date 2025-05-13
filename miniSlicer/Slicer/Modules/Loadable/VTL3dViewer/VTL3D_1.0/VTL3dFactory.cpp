#include "MainWindow.h"

// wxWidgets
#include <wx/app.h>
#include <wx/init.h>
// 若编译为 wxQt 后端，可用 GetHandle() 获取 QWidget*
#ifdef __WXQT__
#  include <QtWidgets/QWidget>
#endif

// -----------------------------------------------------------------------------
// 为动态链接场景提供最小 wxApp（不启动事件循环）
class DummyApp : public wxApp
{
public:
    bool OnInit() override { return true; }
};

wxIMPLEMENT_APP_NO_MAIN(DummyApp);

extern "C" {

//------------------------------------------------------------------------------
// 工厂函数：返回可嵌入的 QWidget 指针。
// 若未初始化 wxWidgets，则在此初始化。
//------------------------------------------------------------------------------
#ifdef __WXQT__
__attribute__((visibility("default"))) QWidget* CreateVTL3dMainWindow(QWidget* parent)
#else
__attribute__((visibility("default"))) void* CreateVTL3dMainWindow(void* parent)
#endif
{
    // 初始化 wxWidgets，仅一次
    if (!wxTheApp)
    {
        wxApp::SetInstance(new DummyApp());
        int argc = 0;
        char** argv = nullptr;
        wxEntryStart(argc, argv);
        wxTheApp->CallOnInit();
    }

    // 创建主窗口（wxFrame）
    MainWindow* frame = new MainWindow();
    frame->Show(false); // 不独立显示，由 Qt 容器托管

#ifdef __WXQT__
    // 利用 wxWindow::GetHandle() 获取底层 QWidget 指针
    QWidget* qtWidget = static_cast<QWidget*>(frame->GetHandle());
    if (parent && qtWidget)
    {
        qtWidget->setParent(parent);
    }
    return qtWidget;
#else
    (void)parent; // 未使用
    return reinterpret_cast<void*>(frame);
#endif
}

} // extern "C" 