"""Prepare a local comparison manifest from a list of {id, files, presets}.

Run with PYTHONPATH=src. Reads through the production loader; writes no DICOM or
patient tags. The manifest contains local source paths and must remain untracked.
"""
import gc
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from qt_dicom_viewer.core.dicom_scanner import _read_instance, _build_series_record
from qt_dicom_viewer.core.volume_manager import VolumeManager
from qt_dicom_viewer.core.volume_view import VolumeViewState, face_rotation, rotate_drag, camera_parameters
from qt_dicom_viewer.volume_presets import VOLUME_PRESET_BY_ID

root = Path(sys.argv[2])
root.mkdir(parents=True, exist_ok=True)
manifest = {'size': [1238, 928], 'cases': []}
states = {'A': VolumeViewState(), 'L': VolumeViewState(rotation=face_rotation('L')),
          'oblique': rotate_drag(VolumeViewState(), (500, 500), (640, 420), (1000, 1000))}
for case in json.loads(Path(sys.argv[1]).read_text()):
    try:
        instances = [_read_instance(Path(p)) for p in case['files']]
        assert len({i.series_instance_uid for i in instances}) == 1
        volume = VolumeManager().get_or_build(_build_series_record(instances))
        pixels = volume.modality_pixels
        case['shape_kji'] = list(pixels.shape)
        case['ijk_to_lps'] = volume.geometry.voxel_to_patient[:, [2, 1, 0, 3]].tolist()
        case['spacing'] = [volume.geometry.column_spacing, volume.geometry.row_spacing, volume.geometry.slice_spacing]
        case['range'] = [float(np.nanmin(pixels)), float(np.nanmax(pixels))]
        case['nan_count'] = int(np.isnan(pixels).sum())
        assert case['nan_count'] == 0, 'Padding comparison needs an explicit mask protocol'
        case['sha256'] = hashlib.sha256(np.ascontiguousarray(pixels, dtype=np.float32).tobytes()).hexdigest()
        case['modality'] = instances[0].modality
        case['cameras'] = {}
        for name, state in states.items():
            camera = camera_parameters(volume.geometry, state, manifest['size'])
            case['cameras'][name] = {key: np.asarray(value).tolist() for key, value in camera.items()}
            case['cameras'][name]['rotation'] = list(state.rotation)
        records = []
        for preset_id, slicer_name in case['presets']:
            preset = VOLUME_PRESET_BY_ID[preset_id]
            window = preset.default_window or volume.default_window
            if preset_id == 'mr-mip':
                from qt_dicom_viewer.model import WindowLevel
                lo, hi = case['range']
                window = WindowLevel((lo+hi)/2, max(.001, hi-lo))
            low = window.center-window.width/2
            records.append({'id': preset_id, 'slicer_name': slicer_name,
                'window': [window.center, window.width],
                'colors': [[low+window.width*t,r,g,b] for t,r,g,b in preset.colors],
                'opacity': [[low+window.width*t,a] for t,a in preset.opacity],
                'shade': preset.shade, 'ambient': preset.ambient, 'diffuse': preset.diffuse,
                'specular': preset.specular, 'specular_power': preset.specular_power,
                'opacity_unit_distance': preset.opacity_unit_distance,
                'mip': preset_id.endswith('mip')})
        case['presets'] = records
        print(case['id'], case['modality'], pixels.shape, case['spacing'], case['range'], flush=True)
        del pixels, volume
        gc.collect()
    except Exception as error:
        case['error'] = str(error)
        print(case['id'], 'ERROR', str(error), flush=True)
    manifest['cases'].append(case)
(root/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
