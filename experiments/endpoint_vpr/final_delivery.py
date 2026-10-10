"""Archive complete evidence chain and produce <=2-page Chinese author briefing."""
import csv,json,subprocess,zipfile
from pathlib import Path
from .runtime import ROOT,Run,state,sha,atomic,utc,preserve_check,checkpoint

def archive_index(run):
    rows=[]
    for p in sorted((ROOT/'outputs_v3').rglob('*')):
        if not p.is_file() or 'reading' in p.parts or '__pycache__' in p.parts or p.is_relative_to(run.path):continue
        rows.append(dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=sha(p),public_role='image_or_large_array_local_source_rebuild_only' if p.suffix in ['.jpg','.png','.npy','.npz','.zip','.pdf'] else 'text_evidence'))
    public=ROOT/'artifacts/v3/final';public.mkdir(parents=True,exist_ok=False);atomic(public/'ALL_LOCAL_EVIDENCE_INDEX.json',rows)
    # Every scientific ledger is already in a stage ZIP. The final archive collects
    # all omitted failure/metadata/driver receipts, exact sources and stage index.
    with zipfile.ZipFile(public/'complete_text_receipts.zip','x',zipfile.ZIP_LZMA) as z:
        for row in rows:
            p=ROOT/row['path']
            if p.suffix not in ['.py','.tex','.txt','.md','.json','.jsonl','.log','.xml','.yaml','.actual','.patch']:continue
            z.write(p,p.relative_to(ROOT).as_posix())
        for root in ['docs/research_v3','configs/v3']:
            for p in sorted((ROOT/root).rglob('*')):
                if p.is_file():z.write(p,p.relative_to(ROOT).as_posix())
        z.write(public/'ALL_LOCAL_EVIDENCE_INDEX.json',public.relative_to(ROOT).as_posix()+'/ALL_LOCAL_EVIDENCE_INDEX.json');assert z.testzip() is None
    chains=[]
    for p in sorted((ROOT/'artifacts/v3').rglob('archive_manifest.json')):
        m=json.loads(p.read_text());assert all((p.parent/x['name']).stat().st_size==x['bytes'] and sha(p.parent/x['name'])==x['sha256'] for x in m['parts']);chains.append(dict(manifest=str(p.relative_to(ROOT)),manifest_sha256=sha(p),**m))
    atomic(public/'PUBLIC_ARCHIVE_CHAIN.json',dict(chains=chains,original_G2_zip_requires_parts_folder='artifacts/v3/g2_backup_repair',complete_text_receipts_sha256=sha(public/'complete_text_receipts.zip'),copyright_bodies_images_external_weights_not_redistributed=True));return public,rows

def author_pdf(body,path):
    import matplotlib
    matplotlib.use('Agg');matplotlib.rcParams['pdf.fonttype']=42
    from matplotlib.backends.backend_pdf import PdfPages
    from matplotlib.font_manager import FontProperties
    import matplotlib.pyplot as plt
    import textwrap
    font=FontProperties(fname='/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf');lines=[]
    for line in body.splitlines():lines += textwrap.wrap(line,width=38,break_long_words=True) if line else ['']
    pages=(len(lines)+43)//44;assert pages<=2,(len(lines),pages)
    with PdfPages(path) as pdf:
        for page in range(pages):
            fig=plt.figure(figsize=(8.27,11.69));fig.text(.09,.94,'VPR-GOAL-V3 作者审阅摘要',fontproperties=font,fontsize=16)
            for k,line in enumerate(lines[page*44:(page+1)*44]):fig.text(.09,.89-k*.0185,line,fontproperties=font,fontsize=10.5)
            fig.text(.09,.045,f'研究执行与论文有效性分开判断；第 {page+1}/{pages} 页。',fontproperties=font,fontsize=9);pdf.savefig(fig);plt.close(fig)
    return pages

def main():
    st=state();assert st['stages']['G6']=='passed_working_draft';run=Run('g7_final_delivery','old preservation, complete evidence archive and honest scientific judgment',dict(independent_status='INDEPENDENT_TEST_UNAVAILABLE',formal_submission=False));print(run.id,flush=True);oldcount=preserve_check();g3=ROOT/'outputs_v3'/st['g3_run'];sel=json.loads((g3/'selection.json').read_text());g5=ROOT/'outputs_v3'/st['g5_run'];results=json.loads((g5/'raw_metrics.json').read_text());tim={r['method']:r for r in results['timing']};p=sel['selected']['P']['name'];pt=tim[p]
    run.command(['git','ls-remote','origin','refs/heads/main','refs/heads/research/temporal-vpr-v2','refs/heads/research/vpr-v3-endpoint-refinement']);remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/main','refs/heads/research/temporal-vpr-v2'],cwd=ROOT,text=True);assert '78eb9e45d3bc469630b0c46ad1ea02b318ee151b' in remote and '81fbf62dfaf5cdd28a005afbe6853289524b4d4d' in remote
    # Ensure all frozen scientific bytes remain intact after interpretation/papers.
    f=json.loads((ROOT/st['freeze_directory']/'freeze.json').read_text());assert all(sha(ROOT/rel)==h for rel,h in f['science_file_sha256'].items())
    paperaudit=json.loads((ROOT/'docs/research_v3/PDF_NUMERIC_AUDIT.json').read_text());assert len(paperaudit['papers'])==4 and all(r['pages']<=6 for r in paperaudit['papers']);changed=subprocess.check_output(['git','diff','--name-only','81fbf62dfaf5cdd28a005afbe6853289524b4d4d','HEAD'],cwd=ROOT,text=True).splitlines();allowed=('experiments/endpoint_vpr/','configs/v3/','docs/research_v3/','docs/goals/GOAL_V3','artifacts/v3/','freezes/v3_','paper/revisions/v3_','.github/workflows/v3-paper-pdf.yml');assert all(x=='.gitignore' or x.startswith(allowed) for x in changed)
    summary=f'''目标 VPR-GOAL-V3 已按 G0→G7 执行。科学结论为 Outcome C：候选约束式终点精修未超过强基线。执行完成不等于方法有效，也不等于正式投稿就绪。

旧成果：从 V2 指定提交建立独立 V3 分支；{oldcount} 个旧文件哈希保持一致。V1、V2 的代码、记录、负结果、冻结包、论文和分支完整保留；现有 SSH、FlClash、Codex、驱动未改动。

输入到输出：查询照片经冻结 CosPlace 输出512维单位描述子，与参考图库做余弦比较。时序用当前及过去得分形成粗候选；局部邻域只由参考索引建立；P 允许有限时序支持损失后按当前视觉分数排序。输出参考图片排名，不输出机器人位姿。坐标/真值仅用于离线评分。

开发证据：St Lucia 全部已见。L9 在10m口径下372个错误中，H1/r4邻域含369个正确候选；同大小随机只覆盖6个。这是上界，不是算法召回。近边界与重复路线使索引偏移不等于米级误差。

公平比较：所有224组有限配置均保留，3584组指标由逐查询记录复算。同一656个验证查询：选中P为598/656（91.16%），强简单局部融合为644/656（98.17%），固定短窗口为641/656（97.71%）。P虽然优于较弱旧L9（495/656），仍低于单帧A（621/656），宽容差和Nordland也未通过继续条件。停止增加模块。

独立验证：未完成。Oxford相机下载需注册；SFU官方小包HTTP/HTTPS和正常直接访问失败。原始下载为0字节，没有偷换已见St Lucia为外部测试。SFU人工约10m间隔不是10m几何真值；St Lucia坐标重投影差不是GPS精度保证。

真实成本：RTX3060 Laptop GPU，batch1，预热20，每个冻结方法三次完整1464图遍历，CUDA同步，包含解码、预处理、编码、传输、相似度、历史与排序。P mean/median/P95为{pt['mean_ms']:.2f}/{pt['median_ms']:.2f}/{pt['P95_ms']:.2f}毫秒。图库编码和模型加载单列；RSS与GPU内存分开。小差值和三次重复不作为显著性/部署保证。

论文与归档：V3 r01→r04源稿、PDF、参考文献、变更、逐数字映射均保存；最终稿不超过6页，含参考文献/AI披露。完整逐查询、命令、退出码、失败及哈希已归档并推送V3分支，单文件小于100MB，分块可无损重组。

投稿建议：目前为实证Working Draft，不按成功新方法论文投稿。请导师判断负结果贡献，补可信新数据并新冻结，补阅受限文献及照片许可，确认会议时区/匿名/模板/署名后再决定。正式投稿、作者顺序、版权和付费未执行。'''
    (ROOT/'docs/research_v3/AUTHOR_SUMMARY_ZH.md').write_text(summary+'\n');brief=ROOT/'docs/research_v3/AUTHOR_SUMMARY_ZH.pdf';pages=author_pdf(summary,brief);run.command(['pdfinfo',str(brief)]);run.command(['pdffonts',str(brief)]);run.write('model_identity.json',json.loads((ROOT/st['freeze_directory']/'model_identity.json').read_text()))
    table='\n'.join(f"| {r['method']} | {r['radius']}m | {r['correct']['1']}/{r['queries']} | {r['rescue']} | {r['harm']} | {r['distance_median']:.3f}/{r['distance_P90']:.3f}/{r['distance_P95']:.3f} |" for r in results['results'] if r['radius'] in [10,25])
    report=f'''# VPR-GOAL-V3 final delivery\n\nResearch execution complete with explicit unavailable independent-test scope; Outcome C, novelty_claim_supported=false, formal_submission_ready=false.\n\nStages G0/G1/G2 pass; G3 scientifically negative; G4 metadata/seen-only freeze pass but independent-data gate unavailable; G5 real-image seen accuracy/timing pass, independent test NOT_RUN; G6 four versioned Working Drafts/PDFs/numeric/literature review; G7 preservation/archive pass.\n\n## Ten scientific judgments\n| Item | Evidence/judgment |\n|---|---|\n| Causal pipeline | Implemented score-only kernels/Strategy/Online; full regression and synthetic tests, source hashes in freeze |\n| Repairable endpoint space | Seen H1/r4 oracle369/372 errors, random6; actual eight category-matched examples, not algorithm recall |\n| Exceeds strong short-window? | No: P598/656 vs fixed fullL3 641/656 and local fixed blend644/656 at10m |\n| Strict/wide retention | Predeclared P gate failed: net−46 strict versus strongest; auxiliary degraded; Nordland loss6 versus L9 |\n| Independent task/data | INDEPENDENT_TEST_UNAVAILABLE; Oxford login, SFU official archive errors; no new images/scoring |\n| Independent positive contribution | Not measured/not asserted. St Lucia/Nordland remain seen |\n| Online added cost | Actual per-method raw4392 timed samples, warm20 and CUDA sync; P mean/median/P95={pt['mean_ms']:.2f}/{pt['median_ms']:.2f}/{pt['P95_ms']:.2f}ms; full table in g5 |\n| Similar prior work | SeqSLAM/OpenSeqSLAM, STA-VPR/AdaptSeqVPR, SMR and local-image reranking; mechanism matrix distinguishes partial full-text access |\n| Defensible contribution | Bounded coverage-versus-policy/baseline/GT/sampling/cost audit; P effective/new-method/generalization claims unsupported |\n| Paper status | Working Draft, not formally submission-ready; supervisor/author review recommended |\n\n## Frozen real first-pass seen-stream results\nAll methods share first8 exclusion and radius-specific no-positive mask; full startup separately. Distances are label distances, not pose RMSE.\n\n| Method | Radius | R@1 correct | Rescue vs A | Harm vs A | median/P90/P95 distance m |\n|---|---:|---:|---:|---:|---:|\n'''+table+'''\n\n## Delivery files\n- New paper: paper/revisions/v3_r04/main.tex and main.pdf; all v3_r01–r04 preserved with numeric_bindings, table_cells, figure data and version change maps.\n- Old papers remain paper/main.pdf, paper/versions/v1_20261010_frozen/, paper/revisions/v2_*/ and paper/submission_candidate/v2/; byte-preservation inventory in artifacts/v3/g0/old_files.json.\n- Full stage public archives/parts in artifacts/v3/, final complete-text receipts plus SHA index and archive chain in artifacts/v3/final/. Original photos/large arrays/weights remain local with source/hash identities, excluded from redistribution.\n- Exact command logs with true exits, source snapshots, failures and raw first-pass/latency/TopK/candidate/eligible/winning-path/GT distance evidence in outputs_v3; complete public ledgers reside in stage archives.\n- AUTHOR_SUMMARY_ZH.md/pdf (<=2 pages), AUTHOR_REVIEW_CHECKLIST.md, LITERATURE_MATRIX.md, REPRODUCE.md, EVIDENCE_MAP.md, all Gx_ACCEPTANCE reports and mutable state.\n\nNo training, driver/system/account change, main/V2 merge/force-push, external-test tuning, author decision, paid GPU, signature or formal submission occurred. A working empirical paper with an unsupported method mechanism has uncertain conference value; obtain supervisor approval of contribution and credible new validation before presenting it as a successful new method. New independent data would need a new source audit/freeze before predictions, not post-test parameter edits.\n'''
    (ROOT/'docs/research_v3/FINAL_DELIVERY.md').write_text(report);(ROOT/'docs/research_v3/EVIDENCE_MAP.md').write_text('# Exact V3 evidence chain\n\nG0 old inventory -> all old artifacts unchanged. G1 '+st['g1_run']+' -> diagnostics/candidate oracle/paired counts/spacing. Authoritative cases '+st['g1_case_audit_run']+' -> eight true category matches; initial H3 fallback is qualified, not cited as negative. G2 '+st['g2_run']+' -> exact historical Top10/count checks and all strong controls. G3 '+st['g3_run']+' ->224 configs/3584 audited groups/selection, all negative results. Freeze '+st['freeze_directory']+' precedes actual timing with independent_performance_not_opened=true; no external dataset. G5 '+st['g5_run']+' -> each real first-pass query and each measured complete pipeline interval. Every V3 table cell links via numeric_bindings.json/table_cells.json to source metric/SHA; PDF_NUMERIC_AUDIT.json checks exact rendered rows and <=6 pages. Static plot points are artifacts/v3/figures/figure_data.json. All stage ZIP/ordered parts indexed in final/PUBLIC_ARCHIVE_CHAIN.json; full local file/SHA list excludes copyright readings from public delivery.\n')
    public,rows=archive_index(run);run.finish(dict(old_files_verified=oldcount,author_brief_pages=pages,old_branches_unchanged=True,papers=paperaudit['papers'],research_outcome='C',independent_test='not_run',local_evidence_files=len(rows),final_receipts_sha256=sha(public/'complete_text_receipts.zip')),dict(passed=True,execution_complete_with_declared_limits=True,method_effectiveness=False,formal_submission_ready=False));(public/'g7_metrics.json').write_bytes((run.path/'raw_metrics.json').read_bytes());(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(public.iterdir()) if p.is_file()))
    (ROOT/'docs/research_v3/G7_ACCEPTANCE.md').write_text('# G7 acceptance\n1. Full old hash/branch/scope/frozen-byte check and four PDF numeric checks.\n2. Exact image-to-descriptor-to-score-to-history/candidate-to-rank explanation in Chinese briefing; GT stays offline.\n3. `.venv-paper/bin/python -m experiments.endpoint_vpr.final_delivery`; actual Git/Poppler commands/exits logged; no local TeX installation.\n4. All positive/negative grid and real timing preserved; final text/archive index/SHA chain verified; briefing pages='+str(pages)+'.\n5. Seen-only labels retained, same masks, no independent-test tuning.\n6. Outcome C; execution complete is not method effectiveness or formal readiness.\n7. New independent source and full related-paper/photo-rights/human-author checks remain unresolved.\n8. Immutable run '+run.id+', final checkpoint/push and remote receipt follow.\n9. Next authorized scientific work requires a new goal/source audit; current ordinary research scope is delivered. Formal human actions remain unperformed.\n');st['stages']['G7']='passed';state(stages=st['stages'],current_stage='complete',stage_status='complete_with_declared_limitations',g7_run=run.id,latest_run_id=run.id,research_outcome='C',novelty_claim_supported=False,formal_submission_ready=False,paper_revision='v3_r04',quality_verdict='WORKING_DRAFT');checkpoint('G7')
if __name__=='__main__':main()
