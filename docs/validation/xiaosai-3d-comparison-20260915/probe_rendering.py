"""Diagnostic renders for the local XiaoSai comparison; does not change app defaults.

Run on a native desktop with a single CT series/phase and an output directory.
See README.md for the reference capture protocol and comparison limits.
"""
import argparse
from pathlib import Path
from dataclasses import replace
import json, math
import numpy as np
from PySide6.QtWidgets import QApplication
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkRenderingCore import vtkWindowToImageFilter
from vtkmodules.vtkIOImage import vtkPNGWriter
from qt_dicom_viewer.core.dicom_scanner import _read_instance,_build_series_record
from qt_dicom_viewer.core.volume_manager import VolumeManager
from qt_dicom_viewer.core.volume_view import VolumeViewState,drag_volume_window,face_rotation
from qt_dicom_viewer.model.volume_models import VolumeDisplayState
from qt_dicom_viewer.volume_presets import VOLUME_PRESET_BY_ID
from qt_dicom_viewer.ui.volume_render_backend import VolumeRenderBackend

class Widget(QVTKRenderWindowInteractor):
 def paintEvent(self,event):pass
class ProbeBackend(VolumeRenderBackend):
 camera_distance_factor=None
 def apply_state(self,state):
  super().apply_state(state)
  camera=self.renderer.GetActiveCamera()
  camera.SetParallelProjection(self.camera_distance_factor is None)
  if self.camera_distance_factor is not None:
   focus=np.array(camera.GetFocalPoint());offset=np.array(camera.GetPosition())-focus
   offset*=self.camera_distance_factor
   camera.SetPosition(*(focus+offset))
   camera.SetViewAngle(math.degrees(2*math.atan(camera.GetParallelScale()/np.linalg.norm(offset))))
   self.renderer.ResetCameraClippingRange()

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('dicom_dir',type=Path)
parser.add_argument('output_dir',type=Path)
args=parser.parse_args()
root=args.output_dir;root.mkdir(parents=True,exist_ok=True)
p=args.dicom_dir
s=_build_series_record([_read_instance(f) for f in sorted(p.glob('*.dcm'))]);v=VolumeManager().get_or_build(s)
app=QApplication([]);w=Widget();w.resize(850,700);w.show();app.processEvents()
b=ProbeBackend(w);b.set_volume(v)
base=VolumeDisplayState('aaa',VOLUME_PRESET_BY_ID['aaa'].default_window)
log={}
def capture(name,display=base,state=VolumeViewState()):
 b.render(state,False,display);app.processEvents()
 grab=vtkWindowToImageFilter();grab.SetInput(b.window);grab.ReadFrontBufferOff();grab.Update()
 writer=vtkPNGWriter();writer.SetFileName(str(root/(name+'.png')));writer.SetInputData(grab.GetOutput());writer.Write()
 log[name]={'window':[display.window.center,display.window.width],'parallel':bool(b.renderer.GetActiveCamera().GetParallelProjection()),'sample_mm':b.mapper.GetSampleDistance(),'jitter':bool(b.mapper.GetUseJittering())}
 print(name,log[name],flush=True)
try:
 capture('aaa')
 for name,delta in [('up',(0,-70)),('down',(0,70)),('right',(85,0)),('left',(-85,0))]:
  capture('aaa-window-'+name,replace(base,window=drag_volume_window(base.window,delta,(850,700))))
 for factor in [1,.75,.5]:
  b.camera_distance_factor=factor;capture('aaa-perspective-'+str(factor))
 b.camera_distance_factor=None
 b.mapper.SetSampleDistance(b._sample_distance/2);capture('aaa-half-step')
 b.mapper.SetSampleDistance(b._sample_distance/4);capture('aaa-quarter-step')
 b.mapper.SetSampleDistance(b._sample_distance);b.mapper.UseJitteringOn();capture('aaa-jitter')
 b.mapper.SetSampleDistance(b._sample_distance/2);capture('aaa-half-step-jitter')
 b.mapper.SetSampleDistance(b._sample_distance);b.mapper.UseJitteringOff()
 capture('aaa-left',state=VolumeViewState(rotation=face_rotation('L')))
finally:
 b.dispose();w.close()
(root/'probe-settings.json').write_text(json.dumps(log,indent=2))
