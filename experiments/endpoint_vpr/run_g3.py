import csv,json
from .runtime import ROOT,Run,state,publish,checkpoint,sha,utc
from .datasets import seen
from .baselines import predictions,local_specs
from .evaluate import evaluate,record,audit_csv

def main():
    st=state();assert st['stages']['G2']=='passed' and st['H1_gate']
    config=dict(protocol_sha256=sha(ROOT/'configs/v3/v3_protocol_proposed.yaml'),grid_sha256=sha(ROOT/'configs/v3/v3_search_grid.yaml'),optional_module='none',negative_results_retained=True,all_prespecified_sensitivities=True)
    run=Run('g3_bounded_grid','32 P + 32 R1 + 160 R2 configurations',config,dict(baseline_run=st['g2_run']));print(run.id,flush=True)
    run.command([str(ROOT/'.venv-p0/bin/python'),'-m','pytest','experiments/endpoint_vpr/tests','-q','--junitxml='+str(run.path/'tests.xml')],env={'PYTHONPATH':'','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1'})
    ds=[d for d in seen() if d['split']!='descriptive'];run.write('model_identity.json',{d['dataset']+'_'+d['split']:d['model_identity'] for d in ds});run.write('canonical_manifest.json',[dict(dataset=d['dataset'],split=d['split'],q=d['q'],g=d['g'],manifest_sha256=d['manifest_sha256']) for d in ds]);specs=local_specs();assert len(specs)==224;run.write('method_specs.json',specs)
    metrics=[];f=(run.path/'per_query.csv').open('w',newline='');w=None
    for d in ds:
        for k,spec in enumerate(specs):
            p,meta=predictions(d,spec);m,rows=evaluate(d,spec,p,meta);metrics.extend(m);w=record(f,w,rows)
            if (k+1)%32==0:print(d['dataset'],d['split'],k+1,'/',len(specs),flush=True)
    f.close();audit=audit_csv(run.path/'per_query.csv',metrics);run.write('independent_numeric_audit.json',audit)
    baseline=json.loads((ROOT/'outputs_v3'/st['g2_run']/'raw_metrics.json').read_text())['results'];allrows=baseline+metrics
    def m(name,dataset='St_Lucia',radius=10):return next(m for m in allrows if m['method']==name and m['dataset']==dataset and m['split']=='validation' and m['radius']==radius)
    def key(spec):
        n=spec['name'];return (-m(n)['correct']['1'],-m(n,radius=25)['correct']['1'],-m(n,'Nordland',5)['correct']['1'],spec.get('H',0),spec.get('r',0),spec.get('epsilon',spec.get('gamma',0)),n)
    chosen={kind:min([s for s in specs if s['kind']==kind],key=key) for kind in ['P','R1','R2']}
    fixedspecs=[s for s in json.loads((ROOT/'outputs_v3'/st['g2_run']/'method_specs.json').read_text()) if s['kind'] not in ['control','R1','R2']]
    bestfixed=min(fixedspecs,key=key);simple=max([chosen['R1'],chosen['R2']],key=lambda s:m(s['name'])['correct']['1']);allstrong=bestfixed if key(bestfixed)<key(simple) else simple
    p=chosen['P']['name'];b=allstrong['name'];pn=m(p)['correct']['1'];bn=m(b)['correct']['1'];wide=m(p,radius=25)['correct']['1']>=m(b,radius=25)['correct']['1'];nloss=m('fixed_L9','Nordland',5)['correct']['1']-m(p,'Nordland',5)['correct']['1'];supported=pn-bn>=2 and wide and nloss<=1
    selection=dict(selected=chosen,strongest_fixed=bestfixed,strongest_non_P=allstrong,P_strict_correct=pn,strong_strict_correct=bn,common_queries=m(p)['queries'],net_over_strong=pn-bn,wide_nondegradation=wide,Nordland_loss_vs_L9=nloss,quantitative_gate_passed=supported,novelty_claim_supported=False,outcome='B' if supported else 'C',independent_test_not_opened=True,selected_utc=utc(),decision='freeze_as_candidate_pending_external_validation' if supported else 'failed_candidate_empirical_audit_no_extra_module')
    # No independent evidence yet: even a development gate does not establish novelty.
    run.write('selection.json',selection);run.finish(dict(results=metrics,selection=selection,configuration_count=224,all_grid_failures_or_negative_results_retained=True),dict(passed=True,numeric_audit=audit['passed'],method_success=supported,finite_search_complete=True))
    (ROOT/'configs/v3/v3_selected_methods.json').write_bytes((run.path/'selection.json').read_bytes())
    report=f'''# G3 acceptance\n1. Executed the declared finite 224-config grid: 32 P, 32 R1, 160 R2. R3 is the H=1 R1 alias, not an invented distinct algorithm.\n2. Coarse T yields finite same-traversal candidates; P permits only candidates within epsilon of best T, then ranks by current S; remaining gallery completes by S. No GT or future input. Cache replay accelerates development only, not timing.\n3. `.venv-p0/bin/python -m experiments.endpoint_vpr.run_g3`; CPU accuracy, 10 synthetic tests, per-query top10/candidates/eligible/paths/threshold sensitivities and raw outcomes preserved.\n4. Selected P: {p}: {pn}/{m(p)['queries']} strict 10m. Strongest non-P: {b}: {bn}/{m(b)['queries']}. Net {pn-bn}; 25m nondegradation={wide}; Nordland loss vs L9={nloss}. Every H/r/gamma/epsilon combination and baseline shuffling/reverse history control remains available.\n5. Identical split resets, masks, encoders and labels. St Lucia/Nordland validation are already seen; cannot claim blind generalization.\n6. Predeclared development gate={supported}. Outcome {selection['outcome']} provisionally. No additional mechanism will be added after a negative P result. Novel contribution remains unsupported pending source and independent checks.\n7. Broad oracle coverage does not guarantee usable performance; strict label uncertainty and high baseline ceiling remain.\n8. Full per-query archive, hashes and selection timestamp; push receipt follows.\n9. Next: complete independent-source access audit, then freeze the final comparison without opening new predictions.\n'''
    publish('g3',run,report);(ROOT/'docs/research_v3/G3_BOUNDED_EXPERIMENTS.md').write_text(report);(ROOT/'docs/research_v3/DECISION_LOG.md').open('a').write('\n'+utc()+' G3 '+json.dumps(selection)+'\n');st['stages']['G3']='passed' if supported else 'scientifically_negative';state(stages=st['stages'],current_stage='G4',g3_run=run.id,latest_run_id=run.id,selected_candidate=chosen['P'],research_outcome=selection['outcome'],novelty_claim_supported=False);checkpoint('G3')
if __name__=='__main__':main()
