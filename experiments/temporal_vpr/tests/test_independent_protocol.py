import sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'experiments/temporal_vpr'))
from prepare_independent import parse_name
from evaluate_independent import hit_vector
from method_suite import Method,specifications

def test_st_lucia_order_uses_pano_sequence_not_utm_or_empty_timestamp():
    a=parse_name('@0499638.99@6958015.36@56@J@-27.50151@0152.99634@100909_0845_03448@@@@@@@@.jpg')
    assert a['traversal']=='100909_0845' and a['source_frame']==3448 and a['timestamp_field']=='' and a['zone']=='56J'

def test_abstention_never_indexes_last_positive_gallery_row():
    assert not hit_vector(np.array([False,False,True]),np.array([-1,-1,-1])).any()
    assert hit_vector(np.array([False,False,True]),np.array([0,-1,2])).tolist()==[False,False,True]

def test_shared_method_factory_resets_and_cannot_read_future():
    scales=dict(A_gap_median=.1,T_gap_median=.1)
    specs=specifications(dict(length=9,velocities=[1.2],weight=.75),scales)
    assert len(specs)==24 and len({s['name'] for s in specs})==24
    s=np.random.default_rng(4).uniform(-1,1,30);v={'cosplace':s}
    for spec in specs:
        if spec['kind'] not in ['temporal','adaptive']:continue
        m=Method(ROOT,spec);first=m.step(v)[0]
        for i in range(12):m.step({'cosplace':np.roll(s,i)})
        m.reset();assert np.array_equal(m.step(v)[0],first)
