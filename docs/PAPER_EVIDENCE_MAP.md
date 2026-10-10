# 论文工作稿证据映射

2026-10-10。`paper/main.tex` 已从独立复核的冻结最终实验填入方法、协议、开发结果、最终结果、敏感性、讨论、摘要及结论，无实验Pending字段。保留已知第一作者与其他作者/通讯信息待核实的工作稿状态；不表示已投稿或通过人类审阅。

主最终run为 `outputs/p4_frozen_20261010_152754_Z1p6iu/`，下表“final”指该run，开发和最终结果分别标识。

| 稿件内容 | 真实证据 |
|---|---|
| 原始A/DINO验证71.33%/51.67%，29纠错/88误伤，oracle81% | `outputs/p2_20261010_134300/dev_baselines/metrics.json`，validation |
| 原始净收益开发三预算零调用、错误10%72.67%及8/4 | `outputs/p3_dinov2_stable_20261010_141000/gate_development/metrics.json`，validation |
| Eigen验证83.33%、51/15、oracle88.33%；train86.67%、59/34 | `outputs/p3_eigenplaces_20261010_141736_ayAvV5/dev_baselines/metrics.json` |
| 开发10/25/50表、25%净收益75.67%及18/5，错误77.33%及22/4 | 同Eigen run `gate_development/metrics.json`，50策略完整 |
| 开发随机25%73.87%、总体SD1.34pp；真实8.92/14.44/13.02/13.38ms | 同run随机汇总及 `online_validation_budget25/metrics.json`，每策略900真实查询 |
| 科学包、实际人工确认与参数冻结 | `outputs/freeze_review_20261010_143800/selection.json`、同目录 `human_confirmation.json`；final `results/freeze_identity.json`保存执行Git提交及确认副本 |
| 摘要/最终表：Nordland A14.15/Eigen10.00/净收益25 10.31%，实际调用78.92%；GP A34.5/Eigen36/净收益34.5%，实际15.5% | final `results/{nordland,gardens}/pair_eigenplaces/accuracy.json`，主半径5/0 |
| 最终单模型R@1/5/10及原始DINO3.38%/23.5% | final两数据集各 `pair_{eigenplaces,dinov2}/accuracy.json`，A_only/B_only |
| 留出17纠错/44误伤机会、541两模型都错；GP31/28及oracle50% | 同accuracy和final `phase_acceptance.json`四格；oracle仅top1诊断 |
| 原始DINO净收益留出调用2/保A14.15%，错误5.08%；GP净收益35.5%及5/3 | final `pair_dinov2/accuracy.json`与逐查询记录 |
| 随机均值/总体SD及实际调用；全部种子0–4 | final `accuracy.json.random_all_seeds`、`accuracy_per_query.csv`；两组随机策略皆保留 |
| 表/图均值，Nordland7.56/13.62/10.66ms、GP5.84/7.97/8.92ms | final `pair_eigenplaces/latency.json` 及各策略 `_latency.csv`，三完整遍历、不含初始化 |
| 半径1/10，GP自定义8，排名/决策未改变 | final `accuracy.json.by_radius`，GP8不等于教程GTsoft-ignore |
| 85000离线/107100在线/510策略半径，ID/模型/数组/门控重算 | final `phase_acceptance.json`、`phase_acceptance_replay_v2.json`及两次完整独立审计日志，均0 |
| 重复组与五维分数分布中位数 | final `shift_diagnostics.json`；P1原始数据审计；没有删重复/重加权或因果宣称 |
| 首张四类匹配的照片、描述子前8项、余弦分数/排名、门控 | final `figures_readable_v3/matching_examples.json`及8组PNG/PDF；固定manifest顺序选取 |
| 三张科学图、11个图表PDF单页/字体、84策略条件各三遍统计 | final `figures_readable_v3/figure_provenance.json`、`rendering_acceptance.json`；图表单页不证明论文页数 |
| 两表一原生独立矢量图的逐点来源 | final `paper_elements/provenance.json`；生成元素逐字嵌入main.tex并已核查 |
| warm-file加载/状态指纹与索引初始化 | final `startup_costs.json`；gallery成本来自各encoder `fingerprint.json.roles.gallery`，不是整机冷启动 |
| 当前实验工作稿源身份和成功编译 | final `paper_draft_provenance.json`、`paper_final_experiment_draft.tex`、`native_final_compile_attempt_1.json`，kind=success、源SHA e6194a58… |
| 独立论文PDF、总页数≤6、论文PDF字体与版面 | **未导出，证据缺失，不能由图表PDF或源字数推断完成** |

所有公式与输入执行边界对应 `core.py`、`policies.py`、`online.py`；最终入口在图像读取之前检查人工确认。只在训练划分拟合小监督选择器，编码器冻结；不是training-free。门限validation-only，最终不校准。真实B前向在门控之后发生；ID与真值仅用于索引、记录和评测，不输入门控。

八项引用的原始来源、元数据与访问限制见 `PAPER_REFERENCES_AUDIT.md`。To-Match采用CVF页码2874–2885；DINO库存作者已纠正。SMR已有纠错/误伤类别，SU实现/完整数值约定未核实而按确认方案排除数字比较。未找到同名论文不能证明新颖性。

旧review run保留原生初始化/资源下载超时及T1后开发稿编译成功的记录，本次最终实验稿也返回success。当前编译工具只返回诊断、不导出PDF；[官方编辑器说明](https://learn.chatgpt.com/docs/artifacts-viewer)支持LaTeX编辑与PDF预览。没有安装本地TeX或LaTeX插件。独立论文PDF与≤6页、作者/匿名/纸张/具体截止时区仍需核实，见 `SUBMISSION_CHECKLIST.md`。
