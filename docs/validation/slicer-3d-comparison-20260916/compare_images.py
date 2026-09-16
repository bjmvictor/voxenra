"""Compose unmodified render crops and measure their RGB differences.

python compare_images.py OUTPUT_ROOT
Requires Pillow and NumPy. No contrast, brightness, color or geometric correction
is applied. All render windows must have the same size and camera.
"""
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw

root = Path(sys.argv[1])
# Fixed anatomy crop, excluding orientation overlays. Protocol size: 1238x928.
box = (435, 290, 815, 660)
mapping = {'aaa': 'CT-AAA', 'bones': 'CT-Bone', 'muscle': 'CT-Muscle',
           'lung2': 'CT-Lung', 'carotid': 'CT-Coronary-Arteries-3'}
metrics = {}
gallery = Image.new('RGB', (1140, 420*len(mapping)), '#121720')
draw = ImageDraw.Draw(gallery)
for row, (name, reference_name) in enumerate(mapping.items()):
    paths = [root/'reference'/(reference_name+'-maximum.png'),
             root/'viewer'/('before-'+name+'.png'), root/'viewer'/('after-'+name+'.png')]
    crops = [Image.open(p).convert('RGB').crop(box) for p in paths]
    arrays = [np.array(im).astype(float) for im in crops]
    metrics[name] = {'before_mae': float(np.abs(arrays[1]-arrays[0]).mean()),
                     'after_mae': float(np.abs(arrays[2]-arrays[0]).mean())}
    for col, (label, im) in enumerate(zip(['Slicer Maximum', 'Before', 'After'], crops)):
        gallery.paste(im, (380*col, row*420+40))
        draw.text((380*col+10, row*420+12), name+' / '+label, fill='white')
gallery.save(root/'presets-comparison.png')
gallery.crop((0, 0, 1140, 420)).save(root/'aaa-comparison.png')
windows = Image.new('RGB', (4*380, 2*420), '#121720')
draw = ImageDraw.Draw(windows)
for col, direction in enumerate(['up', 'down', 'right', 'left']):
    crops = [Image.open(root/'reference'/('CT-AAA-window-'+direction+'.png')).convert('RGB').crop(box),
             Image.open(root/'viewer'/('after-aaa-window-'+direction+'.png')).convert('RGB').crop(box)]
    metrics['window-'+direction] = {'mae':float(np.abs(np.array(crops[0]).astype(float)-np.array(crops[1])).mean())}
    for row, (label, im) in enumerate(zip(['Slicer Maximum', 'After'], crops)):
        windows.paste(im, (col*380, row*420+40))
        draw.text((col*380+10, row*420+12), label+' / '+direction, fill='white')
windows.save(root/'windowing-comparison.png')
(root/'differences.json').write_text(json.dumps({'crop_xyxy':box,'metrics':metrics}, indent=2)+'\n')
print(json.dumps(metrics, indent=2))
