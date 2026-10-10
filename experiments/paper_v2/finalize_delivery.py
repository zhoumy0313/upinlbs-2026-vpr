"""Produce final honest research handoff, complete text archive and persistent state."""
import argparse,csv,json,re,shutil,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'experiments/temporal_vpr'))
from runtime import Run,digest,update_state,utc_now
VERSIONS=['v2_r01','v2_r02','v2_r03','v2_empirical_findings','v2_r04']
TEXT={'.json','.jsonl','.csv','.yaml','.xml','.log','.md','.py','.txt','.tex','.bib'}
def write(path,text):
    p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
def main():
    p=argparse.ArgumentParser();p.add_argument('--verification',required=True);a=p.parse_args()
    state=json.loads((ROOT/'docs/goals/GOAL_V2_STATE.json').read_text());proof=ROOT/'outputs_v2'/a.verification
    verified=json.loads((proof/'metrics.json').read_text());assert json.loads((proof/'checks.json').read_text())['passed']
    assert {r['revision'] for r in verified['results']}==set(VERSIONS)
    assert json.loads((proof/'visual_review.json').read_text())['passed']
    run=Run(ROOT,'g5_final_delivery',dict(outcome='C',quality='READY_FOR_HUMAN_REVIEW',formal_submission_ready=False),dict(verification=a.verification,freeze=state['freeze_directory']))
    print(run.id,flush=True)
    for argv in [['nvidia-smi','--query-gpu=name,driver_version,memory.total','--format=csv,noheader'],['free','-h'],['df','-h',str(ROOT)],['lscpu'],['codex','login','status'],['systemctl','is-active','ssh']]:run.command(argv,allow_failure=True)
    # Safe process names only, never process arguments or credentials.
    processes=[]
    for path in Path('/proc').glob('[0-9]*/comm'):
        try:
            name=path.read_text().strip()
            if any(k in name.lower() for k in ['flclash','codex']):processes.append(dict(pid=path.parent.name,name=name))
        except (OSError,PermissionError):pass
    run.write('process_names.json',processes)
    datasets={k:json.loads((ROOT/'outputs_v2'/state[sk]/'metrics.json').read_text()) for k,sk in [('g2','g2_baseline_run'),('g3','g3_adaptive_run'),('smr','g3_smr_run'),('test','g4_evaluation_run'),('latency','g4_latency_run')]}
    names={'A-only':('g2','A-only'),'B-only':('g2','B-only'),'DINOv2-only':('g2','DINOv2-only'),'RRF_k60':('g2','RRF_k60'),'AB_fixed_0.75':('g2','AB_fixed_0.75'),'fixed_T_best':('g2',datasets['g2']['best_temporal_only']['method']),'fixed_blend_best':('g2',datasets['g3']['fixed_G2_interior_reference']['method']),'adaptive_full':('g3','adaptive_full'),'SMR_first_filter_adapted':('smr','SMR_first_filter_adapted')}
    def fraction(c):return f"{c['correct']}/{c['queries']} ({100*c['correct']/c['queries']:.2f}%)"
    rows=[]
    for name,(source,actual) in names.items():
        tr=next(r for r in datasets[source]['results'] if r['method']==actual and r['split']=='train')['common']['R@1']
        val=next(r for r in datasets[source]['results'] if r['method']==actual and r['split']=='validation')['common']['R@1']
        test=next(r for r in datasets['test']['results'] if r['method']==name and r['radius_m']==25)
        latency=next(r for r in datasets['latency']['results'] if r['method']==name)['total']
        oldN='92/650 (14.15%)' if name=='A-only' else '65/650 (10.00%)' if name=='B-only' else '未对V2重跑'
        oldG='69/200 (34.50%)' if name=='A-only' else '72/200 (36.00%)' if name=='B-only' else '未对V2重跑'
        rows.append(dict(method=name,train=fraction(tr),validation=fraction(val),old_Nordland_seen=oldN,old_Gardens_seen=oldG,StLucia_25m=fraction(test['common']['R@1']),mean_ms=latency['mean_ms'],p95_ms=latency['p95_ms'],rescue=test['rescue'],harm=test['harm']))
    with (run.path/'per_query.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    table='|方法|训练共同592|验证共同292|旧Nordland已见650|旧GP已见200|新St Lucia共同1456、25m|真实均值/P95 ms|\n|---|---|---|---|---|---|---|\n'+''.join(f"|{r['method']}|{r['train']}|{r['validation']}|{r['old_Nordland_seen']}|{r['old_Gardens_seen']}|{r['StLucia_25m']}|{r['mean_ms']:.3f}/{r['p95_ms']:.3f}|\n" for r in rows)
    paper_rows='|版本|总页数|源文件SHA-256|PDF SHA-256|\n|---|---:|---|---|\n'
    paper_rows+='|V1原稿/冻结副本|5|e6194a581902680e499e3784a3dcdbb03c68a696b0498f0a73e5935069c15f94|e693b054abaa6ba0b274f362c9ab051ed7186cd1d3123b8ef51bd6138a50dd12|\n'
    for r in verified['results']:paper_rows+=f"|{r['revision']}|{r['pages']}|{r['tex_sha256']}|{r['pdf_sha256']}|\n"
    history='''# V2 revision history

All versions retain standalone main.tex, complete references.bib, main.pdf, CHANGELOG.md, numeric_cells.csv and source/hash evidence. Original paper/main.* and paper/versions/v1_20261010_frozen remain unchanged. Scientific results never change between drafts.

- v2_r01: first empirical audit from immutable G4 results; prominently retains adaptive failure and 10m reversal. First native compilation timed out during TikZ downloads; subsequent compilation succeeded, no source repair.
- v2_r02: reviewer-oriented qualification adds rare SMR training classes (3 harmful, 6 both-wrong), tighter-tolerance discussion, no causal-mechanism claim.
- v2_r03: clarifies that window/radius controls were predeclared; ordered-versus-shuffled evidence cannot cancel 10m failure; labels timing as measured pipeline cost.
- v2_empirical_findings: preserved alternate empirical discussion title; same scientific evidence as r03.
- v2_r04: final review candidate. Rechecked IEEE policy requires AI disclosure in acknowledgments; adds a distinct acknowledgments section naming tools, abstract/Sections I–VI, figure/code/analysis/text contributions and required human review. All previously compiled versions preserved.

Each version has 154 numeric ledger cells including 110 table cells and 8 sequence-figure points. All five PDFs are six pages including references/declarations, have 17 embedded Type1 fonts and no overflow/undefined references. Native compiler success receipts: outputs_v2/g5_native_compilation_20261010T153403Z_b87b1e11. CI exact-source exports: actions runs 38064036912 and 38064652244; complete r04 compiler output archived in paper/revisions/ci_build_receipts/run_38064652244_attempt_1. Independent local PDF/numeric/preservation checks: '''+a.verification+'; full-page visual review recorded there.\n\n'+paper_rows
    write('paper/revisions/REVISION_HISTORY.md',history)
    for v in VERSIONS:
        with (ROOT/'paper/revisions'/v/'CHANGELOG.md').open('a') as f:f.write('\nAccepted archive: native compile succeeded; exact-source CI PDF and independent exported-PDF audit pass. Six pages including references/declarations. All original scientific results retained. See REVISION_HISTORY.md for the actual substantive changes and provenance.\n')
    claim='''# Claim and numerical evidence map

Author-review candidate: v2_r04. No adaptive superiority, first-sequence, SOTA, navigation or metric localization claim.

Every abstract numeric result, all 110 table cells and all 8 plotted figure points are mapped per version in numeric_cells.csv and paper_numeric_evidence.json (154 ledger entries/version, 770 verified across five preserved versions). Each row records original run/file SHA, development/independent/metadata/latency role, JSON cell, display precision and numerator/denominator. Independent resolver does not import the manuscript generator; PDF tables and abstract are independently extracted and checked against the source rows. Figure coordinates are source-verified and visually checked in rendered PDFs.

|Claim|Evidence and role|Interpretation limits|
|---|---|---|
|Adaptive contribution not established|G2 selected fixed 291/292; G3 adaptive242/292, fixed candidate controls/ablations; G4 primary adaptive1439 vs blend1449/1456|No post-test search; a gain against A alone is insufficient|
|Tolerance reverses selected temporal gain|Frozen G4 per_query.csv/metrics, radius10 A1384 versus T1084; radius25 A1422 versus T1436; radius50 A1426 versus T1456, same1456 queries|Overall C; original primary25m automated B unchanged; no new radius selected|
|Ordered history matters under primary protocols|G2/G4 full_velocity_T_L3/L5/L9 and shuffled_L9|Each dataset retains its own GT; external100%L5 is sensitivity, not adopted winner; correlated observations|
|Freeze before performance access|freezes/v2_20261010T143902Z/freeze.json created_utc; G4 first-access receipt in GOAL_V2_STATE.json|All65 input hashes verified; independence relative to our selection, upstream pretraining overlap unknown|
|Observed sampling differs from README|G4 audit trajectories/sourceframe deltas/coordinate_step_median: 11.417592m gallery,11.962964m query; geo reprojection max1.483050m|Timestamp missing, no uniform-time or physical-speed claim|
|Real online timings|G4 real_online_latency run metrics/raw39528 samples|Batch1 actual images,20warm,3×1464queries/method, CUDA sync, one CPU/BLAS thread; no cache in timing; no independent CI|
|Train-only median confidence scales|Freeze methods[name=adaptive_full].scales; G3 training statistics|592valid train windows, noGT; A.02154515678,T.01837086664; weights not probabilities|
|SMR rare classes and adaptation|G3 train_class_counts.json:0=484,1=3,2=99,3=6; fixed source commit82c88c9, MIT, source-body guard|Source SMOTE-before-CV optimism, different encoder/GT/gallery, first-filter only, rejects counted as misses; not official benchmark reproduction|
|Protocol/method constants|Freeze GT/radii/masks/methods/image_size_hw; G2 grid predeclaration; configs/v2/g3_adaptive_predeclaration.json and smr_adaptation_predeclaration.json; METHOD_V2.md|L{1,3,5,9},V finite, lambda finite; no GT/GPS/filenames in online scoring|
|Historical seen results|V1 P4 report/frozen raw run and preserved5page paper|Old Nordland92/650 A,65/650 B,67/650 gate; GP69/200 A,72/200 B,69/200 gate; never selects V2|
|Related-work precedence|RELATED_WORK_MATRIX.md and SOURCE_READING_NOTES.md with primary source receipts|SeqSLAM/same-conference fulltexts access-limited; cite only verified scope|
|AI and human responsibility|IEEE primary policy receipt; r04 acknowledgments; user authorship reply|Only Mingyang Zhou confirmed; all interpretations/authors/format need human approval|

## Complete numeric cell listing (r04, same values in earlier versions)

|Cell ID|Displayed value|Role|Source run/file|Raw cell|SHA-256|
|---|---|---|---|---|---|
'''
    for c in json.loads((ROOT/'paper/revisions/v2_r04/paper_numeric_evidence.json').read_text())['numeric_cells']:
        claim+=f"|{c['id']}|{c['display']}|{c['role']}|{c['source']}|{c['json_cell']}|{c['source_sha256']}|\n"
    write('paper/revisions/CLAIM_EVIDENCE_MAP.md',claim)
    requirements='''# Primary source reading and submission-format audit

Actual source audit run g5_primary_metadata_audit_20261010T142147Z_4fd4c182, HTTP statuses/hashes/time in metrics.json; full copyrighted bodies local in reading/, not redistributed. Manual reading qualification below is a new audit note; original automated conference.verified={} receipt is preserved.

Read the official [2026 site](https://upinlbs2026.com/) frontend source contexts (conference_bundle_0 SHA d38e591f913398268c6bf50e5b2bd1f60122fbfea44d29bfaa518dfb9600de0c). It states English PDF/IEEE conference format, up to six pages, initial full-paper and abstract deadline October15 2026, notification October26, and links [IEEE template selector](https://template-selector.ieee.org/secure/templateSelector/articleType?publicationTypeId=3&titleId=1) and [CMT](https://cmt3.research.microsoft.com/UPINLBS2026). The stated November15 final-paper date follows the November6–8 conference: interpretation remains unverified and is not an initial-submission extension. Explicit deadline time/timezone, anonymity, required paper size and whether references count remain unverified. We conservatively count all references/declarations in six pages; current PDF is letter (IEEEtran default), not a verified conference-specific size requirement. Do not submit automatically.

Read [IEEE AI policy](https://open.ieee.org/author-guidelines-for-artificial-intelligence-ai-generated-text/) (receipt SHA c810116be957c7411e422ed5cd4cedb9467e60f0c8cc5359103e7095c00d4288): generated text/figures/images/code require acknowledgments identifying system and article sections/extent of use. r04 corrects the earlier section location and specifies abstract/Sections I–VI, OpenAI ChatGPT/Codex, implementation/analysis/figure/manuscript assistance; human authors remain responsible. No unknown funding or additional author invented.

Bibliographic CrossRef primary records verified: SeqSLAM10.1109/ICRA.2012.6224623, Delta10.1109/LRA.2020.3005627, SMR10.1109/IROS60139.2025.11247581, Wei/Li/Zheng10.1109/UPINLBS68186.2025.11468446, Through the Lens of Doubt10.1109/LRA.2026.3674688, StLucia10.1109/TRO.2008.2004520, RRF10.1145/1571941.1572114, tutorial10.1109/MRA.2023.3310859. Primary CVF records verify CosPlace/EigenPlaces/Deep Visual Geo-Localization Benchmark/To Match titles/authors/pages; official arXiv records verify DINOv2/OpenSeqSLAM2.0 (2018 preprint, not asserted accepted IROS paper); Zenodo10.5281/zenodo.4016653 verifies Nordland-Part2020.

Full accessible text and source methods were read for Delta, SMR, To Match, Through the Lens of Doubt, RRF and tutorial, and author follow-up OpenSeqSLAM2.0. Original SeqSLAM and the same-conference ResNet–Sinkhorn full text remain access-limited; no claim about unavailable formulas/results. SMR source executed from MIT repo commit82c88c90377110ce7a3340872f3e1179c3f2d396. Dataset downloader MIT code does not establish permission to redistribute dataset photos, so public evidence excludes photos and pretrained checkpoints.

PDFs compiled on standard Ubuntu public-repository CI, [free-runner documentation](https://docs.github.com/en/billing/concepts/product-billing/github-actions). No paid/larger runners, cache or artifact uploads; PDFs/diagnostics committed only to V2. Native compiler also succeeded; local Ubuntu has no TeX installation added.
'''
    write('docs/research_v2/SOURCE_READING_NOTES.md',requirements)
    intro='''# VPR-GOAL-V2 final research delivery

**结论：完成了可复现的因果时序研究与六页论文迭代，但自适应创新增益没有成立；预先规定的10米评价使所选时序方法收益反转，整体判定 Outcome C。**

质量状态 **READY_FOR_HUMAN_REVIEW**；正式投稿准备 **false**。这是完整研究交付与导师审阅材料，不是录用、作者批准或可直接投稿承诺。

## 阶段与科研决策

G0 pass：独立V2分支与旧稿/标签冻结，最终1470个旧文件逐项SHA复核；.gitignore仅追加且原字节前缀一致。main/旧标签保持78eb9e45d3bc469630b0c46ad1ea02b318ee151b。
G1 pass：4100图像标签/解码/重复审计与开发集TopK/并集Oracle；验证A Top50为300/300，仅说明候选上界，不是算法成绩。旧Nordland留出187重复记录/79组仍保留，±5是序号而非米。
G2 pass：有限80网格+10对照/划分，完整RRF/固定融合/因果固定序列；共同排除前8使验证292。选定L9,V{1.2},lambda1；内部固定融合lambda.75，只用验证选择。
G3 scientifically_negative：唯一预声明规则及完整消融，adaptive242/292弱于成熟固定291/292；停止加模块。固定官方SMR源函数的第一过滤器适配275/292，明确与原论文协议不同。仅该小监督分类器使用train训练，所有视觉编码器冻结。
G4 pass with Outcome C：不可变预测试冻结后，一次完整StLucia独立协议（24方法×3预声明半径）、真实图片在线计时。原始主25m自动标签B保留不改；10m反转导致整体解释C，无测试后参数/预测修改。
G5 pass：r01/r02/r03/empirical/r04均保留源、完整引用、PDF、更新日志；770数字单元独立核验，PDF每版110表格单元与摘要数字再次提取；60回归测试通过，65冻结输入SHA通过，30页渲染人工代理视觉检查无裁切/重叠，17字体全部嵌入且无Type3。r04独立致谢完整披露AI。

## 新旧论文与版本身份

仓库实际根目录：'''+str(ROOT)+'''.
旧主文件 paper/main.tex、paper/main.pdf；可打开原样快照 paper/versions/v1_20261010_frozen/。新稿目录 paper/revisions/<版本>/，最终审阅源/PDF为 paper/revisions/v2_r04/main.tex、main.pdf；另一讨论稿 v2_empirical_findings/main.pdf。自动核验通过后复制到 paper/submission_candidate/v2，所有文件字节与r04一致，仍需人工批准。

'''+paper_rows+'''
## 同协议强Baseline与拟议方法

'''+table+'''
各开发方法共同592训练/292验证；两个旧列是此前已见的V1原结果，V2方法未在这些旧测试上重跑。旧25%门控分别67/650与69/200，调用B78.92%/15.50%，不替换旧记录。两个数据集GT不同，不能直接把绝对百分比相减解释成迁移增益。

开发成熟固定救82、伤1；独立25m固定T救34、伤20，固定融合救34、伤7，自适应救17、伤0。自适应比A高不能证明自适应优于强固定方法。预声明广速度L5的独立25m1456/1456只是敏感性观察，未被挑作新最终方法。

|同一1456查询，预声明半径|A|选定固定T|固定融合|自适应|SMR适配|
|---|---:|---:|---:|---:|---:|
|10m|1384(95.05%)|1084(74.45%)|1296(89.01%)|1389(95.40%)|1253(86.06%)|
|25m主协议|1422(97.66%)|1436(98.63%)|1449(99.52%)|1439(98.83%)|1451(99.66%)|
|50m|1426(97.94%)|1456(100%)|1456(100%)|1440(98.90%)|1456(100%)|

固定T相对A净正确数-300/+14/+30；宽地理容差可以接受有偏移的序列终点，紧容差拒绝。采样不规则、索引速度迁移和平均效应可能有关；目前不能把它们宣称为已验证的唯一因果机制。距离仅用于离线检索GT，不是定位RMSE。

## 研究潜力与新颖性判断

候选覆盖与时序收益支持继续研究，但当前创新假设已被强对照否定。SeqSLAM已有序列路径，Delta已有时间变化表示，SMR已有选择性时序信任，RRF/候选重排/置信度均非首次；本研究是有界因果实现与协议迁移失效审计，不是新网络或SOTA方法。SMR输入、模型、GT、窗口和过滤方式差异全部披露，不能标作原论文完整复现。Wei/Li/Zheng同会议论文目前仅可靠元数据/主题核查，全文机制差异仍须作者获取全文审阅。

实证价值包括强基线接近开发上限时额外门控的失败、统一分母避免虚假过滤收益、地理容差导致结论反转，以及真实端到端耗时。仅一对外部路线、视频串行相关、未知预训练重叠和未证明的新增机制，使其更适合先作为实验/局限分析型论文交导师判断。禁止为了正结果继续在已打开的独立集调参；如开展后续新机制，须新开发数据与新独立冻结。

## 输入—模型输出—检索排序：通俗说明与真实案例

一张照片先解码RGB，固定归一化并将整幅缩放224×224。冻结CosPlace输出512维单位向量x，图库照片预先编码成单位向量y。S_t(j)=x_t·y_j表示当前照片与第j张参考图的相似度；按S从大到小得到候选图像排名，不直接输出坐标或位置误差。

固定时序把最近L张查询的相似度沿参考图库路径平均：T_t(j)=max_v (1/L) sum_lag S_(t-lag)(j-rint(v*lag))。t是查询时间序号，j是候选参考终点，lag是过去偏移，L=9，v=1.2是相对参考索引步进，不是米/秒。越界使整条路径无效；划分/巡航边界清空状态，绝不看未来查询。固定融合将单帧和序列分数以lambda=.75加权。

拟议自适应lambda_t=a*b*c*d：a是当前单帧歧义，b是序列支持，c是历史端点连续性，d是序列终点是否在当前Top50。训练无标签中位差值是固定尺度，lambda不是概率。验证中减少歧义项的消融有帮助，但完整规则把许多本来有效的时序证据压低，仍弱于固定选择；事后不能因此添加新项。

真实局部例图只在本地 outputs_v2/g4_acceptance_20261010T150725Z_c4fe2906/figures/examples/：fixed_rescue.png 查询210809_1210/694，A选到约624.1m外的14868帧，固定T/自适应救回参考1229帧；fixed_harm.png 查询218，A参考7716正确，固定T选526距离约25.2m而在25m协议误伤，自适应保留A；adaptive_loses_fixed.png查询836，自适应未兑现固定路径的救回。它们是按预声明“第一共同符合案例”规则选出的演示，不是统计证据。both_wrong无符合的共同查询，未编造案例；公开保存ID/排名ledger及再生成脚本，不传播许可未明照片。

## 独立数据、环境与真实成本

官方格式化StLucia通过源固定下载器commit2f886d53996d2a4cf549696c5e845c40d77da610及rsync来源获取，实际123494841字节；图库1549/查询1464，8帧共同暖机后1456。源码帧ID恢复顺序，timestamp字段为空。README名义5米间隔与实际坐标中位11.4176/11.9630米不同，保留而不重采样；所有3013GPS经独立PROJ复核，最大差1.48305m小于预声明2m容差。三个半径所有查询都有正样本；同闭集分母、不筛难例。照片和大模型不进Git。

Ubuntu22.04、i7-12700H、约15GiB RAM、RTX3060Laptop6GB、驱动550.107.02、Python3.10.12、Torch2.6.0+cu124/CUDA12.4沿用已有独立环境；SSH/FlClash/Codex与ROS全局配置不改。当前设备状态和退出码见最终run.stdout.log/commands.jsonl；首次P0官方toy已成功并原样保留于docs/P0_ENVIRONMENT_REPORT.md和旧日志。当前磁盘约338GiB可用；本次无系统TeX安装。

在线真实解码+预处理+前向+CPU输出+图库相似度+历史更新+排序，9方法每个20warm再3遍1464图，共39528计时记录；不能将其叫作39528独立测试样本。CPU/BLAS1线程、CUDA同步、GPU时钟未锁、暖文件缓存。A平均10.879ms、自适应11.668ms、SMR适配73.873ms；表给P95。双编码器预处理分别运行，优化共享预处理可能改变其成本。CPU RSS含审计数组，CUDA allocated/reserved非全机显存。离线图库batch16分别12.346/15.206/16.895s，模型初始化/序列化另记整命令墙钟；不冒充在线时延。

## 可复现身份、实际命令、全部失败与证据

科学代码冻结提交ae41a7c038e2da9ba83fc878fe428a49e332859d，冻结提交cdcb31c；冻结目录'''+state['freeze_directory']+'''，创建早于首次性能打开2026-10-10T14:39:59.011566+00:00。主25m结果与全半径/24配置/逐查询/计时保持原样。阶段G0/f8f239、G1/505af8、G2/4376dcd、G3/8db67b0、G4/5b1e3ab；论文源码与CI导出checkpoint0f36c98、aa89b4a、95c4e5a，最后归档checkpoint通过checkpoint日志与远端分支核实。最终不能重写main或旧tag。

具体run_id、完整原始argv、工作目录、允许的环境覆盖、每命令开始/结束/退出码和日志见各outputs_v2/<run>/，公共完整文本备份artifacts/v2/final/evidence.zip；阶段归档artifacts/v2/g1,g2,g3,g4,g4_sensitivity保留，SHA256SUMS验证。最终文本归档包含所有V2失败source_snapshot，弥补阶段ZIP中源码快照只在本地的安排；旧11.877MB证据ZIP不修改。缺少大图/权重/描述子时按下载来源与SHA再建，不能把未知缓存当成对应运行。公共仓库总单文件均小于100MiB。

失败均保留：原ROS pytest插件冲突，G2冗余默认Torch缓存下载中止，SMR标准venv ensurepip不可用后的独立无pip环境，预冻结factory字段别名KeyError，预冻结gallery将已为numpy的encode结果再调用.cpu导致失败；均在性能打开前修复，原源码/错误日志未改。G5独立读表审计首次未处理数字千位逗号、第二次误认冻结字段名，保留两个失败run后修读表器；未修改论文/实验数值。首次native TikZ下载超时有实际诊断，随后成功。完整实际命令索引ACTUAL_COMMANDS.jsonl/COMMAND_INDEX.md及REPRODUCE_V2.md分别区分已执行记录和重建指南，不把计划命令写成运行证据。

## 人工动作与投稿条件

1. 审阅实证/负结果叙事与创新性，决定是否符合小会议研究贡献要求；当前无已证明的新方法优势。
2. 仅周明杨Mingyang Zhou确认主作者，UCAS已知；其他作者/顺序/通讯/邮箱/基金未决定。现稿复用旧稿University of Chinese Academy of Sciences，须人核对单位正式英文，不能由代理决定作者贡献。
3. 官网初次全文截止10月15日，IEEE格式/最多6页/CMT已核；具体时间时区、匿名、paper size、参考文献计页条文与异常final-paper日期仍unverified，以官方系统/导师确认为准；当前保守总计6页含引用与声明。
4. 核查原始文献、特别访问受限论文全文、数据许可与所有AI辅助内容。r04致谢已透明披露，仍需真实作者承担审查。
5. 作者最终批准后自行正式投稿、注册付费、签署版权；本Goal没有执行这些动作，没有发送邮件、变更账户或系统驱动。

研究任务已完成；剩余均为人工学术/署名/投稿决定，而非待运行的隐藏实验。证据支持READY_FOR_HUMAN_REVIEW，不支持直接正式提交或正增益创新宣称。
'''
    write('GOAL_V2_FINAL_DELIVERY.md',intro);write('docs/research_v2/RESEARCH_SUMMARY.md',intro)
    write('docs/research_v2/HANDOFF_FOR_AUTHOR.md','# Author handoff\n\nREADY_FOR_HUMAN_REVIEW; formal_submission_ready=false. Read GOAL_V2_FINAL_DELIVERY.md and v2_r04/main.pdf. Own adaptive contribution unsupported; 10m transfer reverses selected temporal gain, overall C. Confirm Mingyang Zhou/UCAS, other authors/correspondence/funding; review originality and access-limited related papers; verify official anonymity/page size/deadline timezone; approve AI disclosure and all claims. No submission/account/payment/signing actions performed.\n')
    write('docs/research_v2/G4_ACCEPTANCE.md','# G4 acceptance\n\nPassed with overall Outcome C (primary25m evaluator B unchanged). Source, audit, protocol, failure logs and evidence are in G4_FROZEN_RESULTS.md/G4_VALIDITY_AUDIT.md/G4_SENSITIVITY_ANALYSIS.md. 56 tests at G4;216 recall cells/105408 per-query rows;39528 actual online timing samples;65 frozen inputs reverified in final audit. Freeze precedes performance. No old-test selection or new-test tuning. Scientific rule: negative adaptive and tolerance instability preserved; continue G5 empirical analysis only.\n')
    write('docs/research_v2/G5_ACCEPTANCE.md','# G5 acceptance — pass\n\n'+utc_now()+'; '+run.id+'; verification '+a.verification+'. Five complete new6page source/bib/PDF versions;770 independent numeric cells,110 table cells/PDF,8 source-mapped figure points/version;60 tests;1470 old files and65 freeze hashes unchanged. Native compiler successes and exact-source CI PDFs independently checked with pdfinfo/pdffonts/pdftotext and full-page rendering. 17embedded Type1fonts/noType3, no overflowing/undefined targets. First native timeout and two read-table failures preserved; no experimental result changed. Overall Outcome C, primary25m B retained. READY_FOR_HUMAN_REVIEW; formal_submission_ready=false. No test tuning, main edit, unknown authors or submission.\n\nBeginner: image→unit vector→gallery similarities→past-only path scores→ranking→offline GT correctness. Strong fixed baselines must beat simple imagery before a confidence rule can claim benefit. Current rule fails that comparison; radius reversal limits transfer. The paper explains this negative finding and costs without inventing improvement. Sole next task is human scientific/authorship/format review.\n')
    candidate=ROOT/'paper/submission_candidate/v2';candidate.mkdir(parents=True,exist_ok=False)
    for name in ['main.tex','main.pdf','references.bib','numeric_cells.csv','paper_numeric_evidence.json','CHANGELOG.md']:shutil.copy2(ROOT/'paper/revisions/v2_r04'/name,candidate/name)
    write('paper/submission_candidate/v2/README.md','# Automatically audited review candidate\n\nExact bytes copied from preserved v2_r04 after real G4, independent numerical/PDF/reference/version checks. Six pages; empirical Outcome C, not a demonstrated adaptive method improvement. READY_FOR_HUMAN_REVIEW only; authorship/format/claim approval and formal submission remain human actions. Original paper/main.* is unchanged.\n')
    # Actual commands only, with their true recorded exits; future checkpoints cannot be in their own snapshot.
    commands=[];register=[]
    for folder in sorted((ROOT/'outputs_v2').iterdir()):
        if not folder.is_dir():continue
        manifest=folder/'run_manifest.json'
        if manifest.exists():
            m=json.loads(manifest.read_text());status='failure recorded' if 'uncaught_entrypoint_exception' in (folder/'commands.jsonl').read_text() else 'see checks/metrics; not inferred from exit0 alone'
            register.append(dict(run=folder.name,task=m['task'],started_utc=m['started_utc'],git_sha=m['git_sha'],status=status))
            for line in (folder/'commands.jsonl').read_text().splitlines():
                r=json.loads(line)
                if 'argv' in r:commands.append(dict(run=folder.name,**r))
    (run.path/'ACTUAL_COMMANDS.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in commands))
    (run.path/'RUN_REGISTER.json').write_text(json.dumps(register,indent=2)+'\n')
    write('docs/research_v2/COMMAND_INDEX.md','# Actual executed command index\n\nExact command arguments/cwd/environment overrides/UTC/exits in artifacts/v2/final/ACTUAL_COMMANDS.jsonl, source records within final evidence.zip. Includes failures; entrypoint argv also retained per run. Native tool receipts and CI commands are separate. Final snapshot captures commands existing at archive creation; the final push is verifiable by its local checkpoint run and remote commit, not retroactively claimed inside its own commit.\n\n'+''.join(f"- {r['run']}: exit {r['exit_code']}; argv {json.dumps(r['argv'],ensure_ascii=False)}\n" for r in commands))
    write('docs/research_v2/REPRODUCE_V2.md','''# Reproduction and public backup

## Evidence-only audit on a fresh clone (no network encoder inference)

Check out research/temporal-vpr-v2. Verify stage/final SHA256SUMS and ZIP testzip, old tag78eb9e45d3bc469630b0c46ad1ea02b318ee151b, old paper hashes. Standard-library command `python3 experiments/paper_v2/verify_manuscripts.py` reads local original JSON if available or exact members of public evidence.zip; it audits all five papers without scientific package installs. PDFs are standalone IEEEtran/TikZ/PGFPlots with inline complete bibliography. Native compilation or pinned .github/workflows/v2-paper-pdf.yml builds only new sources; no local TeX requirement. pdfinfo/pdffonts/pdftotext independently verify PDFs. Full delivery verifier requires local V1 asset inventory and frozen external files, so a public clone alone must not claim those checks passed.

## Actual experiment replay on retained assets

The source-pinned configs/model_sources*.json, old P0/P1/P2/P3 reports/scripts and freeze provide model/data URLs/SHA, exact encoder choices and all local IDs. G2 uses retained development descriptors from outputs/p3_eigenplaces_20261010_141736_ayAvV5, G1 DINO refresh and data/manifests/p1_20261010_132030_nordland_manifest_v2.json; these large/local assets are not present in a fresh Git clone. Rebuild through old source-pinned extraction recipes, retain image-ID/hash identities and verify against recorded score identities before replaying. Never invent caches or call old outputs an independent test.

Replay development entrypoints: `.venv-p0/bin/python experiments/temporal_vpr/run_g1.py`, `run_g2.py`, `run_g3.py`; `.venv-v2-smr/bin/python experiments/temporal_vpr/run_smr.py`. They create unique runs and update working state; use a separate checkout/state copy to preserve final state and original archives. No stage runner is a safe read-only audit.

For StLucia, official rsync://vandaldata.polito.it/sf_xl/VPR-datasets-downloader/st_lucia/ and downloader commit2f886d53996d2a4cf549696c5e845c40d77da610. prepare_independent.py and validate_independent_geo.py retain download/metadata/projection receipts; build_independent_gallery.py --audit <new_audit_id> creates new descriptors. Frozen original evaluation used `.venv-v2-smr/bin/python experiments/temporal_vpr/evaluate_independent.py --freeze v2_20261010T143902Z`; online timing used `benchmark_independent.py --freeze v2_20261010T143902Z --evaluation g4_independent_evaluation_20261010T143959Z_73e61bb4`. Exact worker commands/environment are in ACTUAL_COMMANDS.jsonl. Original freeze references exact local arrays/files; new directories need a separately labelled replay freeze with identical scientific settings and fresh local identities, never rewriting the original. Re-evaluation is reproduction/post-hoc after test access, never a fresh blind test.

Process-only PYTHONPATH empty, PYTEST_DISABLE_PLUGIN_AUTOLOAD=1, OMP_NUM_THREADS/OPENBLAS_NUM_THREADS=1 and TORCH_HOME=<repo>/weights/p0_torch preserve system ROS/shell/driver state. Existing .venv-p0 Torch2.6+cu124, .venv-v2-smr no-pip environment with fixed base references and imblearn.14.0; exact versions in freeze/argv. Encoders never trained; source MLP supervised on train only.

## Archiving choice

Git retains all authored sources, protocols, reports, old and five new paper versions, small trained SMR model/MIT notice, exact numeric ledgers, complete public text/source snapshots and failure logs. Final evidence.zip contains authored V2 source_snapshot for every run, unlike earlier small stage ZIPs. Photos, external pretrained checkpoints, descriptor/score arrays, virtual environments, caches, raw copyrighted readings and credentials stay local; download source/size/SHA and manifests support reconstruction. Local file preservation has been verified, so ignored is not deleted. No Git LFS/account setup required; all committed single files stay below100MiB. Original V1 evidence.zip remains byte-identical.
''')
    with (ROOT/'docs/research_v2/EXPERIMENT_REGISTER.md').open('a') as f:f.write('\nCurrent qualification: G0 initial ROS test failure preserved; later G0 accepted. G4 overall C, original primary25m B retained. G5 '+run.id+' passed after '+a.verification+' and visual checks; five manuscript versions, negative adaptive and radius reversal retained. Full append-only run register in final archive.\n')
    with (ROOT/'docs/research_v2/DECISION_LOG.md').open('a') as f:f.write('\n'+utc_now()+': G5 passed, overallC unchanged. Publish only empirical review candidate v2_r04 after exact-source six-page/number/font/visual checks. No new method/radius selection; no formal submission.\n')
    with (ROOT/'docs/research_v2/EVIDENCE_INDEX.md').open('a') as f:f.write('\nG5 all source/CSV/claim maps paper/revisions; native tool receipts, exact-source CI38064036912/38064652244, '+a.verification+' local verification, visual_review.json. Final complete text/source_snapshot archive artifacts/v2/final/evidence.zip, ACTUAL_COMMANDS.jsonl, RUN_REGISTER.json and SHA256SUMS. V1 old evidence unchanged.\n')
    human=['Review negative empirical contribution and full citations, especially access-limited related papers','Confirm authors/order/correspondence, official UCAS affiliation and funding','Confirm anonymity, paper size, reference page rule and deadline time/timezone in official CMT','Approve all scientific/AI-assisted claims and perform formal submission/payment/signing manually']
    stages={**state['stages'],'G5':'passed'}
    update_state(ROOT,current_stage='complete',stage_status='completed',stages=stages,latest_run_id=run.id,paper_revision='v2_r04',quality_verdict='READY_FOR_HUMAN_REVIEW',formal_submission_ready=False,human_action_required=human,g5_verification_run=a.verification,g5_delivery_run=run.id)
    write('docs/goals/GOAL_V2_STATUS.md','# VPR-GOAL-V2 — completed\n\nG0/G1/G2/G4/G5 passed; G3 scientifically_negative. Overall Outcome C, primary25m raw B unchanged. Final six-page empirical r04 ready for human review, no demonstrated adaptive superiority. All old1470 files/frozen65 inputs unchanged.60tests;five complete new versions,770 numerical ledger cells verified; all exported PDFs and full-page views checked. Main/old tag retained; V2 backups only. Formal submission not approved. Read GOAL_V2_FINAL_DELIVERY.md.\n')
    run.write('metrics.json',dict(outcome='C',primary25m_raw_label='B',quality='READY_FOR_HUMAN_REVIEW',formal_submission_ready=False,versions=verified['results'],tests=60,old_files_verified=1470,frozen_inputs_verified=65,actual_commands=len(commands),run_register=len(register)))
    run.write('checks.json',dict(passed=True,all_G0_G5_deliverables_completed=True,no_test_tuning=True,original_and_failed_evidence_retained=True,numeric_PDF_visual_review_passed=True,human_actions_pending=True))
    (run.path/'interpretation.md').write_text('Goal achieved as reproducible empirical/negative research. Novel adaptive gain unsupported; overall external tolerance transfer C. Automated candidate review complete; authorship/scientific approval/formal submission remain human actions.\n')
    public=ROOT/'artifacts/v2/final';public.mkdir(parents=True,exist_ok=False)
    for name in ['metrics.json','checks.json','ACTUAL_COMMANDS.jsonl','RUN_REGISTER.json']:shutil.copy2(run.path/name,public/name)
    members=[]
    for folder in sorted((ROOT/'outputs_v2').iterdir()):
        for path in sorted(folder.rglob('*')):
            if path.is_file() and path.suffix in TEXT and 'reading' not in path.parts:members.append(path)
    for prefix in ['experiments/temporal_vpr','experiments/paper_v2','configs/v2','docs/goals','docs/research_v2','paper/revisions','paper/submission_candidate/v2','freezes']:
        members.extend(p for p in sorted((ROOT/prefix).rglob('*')) if p.is_file() and (p.suffix in TEXT or p.suffix=='.pdf'))
    members.append(ROOT/'GOAL_V2_FINAL_DELIVERY.md')
    with zipfile.ZipFile(public/'evidence.zip','x',zipfile.ZIP_DEFLATED) as z:
        for path in sorted(set(members)):
            if path.suffix in TEXT:
                content=path.read_text(errors='replace')
                assert not re.search(r'-----BEGIN (?:OPENSSH|RSA|EC) PRIVATE KEY-----\n',content),path
                assert not re.search(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|sk-proj-[A-Za-z0-9_-]{25,})\b',content),path
            z.write(path,path.relative_to(ROOT).as_posix())
        assert z.testzip() is None
    (public/'SHA256SUMS').write_text(''.join(digest(p)+'  '+p.name+'\n' for p in sorted(public.iterdir()) if p.is_file()))
    assert all(p.stat().st_size<100*1024**2 for p in public.iterdir() if p.is_file())
    print(json.dumps(dict(run=run.id,archive_sha256=digest(public/'evidence.zip'),archive_bytes=(public/'evidence.zip').stat().st_size,quality='READY_FOR_HUMAN_REVIEW')),flush=True)
if __name__=='__main__':main()
