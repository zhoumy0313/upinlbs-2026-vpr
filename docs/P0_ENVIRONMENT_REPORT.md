# P0 环境与官方 CosPlace toy 验收报告

执行日期：2026-10-10，Asia/Shanghai。项目实际根目录：`/home/aaron/upinlbs_vpr/upinlbs_vpr_starter`。

**验收完成：本包 12 个合成单元测试全部通过；官方 CosPlace ResNet18/512 无标签 toy 在 GPU 上运行成功，生成 5 组匹配图。** 没有训练视觉编码器或真实数据选择器，没有下载/评测 Nordland、Gardens Point，也没有读取最终测试结果。没有修改驱动、系统 Python、SSH、FlClash 或 Codex 配置。

本次输出目录：[p0_20261010_111919](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919)。完整[实际命令](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919/COMMANDS.md)包含每步工作目录、进程环境覆盖、开始时间、耗时、退出码和日志链接；机器可读记录见 [commands.jsonl](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919/commands.jsonl)。失败产物保留在同一目录。

## 环境实测

| 项目 | 实测结果 |
|---|---|
| 系统 | Ubuntu 22.04.5 LTS；内核 6.8.0-138-generic；x86_64 |
| CPU | Intel Core i7-12700H；14 核、20 逻辑 CPU |
| 内存 | 总计约 15 GiB，初始可用约 12 GiB；无 swap |
| 磁盘 | 项目所在分区总计 393 GiB，初始可用 350 GiB |
| GPU | NVIDIA GeForce RTX 3060 Laptop GPU；nvidia-smi 总显存 6144 MiB；计算能力 8.6 |
| 驱动 | 550.107.02；nvidia-smi 正常；未安装/修改驱动或系统 CUDA Toolkit |
| Python | 保留 `/usr/bin/python3` 3.10.12；虚拟环境 `.venv-p0` 使用同一解释器 |
| PyTorch | 2.6.0+cu124；torchvision 0.21.0+cu124；运行时 CUDA 12.4 |
| GPU 可用性 | `torch.cuda.is_available()` 为真；CUDA 矩阵乘法与 CPU 对照通过；torchvision CUDA NMS 通过 |
| SSH | 服务 active；OpenSSH 8.9p1；本次没有重新配置或测试到某台远端机器的连接 |
| FlClash | FlClash 与 FlClashCore 进程均在运行；已有代理 TCP 可达 |
| 网络 | GitHub、PyTorch 下载站、PyPI 的 DNS 正常；仓库克隆和包/权重下载最终成功，下载链路发生过截断 |
| Codex | CLI 0.162.0；`codex login status` 返回 `Logged in using ChatGPT`；未重新登录或读取认证文件 |
| 空间开销 | 独立环境约 5.3 GiB；项目权重缓存约 89 MiB；第三方目录约 5 MiB；本次输出约 103 MiB |

证据：[初始审计](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919/environment_before.log)、[toy 完成后审计](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919/environment_after_toy.log)、[真实 GPU 验证](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919/gpu_probe.log)。Codex 状态是本地 CLI 登录检查，未另行做账户额度或专用 API 调用测试。

使用 [PyTorch 官方版本表](https://pytorch.org/get-started/previous-versions/)中的 2.6.0 / 0.21.0 cu124 配对，并参考 [NVIDIA 兼容说明](https://docs.nvidia.com/deploy/cuda-compatibility/minor-version-compatibility.html)，随后以实际 CUDA 运算验收。`nvidia-smi` 显示的 CUDA 支持版本不表示系统已安装 CUDA Toolkit；本次所需运行库仅安装在虚拟环境中。

## 隔离与保留

已读取 PLAN.md、AGENTS.md、configs/protocol.yaml 以及附件手册。手册中后续数据实验、训练、论文及投稿事项没有被自动执行。本次严格停留在 P0/E0。

系统缺少 pip/ensurepip，第一次 `python3 -m venv .venv-p0` 退出 1。随后用 `venv --without-pip` 创建环境，从 PyPA 官方地址下载 get-pip.py，仅用 `.venv-p0/bin/python` 安装 pip。没有运行 sudo/apt，也没有安装全局 Python 包。[系统 Python 复核](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919/system_python_preservation.log)确认全局 pip 仍不存在。

首次 pip 引导继承了已有 ROS PYTHONPATH，出现 launch-ros 的依赖提示。后续安装、测试及推理均只在当前进程清空 PYTHONPATH，并设置 PYTHONNOUSERSITE=1；没有修改 shell 配置或 ROS。虚拟环境 `include-system-site-packages=false`，GPU 验证也确认没有 `/opt/ros` 导入路径。[pip check](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919/dependency_check.log)退出 0。

保留现有代理变量，日志仅记录变量是否存在及连接是否成功，不打印代理值、订阅链接、密钥或认证文件。TORCH_HOME 仅为当前进程指向项目的 `weights/p0_torch`。

原有计划、规则、协议、源码和测试的 SHA-256 前后一致，见 [source_hashes.json](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919/source_hashes.json)与[校验日志](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919/source_preservation_check.log)。Starter 本身没有 Git 仓库，因此没有可提交的项目 commit，使用源文件哈希记录版本；没有擅自初始化 Git。

官方评测仓库 commit：`9c8dfd496b49a49549323b94a6af204cbee91604`。递归子模块 commit：`610247f721452393738690fc56d0f66f5823d581`。第三方源码未改动，[git status](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919/official_source_unchanged.log)为空。

## 实际执行与失败记录

| 步骤 | 退出码与结果 |
|---|---|
| 标准 venv 创建 | 1：ensurepip 缺失；失败日志保留 |
| 无 pip 环境创建、环境内 pip 引导 | 均为 0 |
| 递归克隆官方仓库 | 0 |
| 安装 GPU PyTorch、核心及官方依赖 | 均为 0；PyTorch 下载中断后续传 |
| GPU 数值/算子验证 | 0 |
| 本包 pytest | 0：12 passed in 0.47s；JUnit XML 已保存 |
| 官方 `main.py --help` | 0：核实 device、save_descriptors 等参数 |
| 第一次官方 toy | 1：ResNet18 初始化权重下载截断，官方哈希检查拒绝加载 |
| ResNet18 curl 第一次重下 | 56：SSL unexpected EOF；失败日志保留 |
| ResNet18 断点续传、哈希校验 | 均为 0：SHA-256 与官方文件名中的哈希前缀一致 |
| 第二次官方 toy | 1：CosPlace 权重下载截断，ZIP 中央目录缺失；损坏文件保留 |
| CosPlace 断点续传、结构检查 | 均为 0：weights_only 加载成功，123 个状态项均为有限张量，聚合层权重形状为 512×512 |
| 第三次官方 toy | 0：17 图库 + 5 查询编码并保存匹配；整个进程耗时 4.659 s |
| toy 产物检查 | 0：22 张图像解码、归一化、排序一致性与保存候选核对均通过 |
| pip 依赖检查、源文件检查 | 均为 0 |

4.659 s 包含解释器/模型启动、全部图像编码、检索与保存，不是按研究协议预热后测得的单查询时延；本次未开展正式延迟实验。单元测试中的逻辑回归仅拟合随机合成数据，用于验证原有接口，不是研究训练。

关键日志：[单元测试](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919/unit_tests.log)、[JUnit](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919/unit_tests.xml)、[成功推理](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919/official_toy_success.log)、[第一次失败](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919/official_toy.log)、[第二次失败](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919/official_toy_retry.log)、[产物验证](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919/inspect_toy.log)。没有绕过校验或换用随机权重。

实际 CosPlace 权重 SHA-256：`db09310a175e325fe25e7a460b41886ab9357b19c41d370a9ed3ed81bc9abf9f`。上游 hubconf 未提供该文件的完整 SHA-256；这里记录的是从官方 release 下载并成功加载的本地文件身份。ResNet18 初始化权重完整 SHA-256：`f37072fd47e89c5e827621c5baffa7500819f7896bbacec160b1a16c560e07ec`。

## 匹配示例与模型产物

按[官方 README 示例](https://github.com/gmberton/VPR-methods-evaluation)运行，使用 ResNet18/512、RGB、200×200、batch=1、num_workers=0、FP32、CUDA、`--no_labels --save_descriptors`。官方数据加载顺序是 ToTensor → ImageNet Normalize → tensor Resize（bilinear，antialias=true）。这是官方 toy 设置；研究协议里的 RGB/224×224 没有改动。

| 查询 | 第 1 名：余弦 | 第 2 名：余弦 | 第 3 名：余弦 |
|---|---|---|---|
| q1.jpg | db2.jpg：0.419730 | db3.jpg：0.225187 | db7.jpg：0.221552 |
| q2.jpg | db3.jpg：0.425225 | db4.jpg：0.410861 | db7.jpg：0.395474 |
| q3.jpg | db11.jpg：0.501531 | db10.jpg：0.420908 | db9.jpg：0.398797 |
| q4.jpg | db16.jpg：0.704769 | db17.jpg：0.584456 | db15.jpg：0.583294 |
| q5.jpg | db13.jpg：0.605413 | db12.jpg：0.474988 | db14.jpg：0.372818 |

完整 85 条候选分数：[matches.csv](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919/matches.csv)。行号与文件名对应见 [toy_manifest.json](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919/toy_manifest.json)；它保留官方文件名的字典序，不依靠文件名尾号猜描述子行号。

下图从左到右为 q1.jpg、排名第 1/2/3 的候选。官方图中的 Pred0 表示第 1 名。可以观察到第一个候选也有相似的柱廊，但这里没有读取真值，不能据此填写正确率。

![官方 toy：q1 与前三名候选](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919/official_toy_success/2026-10-10_11-33-16/preds/000.jpg)

其余匹配图：[q2](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919/official_toy_success/2026-10-10_11-33-16/preds/001.jpg)、[q3](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919/official_toy_success/2026-10-10_11-33-16/preds/002.jpg)、[q4](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919/official_toy_success/2026-10-10_11-33-16/preds/003.jpg)、[q5](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919/official_toy_success/2026-10-10_11-33-16/preds/004.jpg)。图像与模型文件仅保存在本地。

描述子：[图库数组](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919/official_toy_success/2026-10-10_11-33-16/database_descriptors.npy)、[查询数组](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919/official_toy_success/2026-10-10_11-33-16/queries_descriptors.npy)。形状分别为 `[17,512]`、`[5,512]`；每行范数在 0.99999994–1.0 之间。相似度矩阵形状为 `[5,17]`。完整验证结果见 [toy_checks.json](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919/toy_checks.json)。

## 图像输入—模型输出—检索排序：8 步说明

1. 图库是以前拍摄的参考照片，查询是现在要找地点的照片；本次分别有 17 张、5 张。
2. 图片解码成 RGB，再变成浮点张量；本次一张图片送入模型时形状为 `[1,3,200,200]`。
3. 每个 RGB 通道用 ImageNet 的均值和标准差规范化；官方代码随后对张量缩放。
4. ResNet18 从颜色、纹理和建筑结构提取特征，经 L2、GeM 聚合、线性层和 L2 输出 `[1,512]` 描述子。
5. 512 个数是学习出的视觉表征，不是 512 个地点类别或地理坐标；本次只加载已有权重推理。
6. 将查询描述子与图库描述子做点积：`S = F_query @ F_database.T`；得到 5×17 个余弦相似度。
7. 每行从高到低排序就得到该查询的候选；单位向量满足 `平方欧氏距离 = 2 - 2×余弦相似度`，因此官方 FAISS 距离从小到大排序与余弦排序一致，本次已逐项验证。
8. 例如 q1 的前三名是 db2、db3、db7；0.419730 是相似度，不是 41.973% 正确率。输出是地点候选，不是位姿。无标签 toy 不计算 Recall，不构成论文性能结果。

## 文件与可复现命令

新增项目文件：`.gitignore`；`scripts/record_command.py`（保存日志和退出码）；`scripts/audit_environment.py`（只读审计）；`scripts/check_torch_gpu.py`（GPU 验证）；`scripts/inspect_toy_outputs.py`（固定读取官方无标签 toy）；`scripts/run_p0_smoke.sh`（重复验收）；本报告。新增目录：`.venv-p0`、`third_party/VPR-methods-evaluation`、`weights/p0_torch` 与本次输出目录。原有源码、测试和 protocol 未改动。

依赖精确版本见 [requirements-p0.lock.txt](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919/requirements-p0.lock.txt)。本次运行配置见 [config.json](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919/config.json)；图像清单、预处理、池化、描述子、权重及实际 Torch Hub 源码哈希见 [toy_fingerprint.json](/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/outputs/p0_20261010_111919/toy_fingerprint.json)。

在当前已准备好的环境中，一条命令重复验收（新建输出目录，不覆盖本次产物）：

```bash
bash /home/aaron/upinlbs_vpr/upinlbs_vpr_starter/scripts/run_p0_smoke.sh
```

脚本复用本次虚拟环境和权重，GPU 不可用时选择 CPU；没有安装/更新驱动的操作。脚本通过 bash 语法检查，其调用的各个验收组件已在本次运行通过；本次没有为验证脚本再重复整轮推理。

本次问题是系统缺少 pip 引导组件、继承的 ROS 导入路径及下载截断，均已在项目内处理并保留证据。下一项建议的单一有界任务：按 P1 建立数据 manifest、核对图像对齐与官方真值语义，并做自检索；仍不查看外部/最终测试指标。此项尚未执行。
