"""One predeclared rule, using only current scores and causal prediction history."""
from collections import deque
import numpy as np
from causal import CausalMatcher,stable_ranking,temporal_scores,blend_scores

def top_gap(scores):
    values=np.asarray(scores);finite=values[np.isfinite(values)]
    if len(finite)<2:return 0.
    top=np.sort(finite)[-2:]
    return float(top[1]-top[0])

def fit_train_gap_scales(scores,length,velocities):
    matcher=CausalMatcher(length,velocities,1.)
    a=[];t=[]
    for current in scores:
        temporal,meta=matcher.step(current)
        if not meta['warmup']:
            a.append(top_gap(current));t.append(top_gap(temporal))
    if not a:raise ValueError('Insufficient training history')
    return {'A_gap_median':max(float(np.median(a)),1e-12),
            'T_gap_median':max(float(np.median(t)),1e-12),
            'fit_role':'Nordland train only, without labels','training_valid_queries':len(a)}

class AdaptiveMatcher:
    def __init__(self,length,velocities,scales,candidate_count=50,ablation=None,fixed_weight=None):
        if scales['A_gap_median']<=0 or scales['T_gap_median']<=0:raise ValueError('Positive train scales')
        self.length=length;self.velocities=tuple(velocities);self.scales=dict(scales)
        self.candidate_count=candidate_count;self.ablation=ablation;self.fixed_weight=fixed_weight
        self.reset()

    def reset(self):
        self.history=deque(maxlen=self.length);self.endpoints=deque(maxlen=3)

    def step(self,current_scores):
        s=np.asarray(current_scores,dtype=float)
        if s.ndim!=1 or not np.isfinite(s).all():raise ValueError('Finite score vector required')
        order=stable_ranking(s);candidates=order[:self.candidate_count]
        self.history.append(s.copy())
        if len(self.history)<self.length:
            return order,{'warmup':True,'lambda':0.,'candidate_count':len(candidates)}
        t=temporal_scores(np.stack(self.history),self.length,self.velocities)
        if not np.isfinite(t[candidates]).any():
            return order,{'warmup':False,'lambda':0.,'no_valid_candidate_path':True,'candidate_count':len(candidates)}
        endpoint=int(np.argmax(t));self.endpoints.append(endpoint)
        ambiguity=float(np.clip(1-top_gap(s)/self.scales['A_gap_median'],0,1))
        support=float(np.clip(top_gap(t)/self.scales['T_gap_median'],0,1))
        steps=np.diff(self.endpoints)
        continuity=float(np.mean(abs(steps-np.median(self.velocities))<=1)) if len(steps) else 1.
        agreement=1. if endpoint in candidates else .25
        if self.ablation=='remove_continuity':continuity=1.
        if self.ablation=='remove_ambiguity':ambiguity=1.
        if self.ablation=='remove_agreement':agreement=1.
        weight=ambiguity*support*continuity*agreement if self.fixed_weight is None else self.fixed_weight
        fused=blend_scores(s,t,weight)
        # Reorder the declared current Top-K; keep the original A tail unchanged.
        rank=np.concatenate([candidates[stable_ranking(fused[candidates])],order[len(candidates):]])
        return rank,dict(warmup=False,**{'lambda':float(weight)},ambiguity=ambiguity,support=support,
            continuity=continuity,candidate_agreement=agreement,T_top1_index=endpoint,candidate_count=len(candidates),
            invalid_candidate_paths=int((~np.isfinite(t[candidates])).sum()))

def adaptive_stream(scores,**settings):
    matcher=AdaptiveMatcher(**settings);ranks=[];metadata=[]
    for row in scores:
        rank,meta=matcher.step(row);ranks.append(rank);metadata.append(meta)
    return np.stack(ranks),metadata
