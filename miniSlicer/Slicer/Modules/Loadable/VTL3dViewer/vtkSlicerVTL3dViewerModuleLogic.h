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

#ifndef __vtkSlicerVTL3dViewerModuleLogic_h
#define __vtkSlicerVTL3dViewerModuleLogic_h

// Slicer includes
#include "vtkSlicerModuleLogic.h"

// MRML includes

// VTK includes

// STD includes

// #include "vtkSlicerVTL3dViewerModuleLogicExport.h" // Temporarily commented out

class vtkSlicerVTL3dViewerModuleLogicPrivate;

// class VTK_SLICER_VTL3DVIEWER_MODULE_LOGIC_EXPORT vtkSlicerVTL3dViewerModuleLogic : // Temporarily commented out export macro
class vtkSlicerVTL3dViewerModuleLogic :
  public vtkSlicerModuleLogic
{
public:
  static vtkSlicerVTL3dViewerModuleLogic *New();
  vtkTypeMacro(vtkSlicerVTL3dViewerModuleLogic, vtkSlicerModuleLogic);
  void PrintSelf(ostream& os, vtkIndent indent) override;

protected:
  vtkSlicerVTL3dViewerModuleLogic();
  ~vtkSlicerVTL3dViewerModuleLogic() override;

  void SetMRMLSceneInternal(vtkMRMLScene* newScene) override;
  /// Register MRML Node classes to Scene. Gets called automatically when the MRMLScene is attached to this logic class.
  void RegisterNodes() override;
  void UpdateFromMRMLScene() override;
  void OnMRMLSceneNodeAdded(vtkMRMLNode* node) override;
  void OnMRMLSceneNodeRemoved(vtkMRMLNode* node) override;

private:
  vtkSlicerVTL3dViewerModuleLogic(const vtkSlicerVTL3dViewerModuleLogic&); // Not implemented
  void operator=(const vtkSlicerVTL3dViewerModuleLogic&);               // Not implemented

  // QScopedPointer<vtkSlicerVTL3dViewerModuleLogicPrivate> d_ptr; // No Qt Pimpl for VTK classes
  vtkSlicerVTL3dViewerModuleLogicPrivate* Internal;
};

#endif 