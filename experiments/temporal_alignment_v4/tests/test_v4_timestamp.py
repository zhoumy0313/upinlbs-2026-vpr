import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from algorithms import TimeAware,scalar_time_reference,Method,specifications
from protocol import nearest,sampled,construct,distances
def test_nearest_earlier_tie():assert nearest(np.array([0.,2.]),1.)==0
def test_nearest_boundary():assert nearest(np.array([0.,2.]),8.)==1
def test_sampling_retains_first_without_mutation():
    r=[dict(timestamp=t) for t in [0.,.1,.2,.3,.4,.9,1.1]];s=sampled(r,5);assert [x['timestamp'] for x in s]==[0.,.2,.4,.9,1.1] and len(r)==7
@pytest.mark.parametrize('W',[.4,.8,1.6])
def test_bilinear_scalar_reference_irregular(W):
    rng=np.random.default_rng(31);gt=np.cumsum(rng.uniform(.12,.29,17));qt=np.cumsum(rng.uniform(.11,.26,15));scores=rng.uniform(-1,1,(len(qt),len(gt)))
    t=TimeAware(gt,W)
    for i,row in enumerate(scores):actual,w=t.step(row,qt[i]);expected=scalar_time_reference(scores[:i+1],qt[:i+1],gt,W);np.testing.assert_allclose(actual,expected,atol=2e-12,rtol=0)
def test_causal_prefix_future_has_no_effect():
    gt=np.arange(20)*.2;qt=np.arange(15)*.2;rng=np.random.default_rng(7);scores=rng.uniform(-1,1,(15,20));a=TimeAware(gt,.8);b=TimeAware(gt,.8)
    for i in range(8):np.testing.assert_array_equal(a.step(scores[i],qt[i])[0],b.step(scores[i],qt[i])[0])
    with pytest.raises(AssertionError):a.step(scores[8],qt[7])
def test_all_specs_stable_permutations_no_gt_interface():
    base,prop=specifications();gt=np.arange(30)*.2;rng=np.random.default_rng(10)
    for spec in base+prop:
        m=Method(spec,gt)
        for i in range(12):
            o,meta=m.step({'cosplace':rng.uniform(-1,1,30),'eigenplaces':rng.uniform(-1,1,30)},100+i*.2)
            assert sorted(o.tolist())==list(range(30))
def test_position_distance_is_three_dimensional_not_frame_number():
    d={'g':[{'xyz':[0,0,0]}],'q':[{'xyz':[0,0,.5],'valid_gt':True},{'xyz':None,'valid_gt':False}]};dist=distances(d);assert dist[0,0]==.5 and np.isnan(dist[1,0])
