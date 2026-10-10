# UPINLBS 2026 — Visual Place Recognition

本项目已完成 Ubuntu 独立环境、官方 CosPlace toy、数据/真值审计、冻结编码器 baseline、监督门控及对照/消融、冻结后的最终实验，以及英文论文工作稿。研究问题是：**什么时候值得调用第二个视觉编码器？**

最终结果没有证明门控普遍优于单模型。论文如实分析互补性、验证预算迁移和真实执行成本；不声称训练免费、新标签首次提出或原论文数值复现。其他作者/通讯信息仍待确定，稿件需作者与导师审阅后决定投稿。

## 论文与结果

- [英文论文PDF：5页含参考文献](paper/main.pdf)、[LaTeX源稿](paper/main.tex)、[PDF验收报告](docs/P5_PDF_ACCEPTANCE_REPORT.md)。
- [最终实验报告](docs/P4_FINAL_EXPERIMENT_REPORT.md)、[开发选择器报告](docs/P3_SELECTOR_REPORT.md)、[引用核查](docs/PAPER_REFERENCES_AUDIT.md)、[投稿审阅清单](docs/SUBMISSION_CHECKLIST.md)。
- [全部510行最终指标](artifacts/results/all_final_metrics.csv)、[各数据集/模型对的accuracy与latency JSON](artifacts/results)、[项目生成的科学图](artifacts/figures)。
- [原始文本证据归档](artifacts/evidence/execution_evidence_20261010.zip)及[逐文件SHA-256清单](artifacts/evidence/execution_evidence_20261010.manifest.json)：573个文件，包含P0–P5命令、退出码、原始失败、逐查询记录、模型/数据指纹、拟合参数和冻结确认。

| 主协议 | CosPlace A-only R@1 | EigenPlaces B-only R@1 | 净收益门控25% R@1 | 实际B调用率 |
|---|---:|---:|---:|---:|
| Nordland留出，r=5，650查询 | 14.15% | 10.00% | 10.31% | 78.92% |
| Gardens Point夜间，r=0，200查询 | 34.50% | 36.00% | 34.50% | 15.50% |

25%是验证集预算；最终实际调用率按真实结果报告，未重新校准。A/B编码器冻结，仅训练读取五个A-only分数统计的小选择器。触发后运行B全图库检索并替换整个排名。107100条真实在线记录使用batch=1、预热20、CUDA同步和三次完整遍历；缓存准确率模拟不冒充模型时延。

## 克隆与恢复证据

```bash
git clone git@github.com:zhoumy0313/upinlbs-2026-vpr.git
cd upinlbs-2026-vpr
python3 scripts/repository_evidence.py verify
python3 scripts/repository_evidence.py restore
```

恢复命令把文本证据还原到原来的 `outputs/<run_id>/` 相对位置，逐项校验SHA，不覆盖内容不同的已有文件。它不下载数据/模型、不生成描述子、不运行最终测试。旧日志中的绝对路径和环境信息保留为历史证据；代码及数据manifest使用项目根目录/相对图像路径。跨机重跑须记录新环境和新run，不能冒用旧缓存身份。

## 环境与分阶段复现

先读原始提出阶段的 [PLAN.md](PLAN.md)、[AGENTS.md](AGENTS.md)、[protocol.yaml](configs/protocol.yaml)，再读[当前执行计划](docs/RESEARCH_EXECUTION_PLAN.md)。原始protocol的提出状态不倒写为预注册；实际最终方案和人工确认在证据包中的 `outputs/freeze_review_20261010_143800/`。

原Ubuntu继续使用已配置的 `.venv-p0`；系统驱动、SSH、FlClash和Codex配置保留。已有独立环境中的单元检查：

```bash
.venv-p0/bin/python -m pytest -q
```

先前31项单元/合成检查通过记录保留在证据归档；它们不等于真实VPR实验。CPU/GPU安装与官方toy设置见[环境报告](docs/P0_ENVIRONMENT_REPORT.md)和[远程保存/跨机说明](docs/GITHUB_BACKUP.md)。GPU研究环境使用Torch 2.6.0+cu124、torchvision 0.21.0+cu124；没有可用GPU时先用CPU，避免安装或修改系统驱动。

准备好公开第三方源、官方checkpoint和数据后，各阶段入口为：

```bash
bash scripts/run_p0_smoke.sh
bash scripts/run_p1_data_audit.sh
bash scripts/run_p2_dev_baselines.sh
bash scripts/run_p3_dev_gates.sh eigenplaces
```

每次写新的run目录。P4是最终测试入口，须提供已确认的冻结包；不能用最终数据选模型、调门限或挑种子。原始DINO结果及唯一一次开发阶段EigenPlaces替换均保留。

## Git存储取舍

普通Git保存源码、测试、配置、manifest、论文、数值结果、项目科学图及11.9 MB文本证据ZIP。数据集、checkpoint、第三方源码、虚拟环境、描述子缓存和数据集照片留在本地，按官方URL/固定commit/校验值重新获取。含匹配照片的完整本地交付包不上传仓库，公开证据保留图像ID、SHA和排序数值。无需为这些官方可下载资产配置Git LFS；详见[存储清单](docs/GITHUB_BACKUP.md)。

此仓库交付本地研究材料和作者工作稿，未自动投稿、签署版权或支付费用。
