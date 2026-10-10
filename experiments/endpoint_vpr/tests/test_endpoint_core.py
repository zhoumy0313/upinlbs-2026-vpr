import inspect
import numpy as np
import pytest
from experiments.endpoint_vpr.core import rank,candidates,refine,Temporal,align_by_ids
from experiments.endpoint_vpr.datasets import checked_load
from experiments.endpoint_vpr.baselines import Strategy

def test_synthetic_drift_and_wrong_neighborhood():
 s=np.array([.1,.2,.9,.4,.3]);t=np.array([.1,.2,.8,.85,.2]);tr=['a']*5
 p,m=refine(s,t,tr,r=1,epsilon=.06);assert p[0]==2
 p,m=refine(s,np.array([.95,.2,.1,.1,.1]),tr,r=1,epsilon=.06);assert p[0]!=2

def test_limits_and_completion():
 s=np.array([.1,.9,.5,.4]);t=np.array([-np.inf,.7,.8,.2]);tr=['a']*4
 assert candidates(t,1,0,tr).tolist()==[2]
 assert refine(s,t,tr,r=0)[0][0]==2
 assert refine(s,t,tr,r=2,epsilon=0)[0][0]==2
 assert np.array_equal(refine(s,t,tr,r=3,epsilon=100)[0],refine(s,t,tr,kind='R1',r=3)[0])
 p,m=refine(s,t,tr,H=3,r=2,epsilon=1);assert sorted(p)==list(range(4));assert len(m['candidates'])==len(set(m['candidates']))

def test_ties_edges_traversal_empty_fallback():
 t=np.array([.5,.5,-np.inf,.4]);tr=['a','a','b','b'];assert rank(t).tolist()==[0,1,3,2]
 assert candidates(t,1,5,tr).tolist()==[0,1]
 p,m=refine([.1,.2,.3,.4],[-np.inf]*4,tr);assert p[0]==3 and m['fallback_reason']=='empty_candidates'
 p,m=refine([.1,.2,.3,.4],t,tr,warm=True);assert p[0]==3 and m['fallback_reason']=='startup'

@pytest.mark.parametrize('bad',[np.nan,np.inf])
def test_invalid(bad):
 with pytest.raises(ValueError):rank([bad,.1])
 with pytest.raises(ValueError):refine([bad,.1],[.1,.2],['a','a'])
 with pytest.raises(ValueError):Temporal().step([bad,.1],['a','a'])

def test_causal_and_reset():
 tr=['a']*10;s=np.random.default_rng(1).random((8,10));m=Temporal(3,[.8,1,1.2]);old=[m.step(x,tr)[0] for x in s[:4]]
 s[4]=0.;n=Temporal(3,[.8,1,1.2]);new=[n.step(x,tr)[0] for x in s[:4]];assert all(np.array_equal(a,b) for a,b in zip(old,new))
 m.reset();v,w=m.step(s[0],tr);assert w and np.array_equal(v,s[0])

def test_scalar_independent_temporal():
 h=np.random.default_rng(3).random((9,20));tr=['a']*20;m=Temporal(9,[.8,1,1.2]);t=[m.step(x,tr)[0] for x in h][-1]
 ref=[]
 for j in range(20):
  vals=[]
  for v in [.8,1,1.2]:
   ix=[j-round(v*lag) for lag in range(9)]
   if min(ix)>=0:vals.append(sum(h[-lag-1,k] for lag,k in enumerate(ix))/9)
  ref.append(max(vals) if vals else -np.inf)
 np.testing.assert_array_equal(np.isfinite(t),np.isfinite(ref));np.testing.assert_allclose(t[np.isfinite(t)],np.array(ref)[np.isfinite(t)],atol=1e-15)

def test_id_alignment_and_bad_cache(tmp_path):
 a=np.array([[.1,.9],[.8,.2]]);b=align_by_ids(a[:,::-1],['q1','q2'],['g2','g1'],['q1','q2'],['g1','g2']);np.testing.assert_array_equal(a,b)
 p=tmp_path/'a.npy';np.save(p,a)
 with pytest.raises(ValueError,match='fingerprint'):checked_load(p,'0'*64)

def test_gt_interface_and_all_ranking():
 assert list(inspect.signature(Strategy.step).parameters)==['self','scores']
 for k in ['P','R1','R2']:
  m=Strategy(dict(name=k,kind=k,backend='fixed_L9',H=1,r=1,epsilon=.01,gamma=.5),['a']*12)
  for _ in range(10):p,meta=m.step({'cosplace':np.arange(12)/12});assert sorted(p)==list(range(12))

def test_manual_metrics_and_thresholds_never_change_rank():
 s=np.array([.2,.9,.6]);r=rank(s);distance=np.array([20,11,9]);assert not (distance[r[:1]]<=10).any();assert (distance[r[:2]]<=10).any();assert (distance[r[:1]]<=25).any();assert np.array_equal(r,rank(s))

def test_no_positive_common_mask_and_geographic_thresholds():
 from experiments.endpoint_vpr.evaluate import evaluate
 from experiments.endpoint_vpr.baselines import predictions
 scores=np.tile(np.arange(12)/12,(14,1));distance=np.full((14,12),100.);distance[:,11]=9.;distance[8,:]=100.
 d=dict(dataset='synthetic_not_real',split='validation',scores={'cosplace':scores,'eigenplaces':scores,'dinov2':scores},q=[dict(image_id=f'q{i}') for i in range(14)],g=[dict(image_id=f'g{i}',traversal='a') for i in range(12)],distance=distance,radii=[10,25],unit='metres',primary=10)
 specs=[dict(name='A',kind='single',encoder='cosplace'),dict(name='P',kind='P',backend='fixed_L9',H=1,r=1,epsilon=.01)]
 ms=[]
 for spec in specs:
  pred,meta=predictions(d,spec);m,rows=evaluate(d,spec,pred,meta);ms.append(m);assert m[0]['queries']==5;assert m[0]['no_positive']==1;assert rows[8]['common_valid']==0
 assert ms[0][0]['queries']==ms[1][0]['queries']

def test_gt_payload_ignored_and_canonical_reorder_preserves_strategy():
 s=np.linspace(.1,.9,15);tr=['a']*15;spec=dict(name='P',kind='P',backend='fixed_L9',H=3,r=2,epsilon=.03);m=Strategy(spec,tr);n=Strategy(spec,tr)
 for i in range(12):
  p,_=m.step({'cosplace':s,'query_GPS':[1,2],'GT_correct':True});q,_=n.step({'cosplace':s,'query_GPS':[9,8],'GT_correct':False});assert np.array_equal(p,q)
 perm=np.random.default_rng(4).permutation(15);ids=[f'g{i}' for i in range(15)];canonical=align_by_ids(s[perm][None,:],['q'],[ids[i] for i in perm],['q'],ids)[0];np.testing.assert_array_equal(s,canonical)

@pytest.mark.parametrize('kwargs',[{'H':0},{'r':-1},{'H':1.5}])
def test_bad_candidate_parameters(kwargs):
 with pytest.raises(ValueError):candidates([.1,.2],kwargs.get('H',1),kwargs.get('r',1),['a','a'])
