"""Seal completed-stage receipts and verify final normal V3 push, without self-reference."""
import json,re,subprocess,zipfile
from pathlib import Path
from .runtime import ROOT,Run,state,sha,atomic

def main():
    st=state();assert st['current_stage']=='complete'
    run=Run('g7_closing_receipts','archive completed G7/driver/checkpoint receipts and verify final V3 backup',{})
    print(run.id,flush=True)
    for rel,h in json.loads((ROOT/st['freeze_directory']/'freeze.json').read_text())['science_file_sha256'].items():assert sha(ROOT/rel)==h,rel
    for paper in json.loads((ROOT/'docs/research_v3/PDF_NUMERIC_AUDIT.json').read_text())['papers']:
        folder=ROOT/'paper/revisions'/paper['revision']
        assert sha(folder/'main.tex')==paper['source_sha256'] and sha(folder/'main.pdf')==paper['pdf_sha256']
    run.command(['git','merge-base','--is-ancestor','81fbf62dfaf5cdd28a005afbe6853289524b4d4d','HEAD'])
    refs=['refs/heads/main','refs/heads/research/temporal-vpr-v2','refs/heads/research/vpr-v3-endpoint-refinement']
    run.command(['git','ls-remote','origin',*refs])
    remote=subprocess.check_output(['git','ls-remote','origin',*refs],cwd=ROOT,text=True)
    assert '78eb9e45d3bc469630b0c46ad1ea02b318ee151b' in remote and '81fbf62dfaf5cdd28a005afbe6853289524b4d4d' in remote and st['last_pushed_sha'] in remote
    rows=[]
    for p in sorted((ROOT/'outputs_v3').glob('*_checkpoint_*/raw_metrics.json')):
        m=json.loads(p.read_text())
        if 'commit' in m:rows.append(dict(run_id=p.parent.name,receipt_sha256=sha(p),**m))
    atomic(ROOT/'docs/research_v3/GIT_CHECKPOINT_INDEX.json',rows)
    public=ROOT/'artifacts/v3/final';target=public/'closing_receipts.zip';assert not target.exists()
    candidates=[]
    # Capture every completed G7 run plus late layout/receipt corrections. The
    # current closing run is local: future Git commands cannot be in its own commit.
    for folder in sorted((ROOT/'outputs_v3').iterdir()):
        if not folder.is_dir() or folder==run.path or not (folder/'acceptance.json').exists():continue
        if folder.name.startswith(('g7_','G7_')):
            candidates.extend(p for p in folder.rglob('*') if p.is_file() and p.suffix in ['.py','.json','.jsonl','.log','.txt','.xml','.yaml','.md','.tex','.actual'])
    with zipfile.ZipFile(target,'x',zipfile.ZIP_LZMA) as z:
        for p in candidates:z.write(p,p.relative_to(ROOT).as_posix())
        for p in [ROOT/'docs/research_v3/GIT_CHECKPOINT_INDEX.json',ROOT/'docs/research_v3/EXPERIMENT_REGISTER.md',ROOT/'experiments/endpoint_vpr/close_delivery.py']:z.write(p,p.relative_to(ROOT).as_posix())
        assert z.testzip() is None
    patterns=[rb'(?m)^-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',rb'gh[pousr]_[A-Za-z0-9]{30,}',rb'sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}']
    checked=0
    for archive in [public/'complete_text_receipts.zip',target]:
        with zipfile.ZipFile(archive) as z:
            for member in z.infolist():
                data=z.read(member);assert not any(re.search(pattern,data) for pattern in patterns),(archive.name,member.filename,'credential pattern')
                checked+=1
    legacy=[]
    for stage in ['g0','g1']:
        for p in (ROOT/'artifacts/v3'/stage).glob('*.zip'):
            lines=(p.parent/'SHA256SUMS').read_text().splitlines()
            recorded=next(line.split()[0] for line in lines if line.split()[-1]==p.name)
            assert sha(p)==recorded;legacy.append(dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=recorded))
    atomic(public/'CLOSING_RECEIPT.json',dict(scientific_G7_checkpoint_sha=st['last_pushed_sha'],
        preceding_remote_snapshot=remote,old_branches_unchanged=True,all_frozen_scientific_bytes_and_paper_hashes_unchanged=True,
        checkpoint_index_sha256=sha(ROOT/'docs/research_v3/GIT_CHECKPOINT_INDEX.json'),
        legacy_archives=legacy,closing_receipts_sha256=sha(target),text_members_credential_scanned=checked,
        author_brief_reflow=json.loads((ROOT/'docs/research_v3/AUTHOR_BRIEF_REFLOW_AUDIT.json').read_text()),
        current_closing_run=str(run.path.relative_to(ROOT)),
        pointer_note='State last_pushed_sha identifies the verified scientific G7 commit. This closing metadata lives in a later normal commit; post-push proof is retained in the local closing run.'))
    with (ROOT/'docs/research_v3/FINAL_DELIVERY.md').open('a') as f:
        f.write('\n## Closing receipt and author-friendly briefing\nPreferred Chinese briefing: AUTHOR_SUMMARY_ZH_r02.pdf (actual page count and unsplit numeric identifiers checked in AUTHOR_BRIEF_REFLOW_AUDIT.json). Original AUTHOR_SUMMARY_ZH.pdf/md remain unchanged. This is layout only. All completed G7 driver/checkpoint/log/source receipts are additionally in artifacts/v3/final/closing_receipts.zip; CLOSING_RECEIPT.json adds original G0/G1 ZIP identities, checkpoint index and text-credential scan. GOAL_V3_STATE.last_pushed_sha refers to the verified scientific checkpoint, not its own later metadata commit. The post-push HEAD/remote proof lives in '+str(run.path.relative_to(ROOT))+'/actual_post_push_verification.json.\n')
    run.write('model_identity.json',dict(not_new_inference=True))
    run.command(['git','add','docs/goals/GOAL_V3_STATE.json','docs/research_v3','artifacts/v3/final','experiments/endpoint_vpr/brief_layout.py','experiments/endpoint_vpr/close_delivery.py'])
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines()
    assert all((ROOT/p).stat().st_size<100*1024*1024 for p in staged)
    run.command(['git','-c','user.name=Codex','-c','user.email=codex@local','commit','-m','G7: preserve completed state, closing evidence and author briefing'])
    run.command(['git','push','origin','HEAD:research/vpr-v3-endpoint-refinement'])
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    run.command(['git','ls-remote','origin',*refs])
    after=subprocess.check_output(['git','ls-remote','origin',*refs],cwd=ROOT,text=True)
    assert head+'\t'+refs[2] in after and '78eb9e45d3bc469630b0c46ad1ea02b318ee151b' in after and '81fbf62dfaf5cdd28a005afbe6853289524b4d4d' in after
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()
    run.write('actual_post_push_verification.json',dict(local_HEAD=head,remote=after,matching_V3=True,old_main_V2_unchanged=True,working_tree_clean=True))
    run.finish(dict(final_commit=head,public_closing_receipts_sha256=sha(target),credential_scanned_members=checked,
                    old_main_V2_unchanged=True,all_four_source_PDF_hashes_unchanged=True),dict(passed=True,actual_push_verified=True,working_tree_clean=True))
    print(json.dumps(dict(final_commit=head,pushed_and_verified=True,working_tree_clean=True)),flush=True)

if __name__=='__main__':main()
