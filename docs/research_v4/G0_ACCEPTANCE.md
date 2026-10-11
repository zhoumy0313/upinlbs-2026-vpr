# G0 stop report — data acquisition not accepted

Current goal is VPR-GOAL-V4. Branch `research/vpr-v4-temporal-alignment` starts from exact V3 `09e7fb0fc63489817a09901fda37ae9896a9c404`. All 14,482 historical files (9,793,914,835 bytes) retained and SHA-checked, including all V1–V3 sources, experiments, failures and paper PDFs. `.gitignore` only appended. Main/V2/V3 remote references remain unchanged.

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

All original argv, working directories, safe environment records, stdout/stderr, true curl exits, retry failures, fingerprints and source snapshots are in the G0 evidence ZIP under artifacts/v4/g0/g0_close_20261011T023030Z_affd191e/. Download failures are retained, with original and final logs. `DATA_MANIFEST.json`, `SOURCE_AUDIT.md`, and `MAC_TRANSFER_RESUME.md` distinguish source descriptions, local observations and planned work.

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
