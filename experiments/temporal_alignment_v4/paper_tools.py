"""Build new standalone V4 drafts and number-to-evidence mappings only."""
import json,re
from runtime import ROOT,write,sha
def metric(metrics,name,r,hz=5):return next(x for x in metrics if x['method']==name and x['radius_m']==r and x['hz']==hz)
def aliases():return [('A','CosPlace'),('B','EigenPlaces'),('RRF60','RRF'),('AB_0.75','Fixed A/B fusion'),('L3','Index L3'),('L5','Index L5'),('L9','Index L9'),('old_fixed_L9','Old fixed L9'),('L3_global_0.25','Index global blend'),('R1_L3_H3_r4','Index local R1'),('R2_L3_H1_r1_g0.5','Index local R2'),('Time_W1.6','Time alignment'),('TimeR1_W1.6_H1_r0.2','Time local R1'),('TimeR2_W1.6_H1_r0.2_g0.5','Time local R2'),('Proposed_W1.6_H1_r0.2_e0.01','Constrained refinement')]
def generate(version,final=False):
    dev=json.loads((ROOT/'docs/research_v4/BASELINE_RESULTS.json').read_text());sel=json.loads((ROOT/'configs/v4/selected_methods.json').read_text());test=json.loads((ROOT/'docs/research_v4/INDEPENDENT_RESULTS.json').read_text());dm=dev['results']+sel['results'];tm=test['results'];timing=json.loads((ROOT/'docs/research_v4/REAL_TIMING_RESULTS.json').read_text()) if final else None
    folder=ROOT/'paper/revisions'/version;folder.mkdir(parents=True,exist_ok=False);evidence=[]
    def table(metrics,seq,label):
        out=[]
        for name,title in aliases():
            fields=[]
            for radius in [.25,.5,1.]:
                m=metric(metrics,name,radius);fields.append('/'.join(f'{100*m[k]:.1f}' for k in ['R1','R5','R10']));evidence.append(dict(version=version,table=label,method=name,radius_m=radius,correct=[m[k] for k in ['correct1','correct5','correct10']],denominator=m['closed_queries'],rendered=fields[-1],source='INDEPENDENT_RESULTS.json' if seq.startswith('freiburg3') else 'BASELINE_RESULTS.json or selected_methods.json'))
            m=metric(metrics,name,.5);fields.append(f"{m['top1_distance_median_all_valid']:.2f}/{m['top1_distance_P90_all_valid']:.2f}")
            if timing:
                t=next(x for x in timing['results'] if x['sequence']==seq and x['method']==name);fields.append(f"{t['mean_ms']:.2f}/{t['P95_ms']:.2f}");evidence.append(dict(version=version,table=label,method=name,mean_ms=t['mean_ms'],P95_ms=t['P95_ms'],source='REAL_TIMING_RESULTS.json'))
            else:fields.append('pending')
            out.append(title+' & '+' & '.join(fields)+r' \\')
        n=[metric(metrics,'A',r)['closed_queries'] for r in [.25,.5,1.]];valid=metric(metrics,'A',.5)['valid_gt_queries'];opened=metric(metrics,'A',.5)['open_queries']
        return r'''\begin{table*}[t]
\centering\caption{'''+label+f''' (5Hz): radius-specific closed denominators {n[0]}, {n[1]}, {n[2]}. Entries are R@1/5/10 in percent. At 0.5m, {valid} valid queries include {opened} open queries. Error median/P90 is over all valid queries (metres); time mean/P95 is real batch-one (ms).'''+r'''}
\label{tab:'''+('dev' if seq.startswith('freiburg2') else 'test')+r'''}
\scriptsize\setlength{\tabcolsep}{5pt}
\begin{tabular}{lccccc}\hline
Method & 0.25m R1/5/10 & 0.5m R1/5/10 & 1.0m R1/5/10 & Error med/P90 & Time mean/P95\\\hline
'''+ '\n'.join(out)+r'''
\hline\end{tabular}\end{table*}
'''
    devtable=table(dm,'freiburg2_pioneer_slam','Pioneer development');testtable=table(tm,'freiburg3_long_office_household','Frozen independent Long Office')
    ttext=r'''Timing was still pending in this initial draft; Table cells explicitly say pending. This version is preserved to distinguish the independent-test result from the later measured deployment evidence.'''
    if final:
        total=timing['total_real_timed_queries'];mismatch=sum(x['cached_top1_mismatches'] for x in timing['results']);repeat=sum(sum(x['repeat_top10_mismatches']) for x in timing['results'])
        ttext=f'''We measured {total:,} complete batch-one query intervals across both streams, 17 frozen representative strategies and three ordered passes per strategy. Each strategy used 20 warm-up images followed by a history reset. The independent CSV aggregation reproduces every mean/P95 and per-pass correct count. Batch-16 cached versus batch-one top-one mismatch count was {mismatch}; repeat top-ten mismatches were {repeat}. Batch-size differences are numerical discrepancies to report, not permission to select new methods. Tables show batch-16 cached accuracy and independently measured batch-one latency; the repository includes every actual online pass accuracy. Gallery decoding/encoding and model loading were measured separately. Timing assumes resident models and a cached prior gallery, warm OS file access, and a desktop laptop GPU; it is not a cold-start, embedded-robot or full-SLAM benchmark.'''
    preamble=r'''\documentclass[conference,letterpaper]{IEEEtran}
\usepackage{amsmath,amssymb,graphicx,booktabs,url,tikz}
\usetikzlibrary{arrows.meta,positioning}
\begin{document}
\title{Timestamp-Aware Temporal Matching on TUM Revisit Streams:\\A Frozen Negative-Result Study}
\author{\IEEEauthorblockN{Mingyang Zhou}\IEEEauthorblockA{University of Chinese Academy of Sciences\\Empirical working draft; author list subject to confirmation}}
\maketitle
\begin{abstract}
Temporal place recognition can smooth errors while shifting the selected reference away from the current camera location. We study this tradeoff using frozen CosPlace and EigenPlaces descriptors on two continuous TUM RGB-D sequences, with camera-pose labels restricted to offline evaluation. A fixed first-half gallery, a ten-second query buffer, and nearest timestamp association define a reproducible 5Hz revisit protocol. We predeclare 139 mature/simple baseline configurations and 36 timestamp-alignment/endpoint-support configurations on Pioneer SLAM, then freeze settings before one independent Long Office evaluation. The selected constrained refinement matches the strongest development primary count (24/229 at 0.5m), but loses at 0.25m (4/172 versus an envelope of 5/172). On the independent sequence it obtains 34/48 at 0.5m, below the frozen baseline envelope of 35/48, and 0/20 at 0.25m while single-frame EigenPlaces obtains 11/20. It also does not improve the selected time-alignment baseline. These results support a negative finding about this particular refinement mechanism, not a positive method contribution. Small correlated closed-set subsets and substantial open-set coverage gaps limit generalization.
\end{abstract}
\begin{IEEEkeywords}visual place recognition, causal temporal matching, timestamp sampling, reproducibility, negative results\end{IEEEkeywords}
\section{Introduction}
Visual place recognition retrieves earlier images that depict the current location; it supplies candidates for geometric localization rather than a complete six-degree-of-freedom camera pose~\cite{tutorial}. Temporal consistency can reject isolated appearance errors, but aggregate sequence evidence need not place its highest score at the most accurate current endpoint. This distinction matters when a coarse retrieval hit is evaluated using camera-position distances rather than broad frame tolerances.

Previous project iterations used already explored outdoor and ordinal datasets. They remain archived, but cannot constitute independent validation of a newly chosen mechanism. Here we obtain two real continuous RGB streams with publicly documented reference poses~\cite{tum}. Pioneer is the sole development collection; Long Office is not used for algorithm or parameter selection. Our question is narrow: does physical-time score alignment followed by constrained visual endpoint refinement outperform strong short-window and naive local strategies under one fixed metric protocol?

The answer for this bounded study is negative. A small improvement over an old long-window control is insufficient when stronger single-frame, short-window, fusion or simple-refinement comparators exist. Moreover, a gain at 0.5m does not offset a collapse at the predeclared 0.25m sensitivity. We therefore present a reproducible evaluation and failure analysis, not a new state-of-the-art localization algorithm. Our concrete outputs are a timestamp/pose manifest with explicit invalid/open cases, a finite and auditable comparison, one frozen independent test, and image-based inference measurements. Whether this limited empirical contribution is appropriate for a conference requires human scientific review.

\section{Prior Work and Scope}
SeqSLAM and OpenSeqSLAM2 establish sequence trajectory and speed-hypothesis matching~\cite{seqslam,openseq}. STA-VPR uses spatial feature alignment and local-matching dynamic time warping, including relaxed endpoints~\cite{sta}. AdaptSeqVPR describes dynamic sequence-step adjustment and a learned discriminator~\cite{adapt}; our access to that work was limited to publisher abstract/metadata, so we do not claim a full implementation or formula-level distinction. SMR predicts when sequence matching is receptive using supervised score features~\cite{smr}. Temporal alignment, speed handling and endpoint relaxation are therefore established ideas.

We use global CosPlace/EigenPlaces descriptors~\cite{cosplace,eigenplaces}; low-resolution full-image inference is our declared protocol adaptation, not a reproduction of their original published dataset scores. Cosine-score temporal aggregation is likewise not an official reproduction of grayscale SeqSLAM, local-strip STA-VPR, AdaptSeqVPR or the supervised SMR predictor. Our baselines include one-based reciprocal rank fusion with constant 60~\cite{rrf}, fixed affine descriptor-score fusion, and explicit simple local controls. We neither retrain visual models nor introduce a ground-truth-guided online module.

\section{Data and Evaluation Protocol}
\subsection{Acquisition and timestamp association}
Official TUM archives were transferred to Ubuntu after proxy/direct downloads failed; both original network failures and the transferred archive SHA256 values are retained. Full gzip/tar readability, safe paths, mandatory lists, image decoding, pose finiteness and timestamp order were checked before retrieval. Pioneer contains 2,921 RGB images and 44,212 pose rows; Long Office contains 2,585 RGB images and 8,710 pose rows. RGB spans are 155.217s and 87.097s, respectively. The raw depth streams are retained but not used.

TUM reference translations describe the RGB camera optical center in the motion-capture world frame; timestamps are Unix seconds~\cite{tumformat}. Each RGB timestamp is associated with its nearest reference pose within 0.03s; ties choose the earlier pose. Pioneer has ten exact duplicate pose timestamps: we retain all raw rows and differences, and use the first original row for each duplicated time. This deterministic many-to-one association is our evaluation policy, not the official greedy one-to-one association utility. Original timestamps, association deltas, positions, unit quaternions, file hashes and roles are recorded. All 2,921/2,585 PNGs decode; 38/2 RGB rows lack a pose within tolerance. Invalid rows are retained rather than assigned fabricated coordinates.

\subsection{Causal revisit construction}
We retain the earliest RGB image in each floor-based bin relative to the sequence's first acquisition time. The primary rate is 5Hz; 1Hz and 3Hz are predeclared artificial development conditions, not independent recordings. The midpoint of the full raw RGB time span separates the fixed gallery from the query period. Valid-pose sampled images before that midpoint form the gallery; queries start at least ten seconds after it. This creates gallery/query counts 377/339 for Pioneer and 217/168 for Long Office; measured minimum time gaps exceed ten seconds. The initial rule passed the predeclared development minimum of 100 closed queries at 0.5m without adjustment. The rule was accepted before any retrieval, and applied identically to the independent sequence.

Positives are all gallery camera centers within Euclidean 3D distance $r$ of the associated query camera center. We fix $r=0.5$m and sensitivity radii 0.25/1.0m. Orientation does not filter positives. Recall is
\begin{equation}
R@K={1\over N_r}\sum_{i\in C_r}\mathbf{1}[\operatorname{TopK}(i)\cap P_i(r)\ne\varnothing],
\end{equation}
where $C_r$ contains valid-pose queries with at least one positive. Every method shares $C_r$ at each radius, including startup fallback; radii have different denominators, so their percentages are not interchangeable. Pioneer has 338 valid-pose queries and one invalid-pose query. Its closed counts are 172/229/278; open counts are 166/109/60. Long Office has 168 valid queries; closed counts are 20/48/89 and open counts 148/120/79. Invalid-query images still update causal history. We attempt every query and reject none: open queries are forced matches, not successful open-set recognition. No calibrated rejection or full-coverage localization claim is made.

\section{Frozen Matching Strategies}
\subsection{Input, descriptors and index controls}
At query time the input is RGB plus a monotonically increasing acquisition timestamp. A frozen network normalizes and warps the image to 224$\times$224 and produces an L2-normalized 512-D descriptor. Cosine similarity against every earlier gallery descriptor gives current scores $S(t,j)$. Online code cannot receive camera centers, quaternions, ground-truth identities, physical speed or future query scores. Reference timestamps and indices are known prior-map metadata.

The index control uses only current/past observations:
\begin{equation}
T_L(i,j)=\max_{v\in V}{1\over L}\sum_{\ell=0}^{L-1}S(i-\ell,j-\operatorname{rint}(v\ell)),
\end{equation}
with $L\in\{3,5,9\}$ and $V=\{0.8,1,1.2\}$. Out-of-gallery paths are invalid; startup ranks current $S$. The historical fixed L9 uses $v=1.2$. Ties-to-even rounding means L3's three positive ratios can yield identical integer offsets; we do not interpret those as three different effective trajectories. Global blends and local R1/R2 controls use declared fixed weights and identical candidate pools.

\subsection{Timestamp alignment and endpoint constraint}
The timestamp baseline uses five uniformly spaced lags $\delta\in[0,W]$, for $W\in\{0.4,0.8,1.6\}$ seconds. It bilinearly interpolates the score surface using observed current/past query times and known gallery times $\tau_j$:
\begin{equation}
T_W(t,j)=\max_{v\in V_t}{1\over5}\sum_{\delta}\widetilde S(t-\delta,\tau_j-v\delta).
\end{equation}
Here $V_t=\{-1.2,-1,-0.8,0,0.8,1,1.2\}$ contains clock-time ratios, not physical motion estimates. Reverse/stationary hypotheses are given to all timestamp controls as well as the candidate. No extrapolation or future query is used. Query history retains the bracket before the oldest needed lag. Startup uses current $S$ until the physical-time span is available. An independent scalar implementation agrees with the vectorized interpolation on irregular synthetic clocks.

The top $H\in\{1,3\}$ temporal endpoints supply a union of gallery timestamp neighborhoods with half-width $b\in\{0.2,0.4\}$s. Only finite temporal scores enter this common pool $C$. The candidate retains
\begin{equation}
E=\{j\in C:T_W(t,j)\ge\max_kT_W(t,k)-\epsilon\},
\end{equation}
for $\epsilon\in\{0.01,0.03,0.06\}$, ranks $E$ by current $S$, then appends every remaining reference in stable current-score order. Empty/startup cases fall back to $S$. Simple R1 removes the constraint in the same pool; R2 blends current and temporal scores with fixed weights. These controls separate alignment from endpoint refinement. All outputs are complete gallery permutations; the ledgers preserve their top ten IDs and candidate/eligible sets. The score threshold is not a probability or confidence certification.

\subsection{Bounded selection and independent freeze}
We predeclare 139 baseline settings and 36 candidate settings, execute each at developer rates 1/3/5Hz, and introduce no additional branch. Selection maximizes the sum of developer correct@1 at 0.25/0.5m, then primary correct@1, then lexicographic name. The selected candidate is $W=1.6$s, $H=1$, $b=0.2$s, $\epsilon=0.01$; fixed fusion assigns EigenPlaces weight 0.75. A positive claim requires exceeding the baseline envelope at both strict radii in development and independent test. The envelope is a descriptive maximum over frozen comparators, not a test-tuned deployable strategy. Code, loaded-state/checkpoint identities, image manifests, raw-archive hashes, clocks, association, radii, gallery/query rules, methods and timing settings were published in an immutable freeze before the first independent retrieval. A single run evaluates all 139 baselines and the selected candidate. No test-dependent parameter change follows.
'''
    results=r'''\section{Results and Failure Analysis}
'''+devtable+testtable+r'''
\subsection{Strong baselines change the apparent conclusion}
At 0.5m the candidate obtains 24/229 developer hits, equal to fixed A/B fusion and several timestamp controls; at 0.25m it obtains 4/172 while the frozen baseline envelope reaches 5/172. The bounded developer gate fails. Long Office gives 34/48 primary hits versus 32/48 for the developer-selected fixed fusion, but the timestamp baseline also gives 34/48 and a simple frozen control gives 35/48. Thus even the primary count does not establish endpoint-refinement benefit over the relevant controls. At 0.25m the candidate gives 0/20, versus 11/20 for single-frame EigenPlaces. We preserve this negative sensitivity rather than change the radius or subset to obtain a favorable method headline.

Each table gives R@1/5/10 at all declared radii. On Long Office the candidate and timestamp baseline tie in primary R@1, but their primary R@5 counts are 41 and 44, respectively. Constrained reranking can harm candidate availability near the top of the list. At 1m their top-one counts are 75 and 76; this wider tolerance cannot repair the failed strict-radii gate. Paired rescue/harm against CosPlace is audited using $N_{\rm rescue}-N_{\rm harm}=N_{\rm correct}-N_{\rm correct,A}$; full query-level differences, candidate coverage and error quantiles are retained, not only selected successes.

\subsection{Sampling, coverage and endpoint interpretation}
Index L9 has developer primary counts 5/45 at 1Hz, 2/138 at 3Hz and 13/229 at 5Hz; the timestamp $W=1.6$s baseline gives 5/45, 14/138 and 24/229. Frame-count windows change their physical duration with sampling, while the time baseline fixes duration. These artificial conditions rebuild both gallery and query and also change spatial reference coverage: they do not isolate timing alone, and they are not independent generalization evidence. The main comparison uses the same 5Hz inputs and common radius-specific query sets.

The primary closed coverage is only 229/338 for Pioneer and 48/168 for Long Office. Forced rankings outside those subsets are visible open-set failures. Position-only positives may depict different viewing directions; frozen global descriptors and a short temporal wrapper cannot be presumed to recover missing visual evidence. Our evaluation measures which earlier camera center was retrieved, not a refined metric camera pose or a geometric correspondence check. Candidate-pool oracle coverage is offline diagnosis only, never an executable method.

\subsection{Actual image inference}
'''+ttext+r'''

\section{Limitations and Conclusion}
This study uses two short indoor collections with overlapping environments, frozen pretrained global descriptors, a full-image low-resolution warp, and a fixed first-half revisit adaptation of an RGB-D SLAM benchmark. It does not reproduce published descriptor benchmarks, use depth, optimize a visual model or demonstrate robustness across many independent routes. Adjacent frames are correlated; the independent strict subset has only twenty queries. Ratios, support thresholds and model choices were selected on the complete development sequence, so developer performance is exploratory rather than another holdout. Translation-only positives do not guarantee matched orientation. Nearest pose association introduces a finite temporal tolerance; retaining duplicate/invalid evidence is more defensible than silently supplying perfect labels.

We find no support for a positive contribution from the tested constrained endpoint refinement. Physical-time normalization can outperform an old long frame window, yet a stronger simple baseline and strict metric sensitivity defeat a broader improvement claim. Future work requires a separately justified representation/geometry mechanism and a new independent collection if it uses these test results for design. We do not automatically add more weights or repeatedly retune this now-seen test. The present manuscript is an empirical working draft; a method paper is not submission-ready on this evidence alone.

\section*{Reproducibility and AI disclosure}
All V1--V3 originals, earlier negative runs, download failures and manuscript versions are retained. V4 source/configuration, small numeric evidence and checkpoint history are available at \url{https://github.com/zhoumy0313/upinlbs-2026-vpr} on the V4 branch. Original images, weights and large arrays remain local with official sources, SHA256 identities and rebuild instructions. Per-query ledgers independently reproduce counts; table cells are mapped to evidence JSON. Formal authorship, template compliance, copyright, fees and submission remain human decisions.

OpenAI ChatGPT/Codex assisted implementation, command execution, analysis, figures and drafting throughout Sections I--VI. Tool-generated code and prose require author review. Numerical statements here come from retained actual runs; negative results and AI assistance are disclosed. This acknowledgment does not assign authorship to an AI system or imply approval of formal submission.

\begin{thebibliography}{12}
\bibitem{tutorial} S. Schubert, P. Neubert, S. Garg, M. Milford, and T. Fischer, ``Visual place recognition: A tutorial,'' \emph{IEEE Robot. Autom. Mag.}, vol.31, no.3, pp.139--153, 2024.
\bibitem{tum} J. Sturm, N. Engelhard, F. Endres, W. Burgard, and D. Cremers, ``A benchmark for the evaluation of RGB-D SLAM systems,'' in \emph{IROS}, 2012, pp.573--580.
\bibitem{tumformat} TUM Computer Vision Group, ``RGB-D benchmark: File formats and download,'' \url{https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats}, accessed Oct.11,2026.
\bibitem{cosplace} G. Berton, C. Masone, and B. Caputo, ``Rethinking visual geo-localization for large-scale applications,'' in \emph{CVPR}, 2022, pp.4878--4888.
\bibitem{eigenplaces} G. Berton, G. Trivigno, B. Caputo, and C. Masone, ``EigenPlaces: Training viewpoint robust models for visual place recognition,'' in \emph{ICCV}, 2023, pp.11080--11090.
\bibitem{seqslam} M. J. Milford and G. F. Wyeth, ``SeqSLAM: Visual route-based navigation for sunny summer days and stormy winter nights,'' in \emph{ICRA}, 2012, pp.1643--1649.
\bibitem{openseq} B. Talbot, S. Garg, and M. Milford, ``OpenSeqSLAM2.0: An open source toolbox for visual place recognition under changing conditions,'' arXiv:1804.02156, 2018.
\bibitem{sta} F. Lu, B. Chen, X.-D. Zhou, and D. Song, ``STA-VPR: Spatio-temporal alignment for visual place recognition,'' \emph{IEEE Robot. Autom. Lett.}, vol.6, no.3, pp.4297--4304, 2021.
\bibitem{adapt} H. Li, G. Peng, J. Zhang, S. Vaikundam, and D. Wang, ``AdaptSeqVPR: An adaptive sequence-based visual place recognition pipeline,'' in \emph{IROS}, 2023, pp.3284--3289.
\bibitem{smr} S. Hussaini, T. Fischer, and M. Milford, ``Improving visual place recognition with sequence-matching receptiveness prediction,'' in \emph{IROS}, 2025, pp.11073--11080.
\bibitem{rrf} G. V. Cormack, C. L. A. Clarke, and S. B\"uttcher, ``Reciprocal rank fusion outperforms condorcet and individual rank learning methods,'' in \emph{SIGIR}, 2009, pp.758--759.
\end{thebibliography}
\end{document}
'''
    # Derive exact RGB duration from actual manifest; no hand-rounded source estimate.
    audit=json.loads((ROOT/'docs/research_v4/DATA_MANIFEST_r02.json').read_text());duration=audit['sequences'][1]['rgb_span_seconds'];preamble=preamble.replace('87.097s',f'{duration:.3f}s')
    text=preamble+results
    if final:
        post=json.loads((ROOT/'docs/research_v4/POSTHOC_DIAGNOSTICS.json').read_text())['orientation'];a,b=post
        diagnosis=f"Post-test offline orientation diagnosis, without filtering or changing methods, finds that {a['positive_rotation_above60deg']}/{a['closed_queries']} Pioneer primary closed queries have no positive reference within 60 degrees of camera rotation; {a['positive_rotation_above120deg']} exceed 120 degrees. The median best-positive rotation is {a['best_positive_rotation_degrees_median']:.2f} degrees, compared with {b['best_positive_rotation_degrees_median']:.2f} degrees on Long Office, where {b['positive_rotation_above60deg']} primary closed queries exceed 60 degrees. This exposes a position-only protocol difficulty, but does not establish a causal explanation for every retrieval error. We retain the accepted protocol and all difficult queries. "
        text=text.replace('Our evaluation measures which earlier camera center was retrieved',diagnosis+'Our evaluation measures which earlier camera center was retrieved')
    if final and (ROOT/'docs/research_v4/PAPER_FIGURES.tex').exists():text=text.replace(r'\subsection{Sampling, coverage and endpoint interpretation}',(ROOT/'docs/research_v4/PAPER_FIGURES.tex').read_text()+'\n'+r'\subsection{Sampling, coverage and endpoint interpretation}')
    (folder/'main.tex').write_text(text);write(folder/'numeric_evidence_map.json',dict(table_cells=evidence,sources={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'docs/research_v4/BASELINE_RESULTS.json',ROOT/'configs/v4/selected_methods.json',ROOT/'docs/research_v4/INDEPENDENT_RESULTS.json']+([ROOT/'docs/research_v4/REAL_TIMING_RESULTS.json'] if final else [])},manuscript_sha256=sha(folder/'main.tex'),version=version,final_timing_included=final))
    return folder
if __name__=='__main__':print(generate('v4_r01',False))
