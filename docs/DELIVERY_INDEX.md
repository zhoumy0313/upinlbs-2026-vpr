# 本地交付索引与未完成项

2026-10-10。工作目录 `/home/aaron/upinlbs_vpr/upinlbs_vpr_starter`。P0–P4实验链已完成；英文实验工作稿已原生编译成功，完整目标还不能标记完成，因为独立论文PDF、≤6页与版面尚无验收证据。保持原目标，不用图表PDF代替论文。

## 直接入口

- [英文论文源文件](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/paper/main.tex)：同一原生编辑器文件，无额外bib/图片文件要求；实验Pending已清除，作者/通讯等仍按已知信息标注。
- [最终实验报告与可重复命令](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/docs/P4_FINAL_EXPERIMENT_REPORT.md)：主要指标、失败解释、8行初学者流程与下一步。
- [论文逐项证据映射](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/docs/PAPER_EVIDENCE_MAP.md)、[引用核查](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/docs/PAPER_REFERENCES_AUDIT.md)、[提交审阅清单](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/docs/SUBMISSION_CHECKLIST.md)。
- [全部最终表格CSV](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p4_frozen_20261010_152754_Z1p6iu/figures_readable_v3/all_final_metrics.csv)：510行含所有容差/策略/oracle，未计时项留空。
- [真实精度—时延PDF](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p4_frozen_20261010_152754_Z1p6iu/figures_readable_v3/final_accuracy_latency.pdf)、[预算漂移PDF](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p4_frozen_20261010_152754_Z1p6iu/figures_readable_v3/final_invocation_drift.pdf)、[互补性PDF](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p4_frozen_20261010_152754_Z1p6iu/figures_readable_v3/final_complementarity.pdf)。
- [匹配示例的模型输出与排序记录](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p4_frozen_20261010_152754_Z1p6iu/figures_readable_v3/matching_examples.json)：8类首张样例，照片PNG/PDF同目录，含512维输出的前8项、范数、top10分数/ID与门控。
- [全部实际执行命令/退出码](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p4_frozen_20261010_152754_Z1p6iu/commands.jsonl)、[主评测日志](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p4_frozen_20261010_152754_Z1p6iu/final_evaluation.log)、[独立复核](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p4_frozen_20261010_152754_Z1p6iu/phase_acceptance.json)、[复核重放](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p4_frozen_20261010_152754_Z1p6iu/phase_acceptance_replay_v2.json)。
- [原生论文编译成功记录](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p4_frozen_20261010_152754_Z1p6iu/native_final_compile_attempt_1.json)、[图表PDF与三遍计时审计](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p4_frozen_20261010_152754_Z1p6iu/rendering_acceptance.json)。
- [源稿与P0–P4完整证据包](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/handoff_complete_20261010_163800/UPINLBS_full_evidence_working_draft.zip)：包含早期环境/toy/数据/baseline/开发门控的原始日志、失败尝试、完整最终实验记录、源代码和匹配示例。包内没有独立论文PDF，也不包含批量数据、权重或虚拟环境。
- [逐阶段覆盖与历史退出码](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/handoff_complete_20261010_163800/stage_coverage.json)、[压缩包CRC与逐文件SHA核验](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/handoff_complete_20261010_163800/bundle_acceptance.json)。历史失败不抹去；各阶段成功的复核run另有完整日志，单元测试数量指当时的测试集。

证据打包的可重复命令（使用新的输出目录以保留旧包）：

```bash
python3 scripts/record_command.py --run-dir outputs/handoff_complete_20261010_163800 --name create_full_evidence_bundle -- python3 scripts/create_full_delivery_bundle.py --output-dir outputs/handoff_complete_20261010_163800
```

打包只读取既有研究文件并校验压缩包，没有重新训练或运行图像实验。生成命令自己的完整日志位于包外同目录，避免把尚未结束的日志当作最终快照。

## 要求与证据审计

| 要求 | 当前判定 | 证据 |
|---|---|---|
| 读取原PLAN、AGENTS、protocol，保留既有服务与驱动 | 已执行；未改驱动、SSH、FlClash、Codex配置 | 原始文件保留，P0报告和后续包身份；不是用文档中的未来任务假装实际运行 |
| CPU/内存/磁盘/GPU/驱动/Python/网络/Codex审计 | 已完成 | `docs/P0_ENVIRONMENT_REPORT.md`、`outputs/p0_20261010_111919/` |
| 独立兼容GPU环境/单元测试/官方CosPlace toy | 已完成 | `.venv-p0`、P0/P0recheck实际CUDA和17图库/5查询toy；31个先前测试记录包含后续扩展，不全为真实数据实验 |
| 图像/ID/真值/检索pipeline | 已完成来源与代码审计；空间精度不作保证 | P1 manifest-v2、4100图解码与重复审计、作者hard/soft语义、自检；`docs/P1_DATA_PIPELINE_REPORT.md` |
| baseline复现 | 已完成固定224研究设置；不声称原论文数值复现 | P2重复run、模型source/完整state SHA、检索一致性及开发实际指标 |
| 问题分析、候选小改进、控制/消融 | 已实现并评测，普遍改进不成立 | P3两对50策略/全部种子/真实计时；目标改为用户确认的实证比较/失效分析，不虚构新颖性 |
| 一次B替换及保留失败 | 已完成且未再次换模型 | P3原始DINO负结果、先于Eigen结果记录的fallback决策、最终原始对仍评测 |
| 测试前人工确认与固定方案 | 已完成 | 精确包SHA、人类确认原文、P4运行内副本，科学代码与参数不因最终结果改变 |
| 最终留出与跨域完整矩阵/敏感性 | 已完成 | P4 85000离线/510策略半径独立重算，两次完整审计通过 |
| 真实batch1计时、调用、内存与离线成本 | 已完成实际有限范围 | 107100在线记录、21策略/每对每集、3遍与CUDA同步；Torch allocator和warm-file限制明确 |
| 所有种子、图表、匹配例和逐点来源 | 已完成 | 最终CSV、三图、8组例、SHA与字体审计；原布局与失败日志保留 |
| 英文论文源、真实数字、引用、披露、编译 | 实验工作稿完成并成功编译；人类审阅待做 | main.tex、证据映射、8引用库存、具体AI使用披露、原生success |
| 独立论文PDF、全文≤6页、PDF字体和版面 | **未完成/缺证据** | 当前工具只返回诊断，无导出论文PDF；不能凭3386个源空白词或11张单页图推断 |
| 其他作者、通讯、匿名、纸张与具体截止时区 | 尚待确认，不妨碍本地工作稿 | 用户已确认第一作者与UCAS，余项在提交清单；不擅自编造 |
| 自动投稿/发消息/付款/版权 | 未执行，且不属于授权范围 | 交付是本地研究材料和作者工作稿 |

## 剩余的具体动作

从原生LaTeX编辑器取得已编译的论文PDF，放到 `paper/main.pdf` 或交回本聊天；之后检查真实总页数≤6、字体、各页布局和数字。若超页，压缩正文/整合表图并在同一源文件中修正，不改科学结果，不缩默认正文字号/边距强塞。

当前原生编译工具的明确范围是返回诊断而不导出PDF；因此该步骤需要可访问的导出文件。作者另核实待定信息与正式细则；本工作稿不能自动当作投稿授权。
