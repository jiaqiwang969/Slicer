/*==============================================================================

  Copyright (c) Laboratory for Percutaneous Surgery (PerkLab)
  Queen's University, Kingston, ON, Canada. All Rights Reserved.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

  This file was originally developed by Kyle Sunderland, PerkLab, Queen's University
  and was supported through CANARIE's Research Software Program, Cancer
  Care Ontario, OpenAnatomy, and Brigham and Women's Hospital through NIH grant R01MH112748.

==============================================================================*/

#ifndef __vtkSlicerDynamicModelerHollowTool_h
#define __vtkSlicerDynamicModelerHollowTool_h

#include "vtkSlicerDynamicModelerModuleLogicExport.h"

// VTK includes
#include <vtkObject.h>
#include <vtkSmartPointer.h>

// STD includes
#include <map>
#include <string>
#include <vector>

class vtkGeneralTransform;
class vtkLinearExtrusionFilter;
class vtkMRMLDynamicModelerNode;
class vtkPolyDataNormals;
class vtkTransformPolyDataFilter;
class vtkTriangleFilter;

#include "vtkSlicerDynamicModelerTool.h"

/// \brief Dynamic modeler tool for creating a shell model (closed surface) from an open surface.
///
/// The shell is created by offsetting the input surface along the surface normal in both directions.
class VTK_SLICER_DYNAMICMODELER_MODULE_LOGIC_EXPORT vtkSlicerDynamicModelerHollowTool : public vtkSlicerDynamicModelerTool
{
public:
  static vtkSlicerDynamicModelerHollowTool* New();
  vtkSlicerDynamicModelerTool* CreateToolInstance() override;
  vtkTypeMacro(vtkSlicerDynamicModelerHollowTool, vtkSlicerDynamicModelerTool);

  /// Human-readable name of the mesh modification tool
  const char* GetName() override;

  /// Run the plane cut on the input model node
  bool RunInternal(vtkMRMLDynamicModelerNode* surfaceEditorNode) override;

protected:
  vtkSlicerDynamicModelerHollowTool();
  ~vtkSlicerDynamicModelerHollowTool() override;
  void operator=(const vtkSlicerDynamicModelerHollowTool&);

protected:
  vtkSmartPointer<vtkTransformPolyDataFilter> InputModelToWorldTransformFilter;
  vtkSmartPointer<vtkGeneralTransform> InputModelNodeToWorldTransform;

  vtkSmartPointer<vtkLinearExtrusionFilter> HollowFilter;
  vtkSmartPointer<vtkTriangleFilter> TriangleFilter;
  vtkSmartPointer<vtkPolyDataNormals> NormalsFilter;

  vtkSmartPointer<vtkTransformPolyDataFilter> OutputModelToWorldTransformFilter;
  vtkSmartPointer<vtkGeneralTransform>        OutputWorldToModelTransform;

private:
  vtkSlicerDynamicModelerHollowTool(const vtkSlicerDynamicModelerHollowTool&) = delete;
};

#endif // __vtkSlicerDynamicModelerHollowTool_h
