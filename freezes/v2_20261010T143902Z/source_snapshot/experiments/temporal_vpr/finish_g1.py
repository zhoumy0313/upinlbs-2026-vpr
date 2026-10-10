"""Publish bounded G1 numerical evidence and record an explicit next-stage plan."""
import argparse
import csv
import json
from pathlib import Path
import shutil
import zipfile
import xml.etree.ElementTree as ET
from runtime import Run,digest,atomic_json,update_state,utc_now

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--diagnosis-run',required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[2]
    data=root/'outputs_v2'/args.diagnosis_run
    m=json.loads((data/'metrics.json').read_text());checks=json.loads((data/'checks.json').read_text())
    assert checks['strict_cache_identity_verified'] and not checks['new_independent_performance_opened']
    run=Run(root,'g1_acceptance',{'development_only':True,'no_novelty_claim':True,
        'next_grid':{'L':[1,3,5,9],'velocities':[0.8,1.0,1.2],'lambda':[0,.25,.5,.75,1],
          'RRF_k':[60],'static_AB_weights':[.25,.5,.75],'score_normalization':'(cosine+1)/2, no fitted statistics',
          'common_mask':'exclude first 8 queries of each split for every method',
          'startup':'report full stream separately; fallback to single frame during method warmup',
          'shuffled_control':'seed 0, permute past L-1 score rows within current causal window, keep current fixed',
          'velocity_sets':[[.8],[1.],[1.2],[.8,1.,1.2]],
          'selection':'validation R@1 common mask, tie shorter window then smaller lambda; train descriptive'}},
        {'diagnosis_run':args.diagnosis_run,'metrics_sha256':digest(data/'metrics.json')})
    run.command([str(root/'.venv-p0/bin/python'),'-m','pytest','tests','experiments/temporal_vpr/tests','-q',
        '--junitxml='+str(run.path/'regression.xml')],{'PYTHONPATH':'','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1'})
    n=sum(int(s.attrib['tests']) for s in ET.parse(run.path/'regression.xml').getroot().findall('testsuite'))
    public=root/'artifacts/v2/g1';public.mkdir(parents=True,exist_ok=False)
    for name in ['metrics.json','checks.json','data_audit.json','examples.json','per_query.csv']:
        shutil.copy2(data/name,public/name)
    run.write('metrics.json',{'stage':'G1','tests_passed':n,'VPR_metrics_path':str((data/'metrics.json').relative_to(root)),
        'scientific_result':'candidate space exists in development; no new method improvement demonstrated'})
    run.write('checks.json',{'phase_passed':True,'literature_full_text_access_limitations_disclosed':True,
        'no_independent_performance_opened':True,'no_old_test_selection':True})
    (run.path/'per_query.csv').write_text('role,count\ntrain,600\nvalidation,300\n')
    (run.path/'interpretation.md').write_text('Accept G1 with explicitly disclosed original-paper access limitations. Proceed with bounded known temporal/RRF baselines, no novelty claim or test-based parameter choice.\n')
    lines=['# G1 diagnosis — development only','',f'Run `{args.diagnosis_run}`; metrics SHA `{digest(data/"metrics.json")}`. Radius ±5 ordinal frames; unchanged gallery of 1750.','','| Split / method | R@1 | R@5 | R@10 | R@20 | R@50 |','|---|---:|---:|---:|---:|---:|']
    for role,models in m['splits'].items():
        for model in ['cosplace','eigenplaces','dinov2']:
            values=[100*models[model]['recall'][f'R@{k}']['recall'] for k in [1,5,10,20,50]]
            lines.append('| '+role+' / '+model+' | '+' | '.join(f'{v:.2f}%' for v in values)+' |')
        values=[100*models['A_B_candidate_union_oracle'][f'Oracle@{k}']['recall'] for k in [1,5,10,20,50]]
        lines.append('| '+role+' / A+B union oracle (diagnostic only) | '+' | '.join(f'{v:.2f}%' for v in values)+' |')
    lines+=['','CosPlace train: 103/600 rank errors with a positive in Top-50, 2/600 missing; validation: 86/300 rank errors and 0/300 missing. GT-supported recent Top-50 candidates are only an offline possibility diagnostic (100 train, 85 validation), never inference features or demonstrated temporal rescues.',
      '', 'All 4100 existing dataset images rehashed and decoded. Nordland raw names 251–2000 correspond to ordinal 1–1750; no train/validation exact duplicate bytes. Old test duplicate audit reproduces 79 groups / 187 records / 542 unique hashes. Visual examples show repeated railway/station structures and large seasonal changes; visual or byte evidence does not prove precise pose or a unique causal explanation for the old accuracy drop. Primary frame tolerance unchanged. GP GThard identity and GTsoft ignore semantics read in original loader/metric code.',
      '', 'Development examples are in the run figures directory; public examples.json contains only IDs/ranks and regenerate instructions: run_g1.py recreates panels from licensed local images. Old descriptive station example: outputs/p4_frozen_20261010_152754_Z1p6iu/figures_readable_v3/example_nordland_both_wrong.png. No old-test retrieval was recomputed here.',
      '', 'Primary literature matrix: RELATED_WORK_MATRIX.md. SMR already addresses trusting temporal matches; adaptive blending is a hypothesis, not an established novelty. Two original papers have metadata/author-follow-up access only, with real HTTP 202/404 records; no unverified equations or scores are attributed to them.',
      '', 'St Lucia official rsync listing is accessible: 3016 regular files, 123,494,841 bytes (~0.123 GB), below the 30 GB cap. Metadata filenames contain UTM zone and traversal/frame IDs, but chronology/segment/GT/licence suitability still requires G4 audit. No data/descriptor performance opened; alternate dataset unused.',
      '', 'Decision: advance to G2 with the grid recorded in this acceptance run before measuring it. All models will share an 8-frame warmup exclusion for main comparisons; full-stream startup will be reported separately.']
    (root/'docs/research_v2/G1_DIAGNOSIS.md').write_text('\n'.join(lines)+'\n')
    report=f'''# G1 acceptance — passed with disclosed literature access limitations

Date: {utc_now()}. Existing 31 tests and V2 tests all pass: {n} total. Development data: 600 train / 300 validation, gallery 1750. No final-test threshold choice or independent score reading. Source/code/inputs: run manifests, strict encoder fingerprints, per-query.csv, data_audit.json, SHA-256 files in artifacts/v2/g1. Negative original DINOv2 caches remain; stale extraction-source fingerprints were rejected and new descriptors built in outputs_v2. Actual commands and zero exits: diagnosis and acceptance commands.jsonl; source access failures retained separately. The first G0 ROS failure remains unchanged.

G1_DIAGNOSIS.md gives the actual R@K, oracle, rank-error counts, examples and GT limitations. RELATED_WORK_MATRIX.md records method/results reading and partial original-paper access explicitly; no full-text claim for inaccessible papers. Original V1 files/results/paper remain unchanged. New files: diagnostics, G1 source/metadata/release scripts and tests, V2 docs and public numeric evidence. Reproduce: `.venv-p0/bin/python experiments/temporal_vpr/run_g1.py` creates a new unique run; test isolation overrides are in argv.json.

Beginner explanation:
1. A photograph enters a frozen encoder and becomes a normalized numeric vector.
2. The vector is compared with all 1750 summer reference vectors.
3. Similarity sorting produces candidate image IDs, not GPS coordinates.
4. Offline labels tell us the first rank with a correct reference within ±5 frames.
5. R@10 is a candidate upper bound, not a new algorithm score.
6. Past observations may help reject visually similar wrong railway scenes.
7. Exact duplicates and station ambiguity require careful GT interpretation.
8. G2 will test this temporal hypothesis without giving GT to the matcher.

Decision: G1 permits bounded baseline exploration; detailed inaccessible-paper comparisons remain a novelty-audit limitation. Next single task: G2 fixed causal temporal and static fusion baselines plus mandatory causal/integration checks. Research mainline still not selected; independent performance unopened.
'''
    (root/'docs/research_v2/G1_ACCEPTANCE.md').write_text(report)
    archive=public/'evidence.zip'
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        folders=[data,run.path]+[p for p in (root/'outputs_v2').glob('g1_primary_sources_*')]+[p for p in (root/'outputs_v2').glob('g1_independent_metadata_*')]
        for folder in folders:
            for path in sorted(folder.rglob('*')):
                if path.is_file() and path.suffix in {'.json','.jsonl','.csv','.yaml','.xml','.log','.md','.py'}:
                    z.write(path,path.relative_to(root).as_posix())
    (public/'SHA256SUMS').write_text(''.join(digest(p)+'  '+p.name+'\n' for p in sorted(public.iterdir()) if p.is_file()))
    state=json.loads((root/'docs/goals/GOAL_V2_STATE.json').read_text());state['stages']['G1']='passed';state['stages']['G2']='in_progress'
    update_state(root,stages=state['stages'],current_stage='G2',stage_status='in_progress',latest_run_id=run.id,
        g1_diagnosis_run=args.diagnosis_run,g2_search_predeclaration=str((run.path/'config_effective.yaml').relative_to(root)))
    (root/'docs/goals/GOAL_V2_STATUS.md').write_text(f'# VPR-GOAL-V2\n\nG0/G1 passed; G2 in progress; G3–G5 pending. Independent performance unopened.\n\nG1 CosPlace validation R@1=71.33%, R@10=97.33%, candidate diagnostic only. No new method improvement established.\nNext: bounded causal temporal/fusion baselines. See docs/research_v2/G1_DIAGNOSIS.md and RELATED_WORK_MATRIX.md for evidence/limits.\n')
    with (root/'docs/research_v2/DECISION_LOG.md').open('a') as f:f.write(f'\n{utc_now()}: G1 accepted; G2 grid and common warmup mask declared in {run.id}, before any G2 score. No old-test-based choice. Access-limited literature remains disclosed.\n')
    with (root/'docs/research_v2/EXPERIMENT_REGISTER.md').open('a') as f:f.write(f'| G1 | GT/order + candidate diagnosis | train/validation only; old test descriptive | {args.diagnosis_run} / {run.id} | passed with text-access limitations |\n')
    with (root/'docs/research_v2/EVIDENCE_INDEX.md').open('a') as f:f.write(f'\nG1 metrics/per-query: artifacts/v2/g1, SHA256SUMS; raw run {args.diagnosis_run}; literature receipts in public stage ZIP, full paper bodies local only.\n')
    print(json.dumps({'run':run.id,'tests':n,'archive_sha256':digest(archive)}))

if __name__=='__main__':main()
