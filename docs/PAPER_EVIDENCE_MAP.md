# 论文工作稿证据映射

当前 `paper/main.tex` 是英文开发工作稿，最终评测部分明确待填，不能当作已完成论文或投稿文件。原生编辑器第一次初始化资源与第二次PDF资源下载超时，保留日志；加入T1字体编码后第三次工具返回success。成功编译不等于已经导出独立PDF，也未确认最终页数。未安装终端TeX、LaTeX插件或修改系统驱动。

| 工作稿内容 | 实际证据 |
|---|---|
| A/DINO开发Recall、29纠错/88误伤机会、oracle81% | `outputs/p2_20261010_134300/dev_baselines/metrics.json`，validation |
| 原始净收益三个预算零调用；错误预测10%为72.67%、8/4 | `outputs/p3_dinov2_stable_20261010_141000/gate_development/metrics.json`，validation |
| EigenPlaces验证83.33%、51/15、oracle88.33%；train86.67%、59/34 | `outputs/p3_eigenplaces_20261010_141736_ayAvV5/dev_baselines/metrics.json` |
| 工作稿开发表及18/5、22/4等路由计数 | 同run `gate_development/metrics.json`，全部50策略 |
| 随机25%均值73.87%、总体标准差1.34个百分点 | 同run `gate_development/metrics.json`，`random_all_seeds_summary.validation.random_matched_net_budget25`；所有种子0–4 |
| A/Eigen/净收益/错误真实均值8.92/14.44/13.02/13.38 ms | 同run `online_validation_budget25/metrics.json`，每种900次真实查询；时钟未锁定 |
| 原始模型对零调用门控10.19 ms与A单独7.78 ms | 原始stable run `online_validation_budget25/metrics.json` |
| 900次A/225次B、45k离线/15.3k在线、train-only标准化 | Eigen run `phase_acceptance.json`、`independent_artifact_replay.log`，退出0 |
| 31个测试、最终入口拒绝无确认包 | Eigen run `prospective_evaluator_synthetic_tests.log`；冻结review run `intentional_missing_confirmation_guard.log`，后者退出1是预期拒绝，没有最终图像访问 |
| 下一阶段的完整模型/清单/参数/门限/矩阵 | `outputs/freeze_review_20261010_143800/selection.json`，Git cd47f41，待人工确认 |
| 最终Nordland和GP跨域指标、最终论文结论 | **未运行，无数字，不得填入开发结果冒充** |
| 三张开发集矢量PDF/PNG、100个策略点、30600行真实计时重算 | `outputs/paper_dev_figures_20261010_150500/figures/`；来源指纹、点CSV及 `figure_acceptance.json`；三个图表PDF各1页、字体嵌入，**不是论文页数核验** |

公式、输入五统计、监督标签、阈值和执行边界对应 `core.py`、`policies.py`、`online.py` 及拟合脚本。8行入门解释与匹配例图选择规则见 `P3_SELECTOR_REPORT.md`。没有把CUDA分配峰值当作完整进程内存、调用预算当作精确测试调用率、帧容差当作米级精度。

引用核查：CosPlace/EigenPlaces的题目、作者和页码由官方代码引用与CVF出版页面核对；To-Match的GitHub README页码2849–2860与CVF出版页2874–2885不同，稿件采用[CVF出版页](https://openaccess.thecvf.com/content/CVPR2025W/IMW/html/Sferrazza_To_Match_or_Not_to_Match_Revisiting_Image_Matching_for_CVPRW_2025_paper.html)。[SMR arXiv v2](https://arxiv.org/abs/2503.06840)确认IROS2025接受信息，稿件保留可核查预印本标识。[SU正式出版](https://doi.org/10.1109/LRA.2026.3674688)与作者仓储支持其书目信息，但无可验证实现/完整数值约定，不作数字比较。其他出版最终元数据和人工阅读审阅仍列入P5；不宣称引用审计已全部完成。

独立编译使用同一 `paper/main.tex` 的内联参考文献，不要求编译器访问外部bib或图片文件。`references.bib` 继续作为来源库存；最后应核对与内联列表一致。IEEE会议格式已从官网前端确认，匿名、纸张、截止时区和完整作者仍待人工核实；保守目标是正文图表参考文献和声明合计≤6页。

8项引用的原始来源与访问限制已整理到 `PAPER_REFERENCES_AUDIT.md`，DINOv2作者库存纠错不影响内联简写或实验。绘图依赖使用单独 `.venv-paper`。当前工具元数据明确原生编译返回诊断而不导出PDF；[官方编辑器说明](https://learn.chatgpt.com/docs/artifacts-viewer)确认LaTeX编辑和PDF预览，但未提供本会话可调用的导出路径。成功编译证据保留，独立论文PDF与总页数仍未确认。
