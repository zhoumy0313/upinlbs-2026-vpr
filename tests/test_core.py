import numpy as np
import pytest
from vpr_research.core import *


def test_cosine_l2_same_ranking():
    rng = np.random.default_rng(7)
    q, d = l2_normalize(rng.normal(size=(6, 8))), l2_normalize(rng.normal(size=(20, 8)))
    scores = q @ d.T
    dist = ((q[:, None] - d[None, :]) ** 2).sum(axis=2)
    np.testing.assert_allclose(dist, 2 - 2 * scores, atol=1e-12)
    np.testing.assert_array_equal(ranking(scores, 20), np.argsort(dist, axis=1))


def test_self_retrieval():
    x = np.eye(12)
    scores = cosine_scores(x, x)
    p = index_positives(np.arange(12), np.arange(12), 0)
    assert recall_at_k(scores, p) == {"R@1": 1., "R@5": 1., "R@10": 1.}


def test_reorder_preserves_metrics_only_with_ids():
    p = index_positives([1, 7], [7, 2, 1], 0)
    scores = np.array([[0., 0., 1.], [1., 0., 0.]])
    assert recall_at_k(scores, p, (1,))["R@1"] == 1
    perm = [2, 0, 1]
    p2 = index_positives([1, 7], np.array([7, 2, 1])[perm], 0)
    assert recall_at_k(scores[:, perm], p2, (1,))["R@1"] == 1


def test_topk_and_radius_monotone():
    rng = np.random.default_rng(1)
    s = rng.normal(size=(30, 30))
    p0 = index_positives(np.arange(30), np.arange(30), 0)
    p5 = index_positives(np.arange(30), np.arange(30), 5)
    r0, r5 = recall_at_k(s, p0), recall_at_k(s, p5)
    assert r0["R@1"] <= r0["R@5"] <= r0["R@10"]
    assert all(r5[k] >= r0[k] for k in r0)


def test_zero_descriptor_fails():
    with pytest.raises(ValueError):
        l2_normalize(np.zeros((2, 5)))


def test_missing_positive_not_silently_dropped():
    with pytest.raises(ValueError):
        recall_at_k(np.eye(12), np.zeros((12, 12), bool))


def test_rescue_harm_identity():
    a = np.array([0, 1, 0, 1, 1], dtype=bool)
    b = np.array([1, 0, 0, 1, 1], dtype=bool)
    mask = np.array([1, 1, 1, 0, 0], dtype=bool)
    audit = routing_audit(a, b, mask)
    assert audit["rescues"] == 1 and audit["harms"] == 1
    assert audit["routed_r1"] == audit["fast_r1"]
    assert audit["oracle_r1_DIAGNOSTIC_ONLY"] >= audit["routed_r1"]


def test_gate_features_no_gt_no_second_model():
    s = np.tile(np.linspace(1, 0, 10), (3, 1))
    f = score_features(s)
    assert f.shape == (3, 5)
    assert np.allclose(f[:, 0], 1.)


def test_route_zero_and_full():
    a, b = np.ones((4, 10)), np.zeros((4, 10))
    np.testing.assert_array_equal(route_scores(a, b, np.zeros(4, bool)), a)
    np.testing.assert_array_equal(route_scores(a, b, np.ones(4, bool)), b)


def test_validation_budget_and_ties():
    x = np.array([.1, .2, .3, .4, .5, .5, .5, .8])
    t = validation_threshold(x, .25)
    assert (x > t).mean() <= .25
    assert np.isinf(validation_threshold(x, 0))
    assert validation_threshold(-x, 1) == 0


def test_gate_fit_independent_of_test_labels():
    from vpr_research.gate import BenefitGate
    rng = np.random.default_rng(17)
    train = rng.normal(size=(240, 5))
    a = train[:, 0] > 0
    b = train[:, 1] > 0
    model = BenefitGate().fit(train, a, b)
    test = rng.normal(size=(20, 5))
    before = model.score(test)
    unused_test_labels = rng.integers(0, 2, size=20)
    unused_test_labels[:] = 1 - unused_test_labels
    np.testing.assert_array_equal(before, model.score(test))
    assert np.isfinite(before).all()


def test_insufficient_classes_fails():
    from vpr_research.gate import BenefitGate
    with pytest.raises(ValueError):
        BenefitGate().fit(np.ones((10, 5)), np.ones(10, bool), np.ones(10, bool))
