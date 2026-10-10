# UPINLBS VPR Starter — 2026-10-10

先读 **PLAN.md**，再读 **AGENTS.md** 和 **configs/protocol.yaml**。

这是“规划 + 可审查的评测/门控辅助代码 + 论文骨架”，不是完整开箱即用的真实模型复现，也没有任何真实VPR实验结果。

## 已包含
- 完整中文执行、学习、数据划分、实验及论文规划。
- 原创 NumPy 评测/路由辅助代码，双逻辑回归门控参考实现。
- 12个合成单元测试；测试结果见 TEST_RESULT.txt。
- 分阶段本地Codex提示词与运行报告模板。
- 英文LaTeX章节骨架和真实来源BibTeX。

## 必须在Ubuntu接着做
- 核查真实CPU/GPU、安装相容PyTorch、确认Codex登录。
- 下载公开数据/模型，适配编码器、manifest、真实在线计时及运行脚本。
- 核实2026官方模板，完成真实实验后写作。

## 仅运行本包辅助测试
```bash
# 在独立Python环境中，不要用sudo pip
python -m pip install -r requirements-core.txt
python -m pytest -q
```

运行测试不需要GPU、外部数据或模型权重。合成测试通过不能证明真实数据结果。

## 论文格式状态
paper/main.tex 使用 IEEEtran 的工作稿骨架。**未核实UPINLBS2026正式模板；不能直接把它当已合规终稿。** 合计6页保守预算包含参考文献和声明。没有虚构实验数字，所有缺失结论保留 TODO。

## 使用方式
将整个目录放到 Ubuntu 的 ~/research/upinlbs_vpr。已有同名目录时先备份并人工合并，不覆盖现有代码/配置。让本地 Codex 从 docs/prompts.md 的 P0 开始，每次只执行一个阶段。

来源信息在 PLAN.md 末尾。数据、checkpoint、第三方仓库及字体均未打包。
