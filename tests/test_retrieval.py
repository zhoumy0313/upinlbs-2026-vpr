import numpy as np
import pytest
from vpr_research.core import cosine_scores, ranking
from vpr_research.retrieval import ExactCosineIndex


def test_index_agrees_with_dense_reference_and_stable_ties():
    rng=np.random.default_rng(31)
    db=rng.normal(size=(13,8));db[4]=db[2]
    query=np.vstack([db[2],rng.normal(size=8)])
    index=ExactCosineIndex(db)
    score,ranks=index.search(query)
    np.testing.assert_allclose(score,cosine_scores(query,db),atol=1e-14)
    np.testing.assert_array_equal(ranks,ranking(cosine_scores(query,db),10))
    assert ranks[0,:2].tolist()==[2,4]


def test_index_rejects_cross_encoder_dimensions_and_zero_vectors():
    with pytest.raises(ValueError):ExactCosineIndex(np.zeros((12,8)))
    index=ExactCosineIndex(np.eye(12))
    with pytest.raises(ValueError):index.search(np.ones((1,8)))
