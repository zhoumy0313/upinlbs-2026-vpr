"""Publish finished G6 process/checkpoint receipts without another experiment."""
import json,shutil,subprocess
from runtime import ROOT,Run,BASE,BRANCH,sha,write,utc
from run_g6 import register
def main():
    state=json.loads((ROOT/'docs/goals/GOAL_V4_STATE.json').read_text());assert state['goal_complete'] and all(v=='passed' for v in state['stages'].values())
    scientific_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    run=Run('publication_final',dict(scientific_checkpoint=scientific_sha,scope='finished G6 actual whole-process and Git receipts only; no new science'))
    g6=ROOT/'outputs_v4'/state['g6_run'];shutil.copytree(g6/'checkpoint',run.path/'g6_checkpoint_receipt')
    wrapper=ROOT/'outputs_v4'/state['latest_run_id'];raw=json.loads((wrapper/'raw_metrics.json').read_text());assert raw['actual_whole_process_exit_code']==0
    for name in ['run_meta.json','raw_metrics.json','commands.jsonl']:shutil.copyfile(wrapper/name,run.path/('g6_execution_'+name))
    run.command(['git','ls-remote','--heads','origin','main','research/temporal-vpr-v2','research/vpr-v3-endpoint-refinement',BRANCH])
    records=register();write(ROOT/'docs/research_v4/RUN_REGISTER.json',records);write(ROOT/'docs/research_v4/FAILURE_REGISTER.json',[r for r in records if r['failed']])
    tracked=subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines()
    allowed=['experiments/temporal_alignment_v4/','configs/v4/','docs/research_v4/','artifacts/v4/','data/manifests/v4/','paper/revisions/v4_','freezes/v4_','.github/workflows/v4']
    assert all(p=='.gitignore' or p in ['docs/goals/GOAL_V4_DATA_READY.md','docs/goals/GOAL_V4_STATE.json'] or any(p.startswith(a) for a in allowed) for p in tracked)
    assert all(not p.endswith(('.tgz','.pth','.npy','.npz')) for p in tracked)
    delivery=dict(goal_id='VPR-GOAL-V4',completed=True,stages=state['stages'],scientific_checkpoint=scientific_sha,branch=BRANCH,base_sha=BASE,independent_test_runs=1,positive_method_claim=False,formal_submission_ready=False,current_paper='paper/revisions/v4_r02/main.tex',current_pdf='paper/revisions/v4_r02/main.pdf',pages=5,source_sha256=sha(ROOT/'paper/revisions/v4_r02/main.tex'),pdf_sha256=sha(ROOT/'paper/revisions/v4_r02/main.pdf'),g6_whole_process_exit_code=0,old_files_preserved=14482,metric_groups=1995,geometric_query_rows=390810,real_timed_query_intervals=25857,publication_run=run.id,utc=utc(),signed_or_submitted=False)
    write(ROOT/'docs/research_v4/FINAL_DELIVERY.json',delivery);state.update(verified_scientific_checkpoint=scientific_sha,final_publication_run=run.id);write(ROOT/'docs/goals/GOAL_V4_STATE.json',state)
    run.finish(delivery);run.checkpoint('G6 final actual execution and pushed checkpoint receipts')
    print(json.dumps(dict(published=True,commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),branch=BRANCH,submission_ready=False)),flush=True)
if __name__=='__main__':main()
