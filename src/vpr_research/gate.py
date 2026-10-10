"""Small supervised gain-minus-harm gate; visual encoders remain frozen.

Not a certified probability model or a safety guarantee. Class probabilities
are used as a ranking score; calibration and out-of-domain behavior require
experiments. No pretrained weights, test labels or second-encoder features are
accepted by score().
"""
from __future__ import annotations
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from .core import routing_labels


class BenefitGate:
    def __init__(self, c: float = 1.0, seed: int = 0):
        self.c = c
        self.seed = seed
        self.models = []

    def fit(self, train_features, train_a_correct, train_b_correct):
        x = np.asarray(train_features, dtype=float)
        yp, yn = routing_labels(train_a_correct, train_b_correct)
        if x.shape != (len(yp), 5) or not np.isfinite(x).all():
            raise ValueError("Need five finite, fast-encoder-only training features")
        if any(len(np.unique(y)) != 2 for y in (yp, yn)):
            raise ValueError("One target lacks both classes; report data insufficiency")
        self.models = []
        for y in (yp, yn):
            model = make_pipeline(StandardScaler(), LogisticRegression(
                C=self.c, solver="lbfgs", max_iter=2000, random_state=self.seed))
            model.fit(x, y)
            self.models.append(model)
        return self

    def components(self, features):
        if len(self.models) != 2:
            raise RuntimeError("Call fit on the training split first")
        x = np.asarray(features, dtype=float)
        if x.ndim != 2 or x.shape[1] != 5 or not np.isfinite(x).all():
            raise ValueError("Need five finite fast-encoder-only features")
        return tuple(m.predict_proba(x)[:, 1] for m in self.models)

    def score(self, features):
        rescue_score, harm_score = self.components(features)
        return rescue_score - harm_score
