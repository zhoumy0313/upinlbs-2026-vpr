import inspect
from pathlib import Path
import sys
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from adaptive import AdaptiveMatcher,adaptive_stream,fit_train_gap_scales
from causal import stable_ranking

def settings():return dict(length=3,velocities=[1.],scales={'A_gap_median':.2,'T_gap_median':.2},candidate_count=5)

def test_adaptive_has_no_future_gt_input_and_resets_history():
    assert list(inspect.signature(AdaptiveMatcher.step).parameters)==['self','current_scores']
    s=np.random.default_rng(4).random((12,20));future=s.copy();future[7:]=100
    a,am=adaptive_stream(s,**settings());b,bm=adaptive_stream(future,**settings())
    np.testing.assert_array_equal(a[:7],b[:7]);assert am[:7]==bm[:7]
    matcher=AdaptiveMatcher(**settings());matcher.step(s[0]);matcher.step(s[1]);matcher.step(s[2]);matcher.reset()
    rank,meta=matcher.step(s[3]);assert meta['warmup'] and not matcher.endpoints

def test_topk_reranking_retains_candidate_set_and_original_tail():
    s=np.random.default_rng(7).random((10,20));r,m=adaptive_stream(s,**settings())
    a=stable_ranking(s)
    for i in range(10):
        assert set(r[i,:5])==set(a[i,:5]);np.testing.assert_array_equal(r[i,5:],a[i,5:])
        assert 0<=m[i]['lambda']<=1

def test_train_scales_fit_without_correctness_labels_and_zero_fixed_weight_is_a():
    s=np.random.default_rng(8).random((12,20));scales=fit_train_gap_scales(s,3,[1.])
    assert scales['training_valid_queries']==10 and 'without labels' in scales['fit_role']
    opts=settings();opts['scales']=scales
    r,m=adaptive_stream(s,**opts,fixed_weight=0.)
    np.testing.assert_array_equal(r,stable_ranking(s))
    with pytest.raises(ValueError):fit_train_gap_scales(s[:1],3,[1.])
