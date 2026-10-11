"""G6 evidence restoration, independent audit and negative-result handover."""
import json,shutil,subprocess,zipfile
from pathlib import Path
from runtime import ROOT,Run,sha,write,utc
def register():
    rows=[]
    for p in sorted((ROOT/'outputs_v4').glob('*/run_meta.json')):
        folder=p.parent;meta=json.loads(p.read_text());raw=json.loads((folder/'raw_metrics.json').read_text()) if (folder/'raw_metrics.json').exists() else {}
        failed=(folder/'process_failure.json').exists() or raw.get('actual_whole_process_exit_code',0)!=0 or bool((folder/'failures.jsonl').exists() and (folder/'failures.jsonl').stat().st_size)
        archive=ROOT/'artifacts/v4'/folder.name.split('_')[0]/folder.name/'evidence.zip'
        rows.append(dict(run_id=folder.name,parent_git_sha=meta['parent_git_sha'],argv=meta['argv'],cwd=meta['cwd'],started_utc=meta['utc'],failed=failed,whole_process_exit_code=raw.get('actual_whole_process_exit_code'),archive=str(archive.relative_to(ROOT)) if archive.exists() else None,source_snapshot=(folder/'source_snapshot').exists(),closing_snapshot='G6 closing history archive; preserves unfinished/failed runs and checkpoint logs'))
    return rows
def main():
    run=Run('g6_archive',dict(science='negative empirical study',no_additional_blind_run=True,no_test_tuning=True,stage_acceptance='completed bounded study does not imply positive-method gate passed'))
    # Preserve actual output of the already completed deterministic cached replay.
    for n in ['replay_full_stdout.log','replay_full_stderr.log']:shutil.copyfile(ROOT/'outputs_v4'/n,run.path/n)
    write(run.path/'replay_execution_reference.json',dict(argv=['.venv-p0/bin/python','experiments/temporal_alignment_v4/replay.py','--cached'],cwd=str(ROOT),actual_exit_code=0,provenance='Actual exec_command completion recorded in this chat before G6; copied logs, no repeated blind test'))
    run.command([str(ROOT/'.venv-p0/bin/python'),str(ROOT/'experiments/temporal_alignment_v4/final_audit.py'),str(run.path/'final_audit.json')])
    audit=json.loads((run.path/'final_audit.json').read_text())
    history=ROOT/'artifacts/v4/g6'/('closing_history_'+run.id);history.mkdir(parents=True,exist_ok=False);rows=[]
    files=[]
    for p in sorted((ROOT/'outputs_v4').glob('*/run_meta.json')):
        folder=p.parent
        if folder==run.path:continue
        for f in sorted(folder.rglob('*')):
            if f.is_file() and f.suffix in ['.py','.md','.json','.jsonl','.yaml','.csv','.log','.xml','.txt','.actual'] and 'source_snapshot' not in f.parts:
                files.append(f)
        # Existing stage archives retain the original code; failed unsealed runs
        # need their exact source snapshot copied here as well.
        archive=ROOT/'artifacts/v4'/folder.name.split('_')[0]/folder.name/'evidence.zip'
        if not archive.exists():files.extend(f for f in sorted((folder/'source_snapshot').rglob('*')) if f.is_file())
    for p in files:rows.append(dict(path=str(p.relative_to(ROOT)),sha256=sha(p),bytes=p.stat().st_size))
    with zipfile.ZipFile(history/'evidence.zip','x',zipfile.ZIP_LZMA) as z:
        for p in files:z.write(p,p.relative_to(ROOT))
        z.writestr('closing_file_index.json',json.dumps(rows,indent=2));assert z.testzip() is None
    assert (history/'evidence.zip').stat().st_size<90*1024**2
    write(history/'archive_manifest.json',dict(run_id=history.name,zip_sha256=sha(history/'evidence.zip'),zip_bytes=(history/'evidence.zip').stat().st_size,files=len(rows),note='Final actual bytes; historical seals are retained as historical records, not claimed to include later checkpoint writes'))
    # Restore public evidence into a new namespace and independently aggregate it.
    destination=run.path/'fresh_restore'
    run.command([str(ROOT/'.venv-p0/bin/python'),str(ROOT/'experiments/temporal_alignment_v4/restore_evidence.py'),'--destination',str(destination),'--numeric-audit'])
    restored=json.loads((destination/'restore_receipt.json').read_text());write(run.path/'fresh_restore_receipt.json',restored)
    # Do not duplicate the full restored archive tree in this run's public ZIP.
    # Restore files remain local, the recipe, exact hashes and receipts are public.
    destination.rename(ROOT/'outputs_v4'/('restored_evidence_'+run.id))
    state=json.loads((ROOT/'docs/goals/GOAL_V4_STATE.json').read_text())
    claims=dict(data=dict(source='docs/research_v4/DATA_MANIFEST_r02.json',sequences=json.loads((ROOT/'docs/research_v4/DATA_MANIFEST_r02.json').read_text())['sequences']),protocol=dict(source='docs/research_v4/PROTOCOL_METADATA.json',values=json.loads((ROOT/'docs/research_v4/PROTOCOL_METADATA.json').read_text())),selected=dict(source='configs/v4/selected_methods.json',proposed=json.loads((ROOT/'configs/v4/selected_methods.json').read_text())['proposed']),figures=dict(source='docs/research_v4/figures/figure_data.json',values=json.loads((ROOT/'docs/research_v4/figures/figure_data.json').read_text())),orientation=dict(source='docs/research_v4/POSTHOC_DIAGNOSTICS.json',values=json.loads((ROOT/'docs/research_v4/POSTHOC_DIAGNOSTICS.json').read_text())),tables='paper/revisions/v4_r02/numeric_evidence_map.json',all_actual_query_counts_and_geometry_audit=str((run.path/'final_audit.json').relative_to(ROOT)),freeze=state['freeze_folder']+'/freeze.json')
    write(ROOT/'docs/research_v4/NUMERIC_CLAIMS.json',claims)
    versions=[]
    for p in sorted((ROOT/'paper').rglob('main.tex')):
        if 'v4_build_receipts' in p.parts:continue
        pdf=p.with_suffix('.pdf');versions.append(dict(source=str(p.relative_to(ROOT)),source_sha256=sha(p),pdf=str(pdf.relative_to(ROOT)) if pdf.exists() else None,pdf_sha256=sha(pdf) if pdf.exists() else None))
    write(ROOT/'docs/research_v4/PAPER_VERSION_INDEX.json',dict(current='paper/revisions/v4_r02/main.tex',current_pdf='paper/revisions/v4_r02/main.pdf',current_pages=5,older_versions=versions))
    records=register();write(ROOT/'docs/research_v4/RUN_REGISTER.json',records);write(ROOT/'docs/research_v4/FAILURE_REGISTER.json',[r for r in records if r['failed']])
    (ROOT/'docs/research_v4/G6_ACCEPTANCE.md').write_text(f'''# G6 — completed, negative scientific conclusion

Run `{run.id}`. Independent offline geometry audit rechecked {audit['checks']['independent_geometry_and_error_audit']['rows']:,} query-ledger rows / {audit['checks']['independent_geometry_and_error_audit']['metric_groups']:,} metric groups, exact Top-K metre labels, open/invalid masks and error quantiles. Every raw RGB hash and nearest-pose link was independently reconstructed; all frozen science/config/model/archive identities still match. The already executed cached replay exactly reproduces all stored Top10 predictions. The pre-freeze regression proof is 94 passed, 0 failures/errors. Scientific kernels and independent-test parameters were not changed.

V4 r01 is 4 pages, r02 is 5 pages including references and AI disclosure. Both native compilations succeeded; exact-source remote PDFs have all fonts embedded, no unresolved references and no overfull boxes. The raw Long Office association prose erratum (0 -> 2 invalid RGB rows) is corrected without altering any experiment; the entire pre-correction source/PDF/map/receipt remains in v4_review_snapshots. Actual 168 test queries all have valid poses. All table rows and sampling graph points are checked against real evidence.

{audit['checks']['old_files_preserved']:,} V1–V3 files are hash-preserved; old branch references unchanged. Public evidence SHA/ZIP integrity and clean-directory restoration passed; restored numeric ledgers reproduce all 1,995 metric groups. Closing archive `{history.relative_to(ROOT)}` also preserves failed unsealed runs and actual Git checkpoint commands/exit codes. Historical seals remain historical; later checkpoint writes are bound by the closing ledger. Images, model checkpoints, restored copies and large arrays remain local and ignored.

G0–G6 are complete as an auditable study. The G3/G4 *positive effect* gates are FALSE: candidate 34/48 vs baseline envelope 35/48 at 0.5m; 0/20 vs EigenPlaces 11/20 at 0.25m. No positive novelty, SOTA, open-set safety or six-DoF localization claim. The empirical draft is not ready as a positive method paper. Human scientific review would be required for any small negative-result submission; authorship/template/formal submission are unapproved and were not performed.

Input→output: RGB is decoded, normalized/resized to 224×224, encoded into a frozen 512-D descriptor, compared against prior gallery descriptors, then ranked using current/past scores and clocks. The constrained pool changes ranked reference IDs; a separate offline evaluator reads camera poses and computes R@K. Scores are not location coordinates or calibrated correctness probabilities.

Next single research task, if the author elects to continue: justify a representation/geometry mechanism on development data and acquire another unseen independent collection before testing it. Do not retune this now-seen Long Office test. No further autonomous experiment is scheduled.
''')
    (ROOT/'docs/research_v4/RESEARCH_STATUS.md').write_text('# V4 research status — complete\n\nG0–G6 completed and verified. Earlier blocked G0 reports are retained as historical acquisition failures. Independent test: one frozen run, now seen. Positive method gates: false. Current empirical working draft: paper/revisions/v4_r02/main.tex and main.pdf (5 pages). No positive-method submission readiness. Complete evidence: FINAL_RESEARCH_REPORT.md, G6_ACCEPTANCE.md, EVIDENCE_MAP.json, RUN_REGISTER.json and public artifacts/v4 archives. Old V1–V3 originals unchanged.\n')
    with (ROOT/'docs/research_v4/REPRODUCE.md').open('a') as f:f.write('\n## Executable fresh evidence restore\n\n```bash\n.venv-p0/bin/python experiments/temporal_alignment_v4/restore_evidence.py --destination /tmp/v4-evidence-new-directory --numeric-audit\n```\n\nThe destination must not exist. Without --numeric-audit, restoration needs only standard-library Python. Each historical archive has a separate namespace; no original or later snapshot is overwritten. --numeric-audit uses the pinned NumPy environment and recomputes all 1,995 metric groups from restored public CSVs. G6 retains the actual successful command, stdout/stderr and restore receipt.\n')
    evidence=json.loads((ROOT/'docs/research_v4/EVIDENCE_MAP.json').read_text());evidence.update(final_acceptance='docs/research_v4/G6_ACCEPTANCE.md',all_numeric_claims='docs/research_v4/NUMERIC_CLAIMS.json',paper_versions='docs/research_v4/PAPER_VERSION_INDEX.json',independent_geometric_audit=str((run.path/'final_audit.json').relative_to(ROOT)),restore='experiments/temporal_alignment_v4/restore_evidence.py',closing_history=str(history.relative_to(ROOT)));write(ROOT/'docs/research_v4/EVIDENCE_MAP.json',evidence)
    with (ROOT/'docs/research_v4/FINAL_RESEARCH_REPORT.md').open('a') as f:f.write('\n## 最终验收与交付\n\nG0–G6已全部完成。r01为4页，最终r02为5页（含引用与AI声明），精确源稿PDF、应用内编译、字体、引用、版面和表格逐值核验通过。Long Office原始流2张超容差关联的文字错误已更正，修订前全稿/PDF/证据映射完整保留；固定168查询均有效，数值未改。全部1,995组指标及390,810条逐查询几何记录复核，公共ZIP新目录恢复可独立重算。G6_ACCEPTANCE.md保存真实命令/退出码及验收；PAPER_VERSION_INDEX.json给出新旧源稿/PDF的路径和SHA。科学结论仍为负，不能作为已证实优于强基线的方法论文投稿。\n')
    # Resolved acquisition blockers stay in historical metadata instead of being
    # presented as the current stop condition after a completed study.
    keys=['stop_condition','required_external_change','last_blocker_audit_run','blocked_utc','blocked_reason']
    state['historical_acquisition_block']={k:state.pop(k) for k in keys if k in state}
    state.update(status='complete',goal_complete=True,current_stage='complete',g6_run=run.id,verified_scientific_checkpoint=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),positive_method_claim=False,formal_submission_ready=False,completed_utc=utc())
    state['stages']['g5']='passed';state['stages']['g6']='passed';write(ROOT/'docs/goals/GOAL_V4_STATE.json',state)
    run.finish(dict(passed=True,old_files_preserved=audit['checks']['old_files_preserved'],metric_groups=1995,geometric_query_rows=audit['checks']['independent_geometry_and_error_audit']['rows'],fresh_restoration_passed=True,closing_history=str(history.relative_to(ROOT)),positive_method_claim=False,submission_ready=False,final_manuscript_pages=5))
    run.checkpoint('G6 complete preservation independent audit evidence restoration and negative-result handover')
if __name__=='__main__':main()
