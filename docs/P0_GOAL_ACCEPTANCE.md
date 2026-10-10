# P0 goal 验收记录

2026-10-10，Asia/Shanghai。goal 范围为此前授权的 P0 环境与 toy 验收闭环；[分步计划](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/docs/P0_GOAL_PLAN.md)已逐项完成。

本轮实际运行了交付的完整重复验收脚本，进程退出 0。新增输出目录为 `/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_recheck_20261010_113854_OTajtv`，上轮日志和产物保留。实际 argv、环境覆盖、耗时与退出码见 [commands.jsonl](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_recheck_20261010_113854_OTajtv/commands.jsonl)。

| 顺序 | 实际步骤 | 验收结果 |
|---|---|---|
| 1 | 环境审计 | 退出 0；SSH active，FlClash/FlClashCore 运行，Codex 已登录 |
| 2 | 合成单元测试 | 退出 0；12 passed in 0.37s |
| 3 | GPU 验证 | 退出 0；CUDA 运算及 torchvision 算子通过 |
| 4 | 官方 CosPlace toy | 退出 0；17 张图库、5 张查询完成编码和匹配 |
| 5 | toy 产物核查 | 退出 0；维度、图像解码、归一化、余弦/L2 排序及官方匹配文件均一致 |
| 6 | 依赖检查 | 退出 0；No broken requirements found |
| 7 | 依赖版本记录 | 退出 0；完整版本记录已保存 |

新增核查：所有查询的前三名 ID 和分数与上轮完全一致；完整候选记录有 85 行、匹配图有 5 张；原有协议、源码和测试哈希未变。见 [goal_acceptance.json](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_recheck_20261010_113854_OTajtv/goal_acceptance.json)。

## 输入到输出：8 步说明

1. 图库保存参考照片，查询照片用于寻找相似地点；toy 中分别有 17 张和 5 张。
2. 图片解码为 RGB，转换、规范化并缩放成 `[1,3,200,200]` 输入张量。
3. CosPlace ResNet18 提取视觉特征，本轮沿用官方预训练权重。
4. 特征经 GeM 聚合和线性层形成 512 维描述子，再做 L2 归一化。
5. 全部图像输出分别组成 `[17,512]` 图库矩阵和 `[5,512]` 查询矩阵。
6. 两者点积得到 `[5,17]` 余弦相似度矩阵，每行表示一个查询对图库的分数。
7. 每行降序排序得到候选；单位向量的余弦排序与官方平方欧氏距离升序排序一致。
8. 候选是参考图像 ID；相似度不是正确概率或位姿。无标签 toy 未计算 Recall，合成测试也不构成真实数据性能实验。

本轮 [候选表](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_recheck_20261010_113854_OTajtv/matches.csv)、[详细模型产物核查](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_recheck_20261010_113854_OTajtv/toy_checks.json)。完整 CPU/内存/磁盘/GPU/Python/网络/Codex 审计、上轮下载失败与修复、模型权重身份和匹配示例见 [P0 环境报告](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/docs/P0_ENVIRONMENT_REPORT.md)。

## 再次执行

```bash
bash /home/aaron/upinlbs_vpr/upinlbs_vpr_starter/scripts/run_p0_smoke.sh
```

本轮新增/更新了本计划、本验收报告与新的输出目录，没有改变研究代码或实验协议。没有执行真实数据训练、读取最终测试结果、修改系统驱动或 SSH/FlClash/Codex 配置。下一单一阶段是 P1 数据清单和对齐/真值语义核查，未执行。
