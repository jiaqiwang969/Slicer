#include "MainWindow.h"

// wxWidgets
#include <wx/app.h>
#include <wx/init.h>
// 若编译为 wxQt 后端，可用 GetHandle() 获取 QWidget*
#ifdef __WXQT__
#  include <QtWidgets/QWidget>
#endif

// Qt for logging (if available and useful, otherwise use std::cout or other C++ logging)
#include <QDebug> // Using Slicer's/Qt's logging for consistency
#include <QDateTime>
#include <QFile>
#include <QTextStream>
#include <QStandardPaths>

// Logging function similar to the one in qSlicerVTL3dViewerModuleWidget.cxx
static void writeFactoryLog(const QString& message)
{
  // Append to the same log file for easier debugging
  QString logPath = QStandardPaths::writableLocation(QStandardPaths::TempLocation) + "/VTL3dViewerDebug.log";
  QFile logFile(logPath);
  if (logFile.open(QIODevice::Append | QIODevice::Text))
  {
    QTextStream stream(&logFile);
    stream << QDateTime::currentDateTime().toString("yyyy-MM-dd hh:mm:ss.zzz") << " [Factory] - " << message << "\\n";
    logFile.close();
  }
  else
  {
    // Fallback if Qt logging isn't fully working here or file can't be opened
    std::cerr << "Factory Log (file error): " << message.toStdString() << std::endl;
  }
}


// -----------------------------------------------------------------------------
// 为动态链接场景提供最小 wxApp（不启动事件循环）
class DummyApp : public wxApp
{
public:
    bool OnInit() override 
    {
        writeFactoryLog("DummyApp::OnInit() called.");
        // Ensure base class OnInit is called if it does anything important.
        if (!wxApp::OnInit())
        {
            writeFactoryLog("DummyApp::OnInit() - wxApp::OnInit() failed.");
            return false;
        }
        writeFactoryLog("DummyApp::OnInit() succeeded.");
        return true; 
    }
    int OnExit() override
    {
        writeFactoryLog("DummyApp::OnExit() called.");
        return wxApp::OnExit();
    }
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
    writeFactoryLog("CreateVTL3dMainWindow called.");

    // 初始化 wxWidgets，仅一次
    if (!wxTheApp)
    {
        writeFactoryLog("wxTheApp is NULL. Initializing wxWidgets.");
        try {
            wxApp::SetInstance(new DummyApp());
            writeFactoryLog("DummyApp instance created and set.");
            int argc = 0;
            char** argv = nullptr; // Or provide actual args if necessary e.g. from parent QApp
            
            writeFactoryLog("Calling wxEntryStart...");
            if (!wxEntryStart(argc, argv)) {
                writeFactoryLog("wxEntryStart failed!");
                // Decide how to handle this, maybe return nullptr or an error indicator
#ifdef __WXQT__
                return nullptr;
#else
                return nullptr;
#endif
            }
            writeFactoryLog("wxEntryStart succeeded.");

            writeFactoryLog("Calling wxTheApp->CallOnInit()...");
            if (!wxTheApp->CallOnInit()) {
                 writeFactoryLog("wxTheApp->CallOnInit() failed!");
                // Decide how to handle this
#ifdef __WXQT__
                return nullptr;
#else
                return nullptr;
#endif
            }
            writeFactoryLog("wxTheApp->CallOnInit() succeeded. wxWidgets initialized.");
        } catch (const std::exception& e) {
            writeFactoryLog(QString("Exception during wxWidgets initialization: %1").arg(e.what()));
#ifdef __WXQT__
            return nullptr;
#else
            return nullptr;
#endif
        } catch (...) {
            writeFactoryLog("Unknown exception during wxWidgets initialization.");
#ifdef __WXQT__
            return nullptr;
#else
            return nullptr;
#endif
        }
    }
    else
    {
        writeFactoryLog("wxTheApp already exists. wxWidgets previously initialized.");
    }

    MainWindow* frame = nullptr;
    try {
        writeFactoryLog("Creating MainWindow instance (new MainWindow())...");
        frame = new MainWindow(); // Potentially problematic line
        if (frame) {
            writeFactoryLog("MainWindow instance created successfully.");
        } else {
            writeFactoryLog("new MainWindow() returned NULL!");
#ifdef __WXQT__
            return nullptr;
#else
            return nullptr;
#endif
        }

        writeFactoryLog("Calling frame->Show(false)...");
        frame->Show(false); // 不独立显示，由 Qt 容器托管
        writeFactoryLog("frame->Show(false) called.");

    } catch (const std::exception& e) {
        writeFactoryLog(QString("Exception during MainWindow creation or Show(): %1").arg(e.what()));
#ifdef __WXQT__
        return nullptr;
#else
        return nullptr;
#endif
    } catch (...) {
        writeFactoryLog("Unknown exception during MainWindow creation or Show().");
#ifdef __WXQT__
        return nullptr;
#else
        return nullptr;
#endif
    }
    

#ifdef __WXQT__
    writeFactoryLog("Running under __WXQT__. Attempting to get QWidget handle.");
    QWidget* qtWidget = nullptr;
    try {
        qtWidget = static_cast<QWidget*>(frame->GetHandle());
        if (qtWidget) {
            writeFactoryLog("frame->GetHandle() succeeded.");
            if (parent)
            {
                writeFactoryLog("Setting parent QWidget.");
                qtWidget->setParent(parent);
                writeFactoryLog("Parent QWidget set.");
            } else {
                writeFactoryLog("No parent QWidget provided.");
            }
        } else {
            writeFactoryLog("frame->GetHandle() returned NULL!");
            // This is an error, but frame might still be valid wx-wise.
            // However, for embedding, a null QWidget* is a failure.
            return nullptr; 
        }
    } catch (const std::exception& e) {
        writeFactoryLog(QString("Exception during GetHandle() or setParent(): %1").arg(e.what()));
        return nullptr;
    } catch (...) {
        writeFactoryLog("Unknown exception during GetHandle() or setParent().");
        return nullptr;
    }
    writeFactoryLog("Returning QWidget handle.");
    return qtWidget;
#else
    writeFactoryLog("Not running under __WXQT__. Returning raw wxFrame pointer.");
    (void)parent; // 未使用
    return reinterpret_cast<void*>(frame);
#endif
}

} // extern "C" 