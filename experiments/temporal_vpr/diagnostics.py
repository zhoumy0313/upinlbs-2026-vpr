"""Offline label-aware diagnostics; never imported by the online matcher."""
from collections import Counter, defaultdict
import numpy as np

KS = (1,5,10,20,50)

def canonical_rows(rows, image_ids):
    lookup = {r['image_id']:r for r in rows}
    if len(lookup)!=len(rows) or len(set(image_ids))!=len(image_ids):
        raise ValueError('Duplicate image identity')
    if set(image_ids)-set(lookup):
        raise ValueError('Missing manifest image identity')
    return [lookup[i] for i in image_ids]

def rank_diagnostics(scores, positives):
    scores=np.asarray(scores)
    positives=np.asarray(positives,dtype=bool)
    if scores.shape!=positives.shape or scores.ndim!=2 or not positives.any(axis=1).all():
        raise ValueError('Require aligned closed-set scores/GT with positives for every query')
    ranks=np.argsort(-scores,axis=1,kind='stable')
    hits=np.take_along_axis(positives,ranks,axis=1)
    earliest=hits.argmax(axis=1)+1
    summary={f'R@{k}':dict(correct=int((earliest<=k).sum()),queries=len(scores),
                         recall=float((earliest<=k).mean())) for k in KS}
    return ranks,earliest,summary

def union_oracle(ranks_a,ranks_b,positives):
    output={}
    for k in KS:
        ra=ranks_a[:,:k];rb=ranks_b[:,:k]
        success=np.take_along_axis(positives,ra,axis=1).any(axis=1)|np.take_along_axis(positives,rb,axis=1).any(axis=1)
        output[f'Oracle@{k}']=dict(correct=int(success.sum()),queries=len(success),recall=float(success.mean()),
                                 diagnostic_only=True,candidate_limit_per_encoder=k)
    return output

def duplicate_audit(rows):
    groups=defaultdict(list)
    for r in rows:groups[r['sha256']].append(r['image_id'])
    duplicate=[ids for ids in groups.values() if len(ids)>1]
    return dict(records=len(rows),unique_hashes=len(groups),duplicate_groups=len(duplicate),
                records_in_duplicate_groups=sum(map(len,duplicate)),
                duplicate_extra_records=sum(len(g)-1 for g in duplicate),groups=duplicate)

def sequence_rescue_diagnostic(earliest, horizon=3, candidate_k=50):
    # Offline ONLY: a GT-supported candidate occurs in every recent Top-K.
    # This is possible support, not an online decision or proven recovery.
    earliest=np.asarray(earliest)
    possible=np.zeros(len(earliest),dtype=bool)
    for i in range(horizon-1,len(earliest)):
        possible[i]=earliest[i]>1 and np.all(earliest[i-horizon+1:i+1]<=candidate_k)
    return possible
