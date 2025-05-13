#include "vtkSlicerVTL3dViewerModuleLogic.h"

// VTK includes
#include <vtkObjectFactory.h>

// MRML includes
#include <vtkMRMLScene.h>

// STD includes
#include <cassert>

//----------------------------------------------------------------------------
// vtkSlicerVTL3dViewerModuleLogicPrivate methods
//----------------------------------------------------------------------------
class vtkSlicerVTL3dViewerModuleLogicPrivate
{
public:
  vtkSlicerVTL3dViewerModuleLogicPrivate();
  ~vtkSlicerVTL3dViewerModuleLogicPrivate();
};

//----------------------------------------------------------------------------
vtkSlicerVTL3dViewerModuleLogicPrivate::vtkSlicerVTL3dViewerModuleLogicPrivate() = default;

//-----------------------------------------------------------------------------
vtkSlicerVTL3dViewerModuleLogicPrivate::~vtkSlicerVTL3dViewerModuleLogicPrivate() = default;

//----------------------------------------------------------------------------
// vtkSlicerVTL3dViewerModuleLogic methods

//----------------------------------------------------------------------------
vtkStandardNewMacro(vtkSlicerVTL3dViewerModuleLogic);

//----------------------------------------------------------------------------
vtkSlicerVTL3dViewerModuleLogic::vtkSlicerVTL3dViewerModuleLogic()
  : Internal(new vtkSlicerVTL3dViewerModuleLogicPrivate)
{
}

//----------------------------------------------------------------------------
vtkSlicerVTL3dViewerModuleLogic::~vtkSlicerVTL3dViewerModuleLogic()
{
  delete this->Internal;
  this->Internal = nullptr;
}

//----------------------------------------------------------------------------
void vtkSlicerVTL3dViewerModuleLogic::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os, indent);
  os << indent << "vtkSlicerVTL3dViewerModuleLogic: " << this->GetClassName() << "\n";
}

//----------------------------------------------------------------------------
void vtkSlicerVTL3dViewerModuleLogic::SetMRMLSceneInternal(vtkMRMLScene * newScene)
{
  // Standard practice is to call Superclass first
  this->Superclass::SetMRMLSceneInternal(newScene);

  // If specific layout updates are needed after setting a new scene, 
  // they should be invoked more appropriately, for example, via ApplicationLogic
  // or by observing specific MRML node events.
  // The previous line:
  // vtkMRMLNode::ExecuteModifiedEvent((vtkObject*)newScene, vtkCommand::LayoutModifiedEvent, nullptr);
  // was incorrect as vtkCommand::LayoutModifiedEvent is not a standard VTK event ID
  // and ExecuteModifiedEvent is typically for general ModifiedEvent.
}

//----------------------------------------------------------------------------
void vtkSlicerVTL3dViewerModuleLogic::RegisterNodes()
{
  assert(this->GetMRMLScene() != nullptr);
  // Register any MRML nodes specific to this module here
  // Example:
  // vtkMRMLScene* scene = this->GetMRMLScene();
  // scene->RegisterNodeClass(vtkSmartPointer<vtkMRMLMyNode>::New());
}

//----------------------------------------------------------------------------
void vtkSlicerVTL3dViewerModuleLogic::UpdateFromMRMLScene()
{
  assert(this->GetMRMLScene() != nullptr);
}

//----------------------------------------------------------------------------
void vtkSlicerVTL3dViewerModuleLogic::OnMRMLSceneNodeAdded(vtkMRMLNode* /*node*/)
{
}

//----------------------------------------------------------------------------
void vtkSlicerVTL3dViewerModuleLogic::OnMRMLSceneNodeRemoved(vtkMRMLNode* /*node*/)
{
} 