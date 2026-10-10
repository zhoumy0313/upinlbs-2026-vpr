import inspect
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from smr_adapter import official_functions,official_window_features,SmrMatcher
ROOT=Path(__file__).resolve().parents[3]

def test_exact_official_diagonal_function_and_causal_feature_window():
    f=official_functions(ROOT)
    sample=np.arange(18).reshape(6,3)
    expected=np.array([[sample[j,0],sample[j+1,1],sample[j+2,2]] for j in range(4)])
    np.testing.assert_array_equal(f['get_diagonals'](sample),expected)
    h=np.random.default_rng(8).uniform(-.5,.9,size=(9,30))
    values=official_window_features(h,f)
    assert values.shape==(4,) and np.isfinite(values).all()
    assert list(inspect.signature(SmrMatcher.step).parameters)==['self','current_scores']
