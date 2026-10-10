"""Evaluation and routing helpers, independent of the image encoders.

Convention: rows are queries; columns are database images. Ground truth is
accepted ONLY by evaluation/label-construction functions, never by routing.
This is original reference code for the proposed experiment, not a reproduction
of any cited paper's uncertainty estimator.
"""
from __future__ import annotations
import numpy as np
from numpy.typing import ArrayLike, NDArray


def _matrix(value: ArrayLike, name: str) -> NDArray[np.float64]:
    x = np.asarray(value, dtype=np.float64)
    if x.ndim != 2 or min(x.shape) == 0 or not np.isfinite(x).all():
        raise ValueError(f"{name} must be a nonempty, finite 2D matrix")
    return x


def l2_normalize(descriptors: ArrayLike) -> NDArray[np.float64]:
    x = _matrix(descriptors, "descriptors")
    norms = np.linalg.norm(x, axis=1, keepdims=True)
    if np.any(norms <= 1e-12):
        raise ValueError("Zero descriptor: investigate extraction instead of hiding it")
    return x / norms


def cosine_scores(queries: ArrayLike, database: ArrayLike) -> NDArray[np.float64]:
    q, d = l2_normalize(queries), l2_normalize(database)
    if q.shape[1] != d.shape[1]:
        raise ValueError("Within one encoder, descriptor dimensions must agree")
    return np.clip(q @ d.T, -1.0, 1.0)


def ranking(scores: ArrayLike, k: int) -> NDArray[np.int64]:
    s = _matrix(scores, "scores")
    if not 1 <= k <= s.shape[1]:
        raise ValueError("k must be between 1 and the database size")
    # Stable ordering makes ties deterministic; this tie rule must be reported.
    return np.argsort(-s, axis=1, kind="stable")[:, :k]


def index_positives(query_ids: ArrayLike, database_ids: ArrayLike,
                    radius: int) -> NDArray[np.bool_]:
    """ONLY for a dataset with verified one-to-one aligned traversal frame IDs.
    radius is a frame-index tolerance, never a distance in metres.
    Never feed IDs or the returned mask into the online routing policy.
    """
    q, d = np.asarray(query_ids), np.asarray(database_ids)
    if (q.ndim != 1 or d.ndim != 1 or q.size == 0 or d.size == 0 or
            not np.issubdtype(q.dtype, np.integer) or
            not np.issubdtype(d.dtype, np.integer)):
        raise ValueError("Frame IDs must be nonempty 1D integer arrays")
    if radius < 0 or int(radius) != radius:
        raise ValueError("radius must be a nonnegative integer")
    if len(np.unique(q)) != len(q) or len(np.unique(d)) != len(d):
        raise ValueError("Duplicate IDs must be resolved in the manifest")
    return np.abs(q[:, None] - d[None, :]) <= radius


def recall_at_k(scores: ArrayLike, positives: ArrayLike,
                ks: tuple[int, ...] = (1, 5, 10)) -> dict[str, float]:
    s = _matrix(scores, "scores")
    p = np.asarray(positives)
    if p.dtype != np.bool_ or p.shape != s.shape:
        raise ValueError("positives must be a boolean matrix matching scores")
    if not p.any(axis=1).all():
        raise ValueError("No-positive queries require a SEPARATE open-set protocol")
    ranks = ranking(s, max(ks))
    hits = np.take_along_axis(p, ranks, axis=1)
    return {f"R@{k}": float(hits[:, :k].any(axis=1).mean()) for k in ks}


def top1_correct(scores: ArrayLike, positives: ArrayLike) -> NDArray[np.bool_]:
    s = _matrix(scores, "scores")
    p = np.asarray(positives)
    if p.dtype != np.bool_ or p.shape != s.shape or not p.any(axis=1).all():
        raise ValueError("Invalid closed-set ground truth")
    return np.take_along_axis(p, ranking(s, 1), axis=1)[:, 0]


def score_features(scores: ArrayLike) -> NDArray[np.float64]:
    """Five FAST-ENCODER-ONLY features, with fixed top-10 definition."""
    s = _matrix(scores, "scores")
    if s.shape[1] < 10:
        raise ValueError("At least 10 database images required by this protocol")
    ordered = np.take_along_axis(s, ranking(s, 10), axis=1)
    return np.column_stack((ordered[:, 0],
                            ordered[:, 0] - ordered[:, 1],
                            ordered[:, 0] - ordered[:, 4],
                            ordered.mean(axis=1), ordered.std(axis=1)))


def routing_labels(a_correct: ArrayLike, b_correct: ArrayLike
                   ) -> tuple[NDArray[np.int64], NDArray[np.int64]]:
    a, b = np.asarray(a_correct), np.asarray(b_correct)
    if a.dtype != np.bool_ or b.dtype != np.bool_ or a.ndim != 1 or a.shape != b.shape:
        raise ValueError("Correctness labels must be aligned boolean vectors")
    return ((~a & b).astype(np.int64), (a & ~b).astype(np.int64))


def route_scores(a_scores: ArrayLike, b_scores: ArrayLike,
                 invoke_b: ArrayLike) -> NDArray[np.float64]:
    """Offline simulation. B scores may be cached here, but are NOT gate inputs.
    Online code must first decide and then compute B only for selected queries.
    Both matrices must use identical query and database manifest ordering.
    """
    a, b = _matrix(a_scores, "a_scores"), _matrix(b_scores, "b_scores")
    mask = np.asarray(invoke_b)
    if a.shape != b.shape or mask.dtype != np.bool_ or mask.shape != (a.shape[0],):
        raise ValueError("Scores and invocation mask must be aligned")
    return np.where(mask[:, None], b, a)


def routing_audit(a_correct: ArrayLike, b_correct: ArrayLike,
                  invoke_b: ArrayLike) -> dict[str, float | int | None]:
    a, b, mask = map(np.asarray, (a_correct, b_correct, invoke_b))
    if (a.ndim != 1 or a.size == 0 or a.shape != b.shape or a.shape != mask.shape or
            any(x.dtype != np.bool_ for x in (a, b, mask))):
        raise ValueError("Expected aligned, nonempty boolean vectors")
    rescue = int((mask & ~a & b).sum())
    harm = int((mask & a & ~b).sum())
    count = int(mask.sum())
    return {
        "n_queries": len(a), "n_invoked": count,
        "invocation_fraction": float(mask.mean()),
        "rescues": rescue, "harms": harm,
        "net_gain_percentage_points": 100.0 * (rescue - harm) / len(a),
        "rescue_fraction_among_invoked": rescue / count if count else None,
        "harm_fraction_among_invoked": harm / count if count else None,
        "fast_r1": float(a.mean()), "second_r1": float(b.mean()),
        "routed_r1": float(np.where(mask, b, a).mean()),
        "oracle_r1_DIAGNOSTIC_ONLY": float((a | b).mean()),
    }


def validation_threshold(scores: ArrayLike, budget: float,
                         positive_only: bool = True) -> float:
    """Threshold fitted on VALIDATION ONLY; use strict 'score > threshold'.
    Ties are conservative: the attained validation fraction may be smaller than
    budget. Test invocation fraction is NOT guaranteed under domain shift.
    """
    x = np.asarray(scores, dtype=np.float64)
    if x.ndim != 1 or x.size == 0 or not np.isfinite(x).all() or not 0 <= budget <= 1:
        raise ValueError("Invalid validation scores or budget")
    n = int(np.floor(budget * len(x)))
    if n == 0:
        return float("inf")
    if n == len(x):
        threshold = float("-inf")
    else:
        ordered = np.sort(x)
        excluded, selected = float(ordered[-(n + 1)]), float(ordered[-n])
        # Use the interior of an untied quantile interval so scalar/batch
        # round-off at the observed excluded score cannot flip a decision.
        # For a tied boundary, retain conservative strict-greater behavior.
        threshold = excluded + (selected - excluded) / 2 if selected > excluded else excluded
    return max(threshold, 0.0) if positive_only else threshold
