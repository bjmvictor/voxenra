"""Independently decode the output of validate_dicom_results.py using dcmqi.

python tests/manual/check_dcmqi_results.py OUTPUT_DIRECTORY DCMQI_BIN_DIRECTORY
Checks the full binary mask in patient coordinates and SR quantities/SEG link.
"""

import gzip
import json
from pathlib import Path
import re
import subprocess
import sys
import numpy as np
import pydicom

root, binaries = map(Path, sys.argv[1:3])
manifest = json.loads((root / "manifest.json").read_text())
output = Path(manifest["output"])
decoded = root / "decoded"
decoded.mkdir(exist_ok=True)
for program, args in [
    (
        "segimage2itkimage",
        [
            "--inputDICOM",
            str(output / "SEG-001.dcm"),
            "--outputDirectory",
            str(decoded),
        ],
    ),
    (
        "tid1500reader",
        [
            "--inputDICOM",
            str(output / "SR-001.dcm"),
            "--outputMetadata",
            str(decoded / "sr.json"),
        ],
    ),
]:
    result = subprocess.run(
        [str(binaries / program), *args], capture_output=True, text=True, timeout=60
    )
    (decoded / (program + ".log")).write_text(result.stdout + result.stderr)
    assert result.returncode == 0, (program, result.stderr)
header, body = (decoded / "1.nrrd").read_bytes().split(b"\n\n", 1)
fields = dict(
    line.split(": ", 1)
    for line in header.decode().splitlines()
    if ": " in line and not line.startswith("#")
)
assert fields["space"] == "left-posterior-superior"
assert (
    fields["encoding"] == "gzip"
    and fields["type"] == "short"
    and fields["endian"] == "little"
)
size = list(map(int, fields["sizes"].split()))
pixels = np.frombuffer(gzip.decompress(body), dtype="<i2").reshape(size[::-1])
vectors = np.array(
    [
        [float(v) for v in x.split(",")]
        for x in re.findall(r"\(([^)]+)\)", fields["space directions"])
    ]
)
origin = np.array([float(v) for v in fields["space origin"].strip("()").split(",")])
expected = np.load(root / "expected-mask.npz")
ijk = np.argwhere(pixels > 0)[:, ::-1]
world = ijk @ vectors + origin
inverse = np.linalg.inv(expected["affine"])
native = world @ inverse[:3, :3].T + inverse[:3, 3]
np.testing.assert_allclose(native, np.rint(native), atol=1e-4)
local = np.rint(native).astype(int) - expected["offset"]
assert np.all(local >= 0) and np.all(local < expected["mask"].shape)
assert len(local) == int(expected["mask"].sum()) == manifest["voxel_count"]
assert len(np.unique(local, axis=0)) == len(local)
assert np.all(expected["mask"][tuple(local.T)])
sr = json.loads((decoded / "sr.json").read_text())
if (output / "SR-002.dcm").exists():
    subprocess.run(
        [
            str(binaries / "tid1500reader"),
            "--inputDICOM",
            str(output / "SR-002.dcm"),
            "--outputMetadata",
            str(decoded / "planar.json"),
        ],
        check=True,
        capture_output=True,
        timeout=60,
    )
    sr["Measurements"].extend(
        json.loads((decoded / "planar.json").read_text())["Measurements"]
    )
quantities = {
    item["quantity"]["CodeMeaning"]: float(item["value"])
    for group in sr["Measurements"]
    for item in group["measurementItems"]
}
for name, key in [
    ("Volume", "volume_cm3"),
    ("Area", "roi_area_mm2"),
    ("Perimeter", "roi_perimeter_mm"),
]:
    assert np.isclose(quantities[name], manifest[key], rtol=1e-12)
seg = pydicom.dcmread(output / "SEG-001.dcm", stop_before_pixels=True)
assert any(
    group.get("segmentationSOPInstanceUID") == seg.SOPInstanceUID
    and group["ReferencedSegment"] == 1
    for group in sr["Measurements"]
)
summary = dict(
    voxels_identical=True,
    voxel_count=len(local),
    sr_groups=len(sr["Measurements"]),
    volume_cm3=quantities["Volume"],
    area_mm2=quantities["Area"],
    perimeter_mm=quantities["Perimeter"],
)
(decoded / "verification.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
