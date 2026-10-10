import json
import numpy as np
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from vpr_research.core import score_features
from vpr_research.online import ConditionalRetriever
from vpr_research.policies import ScorePolicy,export_threshold,fit_head,head_probability
from vpr_research.retrieval import ExactCosineIndex


def test_serialized_head_matches_sklearn_and_scaler_is_train_only():
    rng=np.random.default_rng(73)
    train=rng.normal(size=(200,5));target=(train[:,0]+train[:,2]>0).astype(int)
    unseen=rng.normal(10,3,size=(30,5))
    head=json.loads(json.dumps(fit_head(train,target)))
    reference=make_pipeline(StandardScaler(),LogisticRegression(C=1.,solver="lbfgs",max_iter=2000,random_state=0))
    reference.fit(train,target)
    np.testing.assert_allclose(head["mean"],train.mean(axis=0),atol=1e-14)
    np.testing.assert_allclose(head_probability(head,unseen),reference.predict_proba(unseen)[:,1],atol=1e-14)


def test_no_b_encoder_or_b_retrieval_before_negative_gate():
    events=[]
    class Encoder:
        def encode(self,images):events.append("A_encode");return np.eye(12)[:1]
    class ForbiddenB:
        def encode(self,images):raise AssertionError("B called despite no trigger")
    class Gate:
        def decide(self,features):
            events.append("decision")
            np.testing.assert_allclose(features,score_features(np.eye(12)[:1]))
            return np.array([-1.]),np.array([False])
    pipeline=ConditionalRetriever(Encoder(),ExactCosineIndex(np.eye(12)),ForbiddenB(),ExactCosineIndex(np.eye(12)),Gate())
    result=pipeline.infer(object())
    assert events==["A_encode","decision"] and not result["invoked_B"]
    assert pipeline.a_calls==1 and pipeline.b_calls==0


def test_positive_gate_calls_b_after_decision_and_replaces_full_ranking():
    events=[]
    class A:
        def encode(self,images):events.append("A_encode");return np.eye(12)[:1]
    class B:
        def encode(self,images):events.append("B_encode");return np.eye(12)[[7]]
    class Gate:
        def decide(self,features):events.append("decision");return np.array([1.]),np.array([True])
    pipeline=ConditionalRetriever(A(),ExactCosineIndex(np.eye(12)),B(),ExactCosineIndex(np.eye(12)),Gate())
    result=pipeline.infer(object())
    assert events==["A_encode","decision","B_encode"]
    np.testing.assert_array_equal(result["scores"],np.eye(12)[[7]])
    assert result["ranks"][0,0]==7 and pipeline.b_calls==1


def test_policy_rejects_extra_label_fields_and_single_class_training():
    with pytest.raises(ValueError):fit_head(np.ones((10,5)),np.zeros(10))
    policy=ScorePolicy({"kind":"gap","threshold":export_threshold(0)})
    with pytest.raises(ValueError):policy.decide(np.ones((1,6)))
    with pytest.raises(ValueError):policy.decide([[float("nan")]*5])


def test_infinite_threshold_json_and_random_stream_are_reproducible():
    spec={"kind":"random","seed":3,"threshold":export_threshold(float("inf"))}
    json.dumps(spec,allow_nan=False)
    policy=ScorePolicy(spec)
    x=np.ones((30,5));v,mask=policy.decide(x)
    assert not mask.any()
    policy.reset();v2,_=policy.decide(x)
    np.testing.assert_array_equal(v,v2)


def test_validation_threshold_has_margin_at_untied_cut_and_conservative_ties():
    from vpr_research.core import validation_threshold
    values=np.array([.1,.2,.3,.4])
    threshold=validation_threshold(values,.25,False)
    assert .3<threshold<.4
    jitter=np.array([0,0,1e-15,-1e-15])
    np.testing.assert_array_equal(values>threshold,(values+jitter)>threshold)
    assert (np.array([.1,.2,.3,.3])>validation_threshold([.1,.2,.3,.3],.25,False)).sum()==0
