"""Generate synthetic codec fixtures, then test the actual packaged executable."""
from pathlib import Path
import argparse
import json
import os
import subprocess
import sys


def prepare(directory):
    import hashlib
    import io
    import numpy as np
    import pydicom
    from pydicom.dataset import FileDataset, FileMetaDataset
    from pydicom.encaps import encapsulate
    from pydicom.uid import (CTImageStorage, ExplicitVRLittleEndian, generate_uid,
                             RLELossless, JPEGLSLossless, JPEG2000Lossless, JPEGBaseline8Bit)
    from PIL import Image
    directory.mkdir(parents=True, exist_ok=True)
    manifest = []
    for name, syntax in [('rle', RLELossless), ('jpegls', JPEGLSLossless),
                         ('jpeg2000', JPEG2000Lossless), ('jpeg-baseline', JPEGBaseline8Bit)]:
        meta = FileMetaDataset()
        meta.TransferSyntaxUID = ExplicitVRLittleEndian
        meta.MediaStorageSOPClassUID = CTImageStorage
        meta.MediaStorageSOPInstanceUID = generate_uid()
        ds = FileDataset(None, {}, file_meta=meta, preamble=bytes(128))
        ds.SOPClassUID, ds.SOPInstanceUID = CTImageStorage, meta.MediaStorageSOPInstanceUID
        ds.Rows = ds.Columns = 64
        ds.SamplesPerPixel, ds.PhotometricInterpretation = 1, 'MONOCHROME2'
        ds.BitsAllocated = ds.BitsStored = 16
        ds.HighBit, ds.PixelRepresentation = 15, 1
        pixels = np.arange(4096, dtype=np.int16).reshape(64, 64) - 2048
        if syntax == JPEGBaseline8Bit:
            pixels = np.full((64, 64), 128, dtype=np.uint8)
            ds.BitsAllocated = ds.BitsStored = 8
            ds.HighBit, ds.PixelRepresentation = 7, 0
            stream = io.BytesIO()
            Image.fromarray(pixels).save(stream, format='JPEG', quality=100)
            ds.PixelData = encapsulate([stream.getvalue()])
            ds['PixelData'].is_undefined_length = True
            ds.file_meta.TransferSyntaxUID = syntax
        else:
            ds.PixelData = pixels.tobytes()
            ds.compress(syntax)
        filename = name + '.dcm'
        ds.save_as(directory / filename, enforce_file_format=True)
        manifest.append({'file': filename, 'shape': list(pixels.shape),
                         'sha256': hashlib.sha256(pixels.astype('<i4').tobytes()).hexdigest()})
    (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable', required=True, type=Path)
    parser.add_argument('--directory', type=Path, default=Path('build/codec-check'))
    args = parser.parse_args()
    directory = args.directory.resolve()
    prepare(directory)
    output = directory / 'result.json'
    output.unlink(missing_ok=True)
    environment = dict(os.environ)
    environment.pop('PYTHONPATH', None)
    environment.pop('PYTHONHOME', None)
    result = subprocess.run([str(args.executable.resolve()), '--verify-pixel-codecs',
                             str(directory), str(output)], env=environment, timeout=120)
    if result.returncode or not output.is_file() or not json.loads(output.read_text()).get('passed'):
        raise SystemExit('Packaged pixel decoder verification failed')
    print(output.read_text())


if __name__ == '__main__':
    main()
