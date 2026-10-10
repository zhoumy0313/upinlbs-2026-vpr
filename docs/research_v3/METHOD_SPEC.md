# V3 mathematical contract (before final freeze)

Online input is aligned, finite, current image cosine scores; stored prior score vectors; canonical reference traversal IDs. Query GT, frame numbers, poses and future frames are absent from the matching interface. St Lucia filenames only locate decoded images; they are not parsed for online scores.

CosPlace ResNet18/512, EigenPlaces ResNet50/512 and DINOv2 ViT-S14/CLS/384 are existing frozen source/checkpoint identities. RGB -> ToTensor -> ImageNet normalization -> tensor bilinear antialiased warp224² -> frozen eval encoder -> unit descriptor. CPU similarity re-normalizes float64 and clips cosine to [-1,1]. These compact configurations do not reproduce each source paper's headline results.

T_t(j) = max over declared v of mean over lag0..L-1 S_(t-lag)(j-rint(v*lag)). rint ties to even. Whole paths out of bounds or crossing a reference traversal are -infinity. History resets at every split/query traversal. Before L observations, use A; common accuracy excludes first8 for all methods, with full-stream startup reported separately. Full L3/.8,1,1.2 has identical rounded offsets [0,1,2] for all three velocities: the hypotheses collapse in this small window; never attribute an effect specifically to three distinct L3 trajectories.

C(H,r) unions clipped, same-traversal neighborhoods around stable Top-H finite T endpoints, no NMS, then removes nonfinite T indices consistently for R1/R2/P. Overlaps are deduplicated. H/r are counts of canonical reference frames, not metres. C empty or startup => A with explicit reason.

R0 ranks T. R1 ranks current S in C. R2 ranks (1-gamma)(S+1)/2+gamma(T+1)/2 in C. R3 is H1 R1, a declared alias. P uses A_set={j in C: T(j)>=max(T)-epsilon} and ranks it by S; all remaining references are appended by original stable S rank. This is a complete ranking, not top1 replacement without a defined R@K. Epsilon0 preserves the maximum-T tie set, with S tie resolution; epsilon exceeding all finite candidate gaps is exactly R1. No trained neural layer or extra encoder is added by local policies.

Initial analysis ledgers record `path_offsets` for the first declared velocity hypothesis. That field must not be described as the winning path for multi-velocity T. All evaluated offsets are deterministic from saved BACKENDS/L/velocity and source snapshots; an explicit winning-path trace supplement will accompany frozen comparisons. The score identity, all candidate/eligible indices, top10 image-ID mapping and GT distances make predictions auditable without supplying labels to matching.

Computational scale: descriptor dot product O(ND); temporal aggregation O(|V|LN); stable full-gallery ranks O(N log N); local candidate size <=H(2r+1), further limited by overlap/boundary. This implementation sorts the full gallery repeatedly for diagnostics; it is not a claim of an optimized robot system. Real complete image-pipeline timing, including its actual diagnostics cost, is measured separately from cached accuracy.

Search grid and gate were committed before V3 outputs. P has32 configurations on fixed L9-v1.2 only; R1/R2 have32/160 across four backends. The strongest fixed and local baselines determine whether P has evidence. An improvement over weak L9 alone does not establish a new contribution. No optional mechanism or map-assisted variant is added following P failure.
