import sys
from pathlib import Path
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from diagnostics import canonical_rows,rank_diagnostics,union_oracle,sequence_rescue_diagnostic

def test_exact_first_positive_rank_and_union_are_not_measured_methods():
    s=np.array([[3,2,1],[3,2,1]])
    p=np.array([[False,True,False],[False,False,True]])
    ranks,earliest,metrics=rank_diagnostics(s,p)
    assert earliest.tolist()==[2,3]
    assert metrics['R@1']['correct']==0
    assert metrics['R@5']['correct']==2
    oracle=union_oracle(ranks,np.array([[1,0,2],[2,0,1]]),p)
    assert oracle['Oracle@1']['correct']==2 and oracle['Oracle@1']['diagnostic_only']
    with pytest.raises(ValueError):rank_diagnostics(s,np.zeros_like(p))

def test_manifest_reordering_preserves_id_to_ground_truth_alignment():
    rows=[{'image_id':'q1','frame_index':9},{'image_id':'q2','frame_index':10}]
    assert canonical_rows(rows,['q1','q2'])==canonical_rows(rows[::-1],['q1','q2'])
    with pytest.raises(ValueError):canonical_rows(rows,['q1','q1'])
    with pytest.raises(ValueError):canonical_rows(rows,['unknown'])

def test_gt_diagnostic_has_warmup_and_does_not_claim_online_rescue():
    result=sequence_rescue_diagnostic([2,3,4,99,3,4,5])
    assert result.tolist()==[False,False,True,False,False,False,True]
