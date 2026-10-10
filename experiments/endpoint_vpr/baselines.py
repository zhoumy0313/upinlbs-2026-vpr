import itertools
import numpy as np
from .core import Temporal,rank,rrf,refine
BACKENDS={'fixed_L9':(9,[1.2]),'full_L3':(3,[.8,1.,1.2]),'full_L5':(5,[.8,1.,1.2]),'full_L9':(9,[.8,1.,1.2])}
def strong_specs():
    specs=[dict(name=n,kind='single',encoder=e) for n,e in [('A','cosplace'),('B','eigenplaces'),('DINOv2','dinov2')]]
    specs.append(dict(name='RRF_k60',kind='rrf'))
    specs += [dict(name=f'AB_{w}',kind='AB',weight=w) for w in [.25,.5,.75]]
    specs += [dict(name=n,kind='temporal',backend=n) for n in BACKENDS]
    specs += [dict(name=f'global_fixed_L9_blend_{w}',kind='global_blend',backend='fixed_L9',weight=w) for w in [.25,.5,.75]]
    specs += [dict(name='shuffled_full_L9_seed0',kind='control',L=9,velocities=[.8,1.,1.2],shuffled=True),dict(name='reversed_fixed_L9',kind='control',L=9,velocities=[-1.2],shuffled=False)]
    return specs

def local_specs():
    specs=[]
    for b,H,r in itertools.product(BACKENDS,[1,3],[1,2,4,8]):
        specs.append(dict(name=f'R1_{b}_H{H}_r{r}',kind='R1',backend=b,H=H,r=r))
        specs += [dict(name=f'R2_{b}_H{H}_r{r}_g{w}',kind='R2',backend=b,H=H,r=r,gamma=w) for w in [0,.25,.5,.75,1.]]
    specs += [dict(name=f'P_fixed_L9_H{H}_r{r}_e{e}',kind='P',backend='fixed_L9',H=H,r=r,epsilon=e) for H,r,e in itertools.product([1,3],[1,2,4,8],[0,.01,.03,.06])]
    return specs

class Strategy:
    """Public online input is aligned image scores and gallery traversal IDs only."""
    def __init__(self,spec,traversals):
        self.spec=dict(spec);self.traversals=tuple(traversals);self.kind=spec['kind'];self.reset()
    def reset(self):
        x=self.spec
        if self.kind in ['temporal','global_blend','P','R1','R2']:L,v=BACKENDS[x['backend']];self.temporal=Temporal(L,v)
        elif self.kind=='control':self.temporal=Temporal(x['L'],x['velocities'],x['shuffled'])
        else:self.temporal=None
    def step(self,scores):
        s=np.asarray(scores['cosplace']);t=s;warm=False
        if self.temporal:t,warm=self.temporal.step(s,self.traversals)
        return self._rank_current(scores,t,warm)
    def _rank_current(self,scores,t,warm):
        x=self.spec;s=np.asarray(scores['cosplace']);meta=dict(candidates=[],eligible=[],fallback_reason='')
        if self.kind=='single':values=scores[x['encoder']];result=rank(values)
        elif self.kind=='rrf':values=rrf(s,scores['eigenplaces']);result=rank(values)
        elif self.kind=='AB':w=x['weight'];values=(1-w)*(s+1)/2+w*(scores['eigenplaces']+1)/2;result=rank(values)
        elif self.kind in ['temporal','control']:values=t;result=rank(values)
        elif self.kind=='global_blend':w=x['weight'];values=(1-w)*(s+1)/2+w*(t+1)/2;result=rank(values)
        else:
            result,meta=refine(s,t,self.traversals,kind=self.kind,H=x['H'],r=x['r'],epsilon=x.get('epsilon',0),gamma=x.get('gamma',0),warm=warm);values=s
        meta.update(warmup=warm,T_top3=rank(t)[:3].tolist(),T_top3_scores=[float(t[j]) for j in rank(t)[:3]],top10_scores=[float(values[j]) if np.isfinite(values[j]) else None for j in result[:10]],score_semantics='current_S_for_local_ranked_methods_otherwise_method_score',temporal_best_score=float(np.max(t)),path_offsets=np.rint(np.array(self.temporal.velocities[0])*np.arange(self.temporal.L)).astype(int).tolist() if self.temporal else [])
        return result,meta

def predictions(d,spec):
    tr=[r.get('traversal',r.get('traverse')) for r in d['g']];m=Strategy(spec,tr);out=[];metadata=[]
    cache=d.setdefault('_temporal_cache',{})
    key=spec.get('backend') if spec['kind']!='control' else spec['name']
    if m.temporal and key not in cache:
        cache[key]=[m.temporal.step(row,tr) for row in d['scores']['cosplace']]
    for i in range(len(d['q'])):
        scores={k:v[i] for k,v in d['scores'].items()}
        o,meta=m._rank_current(scores,*cache[key][i]) if m.temporal else m.step(scores)
        out.append(o[:10]);metadata.append(meta)
    return np.stack(out),metadata
