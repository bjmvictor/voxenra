"""PYTHONPATH=src python capture_viewer.py COMPARISON_ROOT (native Qt/OpenGL)."""
import gc
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback
import numpy as np
from PySide6.QtWidgets import QApplication
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkRenderingCore import vtkWindowToImageFilter
from vtkmodules.vtkIOImage import vtkPNGWriter
from vtkmodules.util.numpy_support import vtk_to_numpy
from qt_dicom_viewer.core.dicom_scanner import _read_instance, _build_series_record
from qt_dicom_viewer.core.volume_manager import VolumeManager
from qt_dicom_viewer.core.volume_view import VolumeViewState
from qt_dicom_viewer.model import WindowLevel
from qt_dicom_viewer.model.volume_models import VolumeDisplayState
from qt_dicom_viewer.ui.volume_render_backend import VolumeRenderBackend


class CaptureWidget(QVTKRenderWindowInteractor):
    def paintEvent(self,event):
        pass


root=Path(sys.argv[1])
manifest=json.loads((root/'manifest.json').read_text())
reference=json.loads((root/'reference.json').read_text())
report=json.loads((root/'viewer.json').read_text()) if (root/'viewer.json').exists() else {}
app=QApplication([])
failed=False
for case in manifest['cases']:
    if os.environ.get('COMPARISON_CASE') and case['id'] != os.environ['COMPARISON_CASE']:
        continue
    if 'error' in case:
        report[case['id']]={'error':case['error']}
        continue
    if not reference['cases'].get(case['id'],{}).get('voxels_identical'):
        report[case['id']]={'error':'Slicer voxel comparison did not pass'}
        continue
    backend=widget=None
    try:
        print('VIEWER_LOAD',case['id'],flush=True)
        instances=[_read_instance(Path(p)) for p in case['files']]
        volume=VolumeManager().get_or_build(_build_series_record(instances))
        assert hashlib.sha256(volume.modality_pixels.tobytes()).hexdigest()==case['sha256']
        widget=CaptureWidget()
        ratio=widget.devicePixelRatioF()
        widget.resize(*(round(v/ratio) for v in manifest['size']))
        widget.show();app.processEvents()
        backend=VolumeRenderBackend(widget)
        backend.set_volume(volume)
        if os.environ.get('DIAGNOSTIC_SAMPLE_DIVISOR'):
            backend._sample_distance = min(volume.geometry.column_spacing,volume.geometry.row_spacing,volume.geometry.slice_spacing)/float(os.environ['DIAGNOSTIC_SAMPLE_DIVISOR'])
            backend.mapper.SetSampleDistance(backend._sample_distance)
        output=root/'viewer'/case['id'];output.mkdir(parents=True,exist_ok=True)
        info={'renders':{}};report[case['id']]=info
        for preset in case['presets']:
            display=VolumeDisplayState(preset['id'],WindowLevel(*preset['window']))
            for face,parameters in case['cameras'].items():
                print('VIEWER_RENDER',case['id'],preset['id'],face,backend._sample_distance,flush=True)
                state=VolumeViewState(rotation=tuple(parameters['rotation']))
                times=[]
                for _ in range(4):
                    start=time.perf_counter();backend.render(state,False,display)
                    times.append((time.perf_counter()-start)*1000)
                grab=vtkWindowToImageFilter();grab.SetInput(backend.window);grab.ReadFrontBufferOff();grab.Update()
                assert list(grab.GetOutput().GetDimensions()[:2])==manifest['size']
                name=preset['id']+'-'+face
                writer=vtkPNGWriter();writer.SetFileName(str(output/(name+'.png')))
                writer.SetInputData(grab.GetOutput());writer.Write()
                settled=vtk_to_numpy(grab.GetOutput().GetPointData().GetScalars()).copy()
                backend.render(state,True,display)
                grab.Modified();grab.Update()
                interactive=vtk_to_numpy(grab.GetOutput().GetPointData().GetScalars())
                assert np.array_equal(settled,interactive), 'Interaction changes render quality'
                info['renders'][name]={'median_ms':float(np.median(times[1:])),
                    'sample_mm':backend.mapper.GetSampleDistance(), 'interactive_pixels_identical':True}
                (root/'viewer.json').write_text(json.dumps(report,indent=2)+'\n')
        assert hashlib.sha256(volume.modality_pixels.tobytes()).hexdigest()==case['sha256']
        print('VIEWER_DONE',case['id'],len(info['renders']),flush=True)
    except Exception as error:
        failed=True
        report.setdefault(case['id'],{})['error']=str(error)
        traceback.print_exc()
    finally:
        if backend is not None: backend.dispose()
        if widget is not None: widget.close()
    (root/'viewer.json').write_text(json.dumps(report,indent=2)+'\n')
    gc.collect()
sys.exit(1 if failed else 0)
