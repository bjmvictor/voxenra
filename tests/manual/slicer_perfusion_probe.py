"""Inspect Slicer's handling of the local public supplemental-color CT sample.

Run in a separate Slicer with INTEGRATION_ROOT and PERFUSION_DICOM set.
The reference may not support the source palette/RWVM; record rather than infer.
"""

import json
import os
from pathlib import Path
import traceback

import numpy as np
import slicer
from DICOMScalarVolumePlugin import DICOMScalarVolumePluginClass

root = Path(os.environ["INTEGRATION_ROOT"])
root.mkdir(parents=True, exist_ok=True)
result = {"slicer_version": slicer.app.applicationVersion}
try:
    volume = DICOMScalarVolumePluginClass().loadFilesWithSeriesReader(
        "GDCM", [os.environ["PERFUSION_DICOM"]], "Supplemental color CT"
    )
    assert volume is not None and volume.GetImageData() is not None
    pixels = slicer.util.arrayFromVolume(volume)
    np.save(root / "slicer-perfusion.npy", pixels)
    display = volume.GetDisplayNode()
    result.update(
        loaded=True,
        node_class=volume.GetClassName(),
        shape=list(pixels.shape),
        color_table=display.GetColorNode().GetName()
        if display.GetColorNode()
        else None,
        units=str(volume.GetVoxelValueUnits()),
        value_range=[float(pixels.min()), float(pixels.max())],
    )
    slicer.util.setSliceViewerLayers(background=volume)
    slicer.util.resetSliceViews()
    slicer.util.mainWindow().resize(1400, 900)
    slicer.app.processEvents()
    assert slicer.util.mainWindow().grab().save(str(root / "slicer-perfusion.png"))
except Exception as error:  # noqa: BLE001 - record reference capability failures
    result.update(loaded=False, error=str(error), traceback=traceback.format_exc())
(root / "slicer-perfusion.json").write_text(json.dumps(result, indent=2) + "\n")
slicer.app.exit(0 if result["loaded"] else 1)
