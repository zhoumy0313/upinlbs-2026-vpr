"""Cache provenance and evaluation-only GT. These objects never enter online strategy."""
import json
import numpy as np
from .runtime import ROOT,sha
from .core import align_by_ids
G2=ROOT/'outputs_v2/g2_strong_baselines_20261010T133356Z_5d8c3f15'
SL=ROOT/'outputs_v2/g4_independent_evaluation_20261010T143959Z_73e61bb4'
SLMAN=ROOT/'outputs_v2/g4_independent_data_audit_20261010T135919Z_432bb768/manifest.json'
NMAN=ROOT/'data/manifests/p1_20261010_132030_nordland_manifest_v2.json'

def checked_load(p,expected):
    if sha(p)!=expected:raise ValueError('Cache fingerprint mismatch: '+str(p))
    a=np.load(p,allow_pickle=False)
    if a.ndim!=2 or not np.isfinite(a).all():raise ValueError('Bad cache array')
    return a

def seen():
    slids=json.loads((SL/'score_identities.json').read_text());nids=json.loads((G2/'score_identities.json').read_text())
    sr=json.loads(SLMAN.read_text())['records'];nr=json.loads(NMAN.read_text())['records'];sets=[]
    for dataset,split,start,end in [('St_Lucia','descriptive',0,1464),('St_Lucia','train',0,700),('St_Lucia','validation',800,1464),('Nordland','train',0,600),('Nordland','validation',0,300)]:
        is_sl=dataset=='St_Lucia';identity=slids if is_sl else nids
        cp=identity['cosplace' if is_sl else split+'_cosplace'];qids=cp['query_ids'];gids=cp['gallery_ids']
        rows={r['image_id']:r for r in (sr if is_sl else nr)};g=[rows[v] for v in gids];q=[rows[v] for v in qids][start:end]
        scores={};provenance={}
        for m in ['cosplace','eigenplaces','dinov2']:
            info=identity[m if is_sl else split+'_'+m];p=(SL/(m+'_scores.npy')) if is_sl else G2/(split+'_'+m+'_scores.npy')
            expected=info['score_array_sha256' if is_sl else 'scores_sha256'];a=checked_load(p,expected)
            scores[m]=align_by_ids(a,info['query_ids'],info['gallery_ids'],qids,gids)[start:end]
            provenance[m]=dict(score_path=str(p.relative_to(ROOT)),score_sha256=expected,original_identity=info)
            if is_sl:
                fp=info['fingerprint'];assert sha(ROOT/fp['source']['checkpoint'])==fp['source']['checkpoint_sha256']
        if is_sl:
            qxy=np.array([[r['easting'],r['northing']] for r in q]);gxy=np.array([[r['easting'],r['northing']] for r in g]);dist=np.linalg.norm(qxy[:,None,:]-gxy[None,:,:],axis=-1);radii=[5,10,15,25,50];unit='metres';primary=10
        else:dist=np.abs(np.array([r['frame_index'] for r in q])[:,None]-np.array([r['frame_index'] for r in g])[None,:]);radii=[1,5,10];unit='frames';primary=5
        sets.append(dict(dataset=dataset,split=split,q=q,g=g,scores=scores,distance=dist,radii=radii,primary=primary,unit=unit,model_identity=provenance,manifest_sha256=sha(SLMAN if is_sl else NMAN)))
    return sets
