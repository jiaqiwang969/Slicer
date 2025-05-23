// ****************************************************************************
// This file is part of VocalTractLab3D.
// Copyright (C) 2022, Peter Birkholz, Dresden, Germany
// www.vocaltractlab.de
// author: Peter Birkholz and Rémi Blandin
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program. If not, see <http://www.gnu.org/licenses/>.
//
// ****************************************************************************

#include "ParamSimu3DDialog.h"
#include "Data.h"
#include <fstream>
#include "Backend/Constants.h"
#include <wx/filename.h>
#include <wx/statline.h>
#include "Backend/SoundSpeed.h"
#include <wx/scrolwin.h>

// ****************************************************************************
// IDs.
// ****************************************************************************

static const int IDE_TEMPERATURE        = 3999;
static const int IDE_SND_SPEED          = 4000;
static const int IDE_MESH_DENSITY       = 4001;
static const int IDE_MAX_CUT_ON         = 4002;
static const int IDE_MAX_SIM_FREQ       = 4003;
static const int IDE_NUM_INTEGRATION    = 4004;
static const int IDE_SEC_NOISE_SOURCE   = 4005;
static const int IDE_PERCENT_LOSSES		  = 4006;

// acoustic field computation options
static const int IDE_FREQ_COMPUTE_FIELD = 4009;
static const int IDE_RESOLUTION_FIELD = 4010;
static const int IDE_BBOX_MIN_X       = 4011;
static const int IDE_BBOX_MIN_Y       = 4012;
static const int IDE_BBOX_MAX_X       = 4013;
static const int IDE_BBOX_MAX_Y       = 4014;

// transfer function point
static const int IDE_TF_POINT_X       = 4015;
static const int IDE_TF_POINT_Y       = 4016;
static const int IDE_TF_POINT_Z       = 4017;
static const int IDB_LOAD_TF_POINTS   = 4018;

static const int IDE_WALL_ADMIT_REAL       = 4019;
static const int IDE_WALL_ADMIT_IMAG    = 4020;

// medium selection IDs
static const int IDL_MEDIUM_SELECT      = 4021;
static const int IDE_SALINITY           = 4022;
static const int IDE_DEPTH              = 4023;

static const int IDB_CHK_FDEP_LOSSES	= 5001;
static const int IDB_CHK_WALL_LOSSES    = 5002;
static const int IDB_CHK_WALL_ADMITTANCE = 5003;

static const int IDB_CHK_STRAIGHT       = 5004;
static const int IDB_CHK_MAGNUS			= 5005;
static const int IDB_CHK_CURV			= 5006;
static const int IDB_CHK_VAR_AREA		= 5007;

static const int IDB_CHK_MULTI_TF_PTS = 5008;

static const int IDB_COMPUTE_RAD_FIELD = 5009;

static const int IDL_SCALING_FAC_METHOD = 6000;
static const int IDL_MOUTH_BCOND = 6001;
static const int IDL_FREQ_RES = 6002;
static const int IDL_FIELD_PHYSICAL_QUANTITY = 6003;
static const int IDL_AMPLITUDE_PHASE = 6004;
static const int IDL_GLOTTIS_BCOND = 6005;

static const int IDB_SET_DEFAULT_PARAMS_FAST = 7002;
static const int IDB_SET_DEFAULT_PARAMS_ACCURATE = 7003;
static const int IDB_CLOSE = 7004;

// ****************************************************************************
// The event table.
// ****************************************************************************

BEGIN_EVENT_TABLE(ParamSimu3DDialog, wxDialog)
EVT_TEXT_ENTER(IDE_TEMPERATURE, ParamSimu3DDialog::OnTemperatureEnter)
EVT_TEXT_ENTER(IDE_SND_SPEED, ParamSimu3DDialog::OnSndSpeedEnter)
EVT_TEXT_ENTER(IDE_MESH_DENSITY, ParamSimu3DDialog::OnMeshDensityEnter)
EVT_TEXT_ENTER(IDE_MAX_CUT_ON, ParamSimu3DDialog::OnMaxCutOnEnter)
EVT_TEXT_ENTER(IDE_MAX_SIM_FREQ, ParamSimu3DDialog::OnMaxSimFreq)
EVT_TEXT_ENTER(IDE_NUM_INTEGRATION, ParamSimu3DDialog::OnNumIntegrationEnter)
EVT_TEXT_ENTER(IDE_SEC_NOISE_SOURCE, ParamSimu3DDialog::OnSecNoiseSourceEnter)
EVT_TEXT_ENTER(IDE_PERCENT_LOSSES, ParamSimu3DDialog::OnPercentLosses)
EVT_TEXT_ENTER(IDE_FREQ_COMPUTE_FIELD, ParamSimu3DDialog::OnFreqComputeField)
EVT_TEXT_ENTER(IDE_RESOLUTION_FIELD, ParamSimu3DDialog::OnResolutionField)
EVT_TEXT_ENTER(IDE_BBOX_MIN_X, ParamSimu3DDialog::OnBboxMinX)
EVT_TEXT_ENTER(IDE_BBOX_MIN_Y, ParamSimu3DDialog::OnBboxMinY)
EVT_TEXT_ENTER(IDE_BBOX_MAX_X, ParamSimu3DDialog::OnBboxMaxX)
EVT_TEXT_ENTER(IDE_BBOX_MAX_Y, ParamSimu3DDialog::OnBboxMaxY)

EVT_TEXT_ENTER(IDE_TF_POINT_X, ParamSimu3DDialog::OnTfPointX)
EVT_TEXT_ENTER(IDE_TF_POINT_Y, ParamSimu3DDialog::OnTfPointY)
EVT_TEXT_ENTER(IDE_TF_POINT_Z, ParamSimu3DDialog::OnTfPointZ)
EVT_BUTTON(IDB_LOAD_TF_POINTS, ParamSimu3DDialog::OnLoadTfPts)

EVT_TEXT_ENTER(IDE_WALL_ADMIT_REAL, ParamSimu3DDialog::OnWallAdmitEnter)
EVT_TEXT_ENTER(IDE_WALL_ADMIT_IMAG, ParamSimu3DDialog::OnWallAdmitEnter)

EVT_CHECKBOX(IDB_CHK_FDEP_LOSSES, ParamSimu3DDialog::OnChkFdepLosses)
EVT_CHECKBOX(IDB_CHK_WALL_LOSSES, ParamSimu3DDialog::OnChkWallLosses)
EVT_CHECKBOX(IDB_CHK_WALL_ADMITTANCE, ParamSimu3DDialog::OnChkWallAdmittance)
EVT_CHECKBOX(IDB_CHK_STRAIGHT, ParamSimu3DDialog::OnChkStraight)
EVT_CHECKBOX(IDB_CHK_MAGNUS, ParamSimu3DDialog::OnChkMagnus)
EVT_CHECKBOX(IDB_CHK_CURV, ParamSimu3DDialog::OnChkCurv)
EVT_CHECKBOX(IDB_CHK_VAR_AREA, ParamSimu3DDialog::OnChkVarArea)
EVT_CHECKBOX(IDB_CHK_MULTI_TF_PTS, ParamSimu3DDialog::OnChkMultiTFPts)
EVT_CHECKBOX(IDB_COMPUTE_RAD_FIELD, ParamSimu3DDialog::OnChkComputeRad)

EVT_COMBOBOX(IDL_SCALING_FAC_METHOD, ParamSimu3DDialog::OnScalingFactMethod)
EVT_COMBOBOX(IDL_MOUTH_BCOND, ParamSimu3DDialog::OnMouthBcond)
EVT_COMBOBOX(IDL_GLOTTIS_BCOND, ParamSimu3DDialog::OnGlottisBcond)
EVT_COMBOBOX(IDL_FREQ_RES, ParamSimu3DDialog::OnFreqRes)
EVT_COMBOBOX(IDL_FIELD_PHYSICAL_QUANTITY, ParamSimu3DDialog::OnFieldPhysicalQuantity)
EVT_COMBOBOX(IDL_AMPLITUDE_PHASE, ParamSimu3DDialog::OnAmplitudePhase)
EVT_COMBOBOX(IDL_MEDIUM_SELECT, ParamSimu3DDialog::OnMediumSelect)
EVT_TEXT_ENTER(IDE_SALINITY, ParamSimu3DDialog::OnSalinityEnter)
EVT_TEXT_ENTER(IDE_DEPTH, ParamSimu3DDialog::OnDepthEnter)

EVT_BUTTON(IDB_SET_DEFAULT_PARAMS_FAST, ParamSimu3DDialog::OnSetDefaultParamsFast)
EVT_BUTTON(IDB_SET_DEFAULT_PARAMS_ACCURATE, ParamSimu3DDialog::OnSetDefaultParamsAccurate)
EVT_BUTTON(IDB_CLOSE, ParamSimu3DDialog::OnClose)

END_EVENT_TABLE()

// The single instance of this class.
ParamSimu3DDialog *ParamSimu3DDialog::instance = NULL;

// ****************************************************************************
/// Returns the single instance of this dialog.
// ****************************************************************************

ParamSimu3DDialog* ParamSimu3DDialog::getInstance(wxWindow *parent)
{
    if (instance == NULL)
    {
        instance = new ParamSimu3DDialog(parent);
    }

    instance->updateParams();
    instance->updateWidgets();

    return instance;
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::updateWidgets()
{
  if (m_simuParams.propMethod == MAGNUS)
  {
    m_simuParams.curved = m_simuParamsMagnus.curved;
    m_simuParams.varyingArea = m_simuParamsMagnus.varyingArea;
    m_simuParams.numIntegrationStep = m_simuParamsMagnus.numIntegrationStep;
  }

  wxString st;

  st = wxString::Format("%2.1f", m_simuParams.temperature);
  txtTemperature->SetValue(st);

  st = wxString::Format("%2.1f", m_simuParams.sndSpeed/100.);
  txtSndSpeed->SetValue(st);

  // ---- medium controls ----
  switch (m_simuParams.medium)
  {
  case simulationParameters::AIR:
    lstMedium->SetSelection(0);
    break;
  case simulationParameters::SEA:
    lstMedium->SetSelection(1);
    break;
  case simulationParameters::HELIUM:
    lstMedium->SetSelection(2);
    break;
  }

  st = wxString::Format("%2.1f", m_simuParams.salinity);
  txtSalinity->SetValue(st);
  st = wxString::Format("%3.1f", m_simuParams.depth);
  txtDepth->SetValue(st);

  if (m_simuParams.medium == simulationParameters::SEA)
  {
    txtSalinity->Enable();
    txtDepth->Enable();
  }
  else
  {
    txtSalinity->Disable();
    txtDepth->Disable();
  }

  st = wxString::Format("%2.1f", m_meshDensity);
  txtMeshDensity->SetValue(st);

  st = wxString::Format("%6.f", m_simuParams.maxCutOnFreq);
  txtMaxCutOnFreq->SetValue(st);

  st = wxString::Format("%5.f", m_simuParams.maxComputedFreq);
  txtMaxSimFreq->SetValue(st);

  st = wxString::Format("%d", m_simuParamsMagnus.numIntegrationStep);
  txtNumIntegrationStep->SetValue(st);

  st = wxString::Format("%d", m_secNoiseSource);
  txtSecNoiseSource->SetValue(st);

	st = wxString::Format("%1.2f", 100. * m_simuParams.percentageLosses);
	txtPercLoss->SetValue(st);

  chkViscoThermLoss->SetValue(m_simuParamsFreqDepLosses.viscoThermalLosses);
  if ((m_simuParams.propMethod == STRAIGHT_TUBES) ||
    m_simuParams.constantWallImped)
  {
    chkViscoThermLoss->Disable();
  }
  else
  {
    chkViscoThermLoss->Enable();
  }

  chkWallLosses->SetValue(m_simuParamsFreqDepLosses.wallLosses);
  if ((m_simuParams.propMethod == STRAIGHT_TUBES) ||
    m_simuParams.constantWallImped)
  {
    chkWallLosses->Disable();
  }
  else
  {
    chkWallLosses->Enable();
  }

  chkWallAdmittance->SetValue(m_simuParams.constantWallImped);
  if (!m_simuParams.constantWallImped || (m_simuParams.propMethod == STRAIGHT_TUBES))
  {
    txtWallAdmitReal->Disable();
    txtWallAdmitImag->Disable();
  }
  else
  {
    txtWallAdmitReal->Enable();
    txtWallAdmitImag->Enable();
  }
  if (!m_simuParams.constantWallImped)
  {
    m_simuParams.wallLosses = m_simuParamsFreqDepLosses.wallLosses;
    m_simuParams.viscoThermalLosses = m_simuParamsFreqDepLosses.viscoThermalLosses;
  }

  switch (m_simuParams.propMethod) {
      case MAGNUS:
          chkStraight->SetValue(false);
    chkMagnus->SetValue(true);
          break;
      case STRAIGHT_TUBES:
          chkStraight->SetValue(true);
    chkMagnus->SetValue(false);
          break;
  }

	chkCurv->SetValue(m_simuParamsMagnus.curved);

	chkVarArea->SetValue(m_simuParamsMagnus.varyingArea);

  // scaling factor computation method
  switch (m_contInterpMeth)
  {
  case AREA:
    lstScalingFacMethods->SetValue(m_listScalingMethods[0]);
    break;
  case BOUNDING_BOX:
    lstScalingFacMethods->SetValue(m_listScalingMethods[1]);
    break;
  case FROM_FILE:
    lstScalingFacMethods->SetValue(m_listScalingMethods[2]);
    break;
  }

  // set compute acoustic field options
  st = wxString::Format("%1.1f", m_simuParams.freqField);
  txtFreqComputeField->SetValue(st);

  st = wxString::Format("%d", m_simuParams.fieldResolution);
  txtResolutionField->SetValue(st);

  st = wxString::Format("%1.1f", m_simuParams.bbox[0].x());
  txtBboxMinX->SetValue(st);

  st = wxString::Format("%1.1f", m_simuParams.bbox[0].y());
  txtBboxMinY->SetValue(st);

  st = wxString::Format("%1.1f", m_simuParams.bbox[1].x());
  txtBboxMaxX->SetValue(st);

  st = wxString::Format("%1.1f", m_simuParams.bbox[1].y());
  txtBboxMaxY->SetValue(st);

  // transfer function point
  st = wxString::Format("%1.1f", m_singlePtTf.x());
  txtTfPointX->SetValue(st);

  st = wxString::Format("%1.1f", m_singlePtTf.y());
  txtTfPointY->SetValue(st);

  st = wxString::Format("%1.1f", m_singlePtTf.z());
  txtTfPointZ->SetValue(st);

  chkMultiTFPts->SetValue(m_tfPtsFromFile);
  if (m_tfPtsFromFile)
  {
    txtTfPointX->Disable();
    txtTfPointY->Disable();
    txtTfPointZ->Disable();
    buttonMultiTfPts->Enable();
  }
  else
  {
    txtTfPointX->Enable();
    txtTfPointY->Enable();
    txtTfPointZ->Enable();
    buttonMultiTfPts->Disable();

    m_simuParams.tfPoint.clear();
    m_simuParams.tfPoint.push_back(m_singlePtTf);
  }

  // glottis boundary condition
  switch (m_glottisBoundaryCond) {
    case HARD_WALL:        lstGlottisBcond->SetValue(m_listGlottisBcond[0]); break;
    case ZERO_PRESSURE:    lstGlottisBcond->SetValue(m_listGlottisBcond[1]); break;
    case IFINITE_WAVGUIDE: lstGlottisBcond->SetValue(m_listGlottisBcond[2]); break;
    case RADIATION:        lstGlottisBcond->SetValue(m_listGlottisBcond[3]); break;
    case ADMITTANCE_1:     lstGlottisBcond->SetValue(m_listGlottisBcond[4]); break;
    default:               lstGlottisBcond->SetValue(m_listGlottisBcond[0]); break; // Default to Hard wall
  }
  // mouth boundary condition
  switch (m_mouthBoundaryCond)
  {
    case HARD_WALL:        lstMouthBcond->SetValue(m_listMouthBcond[0]); break;
    case ZERO_PRESSURE:    lstMouthBcond->SetValue(m_listMouthBcond[1]); break;
    case IFINITE_WAVGUIDE: lstMouthBcond->SetValue(m_listMouthBcond[2]); break;
    case RADIATION:        lstMouthBcond->SetValue(m_listMouthBcond[3]); break;
    case ADMITTANCE_1:     lstMouthBcond->SetValue(m_listMouthBcond[4]); break;
    default:               lstMouthBcond->SetValue(m_listMouthBcond[0]); break; // Default to Hard wall
  }

  // frequency resolution
  lstFreqRes->SetValue(m_listFreqRes[m_simuParams.spectrumLgthExponent - m_expSpectrumLgthStart]);

  st = wxString::Format("%1.4f", real(m_simuParams.wallAdmit));
  txtWallAdmitReal->SetValue(st);

  st = wxString::Format("%1.4f", imag(m_simuParams.wallAdmit));
  txtWallAdmitImag->SetValue(st);

  // field physical quantity
  switch (m_simuParams.fieldPhysicalQuantity)
  {
  case PRESSURE:
    lstFieldPhysicalQuantity->SetValue(m_listFieldPhysicalQuantity[0]);
    break;
  case VELOCITY:
    lstFieldPhysicalQuantity->SetValue(m_listFieldPhysicalQuantity[1]);
    break;
  default:
    lstFieldPhysicalQuantity->SetValue(m_listFieldPhysicalQuantity[0]);
    break;
  }

  // field type: amplitude or phase
  if (m_simuParams.showAmplitude)
  {
    lstAmpPhase->SetValue(m_listAmplitudePhase[0]);
  }
  else
  {
    lstAmpPhase->SetValue(m_listAmplitudePhase[1]);
  }

  chkComputeRad->SetValue(m_simuParams.computeRadiatedField);

  m_simu3d->setSimulationParameters(m_meshDensity, m_secNoiseSource, 
		m_simuParams, m_mouthBoundaryCond, m_contInterpMeth, m_glottisBoundaryCond);
}

// ****************************************************************************

void ParamSimu3DDialog::updateParams()
{
  m_meshDensity = m_simu3d->meshDensity();
  m_secNoiseSource = m_simu3d->idxSecNoiseSource();
  m_simuParams.spectrumLgthExponent = m_simu3d->spectrumLgthExponent();
  m_mouthBoundaryCond = m_simu3d->mouthBoundaryCond();
  m_contInterpMeth = m_simu3d->contInterpMeth();
  m_simuParams = m_simu3d->simuParams();
  if (m_simuParams.propMethod == MAGNUS)
  {
    m_simuParamsMagnus = m_simu3d->simuParams();
  }
  if (!m_simuParams.constantWallImped)
  {
    m_simuParamsFreqDepLosses = m_simu3d->simuParams();
  }
}

// ****************************************************************************
/// Set the windows that receive an update request message when a vocal tract
/// parameter was changed.
// ****************************************************************************

void ParamSimu3DDialog::setUpdateRequestReceiver(wxWindow* receiver)
{
    updateRequestReceiver = receiver;
}

// ****************************************************************************
// To update the segment picture and reload the geometry
// ****************************************************************************

void ParamSimu3DDialog::updateGeometry()
{
  if (updateRequestReceiver != NULL)
  {
    m_simu3d->requestReloadGeometry();
    wxCommandEvent event(updateRequestEvent);
    event.SetInt(UPDATE_VOCAL_TRACT);
    wxPostEvent(updateRequestReceiver, event);
  }
}

// ****************************************************************************
// To update the pictures
// ****************************************************************************

void ParamSimu3DDialog::updatePictures()
{
  if (updateRequestReceiver != NULL)
  {
    wxCommandEvent event(updateRequestEvent);
    event.SetInt(UPDATE_PICTURES_AND_CONTROLS);
    wxPostEvent(updateRequestReceiver, event);
  }
}

// ****************************************************************************
/// Constructor.
// ****************************************************************************

ParamSimu3DDialog::ParamSimu3DDialog(wxWindow* parent) :
  wxDialog(parent, wxID_ANY, wxString("Parameters 3D simulations"),
    wxDefaultPosition, wxDefaultSize, wxDEFAULT_DIALOG_STYLE | wxSTAY_ON_TOP)
{

  m_simu3d = Acoustic3dSimulation::getInstance();
  m_tract = Data::getInstance()->vocalTract;
  m_meshDensity = m_simu3d->meshDensity();
  m_secNoiseSource = m_simu3d->idxSecNoiseSource();
  m_simuParams.spectrumLgthExponent = m_simu3d->spectrumLgthExponent();
  m_tfPtsFromFile = false;
  m_mouthBoundaryCond = m_simu3d->mouthBoundaryCond();
  m_glottisBoundaryCond = m_simu3d->glottisBoundaryCond(); // 从 simu3d 获取声门默认边界条件
  m_contInterpMeth = m_simu3d->contInterpMeth(); 
	m_simuParams = m_simu3d->simuParams();
  m_singlePtTf = m_simuParams.tfPoint[0];
  m_simuParamsMagnus = m_simu3d->simuParams();
  m_simuParamsFreqDepLosses = m_simu3d->simuParams();
  m_maxBbox = 1000.;

  this->Move(100, 100);

  // ****************************************************************
  // Init and update the widgets.
  // ****************************************************************

  initWidgets();

  // create the list of scaling factor computation methods
  m_listScalingMethods.clear();
  m_listScalingMethods.push_back("Area");
  m_listScalingMethods.push_back("Bounding box");
  m_listScalingMethods.push_back("From file");

  lstScalingFacMethods->Clear();
  for (int i(0); i < m_listScalingMethods.size(); i++)
  {
    lstScalingFacMethods->Append(m_listScalingMethods[i]);
  }

  // create the list of boundary conditions
  m_listMouthBcond.clear();
  m_listMouthBcond.push_back("Hard wall");
  m_listMouthBcond.push_back("Zero pressure");
  m_listMouthBcond.push_back("Radiation");
  m_listMouthBcond.push_back("Infinite waveguide");
  m_listMouthBcond.push_back("Admittance_1");

  lstMouthBcond->Clear();
  for (int i(0); i < m_listMouthBcond.size(); i++)
  {
    lstMouthBcond->Append(m_listMouthBcond[i]);
  }

  // create the list of field physical qunatities
  m_listFieldPhysicalQuantity.clear();
  m_listFieldPhysicalQuantity.push_back("Pressure");
  m_listFieldPhysicalQuantity.push_back("Velocity");

  lstFieldPhysicalQuantity->Clear();
  for (int i(0); i < m_listFieldPhysicalQuantity.size(); i++)
  {
    lstFieldPhysicalQuantity->Append(m_listFieldPhysicalQuantity[i]);
  }

  // create the list with amplitude and phase
  m_listAmplitudePhase.clear();
  m_listAmplitudePhase.push_back("Amplitude");
  m_listAmplitudePhase.push_back("Phase");

  lstAmpPhase->Clear();
  for (int i(0); i < m_listAmplitudePhase.size(); i++)
  {
    lstAmpPhase->Append(m_listAmplitudePhase[i]);
  }

  // create the list of frequency resolutions
  m_expSpectrumLgthStart = 8;
  m_expSpectrumLgthEnd = 15;
  m_listFreqRes.clear();
  wxString st;
  for (int i(m_expSpectrumLgthStart); i < m_expSpectrumLgthEnd; i++)
  {
  st = wxString::Format(" %2.1f Hz", (double)SAMPLING_RATE / 2./
      (double)(1 << (i - 1)));
  m_listFreqRes.push_back(st.ToStdString());
  }

  lstFreqRes->Clear();
  for (int i(0); i < m_listFreqRes.size(); i++)
  {
    lstFreqRes->Append(m_listFreqRes[i]);
  }

  // create list of mediums
  m_listMedium.clear();
  m_listMedium.push_back("Air");
  m_listMedium.push_back("Sea water");
  m_listMedium.push_back("Helium");

  lstMedium->Clear();
  for (int i(0); i < m_listMedium.size(); ++i)
  {
    lstMedium->Append(m_listMedium[i]);
  }

  updateWidgets();
}

// ****************************************************************************
/// Init the widgets of this dialog.
// ****************************************************************************

void ParamSimu3DDialog::initWidgets()
{
    // 创建可滚动窗口，所有控件放在内部
    wxScrolledWindow* scrollWin = new wxScrolledWindow(this, wxID_ANY, wxDefaultPosition, wxDefaultSize, wxVSCROLL);
    scrollWin->SetScrollRate(5, 5);

    wxBoxSizer* topLevelSizer = new wxBoxSizer(wxVERTICAL);
    wxStaticBoxSizer* sz = NULL;
    wxBoxSizer* lineSizer = NULL;
    wxStaticText* label = NULL;
    wxButton* button; 

    ///////////////////////////////////////////////////////////////////
    // Geometry options
    ///////////////////////////////////////////////////////////////////

    sz = new wxStaticBoxSizer(wxVERTICAL, scrollWin, "Geometry options");

    // ****************************************************************
    // Select the geometrical features
    // ****************************************************************

    lineSizer = new wxBoxSizer(wxHORIZONTAL);

    chkCurv = new wxCheckBox(scrollWin, IDB_CHK_CURV, "Curved");
    lineSizer->Add(chkCurv, 1, wxALL, 2);

    chkVarArea = new wxCheckBox(scrollWin, IDB_CHK_VAR_AREA, "Varying area");
    lineSizer->Add(chkVarArea, 1, wxALL, 2);

    lstScalingFacMethods = new wxComboBox(scrollWin, IDL_SCALING_FAC_METHOD, "", wxDefaultPosition,
      this->FromDIP(wxSize(10, -1)), wxArrayString(), wxCB_DROPDOWN | wxCB_READONLY);
    lineSizer->Add(lstScalingFacMethods, 1, wxALL, 3);

    lineSizer->AddStretchSpacer();

    sz->Add(lineSizer, 0, wxLEFT | wxRIGHT | wxEXPAND, 10);

    topLevelSizer->Add(sz, 0, wxLEFT | wxRIGHT | wxEXPAND, 10);

    ///////////////////////////////////////////////////////////////////
    // Modes computation options
    ///////////////////////////////////////////////////////////////////

    topLevelSizer->AddSpacer(10);
    sz = new wxStaticBoxSizer(wxVERTICAL, scrollWin, "Mode computation options");

    // ****************************************************************
    // Set mesh density.
    // ****************************************************************

    lineSizer = new wxBoxSizer(wxHORIZONTAL);

    label = new wxStaticText(scrollWin, wxID_ANY, "Mesh density (elements per length): ");
    lineSizer->Add(label, 12, wxALL | wxALIGN_CENTER, 3);

    txtMeshDensity = new wxTextCtrl(scrollWin, IDE_MESH_DENSITY, "", wxDefaultPosition,
      wxSize(10, -1), wxTE_PROCESS_ENTER);
    lineSizer->Add(txtMeshDensity, 3, wxALL, 3);

    lineSizer->AddStretchSpacer(9);

    sz->Add(lineSizer, 0, wxEXPAND | wxLEFT | wxRIGHT, 10);

    // ****************************************************************
    // Set the maximal cut-on frequency
    // ****************************************************************

    lineSizer = new wxBoxSizer(wxHORIZONTAL);

    label = new wxStaticText(scrollWin, wxID_ANY, "Maximal cut-off frequency (Hz): ");
    lineSizer->Add(label, 4, wxALL | wxALIGN_CENTER, 3);

    txtMaxCutOnFreq = new wxTextCtrl(scrollWin, IDE_MAX_CUT_ON, "", wxDefaultPosition,
      wxSize(60, -1), wxTE_PROCESS_ENTER);
    lineSizer->Add(txtMaxCutOnFreq, 1, wxALL, 3);

    lineSizer->AddStretchSpacer(3);

    sz->Add(lineSizer, 0, wxLEFT | wxRIGHT | wxEXPAND, 10);

    topLevelSizer->Add(sz, 0, wxEXPAND | wxLEFT | wxRIGHT, 10);

    ///////////////////////////////////////////////////////////////////
    // Physical constants
    ///////////////////////////////////////////////////////////////////

    topLevelSizer->AddSpacer(10);
    sz = new wxStaticBoxSizer(wxVERTICAL, scrollWin, "Physical constants");

    // ****************************************************************
    // Set temperature or sound speed.
    // ****************************************************************

    lineSizer = new wxBoxSizer(wxHORIZONTAL);

    label = new wxStaticText(scrollWin, wxID_ANY, wxString::FromUTF8("Temperature (\xc2\xb0""C): "));
    lineSizer->Add(label, 6, wxALL | wxALIGN_CENTER, 3);

    txtTemperature = new wxTextCtrl(scrollWin, IDE_TEMPERATURE, "", wxDefaultPosition,
      wxSize(10, -1), wxTE_PROCESS_ENTER);
    lineSizer->Add(txtTemperature, 4, wxALL, 3);

    lineSizer->AddStretchSpacer(2);

    label = new wxStaticText(scrollWin, wxID_ANY, "Sound speed (m/s): ");
    lineSizer->Add(label, 6, wxALL | wxALIGN_CENTER, 3);

    txtSndSpeed = new wxTextCtrl(scrollWin, IDE_SND_SPEED, "", wxDefaultPosition,
      wxSize(10, -1), wxTE_PROCESS_ENTER);
    lineSizer->Add(txtSndSpeed, 4, wxALL, 3);

    lineSizer->AddStretchSpacer(2);

    // 将温度 / 声速 行加入物理常量分组
    sz->Add(lineSizer, 0, wxEXPAND | wxLEFT | wxRIGHT, 10);

    // ****************************************************************
    // Medium selection + sea parameters
    // ****************************************************************

    lineSizer = new wxBoxSizer(wxHORIZONTAL);

    label = new wxStaticText(scrollWin, wxID_ANY, "Medium");
    lineSizer->Add(label, 4, wxALL | wxALIGN_CENTER, 3);

    lstMedium = new wxComboBox(scrollWin, IDL_MEDIUM_SELECT, "", wxDefaultPosition,
      this->FromDIP(wxSize(10, -1)), wxArrayString(), wxCB_DROPDOWN | wxCB_READONLY);
    lineSizer->Add(lstMedium, 4, wxALL, 3);

    label = new wxStaticText(scrollWin, wxID_ANY, "Salinity (psu)");
    lineSizer->Add(label, 4, wxALL | wxALIGN_CENTER, 3);

    txtSalinity = new wxTextCtrl(scrollWin, IDE_SALINITY, "", wxDefaultPosition,
      wxSize(10, -1), wxTE_PROCESS_ENTER);
    lineSizer->Add(txtSalinity, 3, wxALL, 3);

    label = new wxStaticText(scrollWin, wxID_ANY, "Depth (m)");
    lineSizer->Add(label, 4, wxALL | wxALIGN_CENTER, 3);

    txtDepth = new wxTextCtrl(scrollWin, IDE_DEPTH, "", wxDefaultPosition,
      wxSize(10, -1), wxTE_PROCESS_ENTER);
    lineSizer->Add(txtDepth, 3, wxALL, 3);

    sz->Add(lineSizer, 0, wxEXPAND | wxLEFT | wxRIGHT, 10);

    topLevelSizer->Add(sz, 0, wxLEFT | wxRIGHT | wxEXPAND, 10);

    ///////////////////////////////////////////////////////////////////
    // Numerical scheme options
    ///////////////////////////////////////////////////////////////////

    topLevelSizer->AddSpacer(10);
    sz = new wxStaticBoxSizer(wxVERTICAL, scrollWin, "Numerical scheme options");

    // ****************************************************************
    // Select the numerical scheme
    // ****************************************************************

    lineSizer = new wxBoxSizer(wxHORIZONTAL);

    chkStraight = new wxCheckBox(scrollWin, IDB_CHK_STRAIGHT, "Straight");
    lineSizer->Add(chkStraight, 1, wxALL, 2);

    chkMagnus = new wxCheckBox(scrollWin, IDB_CHK_MAGNUS, "Magnus");
    lineSizer->Add(chkMagnus, 1, wxALL, 2);

    sz->Add(lineSizer, 0, wxLEFT | wxRIGHT | wxEXPAND, 10);

    // ****************************************************************
    // Set the number of integration steps
    // ****************************************************************

    lineSizer = new wxBoxSizer(wxHORIZONTAL);

    label = new wxStaticText(scrollWin, wxID_ANY, "Number of integration steps: ");
    lineSizer->Add(label, 4, wxALL | wxALIGN_CENTER, 3);

    txtNumIntegrationStep = new wxTextCtrl(scrollWin, IDE_NUM_INTEGRATION, "", wxDefaultPosition,
      wxSize(10, -1), wxTE_PROCESS_ENTER);
    lineSizer->Add(txtNumIntegrationStep, 1, wxALL, 3);

    lineSizer->AddStretchSpacer(3);

    sz->Add(lineSizer, 0, wxLEFT | wxRIGHT | wxEXPAND, 10);

    topLevelSizer->Add(sz, 0, wxLEFT | wxRIGHT | wxEXPAND, 10);
    ///////////////////////////////////////////////////////////////////
    // Boundary conditions options
    ///////////////////////////////////////////////////////////////////

    topLevelSizer->AddSpacer(10);
    sz = new wxStaticBoxSizer(wxVERTICAL, scrollWin, "Boundary conditions options");

    // ****************************************************************
    // Select mouth boundary condition
    // ****************************************************************

    lineSizer = new wxBoxSizer(wxHORIZONTAL);

    // create the list of boundary conditions
    m_listMouthBcond = { "Hard wall", "Zero pressure", "Infinite waveguide", "Radiation", "Admittance_1" };

    label = new wxStaticText(scrollWin, wxID_ANY, "Mouth boundary condition ");
    lineSizer->Add(label, 2, wxALL | wxALIGN_CENTER, 3);

    lstMouthBcond = new wxComboBox(scrollWin, IDL_MOUTH_BCOND, "", wxDefaultPosition,
      this->FromDIP(wxSize(10, -1)), wxArrayString(), wxCB_DROPDOWN | wxCB_READONLY);
    lstMouthBcond->Clear(); // 清空旧选项
    for (auto &s : m_listMouthBcond) lstMouthBcond->Append(s);
    lineSizer->Add(lstMouthBcond, 1, wxALL, 3);

    lineSizer->AddStretchSpacer();

    sz->Add(lineSizer, 0, wxLEFT | wxRIGHT | wxEXPAND, 10);

    // ****************************************************************
    // Select glottis boundary condition
    // ****************************************************************

    lineSizer = new wxBoxSizer(wxHORIZONTAL);

    // create the list of glottis boundary conditions
    m_listGlottisBcond = { "Hard wall", "Zero pressure", "Infinite waveguide", "Radiation", "Admittance_1" };

    label = new wxStaticText(scrollWin, wxID_ANY, "Glottis boundary condition ");
    lineSizer->Add(label, 2, wxALL | wxALIGN_CENTER, 3);

    lstGlottisBcond = new wxComboBox(scrollWin, IDL_GLOTTIS_BCOND, "", wxDefaultPosition,
      this->FromDIP(wxSize(10, -1)), wxArrayString(), wxCB_DROPDOWN | wxCB_READONLY);
    lstGlottisBcond->Clear(); // 清空旧选项
    for (auto &s : m_listGlottisBcond) lstGlottisBcond->Append(s);
    lineSizer->Add(lstGlottisBcond, 1, wxALL, 3);

    lineSizer->AddStretchSpacer();

    sz->Add(lineSizer, 0, wxLEFT | wxRIGHT | wxEXPAND, 10);

    // ****************************************************************
    // Set the percentage of losses
    // ****************************************************************

    lineSizer = new wxBoxSizer(wxHORIZONTAL);

    label = new wxStaticText(scrollWin, wxID_ANY, "Percentage of wall losses: ");
    lineSizer->Add(label, 4, wxALL | wxALIGN_CENTER, 3);

    txtPercLoss = new wxTextCtrl(scrollWin, IDE_PERCENT_LOSSES, "", wxDefaultPosition,
      wxSize(10, -1), wxTE_PROCESS_ENTER);
    lineSizer->Add(txtPercLoss, 1, wxALL | wxALIGN_CENTER, 3);

    lineSizer->AddStretchSpacer(3);

    sz->Add(lineSizer, 0, wxLEFT | wxRIGHT | wxEXPAND, 10);

    // ****************************************************************
    // Set options wall losses
    // ****************************************************************

    lineSizer = new wxBoxSizer(wxHORIZONTAL);

    chkViscoThermLoss = new wxCheckBox(scrollWin, IDB_CHK_FDEP_LOSSES,
      "Visco-thermal losses");
    lineSizer->Add(chkViscoThermLoss, 1, wxALL, 2);

    chkWallLosses = new wxCheckBox(scrollWin, IDB_CHK_WALL_LOSSES,
      "Soft walls");
    lineSizer->Add(chkWallLosses, 1, wxALL, 2);

    sz->Add(lineSizer, 0, wxLEFT | wxRIGHT | wxEXPAND, 10);

    // ****************************************************************
    // Constant wall admittance
    // ****************************************************************

    lineSizer = new wxBoxSizer(wxHORIZONTAL);

    chkWallAdmittance = new wxCheckBox(scrollWin, IDB_CHK_WALL_ADMITTANCE,
      "Constant wall admittance");
    lineSizer->Add(chkWallAdmittance, 0, wxALL, 2);

    sz->Add(lineSizer, 0, wxLEFT | wxRIGHT | wxEXPAND, 10);

    // ****************************************************************

    lineSizer = new wxBoxSizer(wxHORIZONTAL);

    label = new wxStaticText(scrollWin, wxID_ANY, "Real part");
    lineSizer->Add(label, 6, wxALL, 2);

    txtWallAdmitReal = new wxTextCtrl(scrollWin, IDE_WALL_ADMIT_REAL, "", wxDefaultPosition,
      wxSize(10, -1), wxTE_PROCESS_ENTER);
    lineSizer->Add(txtWallAdmitReal, 4, wxALL | wxALIGN_CENTER, 2);

    lineSizer->AddStretchSpacer(2);

    label = new wxStaticText(scrollWin, wxID_ANY, "Imaginary part");
    lineSizer->Add(label, 6, wxALL, 2);

    txtWallAdmitImag = new wxTextCtrl(scrollWin, IDE_WALL_ADMIT_IMAG, "", wxDefaultPosition,
      wxSize(10, -1), wxTE_PROCESS_ENTER);
    lineSizer->Add(txtWallAdmitImag, 4, wxALL | wxALIGN_CENTER, 2);

    lineSizer->AddStretchSpacer(2);

    sz->Add(lineSizer, 0, wxLEFT | wxRIGHT | wxEXPAND, 10);

    topLevelSizer->Add(sz, 0, wxLEFT | wxRIGHT | wxEXPAND, 10);

    ///////////////////////////////////////////////////////////////////
    // Transfer function options
    ///////////////////////////////////////////////////////////////////

    topLevelSizer->AddSpacer(10);
    sz = new wxStaticBoxSizer(wxVERTICAL, scrollWin, "Transfer functions options");

    // ****************************************************************
    // Set the section containing the noise source
    // ****************************************************************

    lineSizer = new wxBoxSizer(wxHORIZONTAL);

    label = new wxStaticText(scrollWin, wxID_ANY, "Index of noise source section: ");
    lineSizer->Add(label, 4, wxALL | wxALIGN_CENTER, 3);

    txtSecNoiseSource = new wxTextCtrl(scrollWin, IDE_SEC_NOISE_SOURCE, "", wxDefaultPosition,
      wxSize(10, -1), wxTE_PROCESS_ENTER);
    lineSizer->Add(txtSecNoiseSource, 1, wxALL, 3);

    lineSizer->AddStretchSpacer(3);

    sz->Add(lineSizer, 0, wxLEFT | wxRIGHT | wxEXPAND, 10);

    // ****************************************************************
    // Set the maximal computed frequency
    // ****************************************************************

    lineSizer = new wxBoxSizer(wxHORIZONTAL);

    label = new wxStaticText(scrollWin, wxID_ANY, "Maximal simulated frequency (Hz): ");
    lineSizer->Add(label, 4, wxALL | wxALIGN_CENTER, 3);

    txtMaxSimFreq = new wxTextCtrl(scrollWin, IDE_MAX_SIM_FREQ, "", wxDefaultPosition,
        wxSize(10, -1), wxTE_PROCESS_ENTER);
    lineSizer->Add(txtMaxSimFreq, 1, wxALL, 3);

    lineSizer->AddStretchSpacer(3);

    sz->Add(lineSizer, 0, wxLEFT | wxRIGHT | wxEXPAND, 10);

    // ****************************************************************
    // Set the frequency steps size
    // ****************************************************************

    lineSizer = new wxBoxSizer(wxHORIZONTAL);

    label = new wxStaticText(scrollWin, wxID_ANY, "Frequency steps");
    lineSizer->Add(label, 2, wxALL | wxALIGN_CENTER, 3);

    lstFreqRes = new wxComboBox(scrollWin, IDL_FREQ_RES, "", wxDefaultPosition,
      this->FromDIP(wxSize(10, -1)), wxArrayString(), wxCB_DROPDOWN | wxCB_READONLY);
    lineSizer->Add(lstFreqRes, 1, wxALL, 3);

    lineSizer->AddStretchSpacer();

    sz->Add(lineSizer, 0, wxLEFT | wxRIGHT | wxEXPAND, 10);

    // ****************************************************************
    // Set the point for transfer function computation
    // ****************************************************************

    lineSizer = new wxBoxSizer(wxHORIZONTAL);

    label = new wxStaticText(scrollWin, wxID_ANY, "Transfer function point (cm)");
    lineSizer->Add(label, 9, wxALL | wxALIGN_CENTER, 3);

    label = new wxStaticText(scrollWin, wxID_ANY, " X ");
    lineSizer->Add(label, 1, wxALL | wxALIGN_CENTER, 3);

    txtTfPointX = new wxTextCtrl(scrollWin, IDE_TF_POINT_X, "", wxDefaultPosition,
      wxSize(10, -1), wxTE_PROCESS_ENTER);
    lineSizer->Add(txtTfPointX, 2, wxALL, 3);

    label = new wxStaticText(scrollWin, wxID_ANY, " Y ");
    lineSizer->Add(label, 1, wxALL | wxALIGN_CENTER, 3);

    txtTfPointY = new wxTextCtrl(scrollWin, IDE_TF_POINT_Y, "", wxDefaultPosition,
      wxSize(10, -1), wxTE_PROCESS_ENTER);
    lineSizer->Add(txtTfPointY, 2, wxALL, 3);

    label = new wxStaticText(scrollWin, wxID_ANY, " Z ");
    lineSizer->Add(label, 1, wxALL | wxALIGN_CENTER, 3);

    txtTfPointZ = new wxTextCtrl(scrollWin, IDE_TF_POINT_Z, "", wxDefaultPosition,
      wxSize(10, -1), wxTE_PROCESS_ENTER);
    lineSizer->Add(txtTfPointZ, 2, wxALL, 3);

    sz->Add(lineSizer, 0, wxLEFT | wxRIGHT | wxEXPAND, 10);

    // ****************************************************************
    // Load the transfer function points from a file
    // ****************************************************************

    lineSizer = new wxBoxSizer(wxHORIZONTAL);

    chkMultiTFPts = new wxCheckBox(scrollWin, IDB_CHK_MULTI_TF_PTS,
      "Multiple transfer function points");
    lineSizer->Add(chkMultiTFPts, 1, wxGROW | wxALL, 3);

    buttonMultiTfPts = new wxButton(scrollWin, IDB_LOAD_TF_POINTS,
      "Load coordinates");
    lineSizer->Add(buttonMultiTfPts, 1, wxGROW | wxALL, 3);

    sz->Add(lineSizer, 0, wxLEFT | wxRIGHT | wxEXPAND, 10);

    topLevelSizer->Add(sz, 0, wxLEFT | wxRIGHT | wxEXPAND, 10);

    ///////////////////////////////////////////////////////////////////
    // Acoustic field computation options
    ///////////////////////////////////////////////////////////////////

    topLevelSizer->AddSpacer(10);
    sz = new wxStaticBoxSizer(wxVERTICAL, scrollWin, "Acoustic field options");

  // ****************************************************************
  // Select the physical quantity of the acoustic field to compute
  // ****************************************************************

    lineSizer = new wxBoxSizer(wxHORIZONTAL);

    label = new wxStaticText(scrollWin, wxID_ANY, "Physical quantity");
    lineSizer->Add(label, 2, wxALL | wxALIGN_CENTER, 3);

    lstFieldPhysicalQuantity = new wxComboBox(scrollWin, IDL_FIELD_PHYSICAL_QUANTITY, "", 
      wxDefaultPosition, this->FromDIP(wxSize(10, -1)), wxArrayString(), 
      wxCB_DROPDOWN | wxCB_READONLY);
    lineSizer->Add(lstFieldPhysicalQuantity, 1, wxALL, 3);

    lstAmpPhase = new wxComboBox(scrollWin, IDL_AMPLITUDE_PHASE, "", wxDefaultPosition,
      this->FromDIP(wxSize(10, -1)), wxArrayString(), wxCB_DROPDOWN | wxCB_READONLY);
    lineSizer->Add(lstAmpPhase, 1, wxALL, 3);

    sz->Add(lineSizer, 0, wxLEFT | wxRIGHT | wxEXPAND, 10);

  // ****************************************************************
  // Select the frequency and the resolution for field computation
  // ****************************************************************

  lineSizer = new wxBoxSizer(wxHORIZONTAL);

  label = new wxStaticText(scrollWin, wxID_ANY, "Frequency (Hz)");
  lineSizer->Add(label, 8, wxALL | wxALIGN_CENTER, 3);

  txtFreqComputeField = new wxTextCtrl(scrollWin, IDE_FREQ_COMPUTE_FIELD, "", wxDefaultPosition,
    wxSize(10, -1), wxTE_PROCESS_ENTER);
  lineSizer->Add(txtFreqComputeField, 3, wxALL, 3);

  lineSizer->AddStretchSpacer();

  label = new wxStaticText(scrollWin, wxID_ANY, "Resolution (points per cm)");
  lineSizer->Add(label, 8, wxALL | wxALIGN_CENTER, 3);

  txtResolutionField = new wxTextCtrl(scrollWin, IDE_RESOLUTION_FIELD, "", wxDefaultPosition,
    wxSize(10, -1), wxTE_PROCESS_ENTER);
  lineSizer->Add(txtResolutionField, 3, wxALL, 3);

  lineSizer->AddStretchSpacer();

  sz->Add(lineSizer, 0, wxLEFT | wxRIGHT | wxEXPAND, 10);

  // ****************************************************************
  // Set the bounding box to compute the acoustic field
  // ****************************************************************

  lineSizer = new wxBoxSizer(wxHORIZONTAL);

  label = new wxStaticText(scrollWin, wxID_ANY, "Min X ");
  lineSizer->Add(label, 1, wxALL | wxALIGN_CENTER, 3);

  txtBboxMinX = new wxTextCtrl(scrollWin, IDE_BBOX_MIN_X, "", wxDefaultPosition,
    wxSize(10, -1), wxTE_PROCESS_ENTER);
  lineSizer->Add(txtBboxMinX, 1, wxALL, 3);

  label = new wxStaticText(scrollWin, wxID_ANY, " max X ");
  lineSizer->Add(label, 1, wxALL | wxALIGN_CENTER, 3);

  txtBboxMaxX = new wxTextCtrl(scrollWin, IDE_BBOX_MAX_X, "", wxDefaultPosition,
    wxSize(10, -1), wxTE_PROCESS_ENTER);
  lineSizer->Add(txtBboxMaxX, 1, wxALL, 3);

  label = new wxStaticText(scrollWin, wxID_ANY, " min Y ");
  lineSizer->Add(label, 1, wxALL | wxALIGN_CENTER, 3);

  txtBboxMinY = new wxTextCtrl(scrollWin, IDE_BBOX_MIN_Y, "", wxDefaultPosition,
    wxSize(10, -1), wxTE_PROCESS_ENTER);
  lineSizer->Add(txtBboxMinY, 1, wxALL, 3);

  label = new wxStaticText(scrollWin, wxID_ANY, " max Y ");
  lineSizer->Add(label, 1, wxALL | wxALIGN_CENTER, 3);

  txtBboxMaxY = new wxTextCtrl(scrollWin, IDE_BBOX_MAX_Y, "", wxDefaultPosition,
    wxSize(10, -1), wxTE_PROCESS_ENTER);
  lineSizer->Add(txtBboxMaxY, 1, wxALL, 3);

  sz->Add(lineSizer, 0, wxLEFT | wxRIGHT | wxEXPAND, 10);

  // ****************************************************************
  // Set if the radiated field must be computed or not
  // ****************************************************************

  lineSizer = new wxBoxSizer(wxHORIZONTAL);

  chkComputeRad = new wxCheckBox(scrollWin, IDB_COMPUTE_RAD_FIELD,
    "Compute radiated field");
  chkComputeRad->SetValue(m_simuParams.computeRadiatedField);
  lineSizer->Add(chkComputeRad, 0, wxALL, 2);

  sz->Add(lineSizer, 0, wxLEFT | wxRIGHT, 10);

  topLevelSizer->Add(sz, 0, wxLEFT | wxRIGHT | wxEXPAND, 10);

  // ****************************************************************
  // Set the default parameters
  // ****************************************************************

  topLevelSizer->AddSpacer(10);
  topLevelSizer->Add(new wxStaticLine(scrollWin), 1, wxEXPAND | wxALL, 10);

  lineSizer = new wxBoxSizer(wxHORIZONTAL);

  button = new wxButton(scrollWin, IDB_SET_DEFAULT_PARAMS_FAST,
    "Default (fast)");
  lineSizer->Add(button, 1, wxALL, 3);

  button = new wxButton(scrollWin, IDB_SET_DEFAULT_PARAMS_ACCURATE,
    "Default (accurate)");
  lineSizer->Add(button, 1,  wxALL, 3);

  lineSizer->AddStretchSpacer();

  button = new wxButton(scrollWin, IDB_CLOSE, "Close");
  lineSizer->Add(button, 1,  wxALL, 3);

  topLevelSizer->Add(lineSizer, 0,  wxALL | wxEXPAND, 10);

  // ****************************************************************
  // Set the top-level-sizer for this window.
  // ****************************************************************

  // 把布局设置到滚动窗口
  scrollWin->SetSizer(topLevelSizer);
  scrollWin->FitInside();

  // 外层再放一个 sizer，用于填充滚动窗口
  wxBoxSizer* dlgSizer = new wxBoxSizer(wxVERTICAL);
  dlgSizer->Add(scrollWin, 1, wxEXPAND | wxALL, 0);
  this->SetSizerAndFit(dlgSizer);
  this->SetMinSize(wxSize(800, 900)); // 合理的最小尺寸，可根据需要调整
  this->Layout();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnTemperatureEnter(wxCommandEvent& event)
{
  double x = 0.0;
  wxString st = txtTemperature->GetValue();
  if ((st.ToDouble(&x)) && (x >= -300.0) && (x <= 300.0))
  {
    m_simuParams.temperature = x;

    // 依据介质计算声速 (m/s)
    double c_ms = vtl3d::soundSpeed(m_simuParams.temperature,
                                    static_cast<vtl3d::Medium>(m_simuParams.medium),
                                    m_simuParams.salinity,
                                    m_simuParams.depth);

    m_simuParams.sndSpeed = c_ms * 100.; // 转 cm/s

    // 仅在空气时更新体密度
    if (m_simuParams.medium == simulationParameters::AIR)
    {
        m_simuParams.volumicMass = STATIC_PRESSURE_CGS * MOLECULAR_MASS /
            (GAS_CONSTANT * (m_simuParams.temperature + KELVIN_SHIFT));
    }

    // 温度改变 ⇒ 需重新计算模式/辐射阻抗
    m_simuParams.needToComputeModesAndJunctions = true;
    m_simuParams.radImpedPrecomputed = false;
  }

  updateWidgets();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnSndSpeedEnter(wxCommandEvent& event)
{
  double x = 0.0;
  wxString st = txtSndSpeed->GetValue();
  if ((st.ToDouble(&x)) && (x >= 0.) && (x <= 10000.0))
  {
    m_simuParams.sndSpeed = x * 100.;

    switch (m_simuParams.medium)
    {
    case simulationParameters::AIR:
        // 空气：理想气体公式反推温度
        m_simuParams.volumicMass = ADIABATIC_CONSTANT * STATIC_PRESSURE_CGS /
            pow(m_simuParams.sndSpeed, 2);
        m_simuParams.temperature = pow(m_simuParams.sndSpeed, 2) * MOLECULAR_MASS /
            GAS_CONSTANT / ADIABATIC_CONSTANT - KELVIN_SHIFT;
        break;
    case simulationParameters::HELIUM:
        {
          // Helium:  c = sqrt(gamma * R_specific * (T+273.15))
          constexpr double gamma = 1.66;
          constexpr double Rspec = 2077.0; // J/kg/K
          double c_ms = m_simuParams.sndSpeed / 100.0;
          m_simuParams.temperature = (c_ms*c_ms)/(gamma*Rspec) - 273.15;
        }
        break;
    case simulationParameters::SEA:
        {
          // 近似用牛顿法迭代反求 T
          double S = m_simuParams.salinity;
          double Z = m_simuParams.depth;
          double c_target = m_simuParams.sndSpeed / 100.0;
          double T = m_simuParams.temperature; // 初值
          for(int i=0;i<10;++i)
          {
            double c_est = vtl3d::soundSpeedSea(T,S,Z);
            double f = c_est - c_target;
            if (std::abs(f) < 1e-6) break;
            // dC/dT (由公式求导)
            double dcdT = 4.591 - 2*0.05304*T + 3*0.0002374*T*T - 0.01025*(S-35.0) - 7.139e-13 * T * Z*Z*Z;
            if (std::abs(dcdT) < 1e-6) break;
            T -= f/dcdT;
          }
          m_simuParams.temperature = T;
        }
        break;
    }

    // 声速手动修改，同样触发重新计算标记
    m_simuParams.needToComputeModesAndJunctions = true;
    m_simuParams.radImpedPrecomputed = false;
  }

  updateWidgets();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnMeshDensityEnter(wxCommandEvent& event)
{
    double x = 0.0;
    wxString st = txtMeshDensity->GetValue();
    if ((st.ToDouble(&x)) && (x >= 1.0) && (x <= 50.0))
    {
      setMeshDensity(x);
    }

    updateWidgets();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnMaxCutOnEnter(wxCommandEvent& event)
{
    double x = 0.0;
    wxString st = txtMaxCutOnFreq->GetValue();
    if ((st.ToDouble(&x)) && (x >= 1.0) && (x <= 500000.0))
    {
      setMaxCutOnFreq(x);
    }

    updateWidgets();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnMaxSimFreq(wxCommandEvent& event)
{
    double x(0.);
    wxString st(txtMaxSimFreq->GetValue());
    if ((st.ToDouble(&x)) && (x >= 0.) && (x <= (double)SAMPLING_RATE))
    {
        m_simuParams.maxComputedFreq = x;
    }

    updateWidgets();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnNumIntegrationEnter(wxCommandEvent& event)
{
    double x = 0.0;
    wxString st = txtNumIntegrationStep->GetValue();
    if ((st.ToDouble(&x)) && (x > 0.) && (x <= 1000.))
    {
      m_simuParamsMagnus.numIntegrationStep = (int)x;
    }

    updateWidgets();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnSecNoiseSourceEnter(wxCommandEvent& event)
{
    double x(0.);
    wxString st = txtSecNoiseSource->GetValue();
    if ((st.ToDouble(&x)) && (x >= 0.) && (x <= 500.))
    {
        m_secNoiseSource = (int)x;
    }

    updateWidgets();
    updatePictures();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnPercentLosses(wxCommandEvent& event)
{
	double x(0.);
	wxString st = txtPercLoss->GetValue();
	if ((st.ToDouble(&x)) && (x >= 0.) && (x <= 100.))
	{
		m_simuParams.percentageLosses = x/100.;
	}

	updateWidgets();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnFreqComputeField(wxCommandEvent& event)
{
  double x(0.);
  wxString st = txtFreqComputeField->GetValue();
  if ((st.ToDouble(&x)) && (x >= 1.) && (x <= 20000.))
  {
    m_simuParams.freqField = x;
  }
  updateWidgets();
  updatePictures();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnResolutionField(wxCommandEvent& event)
{
  double x(0.);
  wxString st = txtResolutionField->GetValue();
  if ((st.ToDouble(&x)) && (x >= 1.) && (x <= 500.))
  {
    m_simuParams.fieldResolution = (int)x;
  }
  updateWidgets();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnBboxMinX(wxCommandEvent& event)
{
  double x(0.);
  wxString st = txtBboxMinX->GetValue();
  if ((st.ToDouble(&x)) && (x >= -m_maxBbox) && (x <= m_maxBbox))
  {
    m_simuParams.bbox[0] = Point(x, m_simuParams.bbox[0].y());
  }
  updateWidgets();
  updatePictures();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnBboxMinY(wxCommandEvent& event)
{
  double x(0.);
  wxString st = txtBboxMinY->GetValue();
  if ((st.ToDouble(&x)) && (x >= -m_maxBbox) && (x <= m_maxBbox))
  {
    m_simuParams.bbox[0] = Point(m_simuParams.bbox[0].x(), x);
  }
  updateWidgets();
  updatePictures();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnBboxMaxX(wxCommandEvent& event)
{
  double x(0.);
  wxString st = txtBboxMaxX->GetValue();
  if ((st.ToDouble(&x)) && (x >= -m_maxBbox) && (x <= m_maxBbox))
  {
    m_simuParams.bbox[1] = Point(x, m_simuParams.bbox[1].y());
  }
  updateWidgets();
  updatePictures();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnBboxMaxY(wxCommandEvent& event)
{
  double x(0.);
  wxString st = txtBboxMaxY->GetValue();
  if ((st.ToDouble(&x)) && (x >= -m_maxBbox) && (x <= m_maxBbox))
  {
    m_simuParams.bbox[1] = Point(m_simuParams.bbox[1].x(), x);
  }
  updateWidgets();
  updatePictures();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnTfPointX(wxCommandEvent& event)
{
  double x(0.);
  wxString st = txtTfPointX->GetValue();
  if ((st.ToDouble(&x)) && (x >= -100.) && (x <= 100.))
  {
    m_singlePtTf = Point_3(x, m_singlePtTf.y(), m_singlePtTf.z());
  }
  chkMultiTFPts->SetValue(false);
  updateWidgets();
  updatePictures();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnTfPointY(wxCommandEvent& event)
{
  double x(0.);
  wxString st = txtTfPointY->GetValue();
  if ((st.ToDouble(&x)) && (x >= -100.) && (x <= 100.))
  {
    m_singlePtTf = Point_3(m_singlePtTf.x(), x, m_singlePtTf.z());
  }
  chkMultiTFPts->SetValue(false);
  updateWidgets();
  updatePictures();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnTfPointZ(wxCommandEvent& event)
{
  double x(0.);
  wxString st = txtTfPointZ->GetValue();
  if ((st.ToDouble(&x)) && (x >= -100.) && (x <= 100.))
  {
    m_singlePtTf = Point_3(m_singlePtTf.x(), m_singlePtTf.y(), x);
  }
  chkMultiTFPts->SetValue(false);
  updateWidgets();
  updatePictures();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnLoadTfPts(wxCommandEvent& event)
{
  wxFileName fileName;
  wxString name = wxFileSelector("Import transfer function points as csv file", fileName.GetPath(),
  fileName.GetFullName(), ".csv", "Points file (*.csv)|*.csv",
  wxFD_OPEN | wxFD_FILE_MUST_EXIST, this);

  ofstream log("log.txt", ofstream::app);
  log << "Load tf points from file:" << endl;
  log << name.ToStdString() << endl;
  bool success = m_simu3d->setTFPointsFromCsvFile(name.ToStdString());
  if (success)
  {
    log << "Importation successfull" << endl;
    updateParams();
    updatePictures();
  }
  else
  {
    wxMessageDialog* dial = new wxMessageDialog(NULL,
      wxT("Error loading file"), wxT("Error"), wxOK | wxICON_ERROR);
    dial->ShowModal();

    log << "Importation failed" << endl;
  }
  log.close();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnWallAdmitEnter(wxCommandEvent& event)
{
  double re(0.), im(0.);
  wxString stRe = txtWallAdmitReal->GetValue();
  wxString stIm = txtWallAdmitImag->GetValue();
  if ((stRe.ToDouble(&re)) && (re >= -10000000.) && (re <= 10000000.)
    && (stIm.ToDouble(&im)) && (im >= -10000000.) && (im <= 10000000.))
  {
    m_simuParams.wallAdmit = complex<double>(re, im);
  }
  updateWidgets();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnChkFdepLosses(wxCommandEvent& event)
{
  m_simuParamsFreqDepLosses.viscoThermalLosses = !m_simuParamsFreqDepLosses.viscoThermalLosses;

	updateWidgets();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnChkWallLosses(wxCommandEvent& event)
{
  m_simuParamsFreqDepLosses.wallLosses = !m_simuParamsFreqDepLosses.wallLosses;
    
  updateWidgets();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnChkWallAdmittance(wxCommandEvent& event)
{
  m_simuParams.constantWallImped = !m_simuParams.constantWallImped;
  if (m_simuParams.constantWallImped)
  {
    m_simuParams.wallLosses = false;
    m_simuParams.viscoThermalLosses = false;
  }

  updateWidgets();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnChkStraight(wxCommandEvent& event)
{
  m_simuParams.propMethod = STRAIGHT_TUBES;
  m_simuParams.numIntegrationStep = 2;
	m_simuParams.curved = false;
  m_simuParams.varyingArea = false;

  // disable unrelevant option for straight
  chkCurv->Disable();
  chkVarArea->Disable();
  txtNumIntegrationStep->Disable();
  lstScalingFacMethods->Disable();
  txtPercLoss->Disable();
  chkWallLosses->Disable();
  chkWallAdmittance->Disable();

  updateWidgets();
  updateGeometry();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnChkMagnus(wxCommandEvent& event)
{
	m_simuParams.propMethod = MAGNUS;

  // Enable all the options in case they were disabled before
  chkCurv->Enable();
  chkVarArea->Enable();
  txtNumIntegrationStep->Enable();
  lstScalingFacMethods->Enable();
  txtPercLoss->Enable();
  chkWallLosses->Enable();
  chkWallAdmittance->Enable();

  updateWidgets();
  updateGeometry();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnChkCurv(wxCommandEvent& event)
{
  m_simuParamsMagnus.curved = !m_simuParamsMagnus.curved;
  updateWidgets();

  updateGeometry();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnChkVarArea(wxCommandEvent& event)
{
  //m_simuParams.propMethod = MAGNUS;
  m_simuParamsMagnus.varyingArea = !m_simuParamsMagnus.varyingArea;
  updateWidgets();

  updateGeometry();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnChkMultiTFPts(wxCommandEvent& event)
{
  m_tfPtsFromFile = !m_tfPtsFromFile;
  updateWidgets();
  updatePictures();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnChkComputeRad(wxCommandEvent& event)
{
  m_simuParams.computeRadiatedField = !m_simuParams.computeRadiatedField;
  updateWidgets();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnScalingFactMethod(wxCommandEvent& event)
{
  auto res = lstScalingFacMethods->GetSelection();

  switch (res)
  {
  case 0:
    m_contInterpMeth = AREA;
    break;
  case 1:
    m_contInterpMeth = BOUNDING_BOX;
    break;
  case 2:
    if (m_simu3d->isGeometryImported())
    {
      m_contInterpMeth = FROM_FILE;
    }
    else
    {
      lstScalingFacMethods->SetValue(m_listScalingMethods[1]);
    }
    break;
  }

  updateWidgets();
  updateGeometry();
}

// ****************************************************************************
// ****************************************************************************
void ParamSimu3DDialog::OnMouthBcond(wxCommandEvent& event)
{
  auto res = lstMouthBcond->GetSelection();

  switch (res)
  {
    case 0: m_mouthBoundaryCond = HARD_WALL; break;
    case 1: m_mouthBoundaryCond = ZERO_PRESSURE; break;
    case 2: m_mouthBoundaryCond = IFINITE_WAVGUIDE; break;
    case 3: m_mouthBoundaryCond = RADIATION; break;
    case 4: m_mouthBoundaryCond = ADMITTANCE_1; break;
    default: m_mouthBoundaryCond = HARD_WALL; break; // Default to Hard wall
  }

  updateWidgets();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnFreqRes(wxCommandEvent& event)
{
  auto res = lstFreqRes->GetSelection();

  m_simuParams.spectrumLgthExponent = m_expSpectrumLgthStart + res;

  updateWidgets();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnFieldPhysicalQuantity(wxCommandEvent& event)
{
  auto res = lstFieldPhysicalQuantity->GetSelection();

  switch (res)
  {
  case 0:
    m_simuParams.fieldPhysicalQuantity = PRESSURE;
    break;
  case 1:
    m_simuParams.fieldPhysicalQuantity = VELOCITY;
    // radiated velocity cannot be computed
    m_simuParams.computeRadiatedField = false;
    break;
  default:
    m_simuParams.fieldPhysicalQuantity = PRESSURE;
    break;
  }

  updateWidgets();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnAmplitudePhase(wxCommandEvent& event)
{
  bool showAmplitude;
  bool fieldIndB;
  auto res = lstAmpPhase->GetSelection();

  
  switch (res)
  {
  case 0:
    showAmplitude = true;
    fieldIndB = true;
    break;
  case 1:
    showAmplitude = false;
    fieldIndB = false;
    break;
  }

  if (showAmplitude != m_simuParams.showAmplitude)
  {
    m_simuParams.showAmplitude = showAmplitude;
    m_simuParams.fieldIndB = fieldIndB;
    m_simuParams.computeFieldImage = true;
    updateWidgets();
    updatePictures();
  }
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnSetDefaultParamsFast(wxCommandEvent& event)
{
  SetDefaultParams(true);
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnSetDefaultParamsAccurate(wxCommandEvent& event)
{
  SetDefaultParams(false);
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::SetDefaultParams(bool fast)
{
  // for fast computations, but very innacurate
  if (fast)
  {
    setMeshDensity(5.);

    setMaxCutOnFreq(20000.);

    m_simuParams.maxComputedFreq = 10000.;

    // for about 40 Hz resolution
    m_simuParams.spectrumLgthExponent = m_expSpectrumLgthStart + 2;
  }
  else
  {
    setMeshDensity(15.);

    setMaxCutOnFreq(40000.);

    m_simuParams.maxComputedFreq = 20000.;

    // for about 10 Hz resolution
    m_simuParams.spectrumLgthExponent = m_expSpectrumLgthStart + 4;
  }

  m_simuParams.sndSpeed = 35000.;
  m_simuParams.volumicMass = ADIABATIC_CONSTANT * STATIC_PRESSURE_CGS /
    pow(m_simuParams.sndSpeed, 2);
  m_simuParams.temperature = pow(m_simuParams.sndSpeed, 2) * MOLECULAR_MASS /
    GAS_CONSTANT / ADIABATIC_CONSTANT - KELVIN_SHIFT;

  m_simuParams.propMethod = MAGNUS;

  m_simuParams.curved = true;

  m_simuParams.varyingArea = true;

  m_mouthBoundaryCond = HARD_WALL;
  m_glottisBoundaryCond = HARD_WALL;

  m_simuParams.percentageLosses = 1.;

  m_simuParams.wallLosses = false;

  m_simuParams.viscoThermalLosses = false;

  m_simuParams.thermalBndSpecAdm = complex<double>(0.005, 0.);

  m_secNoiseSource = 25;

  m_simuParams.tfPoint.clear();
  m_simuParams.tfPoint.push_back(Point_3(100., 0., 0.));
  chkMultiTFPts->SetValue(false);

  m_simuParams.freqField = 5000.;

  m_simuParams.fieldResolution = 30;

  m_simuParams.computeRadiatedField = false;

  updateWidgets();
  updateGeometry();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnClose(wxCommandEvent& event)
{
  this->Close();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::setMeshDensity(double density)
{
  // if the mesh density is modified, 
  // the modes and the radiation impedance must be computed
  if (density != m_meshDensity)
  {
    m_simuParams.needToComputeModesAndJunctions = true;
    m_simuParams.radImpedPrecomputed = false;
    m_meshDensity = density;
  }
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::setMaxCutOnFreq(double freq)
{
  // if the maximal cut off frequency is modified,
  // the modes and the radiation impedance must be computed
  if (freq != m_simuParams.maxCutOnFreq)
  {
    m_simuParams.needToComputeModesAndJunctions = true;
    m_simuParams.radImpedPrecomputed = false;
    m_simuParams.maxCutOnFreq = freq;
  }
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnMediumSelect(wxCommandEvent& event)
{
  int sel = lstMedium->GetSelection();
  switch(sel)
  {
  case 0:
    m_simuParams.medium = simulationParameters::AIR;
    break;
  case 1:
    m_simuParams.medium = simulationParameters::SEA;
    break;
  case 2:
    m_simuParams.medium = simulationParameters::HELIUM;
    break;
  default:
    m_simuParams.medium = simulationParameters::AIR;
    break;
  }

  // 重新计算声速
  double c_ms = vtl3d::soundSpeed(m_simuParams.temperature,
                                  static_cast<vtl3d::Medium>(m_simuParams.medium),
                                  m_simuParams.salinity,
                                  m_simuParams.depth);
  m_simuParams.sndSpeed = c_ms * 100.0;

  // 若空气则更新体密度
  if (m_simuParams.medium == simulationParameters::AIR)
  {
    m_simuParams.volumicMass = STATIC_PRESSURE_CGS * MOLECULAR_MASS /
      (GAS_CONSTANT * (m_simuParams.temperature + KELVIN_SHIFT));
  }

  // 介质切换后必须强制重新计算
  m_simuParams.needToComputeModesAndJunctions = true;
  m_simuParams.radImpedPrecomputed = false;

  updateWidgets();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnSalinityEnter(wxCommandEvent& event)
{
  double x = 0.0;
  wxString st = txtSalinity->GetValue();
  if ((st.ToDouble(&x)) && (x >= 0.) && (x <= 60.))
  {
    m_simuParams.salinity = x;
  }

  // 若为海水则更新声速
  if (m_simuParams.medium == simulationParameters::SEA)
  {
    double c_ms = vtl3d::soundSpeed(m_simuParams.temperature,
                                    vtl3d::Medium::Sea,
                                    m_simuParams.salinity,
                                    m_simuParams.depth);
    m_simuParams.sndSpeed = c_ms * 100.0;
  }

  m_simuParams.needToComputeModesAndJunctions = true;
  m_simuParams.radImpedPrecomputed = false;

  updateWidgets();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnDepthEnter(wxCommandEvent& event)
{
  double x = 0.0;
  wxString st = txtDepth->GetValue();
  if ((st.ToDouble(&x)) && (x >= 0.) && (x <= 11000.))
  {
    m_simuParams.depth = x;
  }

  if (m_simuParams.medium == simulationParameters::SEA)
  {
    double c_ms = vtl3d::soundSpeed(m_simuParams.temperature,
                                    vtl3d::Medium::Sea,
                                    m_simuParams.salinity,
                                    m_simuParams.depth);
    m_simuParams.sndSpeed = c_ms * 100.0;
  }

  m_simuParams.needToComputeModesAndJunctions = true;
  m_simuParams.radImpedPrecomputed = false;

  updateWidgets();
}

// ****************************************************************************
// ****************************************************************************

void ParamSimu3DDialog::OnGlottisBcond(wxCommandEvent &event)
{
  // 根据下拉框索引映射到枚举值
  int idx = lstGlottisBcond->GetCurrentSelection();

  switch (idx)
  {
    case 0: m_glottisBoundaryCond = HARD_WALL; break;
    case 1: m_glottisBoundaryCond = ZERO_PRESSURE; break;
    case 2: m_glottisBoundaryCond = IFINITE_WAVGUIDE; break;
    case 3: m_glottisBoundaryCond = RADIATION; break;
    case 4: m_glottisBoundaryCond = ADMITTANCE_1; break;
    default: m_glottisBoundaryCond = HARD_WALL; break; // Default to Hard wall
  }

  // 将更新写入核心模拟器
  m_simu3d->setSimulationParameters(
    m_meshDensity,
    m_secNoiseSource,
    m_simuParams,
    m_mouthBoundaryCond,
    m_contInterpMeth,
    m_glottisBoundaryCond);

  updateWidgets();
  updatePictures();
}
