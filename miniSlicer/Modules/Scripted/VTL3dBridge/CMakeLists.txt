cmake_minimum_required(VERSION 3.13)
project(VTL3dBridge)

#-----------------------------------------------------------------------------
set(MODULE_NAME VTL3dBridge)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  )

#-----------------------------------------------------------------------------
# 构建 Scripted 模块
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  ) 