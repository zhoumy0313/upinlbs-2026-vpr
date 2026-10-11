from runtime import *
from protocol import *
def main():
    import_path=ROOT/'outputs_v4/g0_import_20261011T032146Z_0de0ebd8/DATA_MANIFEST.json'
    receipts=json.loads(import_path.read_text())['sequences'];assert all(x['status']=='archive_extracted_safely' for x in receipts)
    s=json.loads((ROOT/'docs/goals/GOAL_V4_STATE.json').read_text());s.update(status='active',current_stage='G0',blocked_goal_turn_count=0,resumed_utc=utc(),resumed_by='user supplied official archives and explicitly requested continuation');write(ROOT/'docs/goals/GOAL_V4_STATE.json',s)
    run=Run('g0_metadata_audit',dict(import_receipt_sha256=sha(import_path),draft_protocol_sha256=sha(ROOT/'configs/v4/protocol_draft.yaml'),no_retrieval=True))
    summaries=[]
    for receipt in receipts:
        rows,summary=audit_sequence(receipt,run);summaries.append(summary)
    write(run.path/'DATA_MANIFEST.json',dict(sequences=summaries));write(ROOT/'docs/research_v4/DATA_MANIFEST_r02.json',dict(status='data_locally_audited',sequences=summaries,prior_download_failures_retained=True,independent_retrieval_opened=False))
    (ROOT/'docs/research_v4/G0_RESUME_ACCEPTANCE.md').write_text('# G0 resumed — passed\n\nUser-supplied official archives passed full tar/gzip listing and restrictive safe extraction. All RGB PNGs fully decoded; timestamps strictly monotonic; pose columns finite and quaternion norms checked; nearest GT association includes every valid/invalid row with SHA. See DATA_MANIFEST_r02.json for measured archive bytes, SHA, counts, spans and provenance limits. All old failures/G0 stop reports retained unchanged. No retrieval score or test metric computed. Exact import/audit commands and source snapshots are archived. Next: accept the common development-derived revisit protocol before any retrieval.\n')
    run.finish(dict(sequences=summaries,old_files_preserved=preserve(),passed_G0=True));run.checkpoint('G0 resumed official-data audit')
    g1=Run('g1_protocol',dict(draft_sha256=sha(ROOT/'configs/v4/protocol_draft.yaml'),protocol_adjustments=0,metadata_only=True))
    # Development audit is evaluated first; no test-derived protocol selection.
    dev=load('freiburg2_pioneer_slam');devcoverage=coverage(dev)
    assert next(x for x in devcoverage if x['radius_m']==.5)['closed_queries']>=100,'G1 stop: insufficient development revisit positives; one documented protocol adjustment permitted'
    protocol=json.loads((ROOT/'configs/v4/protocol_draft.yaml').read_text());protocol.update(status='accepted_metadata_protocol_before_retrieval',protocol_adjustments=0,gt_duplicate_policy='use first original pose row for an exact duplicate timestamp; retain all original rows/evidence',development_gate=devcoverage,gt_unit='metres: optical camera center in TUM mocap world',rejection_policy='no rejection; 100% valid query attempted; no open-set detection claim',invalid_query_history_policy='all sampled queries processed including invalid-GT; metrics mask only invalid GT, not difficult/open queries')
    write(ROOT/'configs/v4/protocol_accepted.yaml',protocol)
    summaries=[]
    for seq,hzs in [('freiburg2_pioneer_slam',[1,3,5]),('freiburg3_long_office_household',[5])]:
        for hz in hzs:
            d=load(seq,hz);stats=coverage(d);summary=dict(sequence=seq,hz=hz,gallery=len(d['g']),query=len(d['q']),midpoint=d['midpoint'],minimum_time_gap=d['q'][0]['timestamp']-d['g'][-1]['timestamp'],sampled=d['sampled_rows'],excluded_buffer_or_invalid_gallery=d['excluded_buffer_or_other'],coverage=stats);summaries.append(summary)
            write(ROOT/'data/manifests/v4'/(seq+f'_{hz}Hz_protocol.json'),dict(g=d['g'],q=d['q'],summary=summary))
    write(g1.path/'protocol_metadata_summary.json',summaries);write(ROOT/'docs/research_v4/PROTOCOL_METADATA.json',summaries)
    (ROOT/'docs/research_v4/G1_ACCEPTANCE.md').write_text('# G1 — passed, metadata only\n\nInitial fixed-half gallery/10-second buffer protocol passed the predeclared >=100 development closed-query gate at 0.5m; no protocol adjustment used. Accepted before computing any retrieval. Uniform 5Hz primary and developer-only 1/3Hz artificial subsampling are fully manifested. Complete original PNGs remain. Each row records RGB/GT timestamps, delta, position/quaternion, validity, file SHA and role; nearest association is our declared evaluator adaptation, not the official greedy one-to-one association utility. Startup stays in each denominator with single-frame fallback. Invalid-GT queries remain in history and explicit counts. Open queries remain reported at every radius; no rejection/calibrated confidence detector is claimed. GT is offline evaluation metadata only. Test metadata audit is permitted and has no retrieval results. See PROTOCOL_METADATA.json for all denominators/coverage. Next: predeclare finite strong-baseline/candidate grid and encode development only.\n')
    s=json.loads((ROOT/'docs/goals/GOAL_V4_STATE.json').read_text());s.update(current_stage='G2',g0_resume_run=run.id,g1_run=g1.id);write(ROOT/'docs/goals/GOAL_V4_STATE.json',s)
    g1.finish(dict(protocol_sha256=sha(ROOT/'configs/v4/protocol_accepted.yaml'),metadata=summaries,independent_retrieval_opened=False));g1.checkpoint('G1 universal timestamp and revisit protocol')
if __name__=='__main__':main()
