"""Local real-photo examples; deterministic first-case selection, no photo redistribution."""
import argparse,csv,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]

def main():
    p=argparse.ArgumentParser();p.add_argument('--audit',required=True);p.add_argument('--evaluation',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
    rows=json.loads((ROOT/'outputs_v2'/a.audit/'manifest.json').read_text())['records'];mapping={r['image_id']:r for r in rows};g=[r for r in rows if r['role']=='gallery']
    per=list(csv.DictReader((ROOT/'outputs_v2'/a.evaluation/'per_query.csv').open()));primary=[r for r in per if r['radius_m']=='25' and r['common_valid']=='True']
    by={(r['method'],r['query_image_id']):r for r in primary};fixed=[r for r in primary if r['method']=='fixed_T_best']
    definitions=[('fixed_rescue',lambda r:r['A_correct']=='False' and r['correct_at_1']=='True'),
        ('fixed_harm',lambda r:r['A_correct']=='True' and r['correct_at_1']=='False'),
        ('both_wrong',lambda r:r['A_correct']=='False' and r['correct_at_1']=='False'),
        ('adaptive_loses_fixed',lambda r:r['correct_at_1']=='True' and by['adaptive_full',r['query_image_id']]['correct_at_1']=='False')]
    ledger=[];font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
    for kind,check in definitions:
        chosen=next((r for r in fixed if check(r)),None)
        if chosen is None:ledger.append(dict(case=kind,status='no such common query',query_image_id='',file='',reference_ids='',source='per_query.csv primary25m first in traversal order'));continue
        q=mapping[chosen['query_image_id']];distance=np.array([(r['easting']-q['easting'])**2+(r['northing']-q['northing'])**2 for r in g]);nearest=g[int(np.argmin(distance))]
        columns=[('Query',q,None)]
        for method in ['A-only','fixed_T_best','adaptive_full']:
            r=by[method,q['image_id']];columns.append((method,mapping[r['top1_image_id']] if r['top1_image_id'] else None,r))
        columns.append(('Closest offline GT',nearest,None));canvas=Image.new('RGB',(320*5,290),'white');draw=ImageDraw.Draw(canvas)
        for c,(name,record,result) in enumerate(columns):
            x=c*320;draw.text((x+5,5),name,fill='black',font=font)
            if record:
                with Image.open(ROOT/record['relative_path']) as im:im=im.convert('RGB');im.thumbnail((310,210));canvas.paste(im,(x+5,35))
                label=record['traversal']+' / '+str(record['source_frame']);draw.text((x+5,250),label,fill='black',font=font)
            if result:draw.text((x+5,270),'correct' if result['correct_at_1']=='True' else 'wrong; distance='+str(round(float(result['top1_distance_m']),1))+'m',fill='black',font=font)
        filename=kind+'.png';canvas.save(out/filename)
        ledger.append(dict(case=kind,status='actual local images',query_image_id=q['image_id'],file=filename,
            reference_ids=json.dumps([r['image_id'] if r else None for _,r,_ in columns[1:]]),source='per_query.csv primary25m first in traversal order'))
    with (out/'example_ledger.csv').open('w',newline='') as stream:w=csv.DictWriter(stream,fieldnames=list(ledger[0]));w.writeheader();w.writerows(ledger)

if __name__=='__main__':main()
