"""Run with Slicer --python-script; set SLICER_DICOM_DIR and SLICER_CAPTURE_ROOT.

Uses the installed Slicer DICOM loader and GPU rendering pipeline. Outputs contain
anatomy: keep the output folder local. Run in a separate application instance,
which is closed on completion; existing Slicer scenes are not touched.
"""
import hashlib
import json
import os
from pathlib import Path
import traceback

import numpy as np
import slicer
import vtk


def run():
    from DICOMScalarVolumePlugin import DICOMScalarVolumePluginClass

    root = Path(os.environ['SLICER_CAPTURE_ROOT'])
    root.mkdir(parents=True, exist_ok=True)
    files = sorted(str(p) for p in Path(os.environ['SLICER_DICOM_DIR']).glob('*.dcm'))
    volume = DICOMScalarVolumePluginClass().loadFilesWithSeriesReader('GDCM', files, 'Local CT comparison')
    logic = slicer.modules.volumerendering.logic()
    logic.SetDefaultRenderingMethod('vtkMRMLGPURayCastVolumeRenderingDisplayNode')
    display = logic.CreateDefaultVolumeRenderingNodes(volume)
    display.SetVisibility(True)
    slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUp3DView)
    view = slicer.app.layoutManager().threeDWidget(0).threeDView()
    node = view.mrmlViewNode()
    node.SetBoxVisible(False)
    node.SetAxisLabelsVisible(False)
    node.SetBackgroundColor(2/255, 7/255, 14/255)
    node.SetBackgroundColor2(2/255, 7/255, 14/255)
    slicer.app.processEvents()
    renderer = view.renderWindow().GetRenderers().GetFirstRenderer()
    camera = renderer.GetActiveCamera()
    matrix = vtk.vtkMatrix4x4()
    volume.GetIJKToRASMatrix(matrix)
    dims = volume.GetImageData().GetDimensions()
    center = np.array(matrix.MultiplyPoint([(d-1)/2 for d in dims]+[1])[:3])
    spacing = volume.GetSpacing()
    radius = np.linalg.norm((np.array(dims)-1)*spacing)/2
    size = view.renderWindow().GetSize()
    scale = radius*1.1*max(1, size[1]/size[0])
    # MRML updates otherwise overwrite the direct VTK camera projection.
    node.SetRenderMode(node.Orthographic)
    node.SetFieldOfView(scale)
    camera.SetParallelProjection(True)
    camera.SetFocalPoint(*center)
    camera.SetPosition(*(center+[0, 4*radius, 0]))
    camera.SetViewUp(0, 0, 1)
    camera.SetParallelScale(scale)
    camera.SetClippingRange(radius, 7*radius)
    array = slicer.util.arrayFromVolume(volume)
    info = {
        'version': slicer.app.applicationVersion,
        'revision': slicer.app.repositoryRevision,
        'vtk': vtk.vtkVersion.GetVTKVersion(),
        'dimensions': dims,
        'spacing': spacing,
        'ijk_to_ras': [[matrix.GetElement(r, c) for c in range(4)] for r in range(4)],
        'range': [float(array.min()), float(array.max())],
        'sha256': hashlib.sha256(np.ascontiguousarray(array, dtype=np.float32).tobytes()).hexdigest(),
        'size': size,
        'camera': {'focal': center.tolist(), 'position': camera.GetPosition(),
                   'up': camera.GetViewUp(), 'scale': scale},
        'default_quality': node.GetVolumeRenderingQuality(),
        'surface_smoothing': node.GetVolumeRenderingSurfaceSmoothing(),
        'oversampling_factor': node.GetVolumeRenderingOversamplingFactor(),
        'renders': {},
    }

    def capture(name):
        slicer.app.processEvents()
        view.renderWindow().Render()
        volumes = renderer.GetVolumes()
        volumes.InitTraversal()
        actor = volumes.GetNextVolume()
        mapper, prop = actor.GetMapper(), actor.GetProperty()
        lights = renderer.GetLights()
        lights.InitTraversal()
        lighting = []
        for _ in range(lights.GetNumberOfItems()):
            light = lights.GetNextItem()
            lighting.append({
                'type': light.GetLightType(), 'intensity': light.GetIntensity(),
                'position': light.GetPosition(), 'focal': light.GetFocalPoint(),
                'color': light.GetDiffuseColor(),
            })
        info['renders'][name] = {
            'parallel': camera.GetParallelProjection(), 'scale': camera.GetParallelScale(),
            'position': camera.GetPosition(), 'focal': camera.GetFocalPoint(),
            'sample': mapper.GetSampleDistance(), 'lock_spacing': mapper.GetLockSampleDistanceToInputSpacing(),
            'jitter': mapper.GetUseJittering(), 'auto_adjust': mapper.GetAutoAdjustSampleDistances(),
            'opacity_unit_distance': prop.GetScalarOpacityUnitDistance(),
            'ambient': prop.GetAmbient(), 'diffuse': prop.GetDiffuse(),
            'specular': prop.GetSpecular(), 'lights': lighting,
        }
        grab = vtk.vtkWindowToImageFilter()
        grab.SetInput(view.renderWindow())
        grab.ReadFrontBufferOff()
        grab.Update()
        writer = vtk.vtkPNGWriter()
        writer.SetFileName(str(root/(name+'.png')))
        writer.SetInputData(grab.GetOutput())
        writer.Write()
        print('CAPTURE', name, info['renders'][name], flush=True)

    for preset in ['CT-AAA', 'CT-Bone', 'CT-Muscle', 'CT-Lung', 'CT-Coronary-Arteries-3']:
        display.GetVolumePropertyNode().Copy(logic.GetPresetByName(preset))
        node.SetVolumeRenderingQuality(node.Normal)
        capture(preset+'-normal')
        node.SetVolumeRenderingQuality(node.Maximum)
        capture(preset+'-maximum')

    # Apply the reference formula to native Slicer transfer functions, then
    # render them. This controlled experiment does not simulate UI events.
    info['window_cases'] = {}
    for name, delta in [('up', (0, -.1)), ('down', (0, .1)), ('right', (.1, 0)), ('left', (-.1, 0))]:
        display.GetVolumePropertyNode().Copy(logic.GetPresetByName('CT-AAA'))
        prop = display.GetVolumePropertyNode().GetVolumeProperty()
        opacity = prop.GetScalarOpacity()
        pivot = sum(opacity.GetRange())/2
        shift = -delta[1]*size[1]*(info['range'][1]-info['range'][0])*.5/min(size)
        factor = 1+delta[0]*size[0]*.5/min(size)
        for function, length in [(opacity, 4), (prop.GetRGBTransferFunction(), 6)]:
            points = []
            for i in range(function.GetSize()):
                point = [0.0]*length
                function.GetNodeValue(i, point)
                point[0] = pivot+(point[0]-pivot)*factor+shift
                points.append(point)
            function.RemoveAllPoints()
            for point in points:
                if length == 4:
                    function.AddPoint(*point)
                else:
                    function.AddRGBPoint(*point)
        info['window_cases'][name] = {'shift': shift, 'factor': factor, 'pivot': pivot}
        capture('CT-AAA-window-'+name)
    (root/'settings.json').write_text(json.dumps(info, indent=2)+'\n')
    print('CAPTURE_COMPLETE', flush=True)


status = 0
try:
    run()
except Exception:
    traceback.print_exc()
    status = 1
finally:
    slicer.app.exit(status)
