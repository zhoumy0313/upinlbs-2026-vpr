"""Evidence-complete G0 stop; no false later-stage acceptance."""
from runtime import *
def main():
    first=json.loads((ROOT/'outputs_v4/download_attempt_1.json').read_text())
    fallback=json.loads((ROOT/'outputs_v4/download_bounded_fallback.json').read_text())
    if any(r['bytes'] for r in first+fallback):raise RuntimeError('Data exists; use real archive audit instead of missing-data stop')
    run=Run('g0_close',dict(stop_condition='GOAL_V4 section 5.1 official acquisition failed',initial_attempts_per_sequence=6,alternate_routes_per_sequence=1,development_test_predictions_computed=False))
    run.command([str(ROOT/'.venv-v2-smr/bin/python'),'-m','pytest','experiments/temporal_alignment_v4/tests','-q','--junitxml='+str(run.path/'archive_security_tests.xml')],env=dict(PYTHONPATH='',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'))
    code=run.command([str(ROOT/'.venv-p0/bin/python'),'experiments/temporal_alignment_v4/audit_data.py'],allow_failure=True);assert code==2
    run.command(['git','ls-remote','--heads','origin'])
    run.command([str(ROOT/'.venv-p0/bin/python'),'-c',"import socket,json; print(json.dumps({h:sorted(set(x[4][0] for x in socket.getaddrinfo(h,443))) for h in ['cvg.cit.tum.de','webshare.cvg.cit.tum.de']}))"])
    manifest=dict(status='official_archives_unavailable',acquisition_passed=False,original_proxy='existing FlClash HTTP/Mixed 127.0.0.1:7890; credentials absent; configuration unchanged',initial_attempt=first,bounded_fallback=fallback,sequences=[dict(sequence=x['sequence'],role=x['role'],archive_local_bytes=0,archive_sha256=None,tar_integrity=None,path_safety=None,rgb_count=None,gt_count=None,valid_gt_match_count=None,time_span_seconds=None) for x in first],retrieval_evaluated=False,independent_test_opened=False)
    write(ROOT/'docs/research_v4/DATA_MANIFEST.json',manifest);write(run.path/'DATA_MANIFEST.json',manifest)
    records=run.path/'input_records';records.mkdir()
    for p in sorted((ROOT/'outputs_v4').iterdir()):
        if p.is_dir() and p!=run.path:
            shutil.copytree(p,records/p.name,ignore=shutil.ignore_patterns('evidence.zip','__pycache__'))
        elif p.is_file():shutil.copyfile(p,records/p.name)
    # Preserve original first seal and subsequent checkpoint changes without rewriting either.
    write(run.path/'collection_receipt.json',dict(captured_source_files=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(records.rglob('*')) if p.is_file()],note='Bootstrap first scientific seal predates its Git checkpoint; original seal and complete later logs both retained. Final collected hashes are authoritative for this collection.'))
    old=preserve();state=json.loads((ROOT/'docs/goals/GOAL_V4_STATE.json').read_text())
    state.update(status='waiting_for_official_data',current_stage='G0',stop_condition='G0 official source unavailable after original retries and one bounded alternate route',stages={f'g{i}':'not_accepted_data_unavailable' if i==0 else 'not_run' for i in range(7)},independent_retrieval_opened=False,positive_method_claim=False,formal_submission_ready=False,latest_run_id=run.id,required_external_change='Both official TUM tgz archives transferred to data/raw/v4/tum_rgbd/archives, or demonstrably restored official-host reachability. Do not repeat unchanged network retries.',blocked_goal_turn_count=1)
    write(ROOT/'docs/goals/GOAL_V4_STATE.json',state)
    report=f'''# G0 stop report — data acquisition not accepted

Current goal is VPR-GOAL-V4. Branch `{BRANCH}` starts from exact V3 `{BASE}`. All {old:,} historical files ({json.loads((ROOT/'artifacts/v4/g0/input_receipt.json').read_text())['old_bytes']:,} bytes) retained and SHA-checked, including all V1–V3 sources, experiments, failures and paper PDFs. `.gitignore` only appended. Main/V2/V3 remote references remain unchanged.

## Actual execution and outcomes

| Work | Actual result |
|---|---|
| Existing environment/SSH/Codex/disk/GPU checks | exit 0; RTX 3060 Laptop 6144MiB, driver 550.107.02; no reinstallation |
| Historical unit regression | 75 passed, exit 0; original XML retained |
| New archive security checks | 10 passed, exit 0; synthetic tests only |
| Official Pioneer download through existing proxy, five retries | curl exit 35, HTTP final 000, 0 bytes, TLS unexpected EOF |
| Official Long Office download through existing proxy, five retries | curl exit 35, HTTP final 000, 0 bytes, TLS unexpected EOF |
| Sole fallback, same official URLs, process-only IPv4 direct | both curl exit 28, final redirect HTTP 302, 0 bytes; webshare port 443 timed out |
| Both outer download scripts | real exit 1, recorded tool receipts |
| Saved local import/audit command | expected exit 2: both archives missing; no extraction, RGB/GT audit or retrieval |
| V4 preservation startup checkpoint | 15c7d8cff36c2e143a2805e9fc41fc40b52f97c0 pushed; exact receipt retained |

The effective official host in every attempt was `https://webshare.cvg.cit.tum.de/g/rgbd/dataset/…`. Existing proxy endpoints contain no credentials. No insecure TLS bypass, mirror, account, system-network setting, GPU driver or global Python change was used. The archive SHA, PNG counts, time spans and GT association counts are **unknown**, not zero-valued successful measurements. The source page is accessible but that does not imply the archive host is reachable.

## Stage decision and research status

Goal §5.1 explicitly says “官方数据无法取得或真值无法校验 → 交付下载诊断、停止盲测”. This gate is exercised. G0 preservation and diagnostics are complete; **G0 data readiness fails**, G1–G6 have **not run**. Initial protocol is saved as a draft only: 5Hz, nearest timestamp GT within 0.03s, first-half gallery with 10s query buffer, metre radii 0.25/0.5/1.0. It is not accepted or frozen. No methods, strong baselines, new mechanism results, independent test, real latency, V4 paper or novelty claims have been fabricated.

The intended contribution needs a strict comparison with mature short windows and simple local reranking, timestamp alignment alone having substantial prior art. V3's already seen negative evidence remains unchanged and is not a substitute for this independent test. No V4 manuscript has been created from absent results; the currently open V3 r04 source/PDF are intact. V4 is **not ready for submission** because its data, scientific experiments and independent evidence are absent.

## Reproduction and next single task

All original argv, working directories, safe environment records, stdout/stderr, true curl exits, retry failures, fingerprints and source snapshots are in the G0 evidence ZIP under artifacts/v4/g0/{run.id}/. Download failures are retained, with original and final logs. `DATA_MANIFEST.json`, `SOURCE_AUDIT.md`, and `MAC_TRANSFER_RESUME.md` distinguish source descriptions, local observations and planned work.

The sole next task is to obtain the **two exact official tgz archives**. The Mac browser/scp procedure is fully written in MAC_TRANSFER_RESUME.md; the existing Ubuntu route has exhausted its permitted bounded alternatives. Once present, `.venv-p0/bin/python experiments/temporal_alignment_v4/audit_data.py` creates a new audited run and safely extracts, then Codex can decode images, verify all metadata and progress the remaining goal automatically. No phase approval is requested. Human formal actions/author approval remain outstanding for any eventual submission.

## Input → model → ranking (planned, not yet a V4 measurement)

1. Input is each real RGB PNG and its acquisition timestamp; raw depth is retained but not used.
2. Frozen CosPlace/EigenPlaces resize/normalize consistently at 224×224.
3. The model emits an L2-normalized 512-dimensional visual descriptor, not camera coordinates.
4. Dot products against earlier gallery descriptors yield one similarity score per reference image.
5. A causal matcher may read current/past scores and RGB timestamps; GT never enters that interface.
6. Time-aware path aggregation and bounded endpoint refinement would yield a complete ranked gallery list.
7. Only the separate evaluator associates motion-capture poses and measures radius-specific Recall/error.
8. Open/no-positive queries must remain visible; true batch-one image inference needs measured timing after real data exists.
'''
    (ROOT/'docs/research_v4/G0_ACCEPTANCE.md').write_text(report)
    (ROOT/'docs/research_v4/RESEARCH_STATUS.md').write_text('# V4 research status\n\nG0 data-ready acceptance: FAILED. G1–G6: NOT RUN. Independent test: UNOPENED. New method claim: UNSUPPORTED / NOT EVALUATED. V4 submission readiness: NO. Old V1–V3 papers preserved.\n\nRequired next change: two official TUM archives, see MAC_TRANSFER_RESUME.md. Do not run retrieval or regenerate papers from missing inputs.\n')
    with (ROOT/'docs/research_v4/SOURCE_AUDIT.md').open('a') as f:f.write('\n## Final observed acquisition outcome\n\nBoth official proxy-route curl commands completed with exit 35 after five retries; sole IPv4 direct fallback completed with exit 28. Both archives have zero local bytes and no SHA. No tar extraction was possible. Exact final URLs/HTTP codes and logs are retained in G0 evidence; official-source descriptions above are not claimed as local measurements.\n')
    write(run.path/'outer_tool_exit_receipts.json',dict(bootstrap=0,download_original=1,download_bounded_fallback=1,ad_hoc_archive_tests=0,source='actual unified exec tool completions; individual UTC command logs retained'))
    run.finish(dict(old_files_preserved=old,legacy_tests=75,synthetic_archive_safety_tests=10,download_original=first,download_fallback=fallback,local_import_exit_code=code,scientific_G0_accepted=False,independent_test_opened=False,next_stage='G0 data import after external file availability'),passed=False)
    run.checkpoint('G0 official-download failure and safe stop')
    print(json.dumps(dict(run_id=run.id,G0_accepted=False,checkpoint_pushed=True,old_files_preserved=old)),flush=True)
if __name__=='__main__':main()
