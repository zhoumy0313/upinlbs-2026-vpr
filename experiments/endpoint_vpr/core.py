"""V3 image-score-only causal kernels; no query identity, pose or GT interface."""
from collections import deque
import numpy as np

def rank(s):
    s=np.asarray(s,dtype=float)
    if s.ndim!=1 or np.isnan(s).any() or np.isposinf(s).any():raise ValueError('Invalid scores')
    return np.argsort(-s,kind='stable')

def candidates(t,H,r,traversals):
    if H<1 or int(H)!=H or r<0 or int(r)!=r:raise ValueError('Integral bounded H/r')
    if len(t)!=len(traversals):raise ValueError('Gallery identity mismatch')
    ends=[int(j) for j in rank(t) if np.isfinite(t[j])][:H]
    return np.array(sorted({j for e in ends for j in range(max(0,e-r),min(len(t),e+r+1)) if traversals[j]==traversals[e] and np.isfinite(t[j])}),int)

def refine(s,t,traversals,kind='P',H=1,r=1,epsilon=0,gamma=0,warm=False):
    s=np.asarray(s,float);t=np.asarray(t,float)
    if s.shape!=t.shape or s.ndim!=1 or not np.isfinite(s).all():raise ValueError('Finite aligned current scores')
    rank(t)
    if epsilon<0 or not np.isfinite(epsilon) or not 0<=gamma<=1:raise ValueError('Invalid epsilon/gamma')
    c=candidates(t,H,r,traversals)
    reason='startup' if warm else 'empty_candidates' if not len(c) else ''
    if reason:return rank(s),dict(candidates=c.tolist(),eligible=[],fallback_reason=reason)
    if kind=='P':
        a=c[t[c]>=np.max(t[np.isfinite(t)])-epsilon];order=a[rank(s[a])]
    elif kind=='R1':a=c;order=a[rank(s[a])]
    elif kind=='R2':a=c;values=(1-gamma)*(s[c]+1)/2+gamma*(t[c]+1)/2;order=a[rank(values)]
    else:raise ValueError(kind)
    remaining=rank(s);remaining=remaining[~np.isin(remaining,order)]
    result=np.concatenate([order,remaining]);assert len(set(result))==len(s)
    return result,dict(candidates=c.tolist(),eligible=a.tolist(),fallback_reason='')

class Temporal:
    def __init__(self,L=9,velocities=(1.2,),shuffled=False):
        if L<1 or int(L)!=L or not velocities or not np.isfinite(velocities).all():raise ValueError('Invalid temporal settings')
        self.L=L;self.velocities=tuple(velocities);self.shuffled=shuffled;self.reset()
    def reset(self):self.history=deque(maxlen=self.L);self.rng=np.random.default_rng(0)
    def step(self,s,traversals):
        s=np.asarray(s,float)
        if s.ndim!=1 or not np.isfinite(s).all() or len(s)!=len(traversals):raise ValueError('Finite aligned scores required')
        if self.history and self.history[-1].shape!=s.shape:raise ValueError('Gallery changed without reset')
        self.history.append(s.copy());warm=len(self.history)<self.L
        if warm:return s.copy(),True
        h=np.stack(self.history)
        if self.shuffled and self.L>2:h[:-1]=h[:-1][self.rng.permutation(self.L-1)]
        n=len(s);j=np.arange(n);best=np.full(n,-np.inf);tr=np.asarray(traversals)
        for v in self.velocities:
            offsets=np.rint(float(v)*np.arange(self.L)).astype(int);valid=np.ones(n,bool);total=np.zeros(n)
            for lag,o in enumerate(offsets):
                ix=j-o;inside=(ix>=0)&(ix<n);clipped=ix.clip(0,n-1)
                inside &= tr[clipped]==tr;valid &= inside;total[inside]+=h[-1-lag,ix[inside]]
            values=np.full(n,-np.inf);values[valid]=total[valid]/self.L;best=np.maximum(best,values)
        return best,False

def rrf(a,b,k=60):
    out=np.zeros(len(a))
    for s in [a,b]:out[rank(s)]+=1/(k+np.arange(1,len(a)+1))
    return out

def align_by_ids(array,row_ids,col_ids,query_ids,gallery_ids):
    if len(set(row_ids))!=len(row_ids) or len(set(col_ids))!=len(col_ids):raise ValueError('Duplicate IDs')
    qi={v:i for i,v in enumerate(row_ids)};gi={v:i for i,v in enumerate(col_ids)}
    return np.asarray(array)[np.ix_([qi[v] for v in query_ids],[gi[v] for v in gallery_ids])]
