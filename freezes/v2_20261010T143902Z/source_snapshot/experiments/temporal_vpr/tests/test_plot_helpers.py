import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from plot_helpers import baseline_plot_points

def test_plot_refuses_inconsistent_counts_and_labels_development():
    row={'split':'validation','method':'temporal_fixture','settings':{'velocities':[.8,1,1.2],'length':3,'weight':.5},
         'common':{'R@1':{'queries':10,'correct':7,'recall':.7}}}
    assert baseline_plot_points({'results':[row]})[0]['data_role'].startswith('development')
    row['common']['R@1']['correct']=8
    with pytest.raises(ValueError):baseline_plot_points({'results':[row]})
