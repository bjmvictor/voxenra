"""Compare matching native render pairs; no image alignment or recoloring.

python compare_images.py COMPARISON_ROOT
Metrics use the union of visible pixels, excluding the orientation marker.
"""
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image,ImageDraw,ImageOps

root=Path(sys.argv[1])
manifest=json.loads((root/'manifest.json').read_text())
reference=json.loads((root/'reference.json').read_text())
viewer=json.loads((root/'viewer.json').read_text())
results={}
output=root/'comparison';output.mkdir(exist_ok=True)
labels={'catphan604':'CatPhan604 CT','micro-ct':'Small-animal CT','ct320':'320-slice CT',
        'mr-thin':'1 mm brain MR','mr-thick':'4.8 mm spacing brain MR'}

def panel(images,titles,box,width=480,height=430):
    out=Image.new('RGB',(width*len(images),height),'#101820')
    draw=ImageDraw.Draw(out)
    for i,(im,title) in enumerate(zip(images,titles)):
        crop=ImageOps.contain(im.crop(box),(width-16,height-42))
        out.paste(crop,(i*width+(width-crop.width)//2,34+(height-42-crop.height)//2))
        draw.text((i*width+10,10),title,fill='white')
    return out

for case in manifest['cases']:
    case_id=case['id']
    if viewer.get(case_id,{}).get('error') or 'error' in case:
        results[case_id]={'error':case.get('error') or reference['cases'].get(case_id,{}).get('error') or viewer[case_id]['error']}
        continue
    case_results={}
    expected={p['id']+'-'+face for p in case['presets'] for face in case['cameras']}
    assert set(viewer.get(case_id,{}).get('renders',{})) == expected, f'Incomplete captures: {case_id}'
    for name in viewer[case_id]['renders']:
        im1=Image.open(root/'reference'/case_id/(name+'.png')).convert('RGB')
        im2=Image.open(root/'viewer'/case_id/(name+'.png')).convert('RGB')
        a,b=np.array(im1).astype(float),np.array(im2).astype(float)
        assert a.shape==b.shape
        mask=np.any(abs(a-[2,7,14])>12,axis=2)|np.any(abs(b-[2,7,14])>12,axis=2)
        # Production viewer's orientation cube is not present in reference.
        mask[:220,-220:]=False
        yy,xx=np.where(mask)
        assert len(xx)>100, f'No visible volume: {case_id}/{name}'
        box=(max(0,int(xx.min())-12),max(0,int(yy.min())-12),min(im1.width,int(xx.max())+13),min(im1.height,int(yy.max())+13))
        difference=abs(a-b)[mask]
        case_results[name]={'foreground_pixels':int(mask.sum()),'mae':float(difference.mean()),
            'p95_channel_difference':float(np.percentile(difference,95)), 'bbox':box,
            'viewer_median_ms':viewer[case_id]['renders'][name]['median_ms']}
        panel([im1,im2],[labels.get(case_id,case_id)+' / Slicer '+reference['cases'][case_id]['reference_quality'],
              labels.get(case_id,case_id)+' / Viewer'],box).save(output/(case_id+'-'+name+'.png'))
    results[case_id]={'renders':case_results,'mae_min':min(v['mae'] for v in case_results.values()),
                     'mae_max':max(v['mae'] for v in case_results.values())}
    if case['modality']=='MR':
        one=Image.open(root/'reference'/case_id/'slicer-mr-default-A.png').convert('RGB')
        two=Image.open(root/'viewer'/case_id/'mr-general-A.png').convert('RGB')
        a,b=np.array(one).astype(float),np.array(two).astype(float)
        mask=np.any(abs(a-[2,7,14])>12,axis=2)|np.any(abs(b-[2,7,14])>12,axis=2);mask[:220,-220:]=False
        yy,xx=np.where(mask);box=(int(xx.min())-12,int(yy.min())-12,int(xx.max())+13,int(yy.max())+13)
        panel([one,two],['Slicer native MR-Default (different preset)','Viewer MR General (different preset)'],box).save(output/(case_id+'-default-presets.png'))
(root/'differences.json').write_text(json.dumps(results,indent=2)+'\n')
for key,value in results.items():
    print(key,value.get('error') or (len(value['renders']),round(value['mae_min'],3),round(value['mae_max'],3)))

# Review every pair together; the full-resolution originals remain available.
names=[case_id+'-'+name for case_id,result in results.items() for name in result.get('renders',{})]
if not names: sys.exit('No completed image pairs')
sheet=Image.new('RGB',(1440,215*((len(names)+2)//3)),'#101820')
for i,name in enumerate(names):
    with Image.open(output/(name+'.png')) as pair:
        sheet.paste(pair.resize((480,215)),((i%3)*480,(i//3)*215))
sheet.save(output/'all-pairs.png')
selected=['catphan604-aaa-oblique','micro-ct-aaa-oblique','ct320-aaa-oblique',
          'mr-thin-mr-general-oblique','mr-thick-mr-general-oblique']
selected=[name for name in selected if name in names] or names[:5]
overview=Image.new('RGB',(960,430*len(selected)),'#101820')
for i,name in enumerate(selected):
    with Image.open(output/(name+'.png')) as pair: overview.paste(pair,(0,430*i))
overview.save(output/'overview.png')
