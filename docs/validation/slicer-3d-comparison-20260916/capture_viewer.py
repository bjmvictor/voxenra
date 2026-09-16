"""Capture the current viewer and the previous rendering configuration.

PYTHONPATH=src python capture_viewer.py DICOM_DIR REFERENCE_DIR OUTPUT_DIR
Reference captures and settings.json come from capture_slicer.py.
Output contains anatomy and must remain local.
"""
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from PySide6.QtWidgets import QApplication
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkRenderingCore import vtkWindowToImageFilter
from vtkmodules.vtkIOImage import vtkPNGWriter

from qt_dicom_viewer.core.dicom_scanner import _read_instance, _build_series_record
from qt_dicom_viewer.core.volume_manager import VolumeManager
from qt_dicom_viewer.core.volume_view import VolumeViewState, drag_volume_window
from qt_dicom_viewer.model.volume_models import VolumeDisplayState
from qt_dicom_viewer.ui.volume_render_backend import VolumeRenderBackend, volume_to_vtk
from qt_dicom_viewer.volume_presets import VOLUME_PRESET_BY_ID


class CaptureWidget(QVTKRenderWindowInteractor):
    def paintEvent(self, event):
        pass  # Avoid reentrant Cocoa rendering; matches VolumeInteractor.


class PreviousBackend(VolumeRenderBackend):
    def set_volume(self, volume):
        super().set_volume(volume)
        self._image, self._pixels = volume_to_vtk(volume)
        self.actor.SetUserMatrix(None)
        self.mapper.SetInputData(self._image)
        self._sample_distance *= 4
        self.mapper.SetSampleDistance(self._sample_distance)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dicom_dir', type=Path)
    parser.add_argument('reference_dir', type=Path)
    parser.add_argument('output_dir', type=Path)
    args = parser.parse_args()
    reference = json.loads((args.reference_dir/'settings.json').read_text())
    instances = [_read_instance(p) for p in sorted(args.dicom_dir.glob('*.dcm'))]
    assert len({i.series_instance_uid for i in instances}) == 1
    volume = VolumeManager().get_or_build(_build_series_record(instances))
    digest = hashlib.sha256(np.ascontiguousarray(volume.modality_pixels, dtype=np.float32).tobytes()).hexdigest()
    assert digest == reference['sha256'], 'Voxel buffers differ from the Slicer input'
    app = QApplication([])
    widget = CaptureWidget()
    ratio = widget.devicePixelRatioF()
    width, height = reference['size']
    widget.resize(round(width/ratio), round(height/ratio))
    widget.show()
    app.processEvents()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    measurements = {'sha256': digest, 'renders': {}}
    for label, backend_class in [('before', PreviousBackend), ('after', VolumeRenderBackend)]:
        backend = backend_class(widget)
        backend.set_volume(volume)
        def capture(name, display):
            elapsed = []
            for _ in range(4):
                start = time.perf_counter()
                backend.render(VolumeViewState(), False, display)
                elapsed.append((time.perf_counter()-start)*1000)
            grab = vtkWindowToImageFilter()
            grab.SetInput(backend.window)
            grab.ReadFrontBufferOff()
            grab.Update()
            assert grab.GetOutput().GetDimensions()[:2] == (width, height)
            writer = vtkPNGWriter()
            writer.SetFileName(str(args.output_dir/(label+'-'+name+'.png')))
            writer.SetInputData(grab.GetOutput())
            writer.Write()
            measurements['renders'][label+'-'+name] = {
                'median_ms': float(np.median(elapsed[1:])),
                'sample_mm': backend.mapper.GetSampleDistance(),
                'wl': display.window.center, 'ww': display.window.width,
            }
        for name in ['aaa', 'bones', 'muscle', 'lung2', 'carotid']:
            capture(name, VolumeDisplayState(name, VOLUME_PRESET_BY_ID[name].default_window))
        if label == 'after':
            preset = VOLUME_PRESET_BY_ID['aaa']
            base = VolumeDisplayState('aaa', preset.default_window)
            for name, delta in [('up',(0,-.1)),('down',(0,.1)),('right',(.1,0)),('left',(-.1,0))]:
                window = drag_volume_window(base.window, (delta[0]*width, delta[1]*height), (width,height),
                    scalar_range=reference['range'][1]-reference['range'][0],
                    opacity_range=tuple(p[0] for p in preset.opacity))
                capture('aaa-window-'+name, replace(base, window=window))
        backend.dispose()
        # dispose finalizes the QVTK window; use a fresh widget for the next run.
        widget.close()
        if label == 'before':
            widget = CaptureWidget()
            widget.resize(round(width/ratio), round(height/ratio))
            widget.show()
            app.processEvents()
    (args.output_dir/'settings.json').write_text(json.dumps(measurements, indent=2)+'\n')
    print(json.dumps(measurements, indent=2))


if __name__ == '__main__':
    main()
