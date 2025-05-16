/*==============================================================================

  Program: 3D Slicer

  Copyright (c) Kitware Inc.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

==============================================================================*/

#ifndef __qSlicerVTL3dViewerModule_h
#define __qSlicerVTL3dViewerModule_h

// Slicer includes
#include "qSlicerLoadableModule.h"

#include "qSlicerVTL3dViewerModuleExport.h"

class qSlicerVTL3dViewerModulePrivate;

class Q_SLICER_QTMODULES_VTL3DVIEWER_EXPORT qSlicerVTL3dViewerModule :
  public qSlicerLoadableModule
{
  Q_OBJECT
  Q_PLUGIN_METADATA(IID "org.slicer.modules.loadable.qSlicerLoadableModule/1.0");
  Q_INTERFACES(qSlicerLoadableModule);

public:
  typedef qSlicerLoadableModule Superclass;
  qSlicerVTL3dViewerModule(QObject *parent = nullptr);
  ~qSlicerVTL3dViewerModule() override;

  QString title() const override;
  QString helpText() const override;
  QString acknowledgementText() const override;
  QStringList contributors() const override;
  QIcon icon() const override;
  QStringList categories() const override;
  // QStringList dependencies() const override;

protected:
  void setup() override;
  qSlicerAbstractModuleRepresentation *createWidgetRepresentation() override;
  vtkMRMLAbstractLogic *createLogic() override;

protected:
  QScopedPointer<qSlicerVTL3dViewerModulePrivate> d_ptr;

private:
  Q_DECLARE_PRIVATE(qSlicerVTL3dViewerModule);
  Q_DISABLE_COPY(qSlicerVTL3dViewerModule);
};

#endif 