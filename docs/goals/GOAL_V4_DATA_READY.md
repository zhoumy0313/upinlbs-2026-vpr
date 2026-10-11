# VPR Goal V4 — 数据获取与下一轮研究启动指令

版本：2026-10-11；状态：**启动计划，尚未运行 V4 实验**。
适用仓库：`https://github.com/zhoumy0313/upinlbs-2026-vpr`。
既有 V3 基线：`research/vpr-v3-endpoint-refinement@09e7fb0fc63489817a09901fda37ae9896a9c404`。

## 0. 本轮唯一总目标

在保留 V1/V2/V3 的前提下，取得**从未参与前几轮模型选优**的真实有位姿标签的连续相机数据；基于开发数据设计并比较一个**时间采样/路径对齐约束下的候选终点精修**方法；冻结方案后在另一条独立序列上运行一次完整评测；如方法不超过强基线，报告失败、不事后改测试阈值，并保留旧论文。

**不接受**“成功下载两包文件 = 证明科研创新”“测试集换阈值后表现提高 = 改进”。

## 1. 数据清单和角色（优先级已固定）

| 角色 | 数据 | 官方源 | 体量 | 约束 |
|---|---|---|---|---|
| 开发/训练/验证 | TUM RGB-D `freiburg2_pioneer_slam` | https://cvg.cit.tum.de/rgbd/dataset/freiburg2/rgbd_dataset_freiburg2_pioneer_slam.tgz | 约1.5GB压缩包 | 室内 Pioneer 机器人，多个回环；有 RGB 时间戳和姿态真值；**可看模型效果并选参数** |
| 最终独立测试 | TUM RGB-D `freiburg3_long_office_household` | https://cvg.cit.tum.de/rgbd/dataset/freiburg3/rgbd_dataset_freiburg3_long_office_household.tgz | 约1.4–1.6GB压缩包 | 另一段完整办公室回环；**先定协议与参数，后首次检索评测** |
| 可选室外补充 | KITTI Odometry `00/05/06` | https://www.cvlibs.net/datasets/kitti/eval_odometry.php | 官方灰度套装约22GB + 4MB位姿 | **官方要求注册**，必须由用户在浏览器完成，不索取帐号密码；不阻塞 TUM 主线 |

官方 TUM `.tgz` 链接会重定向至 `webshare.cvg.cit.tum.de`；失败时可用浏览器打开官方数据下载页面 `https://cvg.cit.tum.de/data/datasets/rgbd-dataset/download`，单击对应 `.tgz`，再用 scp 从 Mac 传到 Ubuntu。**不要下载名字带 `_validation` 的 TUM 数据：官方说明这些没有公开真值。**

数据原始文件只保留 Ubuntu `data/raw/v4/`，不上传 GitHub。先用现有 FlClash/代理，不修改系统网络、显卡驱动或全局 Python。

## 2. 真实下载（在 Ubuntu 项目根目录执行）

```bash
mkdir -p data/raw/v4/tum_rgbd/archives data/raw/v4/tum_rgbd/extracted

# 如 SSH 终端尚未自动继承 FlClash，先确认 127.0.0.1:7890 是实际 HTTP/Mixed 端口：
# export HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890

curl -fL --retry 5 --retry-all-errors --connect-timeout 20 \
  --continue-at - \
  -o data/raw/v4/tum_rgbd/archives/rgbd_dataset_freiburg2_pioneer_slam.tgz \
  'https://cvg.cit.tum.de/rgbd/dataset/freiburg2/rgbd_dataset_freiburg2_pioneer_slam.tgz'

curl -fL --retry 5 --retry-all-errors --connect-timeout 20 \
  --continue-at - \
  -o data/raw/v4/tum_rgbd/archives/rgbd_dataset_freiburg3_long_office_household.tgz \
  'https://cvg.cit.tum.de/rgbd/dataset/freiburg3/rgbd_dataset_freiburg3_long_office_household.tgz'

for f in data/raw/v4/tum_rgbd/archives/*.tgz; do
  echo "Checking $f"
  tar -tzf "$f" >/dev/null || exit 1
  sha256sum "$f"
done

# 只在成功检查、确认归档内路径安全后解压。
tar -xzf data/raw/v4/tum_rgbd/archives/rgbd_dataset_freiburg2_pioneer_slam.tgz -C data/raw/v4/tum_rgbd/extracted
tar -xzf data/raw/v4/tum_rgbd/archives/rgbd_dataset_freiburg3_long_office_household.tgz -C data/raw/v4/tum_rgbd/extracted
```

正常情况下应找到各序列目录的 `rgb.txt`、`groundtruth.txt`、`rgb/`。只使用 RGB 图像；`depth/` 暂不参与研究。若失败，保存 curl status/最终 URL/大小/代理记录（删除可能的令牌），尝试官方网页浏览器下载再 scp；不要在公网搜不明镜像，也不要声称已下载成功。

## 3. Codex 需要的输入（不需要你上传模型或图像到 ChatGPT）

1. **Git 仓库**：使用现有本地仓库及 V3 HEAD；V4 独立新分支 `research/vpr-v4-temporal-alignment`。原 main / V1 / V2 / V3 冻结数据、日志、稿件全保留。
2. **一份本文件**：保存为 `docs/goals/GOAL_V4_DATA_READY.md`；这是任务与验收标准。
3. **原始 TUM 数据**：两包数据在 Ubuntu 的绝对路径；提供 `sha256sum`、文件数、RGB/真值时间跨度、有效图像/真值匹配数；不要提供任何秘密或登录信息。
4. **V1–V3 资产**：复用已有编码器与权重指纹，时序匹配、Top-K、精修、在线计时、回归测试，先验收再重用。不重复下载模型、不重装系统。
5. **实验角色定义**：`pioneer_slam` = 仅开发；`long_office_household` = 冻结后一次性测试；KITTI = 可选且仅用户先完成注册。
6. **作者人工动作**：如 KITTI 下载必须注册，由用户自行注册下载到 Ubuntu；所有其他步骤由 Codex 执行并记录。

## 4. V4 G0–G6 自动执行任务

### G0 数据获取和证据登记

- 先 `git status`、`git rev-parse HEAD`，建立独立分支；核验旧实验/论文原文件哈希不变；建立 `outputs_v4/`、`configs/v4/`、`docs/research_v4/`、`paper/revisions/v4_r01/`。
- 检查两包来源、大小、归档完整性、原始校验和、路径安全；保存 `SOURCE_AUDIT.md`、`DATA_MANIFEST.json`、精确命令及退出码。
- 如果官方源失败，完成可复现网络诊断和浏览器/scp 备选步骤；不可换成无真值数据并继续声称完成独立测试。

### G1 真值适配与数据协议（在看最终模型预测前）

- 读取 `rgb.txt` 与 `groundtruth.txt`，按**时间戳**匹配 RGB 与真值；单位为米的 3D 平移位置来自 TUM 的参考姿态。每张图片记录原时间戳、RGB 文件、匹配的真值时间及误差、XYZ、四元数、SHA、序列与split。
- 选择无未来数据的 **same-sequence revisit** 协议。首选固定图库前半段、后半段连续查询；也可测试开发集内因回环稀疏而需要的增长图库协议，但**不能在未看盲测模型效果之前悄悄为最终集改协议**。在开发集上通过真实真值/时间戳决定一个共同可执行的协议后，保存固定协议，之后在盲测集只能应用不能重新选优。
- 固定时间采样频率 **5Hz**；保留完整 RGB 原始序列，不永久删帧；匹配关联最大时间差暂定 0.03s，超差保留 `invalid_gt` 记录。固定图库在同一序列内不得与查询时间重叠；用于重复到访的查询，至少与参考帧相隔 **10s**。如不满足，开发阶段可用标签审计一次性制定并冻结统一规则，不允许看盲测算法 Recall 后改规则。
- 室内主距离阈值先声明 **0.5m**，同时报告 0.25m、1.0m 的敏感性；不沿用室外 10/25 米口径。计算每条序列的查询总数、存在正确参考的闭集数、无正确参考的开放集数和位置距离分布。共同子集统计 Recall@1/5/10；开放集必须报告查询覆盖和拒绝情况，不把它们静默删除。
- 注意位置真值是评价信息，**在线算法不可访问真值、位姿、绝对坐标、真实速度或真实步长**。算法可以使用 RGB、单调时间戳、已知图库索引、过去的图像描述子/分数。
- 如果开发数据闭集样本低于能做有意义实验的规模，停在 G1 并报告问题；不可为了可发表结果在盲测集中用标签挑选最容易的区域。

### G2 在开发序列上复现强基线

- CosPlace A-only、EigenPlaces B-only、RRF/双模型固定融合；原 V2/V3 的 L3/L5/L9 多速度时序与固定融合；简单局部候选重排（R1/R2）。
- 各方法使用同一 5Hz RGB、GT 关联、图库/查询协议、共同查询集；同一编码器预处理 224x224；记录命中率、TopK 正确候选覆盖、匹配位置误差分布及完整 R@K/纠错/误伤/耗时。
- 在开发集上测试预声明的 1Hz/3Hz/5Hz 采样扰动作为**分布变化实验**；在每个采样条件中统一重建图库和查询，比较固定帧速度是否失效。注意这些为人为子采样，不当作另一条独立数据采集。
- 分析正确候选存在却终点偏移的查询并画真实轨迹片段/候选距离分布（仅作诊断）；本轮绝不把 Oracle 当作可运行方法。

### G3 有界新方法探索（仅开发集）

- 研究一个清晰的 *timestamp-/sampling-aware causal temporal alignment with endpoint refinement*，而非再次乘更多自适应权重。
- 基准方案 1：固定 L3/L5/L9 且固定索引步进，严格实现与 V2 相同的历史因果方向。
- 基准方案 2：用已知 RGB 时间间隔对过去查询的时序采样进行归一化/插值，做时间感知轨迹搜索；参考侧仅用图库时间戳/索引，禁止用参考真值位移。
- 候选方案：在时间感知路径得分选出的多个候选轨迹端点附近，使用当前视觉相似度进行 **受约束的终点细化**；和不加约束、固定融合、简单局部精修作严格同候选池消融。
- 先小网格和独立同源实现对照，避免无限搜索；最多一个主要新机制与一次有理由的消融分支。不得用最终 TUM 序列做模型选型或超参数调节。
- 若严格的 0.25/0.5m 评价没有超过 **开发集最强成熟/简单时序** 基线，不得写“提出的方法有效”。可结束探索，交付经验分析并告诉作者仍需换题或提升方法，而不是继续自动造创新。
- 重点核查 SeqSLAM、STA-VPR、AdaptSeqVPR、SMR 中时间/速度调整与终点放宽的已有技术，不能将这些思想宣称首次提出。

### G4 冻结并只做一次独立测试

- 使用 `long_office_household`，在首次打开其 **检索结果指标** 前固定代码 SHA、模型/权重、5Hz 采样、关联阈值、地图/查询构造、正样本定义、时序长度、速度集合、终点精修参数、比较方法与随机种子。
- 公开真值元数据审计可先做；但不得先根据这段的基线/候选算法分数调整开发设置。
- 只执行一次完整盲评，所有强基线、拟议方法、敏感性及失败例必须同一 protocol、同一查询集合、同一照片顺序。
- 如果盲测样本少或方法不改善，保留负结果。若尚无可靠盲测下载/GT，不得把旧 St Lucia 称作新增独立验证。

### G5 实际在线推理、图表与论文

- 真实 RGB 解码 + 模型 batch=1 + CPU/GPU transfer + 全图库相似度 + 过去历史更新 + 轨迹搜索 + 精修 + 排序，CUDA 同步；预热与三遍统计；离线缓存模拟不能写成在线性能。
- 主表必须包含单帧、最强固定 L3/L5/L9、简单局部精修、时间感知基线、候选新方法；0.25/0.5/1m R@1/5/10、闭集分母、可拒绝样本、匹配距离中位/P90、均值/P95 耗时。
- V1/V2/V3 稿件与实验证据**字节不变**。新论文从 `paper/revisions/v4_r01/` 创建，只有真正得到强基线之上的可信结果，才写正向方法贡献；否则标作 empirical working draft。最多六页含引用与声明；AI 披露与论文数字逐值绑定。

### G6 完整交付归档

- 每阶段 append-only 独立 run_id，保留 `run_config.yaml`、Git commit、argv/CWD/环境（不含凭据）、stderr/stdout/真实退出码、原/最终失败文件、SHA、描述子行映射、逐查询 CSV、模型/数据指纹、表图源码、回放脚本、阶段验收与下一步建议。
- 推送**V4 独立分支**的源码、配置、报告、数字和小型证据 ZIP；原图、模型权重和大型数组只保留本机，源码中有可重建来源及 SHA。
- 若远程下载、命令、网络、构建失败，记录失败并最多采取一次有界备选；失败不可用无根据“成功”替代。
- 人类决定作者/通讯、最终投稿、版权签字、付费；Codex 不代替这些决定。

## 5. 预先规定的止损条件

1. **G0**：官方数据无法取得或真值无法校验 → 交付下载诊断、停止盲测，不转成未授权镜像。
2. **G1**：新数据不满足固定图像/真值/回访评价 → 完成数据报告，在开发集内调整一次协议并版本化；仍不可测试集刷分。
3. **G3**：候选方法达不到强基线 → 不得宣称新方法有效；可交付负结果研究报告与旧论文，不强行自动生成“正创新”。
4. **G4**：冻结后盲测失败 → 不再按新测试结果修改方法继续称为盲测；之后如研究新方法，必须重新确定另一个独立新测试。
5. **G5**：只因阈值改变、过滤困难查询或改小样本得到的提升，不可称为泛化改善；所有阴性/边界情况保留。

## 6. 给作者的阶段汇报格式

每阶段简短回答：做了什么；真实执行了哪些命令、退出码；新代码在哪；已有/新指标及样本量；当前结论（成功/失败/未做）；怎么复现；下一单一任务；需要作者人工完成什么。

**启动 Codex 的短指令：**
> 读取 `docs/goals/GOAL_V4_DATA_READY.md`，将 `VPR-GOAL-V4` 设为当前目标。从 V3 HEAD 创建独立 V4 分支，按 G0→G6 执行。先下载并审计两条 TUM 官方 RGB-D 序列、冻结无泄漏数据协议，再复现强基线并只开发一个有界新方法。全部旧成果、旧论文和历史失败必须保留；所有新阶段追加日志、归档、checkpoint。已打开的 St Lucia 仅用于解释/参考，不能充作独立验证。需要 KITTI 注册/作者批准时暂停那项，先做可自动完成的 TUM 主线。最终交付实验、新论文版本、证据及录用风险判断，不代替我提交论文。
