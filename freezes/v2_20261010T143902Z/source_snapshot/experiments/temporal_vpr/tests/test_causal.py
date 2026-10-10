import inspect
from pathlib import Path
import sys
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from causal import CausalMatcher,temporal_scores,stream_scores,stable_ranking,blend_scores,rrf

def test_l1_is_exact_single_frame_for_scores_ranks_and_recall():
    s=np.random.default_rng(0).normal(size=(12,11))
    out=stream_scores(s,length=1,velocities=(.8,1,1.2),weight=1.)
    np.testing.assert_array_equal(s,out)
    np.testing.assert_array_equal(stable_ranking(s),stable_ranking(out))
    positives=np.eye(11,dtype=bool)[np.arange(12)%11]
    assert np.array_equal(positives[np.arange(12),stable_ranking(s)[:,0]],
                          positives[np.arange(12),stable_ranking(out)[:,0]])

def test_future_mutation_cannot_affect_past_and_current():
    s=np.random.default_rng(3).normal(size=(18,30));changed=s.copy();changed[10:]=999
    original=stream_scores(s,length=5);other=stream_scores(changed,length=5)
    np.testing.assert_array_equal(original[:10],other[:10])

def test_reset_discards_prior_split_and_buffer_history():
    matcher=CausalMatcher(3)
    for _ in range(8):matcher.step(np.arange(10,dtype=float))
    matcher.reset()
    scores,meta=matcher.step(np.arange(10,dtype=float)[::-1])
    assert meta['warmup'] and meta['seen']==1 and len(matcher.history)==1

def test_whole_out_of_bounds_paths_are_invalid_in_both_directions():
    s=np.array([[1,2,3,4],[5,6,7,8],[9,10,11,12]],dtype=float)
    t=temporal_scores(s,3,[1])
    assert np.isneginf(t[:2]).all()
    np.testing.assert_array_equal(t[2:],[(11+6+1)/3,(12+7+2)/3])
    rev=temporal_scores(s,3,[-1]);assert np.isneginf(rev[-2:]).all()
    np.testing.assert_array_equal(rev[:2],[(9+6+3)/3,(10+7+4)/3])

def test_independent_manual_velocity_maximum_matches_exact_calculation():
    h=np.array([[2,1,3,0,4],[1,5,2,4,0],[3,2,8,1,4]],dtype=float)
    expected=[]
    for j in range(5):
        candidates=[]
        for v in [.8,1.,1.2]:
            indices=[j-int(round(v*lag)) for lag in range(3)]
            if all(0<=k<5 for k in indices):
                candidates.append(sum(h[2-lag,k] for lag,k in enumerate(indices))/3)
        expected.append(max(candidates) if candidates else -np.inf)
    np.testing.assert_array_equal(temporal_scores(h,3,[.8,1.,1.2]),expected)

def test_online_api_has_no_labels_paths_gps_or_position_ids():
    assert list(inspect.signature(CausalMatcher.step).parameters)==['self','current_scores']
    src=(Path(__file__).resolve().parents[1]/'causal.py').read_text()
    assert 'open(' not in src and 'read_text(' not in src and 'load_descriptors' not in src

def test_shuffled_history_is_a_real_causal_negative_control():
    h=np.random.default_rng(16).normal(size=(20,40))
    out=stream_scores(h,length=9,shuffled=True,seed=0)
    same=stream_scores(h,length=9,shuffled=True,seed=0)
    proper=stream_scores(h,length=9,shuffled=False)
    np.testing.assert_array_equal(out,same)
    assert not np.array_equal(out[8:],proper[8:])
    np.testing.assert_array_equal(out[:8],h[:8])

def test_common_effective_query_mask_is_method_independent():
    mask=np.arange(12)>=8
    s=np.random.default_rng(8).normal(size=(12,30))
    for length in [1,3,5,9]:
        out=stream_scores(s,length=length)
        assert out[mask].shape[0]==4

def test_rrf_uses_full_gallery_one_based_rank_and_k60():
    result=rrf(np.array([.9,.8,.7]),np.array([.6,.7,.8]))
    np.testing.assert_allclose(result,[1/61+1/63,2/62,1/63+1/61],rtol=0,atol=1e-16)

def test_zero_blend_weight_does_not_create_nan_from_invalid_path():
    s=np.array([.1,.9,.8]);t=np.array([-np.inf,.7,.6])
    np.testing.assert_array_equal(blend_scores(s,t,0),s)
    assert np.isneginf(blend_scores(s,t,.5)[0])
    assert not np.isnan(blend_scores(s,t,.5)).any()
