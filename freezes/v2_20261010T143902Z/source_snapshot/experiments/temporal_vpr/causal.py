"""Label-free online score operations. No manifest, filename, GPS or GT input."""
from collections import deque
import numpy as np

def stable_ranking(scores,k=None):
    scores=np.asarray(scores)
    if np.isnan(scores).any():raise ValueError('NaN scores')
    ranks=np.argsort(-scores,axis=-1,kind='stable')
    return ranks if k is None else ranks[...,:k]

def cosine_unit_scores(query,gallery):
    q=np.asarray(query,dtype=np.float64);g=np.asarray(gallery,dtype=np.float64)
    q=q/np.linalg.norm(q,axis=-1,keepdims=True)
    g=g/np.linalg.norm(g,axis=-1,keepdims=True)
    return np.clip(q@g.T,-1,1)

def fixed_affine(scores):
    # Cosine and average cosine have the same known [-1,1] range.
    return (np.asarray(scores,dtype=np.float64)+1)/2

def rrf(a,b,k=60):
    a=np.asarray(a);b=np.asarray(b)
    if a.shape!=b.shape or a.ndim!=1 or k<0:raise ValueError('Aligned score vectors required')
    result=np.zeros(len(a),dtype=np.float64)
    for scores in [a,b]:
        order=stable_ranking(scores)
        result[order]+=1/(k+np.arange(1,len(order)+1,dtype=np.float64))
    return result

def temporal_scores(history,length,velocities):
    """Endpoint j; current history[-1]; round-to-even explicitly follows np.rint."""
    h=np.asarray(history,dtype=np.float64)
    if h.ndim!=2 or length<1 or len(h)<length:raise ValueError('Insufficient causal history')
    if not velocities or not np.isfinite(velocities).all():raise ValueError('Finite nonempty velocities')
    if not np.isfinite(h).all():raise ValueError('Finite input scores required')
    n=h.shape[1];j=np.arange(n);best=np.full(n,-np.inf)
    for v in velocities:
        offsets=np.rint(float(v)*np.arange(length)).astype(int)
        valid=np.ones(n,dtype=bool);total=np.zeros(n)
        for lag,offset in enumerate(offsets):
            indices=j-offset;inside=(indices>=0)&(indices<n)
            valid &= inside
            total[inside]+=h[-1-lag,indices[inside]]
        values=np.full(n,-np.inf);values[valid]=total[valid]/length
        best=np.maximum(best,values)
    return best

def blend_scores(current,temporal,weight):
    if not 0<=weight<=1:raise ValueError('Weight must lie in [0,1]')
    s=np.asarray(current,dtype=np.float64);t=np.asarray(temporal,dtype=np.float64)
    if s.shape!=t.shape:raise ValueError('Aligned score vectors required')
    if weight==0:return s.copy() # Avoid 0 * -inf; exact A-only behavior.
    if weight==1:return t.copy()
    result=(1-weight)*fixed_affine(s)+weight*fixed_affine(t)
    result[~np.isfinite(t)]=-np.inf
    return result

class CausalMatcher:
    def __init__(self,length=5,velocities=(.8,1.,1.2),weight=1.,shuffled=False,seed=0):
        if int(length)!=length or length<1:raise ValueError('Positive integral window')
        self.length=int(length);self.velocities=tuple(velocities);self.weight=weight
        self.shuffled=shuffled;self.seed=seed;self.reset()

    def reset(self):
        self.history=deque(maxlen=self.length)
        self.rng=np.random.default_rng(self.seed)
        self.seen=0

    def step(self,current_scores):
        s=np.asarray(current_scores,dtype=np.float64)
        if s.ndim!=1 or not np.isfinite(s).all():raise ValueError('Finite score vector required')
        if self.history and s.shape!=self.history[-1].shape:raise ValueError('Gallery changed without reset')
        self.history.append(s.copy());self.seen+=1
        warmup=len(self.history)<self.length
        if warmup:return s.copy(),{'warmup':True,'seen':self.seen}
        history=np.stack(self.history)
        if self.shuffled and self.length>2:
            history[:-1]=history[:-1][self.rng.permutation(self.length-1)]
        temporal=temporal_scores(history,self.length,self.velocities)
        return blend_scores(s,temporal,self.weight),{'warmup':False,'seen':self.seen}

def stream_scores(scores,**settings):
    matcher=CausalMatcher(**settings)
    return np.stack([matcher.step(row)[0] for row in scores])
