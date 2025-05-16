#include "qSlicerVTL3dViewerModule.h"
#include "qSlicerVTL3dViewerModuleWidget.h"
#include "vtkSlicerVTL3dViewerModuleLogic.h"

#include <QtPlugin>
#include <QIcon>
#include <QDebug>

// Slicer includes
#include "qSlicerCoreApplication.h"
#include "qSlicerModuleManager.h"

//-----------------------------------------------------------------------------
class qSlicerVTL3dViewerModulePrivate
{
  Q_DECLARE_PUBLIC(qSlicerVTL3dViewerModule);
protected:
  qSlicerVTL3dViewerModule* const q_ptr;
public:
  qSlicerVTL3dViewerModulePrivate(qSlicerVTL3dViewerModule& object);
  virtual ~qSlicerVTL3dViewerModulePrivate();
};

//-----------------------------------------------------------------------------
// qSlicerVTL3dViewerModulePrivate methods

//-----------------------------------------------------------------------------
qSlicerVTL3dViewerModulePrivate::qSlicerVTL3dViewerModulePrivate(qSlicerVTL3dViewerModule& object)
  : q_ptr(&object)
{
}

//-----------------------------------------------------------------------------
qSlicerVTL3dViewerModulePrivate::~qSlicerVTL3dViewerModulePrivate() = default;

//-----------------------------------------------------------------------------
// qSlicerVTL3dViewerModule methods

//-----------------------------------------------------------------------------
qSlicerVTL3dViewerModule::qSlicerVTL3dViewerModule(QObject* _parent)
  : Superclass(_parent)
  , d_ptr(new qSlicerVTL3dViewerModulePrivate(*this))
{
  qCritical() << "VTL3dViewerModule constructor CALLED"; // DEBUGGING
}

//-----------------------------------------------------------------------------
qSlicerVTL3dViewerModule::~qSlicerVTL3dViewerModule() = default;

//-----------------------------------------------------------------------------
QString qSlicerVTL3dViewerModule::title() const
{
  return "VTL3d Viewer"; // Provide an implementation for the module title
}

//-----------------------------------------------------------------------------
QString qSlicerVTL3dViewerModule::helpText() const
{
  return "This is a placeholder help text for VTL3dViewer module.";
}

//-----------------------------------------------------------------------------
QString qSlicerVTL3dViewerModule::acknowledgementText() const
{
  return "This work was not supported by any direct funding.";
}

//-----------------------------------------------------------------------------
QStringList qSlicerVTL3dViewerModule::contributors() const
{
  QStringList moduleContributors;
  moduleContributors << QString("Your Name Here");
  return moduleContributors;
}

//-----------------------------------------------------------------------------
QIcon qSlicerVTL3dViewerModule::icon() const
{
  return QIcon(":/Icons/VTL3dViewer.png"); // Placeholder icon
}

//-----------------------------------------------------------------------------
QStringList qSlicerVTL3dViewerModule::categories() const
{
  return QStringList() << "PipeSonic"; // 修改为更容易找到的分类
}

/*
//-----------------------------------------------------------------------------
QStringList qSlicerVTL3dViewerModule::dependencies() const
{
  return QStringList(); // Add dependencies if any, e.g. "Volumes"
}
*/

//-----------------------------------------------------------------------------
void qSlicerVTL3dViewerModule::setup()
{
  qCritical() << "VTL3dViewerModule setup() CALLED"; // DEBUGGING
  this->Superclass::setup();
  // Register IOs or other setup tasks here if needed
}

//-----------------------------------------------------------------------------
qSlicerAbstractModuleRepresentation* qSlicerVTL3dViewerModule::createWidgetRepresentation()
{
  qCritical() << "VTL3dViewerModule createWidgetRepresentation() CALLED"; // DEBUGGING
  return new qSlicerVTL3dViewerModuleWidget;
}

//-----------------------------------------------------------------------------
vtkMRMLAbstractLogic* qSlicerVTL3dViewerModule::createLogic()
{
  return vtkSlicerVTL3dViewerModuleLogic::New();
} 