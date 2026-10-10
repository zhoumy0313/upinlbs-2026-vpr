import importlib.util
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('audit',Path(__file__).with_name('verify_manuscripts.py'))
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)

def test_radius_is_explicit_and_not_best_radius():
    doc={'results':[{'method':'A','radius_m':r,'common':{'R@1':{'correct':n,'queries':10}}} for r,n in [(10,2),(25,5),(50,9)]]}
    assert audit.resolve(doc,'results[method=A;radius_m=10].common.R@1','independent frozen accuracy')['correct']==2
    assert audit.resolve(doc,'results[method=A;radius25].common.R@1','independent frozen accuracy')['correct']==5

def test_validation_not_training():
    doc={'results':[{'method':'A','split':s,'common':{'R@1':{'correct':n,'queries':10}}} for s,n in [('train',9),('validation',4)]]}
    assert audit.resolve(doc,'results[method=A].R@1','development')==4

def test_ambiguous_sources_rejected():
    doc={'results':[{'method':'A','split':'validation','common':{'R@1':{'queries':n}}} for n in [10,11]]}
    with pytest.raises(AssertionError):audit.resolve(doc,'validation.common.R@1.queries','development')

def test_latency_units_unchanged():
    assert audit.resolve({'results':[{'method':'A','total':{'p95_ms':11.4}}]},'results[method=A].total.p95_ms','independent real latency')==11.4
