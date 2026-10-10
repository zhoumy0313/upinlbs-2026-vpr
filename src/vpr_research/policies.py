"""Train-only logistic heads; serialized decisions accept five A-only numbers."""
import numpy as np
from scipy.special import expit
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


def feature_matrix(features):
    x=np.asarray(features,dtype=np.float64)
    if x.ndim!=2 or x.shape[1]!=5 or not len(x) or not np.isfinite(x).all():
        raise ValueError("Expected five finite A-only score statistics per query")
    return x


def fit_head(train_features, labels, columns=(0,1,2,3,4), c=1., seed=0, max_iter=2000):
    x=feature_matrix(train_features)[:,columns]
    y=np.asarray(labels)
    if y.shape!=(len(x),) or set(np.unique(y))!={0,1}:
        raise ValueError("Head needs both binary classes in training; report insufficiency")
    scaler=StandardScaler().fit(x)
    classifier=LogisticRegression(C=c,solver="lbfgs",class_weight=None,max_iter=max_iter,random_state=seed)
    classifier.fit(scaler.transform(x),y)
    if classifier.n_iter_[0]>=max_iter:
        raise ValueError("Logistic head did not converge; retain run and investigate")
    return {"columns":list(columns),"mean":scaler.mean_.tolist(),"scale":scaler.scale_.tolist(),
            "variance":scaler.var_.tolist(),"coef":classifier.coef_[0].tolist(),
            "intercept":float(classifier.intercept_[0]),"classes":classifier.classes_.tolist(),
            "n_iter":int(classifier.n_iter_[0]),"n_train":len(x),
            "train_class_counts":{"0":int((y==0).sum()),"1":int((y==1).sum())},
            "hyperparameters":{"C":c,"solver":"lbfgs","class_weight":None,"max_iter":max_iter,"seed":seed}}


def head_probability(head,features):
    x=feature_matrix(features)[:,head["columns"]]
    standardized=(x-np.array(head["mean"]))/np.array(head["scale"])
    return expit(standardized @ np.array(head["coef"])+head["intercept"])


def export_threshold(value):
    if np.isposinf(value):return {"kind":"never","value":None}
    if np.isneginf(value):return {"kind":"always","value":None}
    return {"kind":"finite","value":float(value)}


def threshold_value(spec):
    if spec["kind"]=="never":return float("inf")
    if spec["kind"]=="always":return float("-inf")
    if spec["kind"]!="finite" or not np.isfinite(spec["value"]):
        raise ValueError("Invalid threshold serialization")
    return float(spec["value"])


class ScorePolicy:
    """No query ID, correctness, B descriptor or B score in this API."""
    def __init__(self,spec):
        self.spec=spec
        self.reset()

    def reset(self):
        self.random=np.random.default_rng(self.spec.get("seed",0))

    def score(self,features):
        x=feature_matrix(features)
        kind=self.spec["kind"]
        if kind=="always_A":return np.full(len(x),-1.)
        if kind=="always_B":return np.full(len(x),1.)
        if kind=="gap":return -x[:,1]
        if kind=="random":return self.random.random(len(x))
        heads=self.spec["heads"]
        scores=[head_probability(h,x) for h in heads]
        if kind in {"net_benefit","error_two_head","net_benefit_no_std"}:return scores[0]-scores[1]
        if kind in {"rescue_only","error_single_head"}:return scores[0]
        raise ValueError("Unknown policy kind")

    def decide(self,features):
        values=self.score(features)
        return values,values>threshold_value(self.spec["threshold"])
