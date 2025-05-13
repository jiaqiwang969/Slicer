#include "qSlicerVTL3dViewerModuleWidget.h"

// Qt includes
#include <QDebug>
#include <QVBoxLayout>
#include <QLabel>

// SlicerQt includes
#include "qSlicerVTL3dViewerModuleWidget.h"

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
  virtual ~qSlicerVTL3dViewerModuleWidgetPrivate();

  // Ui_qSlicerVTL3dViewerModuleWidget ui; // If you have a .ui file
};

//-----------------------------------------------------------------------------
qSlicerVTL3dViewerModuleWidgetPrivate::qSlicerVTL3dViewerModuleWidgetPrivate(qSlicerVTL3dViewerModuleWidget& object)
  : q_ptr(&object)
{
}

//-----------------------------------------------------------------------------
qSlicerVTL3dViewerModuleWidgetPrivate::~qSlicerVTL3dViewerModuleWidgetPrivate() = default;

//-----------------------------------------------------------------------------
// qSlicerVTL3dViewerModuleWidget methods

//-----------------------------------------------------------------------------
qSlicerVTL3dViewerModuleWidget::qSlicerVTL3dViewerModuleWidget(QWidget* _parent)
  : Superclass(_parent)
  , d_ptr(new qSlicerVTL3dViewerModuleWidgetPrivate(*this))
{
}

//-----------------------------------------------------------------------------
qSlicerVTL3dViewerModuleWidget::~qSlicerVTL3dViewerModuleWidget() = default;

//-----------------------------------------------------------------------------
void qSlicerVTL3dViewerModuleWidget::setup()
{
  Q_D(qSlicerVTL3dViewerModuleWidget);
  this->Superclass::setup();

  // d->ui.setupUi(this); // If you have a .ui file

  // Placeholder UI
  QVBoxLayout *layout = new QVBoxLayout(this);
  QLabel *placeholderLabel = new QLabel(tr("VTL3dViewer Placeholder - wxWidgets GUI will be embedded here."), this);
  placeholderLabel->setAlignment(Qt::AlignCenter);
  layout->addWidget(placeholderLabel);
  this->setLayout(layout);
} 