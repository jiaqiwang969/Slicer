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

#ifndef __qSlicerVTL3dViewerModuleWidget_h
#define __qSlicerVTL3dViewerModuleWidget_h

// Slicer includes
#include "qSlicerAbstractModuleWidget.h"

#include "qSlicerVTL3dViewerModuleExport.h"

class qSlicerVTL3dViewerModuleWidgetPrivate;
class vtkMRMLNode;

class Q_SLICER_QTMODULES_VTL3DVIEWER_EXPORT qSlicerVTL3dViewerModuleWidget :
  public qSlicerAbstractModuleWidget
{
  Q_OBJECT

public:
  typedef qSlicerAbstractModuleWidget Superclass;
  qSlicerVTL3dViewerModuleWidget(QWidget *parent = nullptr);
  ~qSlicerVTL3dViewerModuleWidget() override;

protected:
  void setup() override;

protected:
  QScopedPointer<qSlicerVTL3dViewerModuleWidgetPrivate> d_ptr;

private:
  Q_DECLARE_PRIVATE(qSlicerVTL3dViewerModuleWidget);
  Q_DISABLE_COPY(qSlicerVTL3dViewerModuleWidget);
};

#endif 