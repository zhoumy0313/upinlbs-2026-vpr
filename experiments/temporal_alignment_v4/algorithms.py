"""Only image scores and monotonic acquisition timestamps enter this module."""
import sys,itertools
from collections import deque
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from experiments.endpoint_vpr.core import rank,Temporal,refine,rrf
VELOCITIES=(-1.2,-1.,-.8,0.,.8,1.,1.2)
def specifications():
    baseline=[dict(name='A',kind='single',encoder='cosplace'),dict(name='B',kind='single',encoder='eigenplaces'),dict(name='RRF60',kind='rrf')]
    baseline += [dict(name=f'AB_{w}',kind='AB',weight=w) for w in [.25,.5,.75]]
    backends=[(f'L{L}',L,[.8,1.,1.2]) for L in [3,5,9]]+[('old_fixed_L9',9,[1.2])]
    for name,L,v in backends:
        b=dict(L=L,velocities=v)
        baseline.append(dict(name=name,kind='index',**b))
        baseline += [dict(name=name+f'_global_{w}',kind='index_global',weight=w,**b) for w in [.25,.5,.75]]
        for H,r in itertools.product([1,3],[1,2,4]):
            baseline.append(dict(name=f'R1_{name}_H{H}_r{r}',kind='index_R1',H=H,r=r,**b))
            baseline += [dict(name=f'R2_{name}_H{H}_r{r}_g{g}',kind='index_R2',H=H,r=r,gamma=g,**b) for g in [.5,1.]]
    candidate=[]
    for W in [.4,.8,1.6]:
        b=dict(W=W,velocities=list(VELOCITIES),lag_points=5)
        baseline.append(dict(name=f'Time_W{W}',kind='time',**b))
        baseline += [dict(name=f'TimeGlobal_W{W}_g{g}',kind='time_global',weight=g,**b) for g in [.5,1.]]
        for H,r in itertools.product([1,3],[.2,.4]):
            baseline.append(dict(name=f'TimeR1_W{W}_H{H}_r{r}',kind='time_R1',H=H,r_seconds=r,**b))
            baseline += [dict(name=f'TimeR2_W{W}_H{H}_r{r}_g{g}',kind='time_R2',H=H,r_seconds=r,gamma=g,**b) for g in [.5,1.]]
            candidate += [dict(name=f'Proposed_W{W}_H{H}_r{r}_e{e}',kind='time_P',H=H,r_seconds=r,epsilon=e,**b) for e in [.01,.03,.06]]
    return baseline,candidate
def bracket(times,target):
    hi=np.searchsorted(times,target,side='left');hi=np.clip(hi,0,len(times)-1);lo=np.maximum(0,hi-1)
    exact=times[hi]==target;lo=np.where(exact,hi,lo)
    denom=times[hi]-times[lo];weight=np.divide(target-times[lo],denom,out=np.zeros_like(target,dtype=float),where=denom!=0)
    valid=(target>=times[0])&(target<=times[-1])
    return lo,hi,weight,valid
class TimeAware:
    def __init__(self,gallery_times,W,velocities=VELOCITIES,lag_points=5):
        self.gt=np.asarray(gallery_times,float);assert np.all(np.diff(self.gt)>0)
        self.W=float(W);self.v=tuple(velocities);self.lags=np.linspace(0,W,lag_points)
        self.reference_plans=[[bracket(self.gt,self.gt-v*lag) for lag in self.lags] for v in self.v]
        self.reset()
    def reset(self):self.history=deque();self.first=None
    def step(self,s,t):
        s=np.asarray(s,float);assert s.shape==self.gt.shape and np.isfinite(s).all()
        if self.history:assert t>self.history[-1][0]
        if self.first is None:self.first=t
        self.history.append((float(t),s.copy()))
        while len(self.history)>2 and self.history[1][0]<t-self.W:self.history.popleft()
        if t-self.first<self.W-1e-8:return s.copy(),True
        times=np.array([x[0] for x in self.history]);h=np.stack([x[1] for x in self.history]);lagged=[]
        for lag in self.lags:
            target=np.array([t-lag]);lo,hi,w,valid=bracket(times,target)
            if not valid[0]:return s.copy(),True
            lagged.append(h[lo[0]]*(1-w[0])+h[hi[0]]*w[0])
        best=np.full(len(s),-np.inf)
        for plans in self.reference_plans:
            total=np.zeros(len(s));valid_all=np.ones(len(s),bool)
            for hs,(lo,hi,w,valid) in zip(lagged,plans):total += hs[lo]*(1-w)+hs[hi]*w;valid_all &= valid
            values=np.where(valid_all,total/len(self.lags),-np.inf);best=np.maximum(best,values)
        return best,False
def time_candidates(t,H,r_seconds,gallery_times):
    ends=[int(j) for j in rank(t) if np.isfinite(t[j])][:H]
    c=np.zeros(len(t),bool)
    for j in ends:c |= np.abs(gallery_times-gallery_times[j])<=r_seconds+1e-8
    return np.flatnonzero(c&np.isfinite(t))
class Method:
    def __init__(self,spec,gallery_times):
        self.spec=dict(spec);self.gt=np.asarray(gallery_times,float);self.kind=spec['kind'];self.temporal=None
        if self.kind.startswith('index'):self.temporal=Temporal(spec['L'],spec['velocities'])
        if self.kind.startswith('time'):self.temporal=TimeAware(self.gt,spec['W'],spec['velocities'],spec['lag_points'])
    def reset(self):
        if self.temporal:self.temporal.reset()
    def step(self,scores,timestamp):
        x=self.spec;s=np.asarray(scores['cosplace'],float);t=s;warm=False;meta=dict(candidates=[],eligible=[],startup=False)
        if self.temporal:
            t,warm=self.temporal.step(s,[0]*len(s)) if self.kind.startswith('index') else self.temporal.step(s,timestamp)
        if self.kind=='single':out=rank(scores[x['encoder']])
        elif self.kind=='rrf':out=rank(rrf(s,scores['eigenplaces']))
        elif self.kind=='AB':out=rank((1-x['weight'])*s+x['weight']*scores['eigenplaces'])
        elif self.kind in ['index','time']:out=rank(t)
        elif self.kind.endswith('_global'):out=rank((1-x['weight'])*s+x['weight']*t)
        elif self.kind.startswith('index_'):
            out,oldmeta=refine(s,t,[0]*len(s),kind=self.kind.split('_')[1],H=x['H'],r=x['r'],gamma=x.get('gamma',0),warm=warm);meta.update(oldmeta)
        else:
            c=time_candidates(t,x['H'],x['r_seconds'],self.gt);meta['candidates']=c.tolist()
            if warm or not len(c):out=rank(s)
            else:
                a=c[t[c]>=np.max(t)-x['epsilon']] if self.kind=='time_P' else c
                values=(1-x['gamma'])*s[a]+x['gamma']*t[a] if self.kind=='time_R2' else s[a]
                head=a[rank(values)];tail=rank(s);out=np.concatenate([head,tail[~np.isin(tail,head)]]);meta['eligible']=a.tolist()
        meta.update(startup=bool(warm),T_top1=int(rank(t)[0]),temporal_max=float(np.max(t)))
        assert len(out)==len(s) and len(np.unique(out))==len(s)
        return out,meta
def predict(d,spec):
    method=Method(spec,[r['timestamp'] for r in d['g']]);out=[];meta=[]
    for i,q in enumerate(d['q']):
        o,m=method.step({k:v[i] for k,v in d['scores'].items()},q['timestamp']);out.append(o[:10]);meta.append(m)
    return np.stack(out),meta
def scalar_time_reference(scores,query_times,gallery_times,W,velocities=VELOCITIES,lag_points=5):
    """Independent slow scalar interpolation oracle for implementation verification only."""
    h=np.asarray(scores);qt=np.asarray(query_times);gt=np.asarray(gallery_times);out=np.full(len(gt),-np.inf)
    if qt[-1]-qt[0]<W-1e-8:return h[-1].copy()
    for j in range(len(gt)):
        best=-np.inf
        for v in velocities:
            total=0.;valid=True
            for lag in np.linspace(0,W,lag_points):
                target=gt[j]-v*lag
                if target<gt[0] or target>gt[-1]:valid=False;break
                vals=[np.interp(qt[-1]-lag,qt,h[:,k]) for k in range(len(gt))]
                total += np.interp(target,gt,vals)
            if valid:best=max(best,total/lag_points)
        out[j]=best
    return out
