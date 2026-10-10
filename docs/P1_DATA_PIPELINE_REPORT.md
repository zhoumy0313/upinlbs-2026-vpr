# P1 数据与管线验收报告

日期：2026-10-10。P1 已通过；总论文 goal 仍为 active。后续依次为开发集 baseline、候选改进与公平对照、冻结、最终实验、6页以内稿件。P0 环境沿用，没有修改 SSH、FlClash、Codex、系统 Python 或驱动；本阶段编码器冻结，没有开展研究训练或最终跨季节/跨昼夜评测。

## 实际结果

| 检查 | 实际结果 | 范围 |
|---|---|---|
| 单元测试 | 20 passed，退出0 | 原12项合成测试＋8项数据/隔离测试 |
| Nordland 归档 | 985,423,099字节，官方 MD5 匹配 | 作者发布的 Part-2020，不是完整 Nordland |
| Nordland 解码与对应 | summer/winter 各1750；原始数字ID均为251–2000且一致 | 所有3500张完整解码、逐文件SHA-256 |
| Nordland 划分 | gallery1750；train600、validation300、buffer200、test650 | frame_index 从1开始；原文件251对应第1帧 |
| Gardens Point | day_left/day_right/night_right 各200；原始ID0–199一致 | 全部600张解码与逐文件SHA-256 |
| GP 划分 | inspection_only200、gallery200、external_test200 | day_left 不进入图库 |
| GP 同图自检索 | 200/200 top1 为自身；200×512描述子 | 全部 day_right；不是跨昼夜成绩 |
| Nordland 同图自检索 | 64/64 top1 为自身；64×512描述子 | 均匀抽取 summer64张；没有声称全图库1750张自检 |
| 独立复现 | 完整脚本退出0，内部11条命令均退出0 | 新建 append-only run；pip check通过 |
| 重复一致性 | 两次 manifest 完全一致，描述子与排序对应通过核对 | 最大描述子差见 phase_acceptance.json |

自检使用 CosPlace ResNet18/512、CUDA、RGB、224×224、官方评测操作顺序 ToTensor→ImageNet Normalize→Resize、L2归一化。模型 eval、参数 requires_grad=False、inference_mode 均已设置，实际加载的参数 SHA-256、预处理与图像ID保存在 fingerprint.json。自检的 wall_seconds 包含图像加载与检查，**不作为在线时延指标**；P2重新建立可用于实验的完整缓存指纹，不能把此处小样本自检当作 baseline。

## 产物与版本

主 run：`outputs/p1_20261010_132030`；完整复现：`outputs/p1_recheck_20261010_133612_JLRNvs`。主 run 中有：

- `commands.jsonl` / `COMMANDS.md`：实际 argv、命令、环境覆盖、时间、退出码与日志。
- `nordland_manifest_v2.json`、`gardens_point_manifest_v2.json`：明确图像ID、原始文件数字ID、顺序frame_index、划分、尺寸、SHA-256；同内容副本位于 `data/manifests/`。
- `*_data_audit_v2.json`：数量、归档身份、重复组与协议SHA-256；`label_metrics_computed=false`。
- `*_self_retrieval/`：图库描述子、图像ID、逐图匹配、模型指纹和自检指标。
- `nordland_alignment.jpg`、`gardens_alignment.jpg`：原始对应示例，仅数据检查，没有模型预测或最终成绩。
- `source_snapshot.json`：项目代码/配置及固定作者评测代码的 SHA-256；`phase_acceptance.json`：可检查验收。
- `conference_requirements.json` 和官网资源快照：投稿核查证据。

研究代码初始 Git 提交为 `5467a04feda3815d29ca093238818b3c1ca72f53`。只是本地版本控制，没有配置远端或上传图像/权重；数据归档、原图、权重、缓存和 outputs 均被忽略。此次快照由 Codex 身份提交，不修改用户全局 Git 身份或认证。

## 保留的异常和修正

Nordland 单连接下载速度慢，本任务终止了自己的下载进程，实际退出 **-15**；日志、部分文件保留。改用6个明确范围请求后，拼接完成且官方 MD5 匹配，退出0。不是隐藏失败或换数据源。

GP 第一版 manifest 将 day_left 也标为 gallery。自检前发现并修正为 inspection_only，以 **v2 新文件**保存，第一版保留作审计；后续只能使用 v2。测试覆盖该规则，200张图库自检也检查实际 traverse=day_right。

GP night_right 的 Image179.jpg 与 Image183.jpg 字节相同。Nordland winter 有96组重复，涉及230张、134份额外副本；17组仅在buffer，79组仅在test，没有跨train/validation重复组。全部保留原图、数量和标签。重复图像会限制定位可区分性，应在论文数据局限中披露；不能因此删除困难帧、移动区段或改容差。

GP 下载地址没有找到发布者完整校验值；本地 SHA-256/MD5 只固定获取文件身份。作者来源的对应关系加上文件ID对齐和代表图检查支持评测约定，不能据此声称每个拍摄位置严格一致或拥有米制坐标。

## 单条复现命令

在项目根目录执行：

```bash
bash scripts/run_p1_data_audit.sh
```

脚本创建全新 outputs 目录，清除本进程继承的 ROS PYTHONPATH，沿用 `.venv-p0` 和 `weights/p0_torch`，验证/按需下载数据，重新生成清单、图库自检和配对示例，记录每条命令及退出码。首次使用要求本阶段已完成的两个作者源码 clone；不安装全局包、不修改代理配置。每次新 manifest 都保留，需纳入后续版本快照；同一数据内容的 manifest 应一致。

## 从图像输入到检索输出：给初学者的8步解释

1. 输入是一张实际图片；清单给它唯一 image_id，并用 SHA-256固定文件内容。
2. 文件名数字ID用于检查序列对应；frame_index 用于离线划分与标签，不能进入在线模型或门控。
3. 编码器只收到 image_id、图片路径和哈希；默认禁止选择最终/外部测试 split。
4. 图片转换为RGB，按已固定操作做归一化和224×224缩放，得到模型需要的张量。
5. 冻结 CosPlace 把图像变成512个数；它们是视觉描述子，不是预测经纬度或类别名称。
6. L2归一化后，描述子点积等于余弦相似度；一张查询与每张图库图像各产生一个分数。
7. 分数从高到低排序，并列按固定图库顺序；描述子行与保存的 image_id 始终对应。
8. 此阶段把同一图库图片同时作为输入和检索对象，检查第1名是否为自身；真实定位还需要下一阶段不同季节查询、独立真值和R@K评测。

## 未完成与下一阶段

没有训练研究选择器，没有生成冬季/夜间最终查询的模型描述子或最终检索成绩，没有确认创新有效性，没有完成论文/PDF。下一单一有界任务为 **P2：只在 Nordland train/validation 上验证统一冻结 A/B baseline 并分析互补性**；先适配并核查 DINOv2 CLS/384与预处理/权重来源，再提取完整summer图库和winter开发段，记录正确/纠错/误伤/双错与代表错例。最终段650和GP跨域成绩须在具体方法和协议冻结后再运行。

完整总体计划见 `docs/RESEARCH_EXECUTION_PLAN.md`，来源语义与投稿核查见 `docs/P1_SOURCE_AUDIT.md`。投稿按英文、全稿含参考文献≤6页准备；第一作者已记录，其他作者和通讯信息待定，匿名与截止时区仍需核实。
