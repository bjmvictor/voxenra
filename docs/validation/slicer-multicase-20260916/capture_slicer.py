"""Slicer --python-script; COMPARISON_ROOT points to a local prepared manifest.

Uses independent Slicer DICOM decoding. CT uses native Slicer presets; MR records
both matching viewer curves and the native MR-Default appearance separately.
"""
import gc
import hashlib
import json
import os
from pathlib import Path
import traceback
import numpy as np
import slicer
import pydicom
import vtk

root = Path(os.environ['COMPARISON_ROOT'])
manifest = json.loads((root/'manifest.json').read_text())
report = json.loads((root/'reference.json').read_text()) if (root/'reference.json').exists() else {'version': slicer.app.applicationVersion, 'vtk': vtk.vtkVersion.GetVTKVersion(), 'cases': {}}


def capture_case(case):
    from DICOMScalarVolumePlugin import DICOMScalarVolumePluginClass
    slicer.mrmlScene.Clear(0)
    # Same geometric ordering as DICOMUtils.getSortedImageFiles; no DB import
    # is needed for the isolated capture instance. Filenames are not slice order.
    headers = [(p,pydicom.dcmread(p,stop_before_pixels=True,specific_tags=['ImageOrientationPatient','ImagePositionPatient'])) for p in case['files']]
    orientation=np.asarray(headers[0][1].ImageOrientationPatient,dtype=float).reshape(2,3)
    normal=np.cross(*orientation)
    ordered_files=[p for p,d in sorted(headers,key=lambda pair:np.dot(np.asarray(pair[1].ImagePositionPatient,dtype=float),normal))]
    print('LOAD',case['id'],len(ordered_files),flush=True)
    volume = DICOMScalarVolumePluginClass().loadFilesWithSeriesReader(os.environ.get('DICOM_READER','GDCM'), ordered_files, 'Local comparison')
    print('LOADED',case['id'],flush=True)
    assert volume is not None and volume.GetImageData() is not None
    matrix = vtk.vtkMatrix4x4()
    volume.GetIJKToRASMatrix(matrix)
    ras = np.array([[matrix.GetElement(i,j) for j in range(4)] for i in range(4)])
    lps = np.diag([-1,-1,1,1]) @ ras
    pixels = slicer.util.arrayFromVolume(volume)
    info = {'dimensions':volume.GetImageData().GetDimensions(), 'spacing':volume.GetSpacing(),
            'ijk_to_lps':lps.tolist(), 'range':[float(pixels.min()),float(pixels.max())], 'reference_quality':'Normal' if case.get('modality')=='MR' else 'Maximum', 'renders':{}}
    report['cases'][case['id']] = info
    if 'error' not in case:
        transform = np.linalg.inv(lps[:,[2,1,0,3]]) @ np.array(case['ijk_to_lps'])[:,[2,1,0,3]]
        permutation = np.argmax(np.abs(transform[:3,:3]), axis=0).tolist()
        assert len(set(permutation)) == 3
        signed = np.zeros((3,3))
        for j,i in enumerate(permutation):
            signed[i,j] = np.sign(transform[i,j])
            expected_offset = pixels.shape[i]-1 if signed[i,j]<0 else 0
            assert abs(transform[i,3]-expected_offset)<.01
        assert np.allclose(transform[:3,:3], signed, atol=1e-5)
        aligned = pixels.transpose(permutation)
        for j,i in enumerate(permutation):
            if signed[i,j]<0: aligned = np.flip(aligned,j)
        assert list(aligned.shape) == case['shape_kji']
        info['aligned_sha256'] = hashlib.sha256(np.ascontiguousarray(aligned,dtype=np.float32).tobytes()).hexdigest()
        info['voxels_identical'] = info['aligned_sha256'] == case['sha256']
        info['index_transform'] = transform.tolist()
        assert info['voxels_identical'], 'Decoded voxels differ'
    else:
        info['viewer_error'] = case['error']
    logic = slicer.modules.volumerendering.logic()
    logic.SetDefaultRenderingMethod('vtkMRMLGPURayCastVolumeRenderingDisplayNode')
    display = logic.CreateDefaultVolumeRenderingNodes(volume)
    display.SetVisibility(True)
    slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUp3DView)
    view = slicer.app.layoutManager().threeDWidget(0).threeDView()
    node = view.mrmlViewNode()
    node.SetBoxVisible(False)
    node.SetAxisLabelsVisible(False)
    node.SetBackgroundColor(2/255,7/255,14/255)
    node.SetBackgroundColor2(2/255,7/255,14/255)
    node.SetRenderMode(node.Orthographic)
    node.SetVolumeRenderingQuality(node.Normal if case.get('modality')=='MR' else node.Maximum)
    node.SetVolumeRenderingSurfaceSmoothing(False)
    slicer.app.processEvents()
    assert list(view.renderWindow().GetSize()) == manifest['size'], 'Viewport size changed'
    renderer = view.renderWindow().GetRenderers().GetFirstRenderer()
    camera = renderer.GetActiveCamera()
    output = root/'reference'/case['id']
    output.mkdir(parents=True,exist_ok=True)
    if 'error' in case:
        dims = volume.GetImageData().GetDimensions()
        center = (lps @ np.array([*(np.array(dims)-1)/2,1]))[:3]
        radius = np.linalg.norm((np.array(dims)-1)*volume.GetSpacing())/2
        cameras = {'A':{'position':(center+[0,-4*radius,0]).tolist(),'focal':center.tolist(),
                       'up':[0,0,1],'scale':radius*1.1,'clipping':[radius,7*radius]}}
        presets = [{'id':'aaa','slicer_name':'CT-AAA','mip':False}]
    else:
        cameras, presets = case['cameras'], case['presets']
        if case['modality']=='MR':
            presets = presets + [{'id':'slicer-mr-default','slicer_name':'MR-Default','mip':False}]
    for preset in presets:
        property_node = display.GetVolumePropertyNode()
        if preset['slicer_name']:
            property_node.Copy(logic.GetPresetByName(preset['slicer_name']))
        else:
            prop = property_node.GetVolumeProperty()
            colors,opacity = vtk.vtkColorTransferFunction(),vtk.vtkPiecewiseFunction()
            for p in preset['colors']: colors.AddRGBPoint(*p)
            for p in preset['opacity']: opacity.AddPoint(*p)
            gradient = vtk.vtkPiecewiseFunction()
            gradient.AddPoint(0,1);gradient.AddPoint(255,1)
            prop.SetColor(colors);prop.SetScalarOpacity(opacity);prop.SetGradientOpacity(gradient)
            prop.SetInterpolationTypeToLinear()
            for key,method in [('shade','SetShade'),('ambient','SetAmbient'),('diffuse','SetDiffuse'),
                               ('specular','SetSpecular'),('specular_power','SetSpecularPower'),
                               ('opacity_unit_distance','SetScalarOpacityUnitDistance')]:
                getattr(prop,method)(preset[key])
        node.SetRaycastTechnique(node.MaximumIntensityProjection if preset['mip'] else node.Composite)
        for face, parameters in cameras.items():
            if preset['id']=='slicer-mr-default' and face!='A': continue
            node.SetFieldOfView(parameters['scale'])
            camera.SetPosition(*(np.array(parameters['position'])*[-1,-1,1]))
            camera.SetFocalPoint(*(np.array(parameters['focal'])*[-1,-1,1]))
            camera.SetViewUp(*(np.array(parameters['up'])*[-1,-1,1]))
            camera.SetClippingRange(*parameters['clipping'])
            slicer.app.processEvents()
            view.renderWindow().Render()
            grab = vtk.vtkWindowToImageFilter()
            grab.SetInput(view.renderWindow());grab.ReadFrontBufferOff();grab.Update()
            writer = vtk.vtkPNGWriter()
            name = preset['id']+'-'+face
            writer.SetFileName(str(output/(name+'.png')))
            writer.SetInputData(grab.GetOutput());writer.Write()
            print('FRAME',case['id'],name,flush=True)
            info['renders'][name] = {'parallel':camera.GetParallelProjection(),'scale':camera.GetParallelScale()}
    print('SLICER_DONE',case['id'],'identical=',info.get('voxels_identical'),len(info['renders']),flush=True)


failed = False
for case in manifest['cases']:
    if os.environ.get('COMPARISON_CASE') and case['id'] != os.environ['COMPARISON_CASE']:
        continue
    try:
        capture_case(case)
    except Exception as error:
        failed = True
        report['cases'].setdefault(case['id'],{})['error'] = str(error)
        traceback.print_exc()
    (root/'reference.json').write_text(json.dumps(report,indent=2)+'\n')
    gc.collect()
slicer.app.exit(1 if failed else 0)
