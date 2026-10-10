"""Nonmutating replay of declared seen-data methods into a new raw run."""
import argparse, json
from .runtime import ROOT, Run, state, sha
from .datasets import seen
from .baselines import predictions, strong_specs, local_specs
from .evaluate import evaluate, record, audit_csv

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', choices=['St_Lucia','Nordland'], default='St_Lucia')
    parser.add_argument('--split', choices=['train','validation'], default='validation')
    parser.add_argument('--suite', choices=['selected','baselines','grid'], default='selected')
    args = parser.parse_args()
    st = state()
    freeze = json.loads((ROOT/st['freeze_directory']/'freeze.json').read_text())
    for rel, digest in freeze['science_file_sha256'].items():
        assert sha(ROOT/rel) == digest, rel
    if args.suite == 'selected':
        wanted = {'A','fixed_L9','full_L3'} | {v['name'] for v in freeze['selection']['selected'].values()}
        specs = [x for x in freeze['methods'] if x['name'] in wanted]
    elif args.suite == 'baselines':
        specs = strong_specs()
    else:
        specs = local_specs()
    d = next(d for d in seen() if d['dataset'] == args.dataset and d['split'] == args.split)
    run = Run('replay_seen', 'fixed seen-data cached-accuracy replay; no phase/push/test-state mutation',
              dict(dataset=args.dataset,split=args.split,suite=args.suite,methods=specs,
                   cached_accuracy_only=True,online_latency_not_measured=True),
              dict(freeze_sha256=sha(ROOT/st['freeze_directory']/'freeze.json')))
    metrics = []
    with (run.path/'per_query.csv').open('w',newline='') as f:
        writer = None
        for spec in specs:
            ranks, meta = predictions(d, spec)
            values, rows = evaluate(d, spec, ranks, meta)
            metrics += values
            writer = record(f,writer,rows)
    checks = audit_csv(run.path/'per_query.csv',metrics)
    run.write('model_identity.json',json.loads((ROOT/st['freeze_directory']/'model_identity.json').read_text()))
    run.write('input_manifest.json.actual',dict(query=d['q'],gallery=d['g'],data_role='already_seen'))
    run.finish(dict(results=metrics,audit=checks,online_latency='not_measured'),
               dict(passed=True,immutable_stages_untouched=True,new_independent_test_not_opened=True))
    print(json.dumps(dict(run_id=run.id,methods=len(specs),groups=len(metrics),path=str(run.path))))

if __name__ == '__main__':
    main()
