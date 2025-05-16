#include "qSlicerVTL3dViewerModuleWidget.h"

// Qt includes
#include <QDebug>
#include <QVBoxLayout>
#include <QLabel>
#include <QLibrary>
#include <QMessageBox>
#include <QFile>
#include <QDir>
#include <QTextStream>
#include <QDateTime>
#include <QApplication>
#include <QStandardPaths>
#include <QProcess>
#include <QPushButton>

// SlicerQt includes
#include "qSlicerVTL3dViewerModuleWidget.h"
#include "qSlicerCoreApplication.h"
#include "qSlicerModuleManager.h"
#include "vtkSlicerVTL3dViewerModuleLogic.h"

// VTL3d Factory header (assuming it's made available by VTL3D_1.0 target's include directories)
#include "VTL3dFactory.h"

// 新增：用于调试的日志文件
static void writeDebugLog(const QString& message)
{
  QString logPath = QStandardPaths::writableLocation(QStandardPaths::TempLocation) + "/VTL3dViewerDebug.log";
  QFile logFile(logPath);
  if (logFile.open(QIODevice::Append | QIODevice::Text))
  {
    QTextStream stream(&logFile);
    stream << QDateTime::currentDateTime().toString("yyyy-MM-dd hh:mm:ss.zzz") << " - " << message << "\n";
    logFile.close();
    qDebug() << "Log written to:" << logPath;
  }
  else
  {
    qDebug() << "Failed to open log file:" << logPath;
  }
}

//-----------------------------------------------------------------------------
// qSlicerVTL3dViewerModuleWidgetPrivate methods

//-----------------------------------------------------------------------------
class qSlicerVTL3dViewerModuleWidgetPrivate
{
  Q_DECLARE_PUBLIC(qSlicerVTL3dViewerModuleWidget);
protected:
  qSlicerVTL3dViewerModuleWidget* const q_ptr;
public:
  qSlicerVTL3dViewerModuleWidgetPrivate(qSlicerVTL3dViewerModuleWidget& object);
  ~qSlicerVTL3dViewerModuleWidgetPrivate();

  QLibrary vtl3dGuiLibrary;
  QWidget* vtl3dEmbeddedWidget;

  // Ui_qSlicerVTL3dViewerModuleWidget ui; // If you have a .ui file
};

//-----------------------------------------------------------------------------
qSlicerVTL3dViewerModuleWidgetPrivate::qSlicerVTL3dViewerModuleWidgetPrivate(qSlicerVTL3dViewerModuleWidget& object)
  : q_ptr(&object)
  , vtl3dEmbeddedWidget(nullptr)
{
}

//-----------------------------------------------------------------------------
qSlicerVTL3dViewerModuleWidgetPrivate::~qSlicerVTL3dViewerModuleWidgetPrivate()
{
  if (this->vtl3dGuiLibrary.isLoaded())
  {
    this->vtl3dGuiLibrary.unload();
  }
}

//-----------------------------------------------------------------------------
// qSlicerVTL3dViewerModuleWidget methods

//-----------------------------------------------------------------------------
qSlicerVTL3dViewerModuleWidget::qSlicerVTL3dViewerModuleWidget(QWidget* _parent)
  : Superclass(_parent)
  , d_ptr(new qSlicerVTL3dViewerModuleWidgetPrivate(*this))
{
  writeDebugLog("VTL3dViewerModuleWidget constructor started");
  qCritical() << "VTL3dViewerModuleWidget constructor CALLED"; // DEBUGGING
  writeDebugLog("VTL3dViewerModuleWidget constructor completed");
}

//-----------------------------------------------------------------------------
qSlicerVTL3dViewerModuleWidget::~qSlicerVTL3dViewerModuleWidget() 
{
  writeDebugLog("VTL3dViewerModuleWidget destructor called");
}

//-----------------------------------------------------------------------------
void qSlicerVTL3dViewerModuleWidget::setup()
{
  try
  {
    writeDebugLog("setup() method started");
    Q_D(qSlicerVTL3dViewerModuleWidget);
    this->Superclass::setup();
    
    // 列出可能有用的路径供调试
    writeDebugLog("Application dir: " + QCoreApplication::applicationDirPath());
    writeDebugLog("Current dir: " + QDir::currentPath());
    
    // d->ui.setupUi(this); // If you have a .ui file

    // --- Dynamically load VTL3d GUI library ---
    QString libraryName = "VTL3dGui"; // Use the base name of the library
    writeDebugLog("Attempting to load library: " + libraryName);
    
    // 尝试多个可能的路径
    QStringList possiblePaths;
    possiblePaths << libraryName 
                  << QCoreApplication::applicationDirPath() + "/../lib/" + libraryName
                  << QCoreApplication::applicationDirPath() + "/../lib/Slicer-4.13/qt-loadable-modules/" + libraryName
                  << QCoreApplication::applicationDirPath() + "/lib" + libraryName
                  << QCoreApplication::applicationDirPath() + "/lib/libVTL3dGui.so";
                  
    // 列出所有可能的路径
    for (const QString& path : possiblePaths) {
      writeDebugLog("Possible library path: " + path);
      writeDebugLog("File exists: " + QString(QFile::exists(path) ? "Yes" : "No"));
    }
    
    // 检查环境变量
    QProcessEnvironment env = QProcessEnvironment::systemEnvironment();
    writeDebugLog("LD_LIBRARY_PATH: " + env.value("LD_LIBRARY_PATH", "not set"));
    
    // 尝试加载库
    try {
      d->vtl3dGuiLibrary.setFileName(libraryName);
      writeDebugLog("Setting library name to: " + d->vtl3dGuiLibrary.fileName());

      if (!d->vtl3dGuiLibrary.load())
      {
        QString errorMsg = QString("Could not load VTL3d GUI library ('%1').\nError: %2")
                             .arg(libraryName, d->vtl3dGuiLibrary.errorString());
        writeDebugLog("Library load failed: " + errorMsg);
        QLabel *errorLabel = new QLabel(errorMsg, this);
        errorLabel->setAlignment(Qt::AlignCenter);
        errorLabel->setWordWrap(true);
        this->setLayout(new QVBoxLayout());
        this->layout()->addWidget(errorLabel);
        return;
      }

      writeDebugLog("VTL3d GUI library loaded successfully.");

      // --- Resolve the factory function --- 
      typedef QWidget* (*CreateVTL3dMainWindowFunc)(QWidget* parent);
      CreateVTL3dMainWindowFunc createVTL3dGUIMainWindow =
          (CreateVTL3dMainWindowFunc)d->vtl3dGuiLibrary.resolve("CreateVTL3dMainWindow");

      if (!createVTL3dGUIMainWindow)
      {
        QString errorMsg = QString("Could not find 'CreateVTL3dMainWindow' function in VTL3d GUI library ('%1').")
                             .arg(libraryName);
        writeDebugLog("Function not found: " + errorMsg);
        QLabel *errorLabel = new QLabel(errorMsg, this);
        errorLabel->setAlignment(Qt::AlignCenter);
        errorLabel->setWordWrap(true);
        this->setLayout(new QVBoxLayout());
        this->layout()->addWidget(errorLabel);
        return;
      }

      writeDebugLog("'CreateVTL3dMainWindow' function resolved successfully.");

      // --- Create and embed the VTL3d GUI --- 
      // Remove any existing placeholder widgets
      QLayoutItem* item;
      if (this->layout()) // Check if a layout already exists
      {
        while ((item = this->layout()->takeAt(0)) != nullptr)
        {
          delete item->widget();
          delete item;
        }
      }
      else
      {
        this->setLayout(new QVBoxLayout()); // Create a layout if none exists
      }
      
      writeDebugLog("About to call CreateVTL3dMainWindow...");
      
      // 添加安全模式：先只创建一个占位界面，不立即加载 VTL3d
      bool safeMode = true; // 设置为 true 启用安全模式
      
      if (safeMode) {
        writeDebugLog("安全模式已启用 - 创建占位界面");
        QWidget* placeholderWidget = new QWidget(this);
        QVBoxLayout* layout = new QVBoxLayout(placeholderWidget);
        
        QPushButton* loadVTL3dButton = new QPushButton("加载 VTL3d 界面", placeholderWidget);
        layout->addWidget(new QLabel("VTL3d 加载器 - 安全模式", placeholderWidget));
        layout->addWidget(loadVTL3dButton);
        
        // 添加库路径和状态信息
        QLabel* libraryPathLabel = new QLabel("库路径: " + d->vtl3dGuiLibrary.fileName(), placeholderWidget);
        layout->addWidget(libraryPathLabel);
        
        QLabel* libraryLoadedLabel = new QLabel(QString("库已加载: %1").arg(d->vtl3dGuiLibrary.isLoaded() ? "是" : "否"), placeholderWidget);
        layout->addWidget(libraryLoadedLabel);
        
        // 连接按钮点击事件
        QObject::connect(loadVTL3dButton, &QPushButton::clicked, [this, createVTL3dGUIMainWindow, d]() {
          writeDebugLog("用户请求加载 VTL3d GUI");
          try {
            QWidget* vtl3dWidget = createVTL3dGUIMainWindow(this);
            if (vtl3dWidget) {
              writeDebugLog("成功创建 VTL3d 界面");
              // 清除当前布局中的所有部件
              QLayoutItem* item;
              while ((item = this->layout()->takeAt(0)) != nullptr) {
                delete item->widget();
                delete item;
              }
              // 添加 VTL3d 界面
              this->layout()->addWidget(vtl3dWidget);
              d->vtl3dEmbeddedWidget = vtl3dWidget;
            } else {
              writeDebugLog("无法创建 VTL3d 界面，返回了空指针");
              QMessageBox::warning(this, "错误", "无法创建 VTL3d 界面，返回了空指针");
            }
          } catch (const std::exception& e) {
            writeDebugLog(QString("加载 VTL3d GUI 时发生标准异常: %1").arg(e.what()));
            QMessageBox::critical(this, "错误", QString("加载 VTL3d GUI 时发生异常: %1").arg(e.what()));
          } catch (...) {
            writeDebugLog("加载 VTL3d GUI 时发生未知异常");
            QMessageBox::critical(this, "错误", "加载 VTL3d GUI 时发生未知异常");
          }
        });
        
        this->layout()->addWidget(placeholderWidget);
        writeDebugLog("安全模式界面已创建");
      } else {
        try {
          d->vtl3dEmbeddedWidget = createVTL3dGUIMainWindow(this); // Pass `this` (the Slicer module widget) as parent
          writeDebugLog("CreateVTL3dMainWindow called successfully");

          if (d->vtl3dEmbeddedWidget) {
            writeDebugLog("VTL3d GUI widget created. Adding to layout.");
            this->layout()->addWidget(d->vtl3dEmbeddedWidget);
          } else {
            QString errorMsg = QString("VTL3d GUI factory function ('CreateVTL3dMainWindow') did not return a valid widget from library ('%1').")
                                .arg(libraryName);
            writeDebugLog("Widget creation failed: " + errorMsg);
            QLabel *errorLabel = new QLabel(errorMsg, this);
            errorLabel->setAlignment(Qt::AlignCenter);
            errorLabel->setWordWrap(true);
            this->layout()->addWidget(errorLabel);
          }
        } catch (const std::exception& e) {
          writeDebugLog(QString("Exception calling CreateVTL3dMainWindow: %1").arg(e.what()));
          QLabel *errorLabel = new QLabel(QString("Exception calling CreateVTL3dMainWindow: %1").arg(e.what()), this);
          this->layout()->addWidget(errorLabel);
        } catch (...) {
          writeDebugLog("Unknown exception calling CreateVTL3dMainWindow");
          QLabel *errorLabel = new QLabel("Unknown exception calling CreateVTL3dMainWindow", this);
          this->layout()->addWidget(errorLabel);
        }
      }
    }
    catch (const std::exception& e) {
      writeDebugLog(QString("STD exception: %1").arg(e.what()));
      QLabel *errorLabel = new QLabel(QString("Exception: %1").arg(e.what()), this);
      this->setLayout(new QVBoxLayout());
      this->layout()->addWidget(errorLabel);
    }
    catch (...) {
      writeDebugLog("Unknown exception occurred while loading VTL3d library");
      QLabel *errorLabel = new QLabel("Unknown exception occurred while loading VTL3d library", this);
      this->setLayout(new QVBoxLayout());
      this->layout()->addWidget(errorLabel);
    }
    
    writeDebugLog("qSlicerVTL3dViewerModuleWidget::setup() finished.");
  }
  catch (const std::exception& e) {
    writeDebugLog(QString("Exception in setup(): %1").arg(e.what()));
  }
  catch (...) {
    writeDebugLog("Unknown exception in setup()");
  }
} 