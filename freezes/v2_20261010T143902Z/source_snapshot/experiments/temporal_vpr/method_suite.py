"""Single frozen method factory used by evaluation and real-image timing."""
import numpy as np
from causal import CausalMatcher,stable_ranking,rrf,fixed_affine
from adaptive import AdaptiveMatcher
from smr_adapter import SmrMatcher

def specifications(interior,scales):
    methods=[dict(name='A-only',kind='single',encoder='cosplace'),dict(name='B-only',kind='single',encoder='eigenplaces'),
        dict(name='DINOv2-only',kind='single',encoder='dinov2'),dict(name='RRF_k60',kind='rrf',k=60)]
    methods += [dict(name=f'AB_fixed_{w}',kind='fusion',B_weight=w) for w in [.25,.5,.75]]
    methods += [dict(name='fixed_T_best',kind='temporal',length=9,velocities=[1.2],weight=1),
        dict(name='fixed_blend_best',kind='temporal',**interior)]
    methods += [dict(name=f'full_velocity_T_L{length}',kind='temporal',length=length,velocities=[.8,1.,1.2],weight=1) for length in [3,5,9]]
    methods += [dict(name='shuffled_L9',kind='temporal',length=9,velocities=[.8,1.,1.2],weight=1,shuffled=True,seed=0),
        dict(name='velocity08_L9',kind='temporal',length=9,velocities=[.8],weight=1),
        dict(name='velocity10_L9',kind='temporal',length=9,velocities=[1.],weight=1),
        dict(name='reverse_velocity_L9',kind='temporal',length=9,velocities=[-1.2],weight=1)]
    variants=[('adaptive_full',{}),('remove_continuity',dict(ablation='remove_continuity')),
        ('remove_ambiguity',dict(ablation='remove_ambiguity')),('remove_agreement',dict(ablation='remove_agreement')),
        ('fixed_lambda1_Top50',dict(fixed_weight=1.)),('fixed_lambda05_Top50',dict(fixed_weight=.5)),
        ('replace_adaptive_with_G2_fixed_lambda',dict(fixed_weight=interior['weight']))]
    methods += [dict(name=name,kind='adaptive',length=9,velocities=[1.2],scales=scales,candidate_count=50,**change) for name,change in variants]
    methods.append(dict(name='SMR_first_filter_adapted',kind='smr',length=9))
    return methods

class Method:
    def __init__(self,root,spec,pipeline=None):
        self.spec=dict(spec);self.kind=spec['kind'];opts={k:v for k,v in spec.items() if k not in ['name','kind']}
        self.matcher=(CausalMatcher(**opts) if self.kind=='temporal' else AdaptiveMatcher(**opts) if self.kind=='adaptive'
                      else SmrMatcher(root,pipeline,opts['length']) if self.kind=='smr' else None)

    def reset(self):
        if self.matcher:self.matcher.reset()

    def step(self,scores):
        if self.kind=='single':return stable_ranking(scores[self.spec['encoder']]),dict(warmup=False)
        if self.kind=='rrf':return stable_ranking(rrf(scores['cosplace'],scores['eigenplaces'],self.spec['k'])),dict(warmup=False)
        if self.kind=='fusion':
            w=self.spec['B_weight'];return stable_ranking((1-w)*fixed_affine(scores['cosplace'])+w*fixed_affine(scores['eigenplaces'])),dict(warmup=False)
        prediction,metadata=self.matcher.step(scores['cosplace'])
        return (stable_ranking(prediction) if self.kind=='temporal' else prediction),metadata

def needed_encoders(spec):
    return [spec['encoder']] if spec['kind']=='single' else ['cosplace','eigenplaces'] if spec['kind'] in ['rrf','fusion'] else ['cosplace']
