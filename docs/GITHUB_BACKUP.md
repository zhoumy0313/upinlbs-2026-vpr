# GitHub保存范围与跨机复现

目标仓库：`git@github.com:zhoumy0313/upinlbs-2026-vpr.git`。用户已明确授权保存项目到该仓库。原有本地Git历史保留，不强制推送、不重写冻结提交。

GitHub普通Git会拒绝超过100 MiB的文件，并对超过50 MiB的文件提示警告，见[官方大文件说明](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)。本项目选择把可下载/可生成的大资产排除，而不是把整个工作目录上传。

## 实际取舍

| 内容 | 保存方式 | 原因 |
|---|---|---|
| `src/`、`tests/`、`scripts/`、配置、文档、manifest | 普通Git | 复现方法、协议、版本和数据身份所需 |
| `paper/main.tex`、BibTeX、5页`main.pdf` | 普通Git | 作者可直接阅读和继续编辑 |
| `artifacts/results/`、`artifacts/figures/` | 普通Git | 小体积数值结果和项目生成的科学图，无原始照片 |
| 原始命令、失败、指纹、全部逐查询CSV、冻结参数/确认、阶段验收 | `artifacts/evidence/execution_evidence_20261010.zip` | 573个文本文件压缩后11,877,017字节；恢复后仍是原始路径、数值与记录 |
| 下载数据和解压照片（当前data约3.0 GiB） | 本地；从原作者下载 | 避免批量再分发和Git历史膨胀 |
| 模型权重（当前weights约267 MiB） | 官方URL+固定SHA-256 | 可以重下；不因某个权重刚好小于上限就进入Git |
| 描述子`npy/npz`、缓存、第三方源码、虚拟环境（约5.3 GiB） | 本地或重新生成/安装 | 与固定输入/源/模型身份绑定，无需版本化二进制运行环境 |
| 匹配照片条带、含照片的完整本地交付ZIP | 原Ubuntu本地保留 | 公开仓库保留ID/哈希/分数/排序及生成脚本，避免扩散数据集照片 |
| SSH密钥、认证、代理订阅、Codex配置 | 不入Git、不打包 | 不属于研究复现材料 |

证据ZIP SHA-256为 `aa00e62b92414f3d6ce2889cf6aea07c029c777d2aaec14819bc5b891cf7b1c3`。它是一次性实验快照；以后新增实验用新的版本/文件，不反复重写大压缩包。完整本地26 MB交付包仍在 `outputs/handoff_pdf_20261010_194500/`，本次没有上传它或创建GitHub Release。

原始提出protocol、历史失败和旧错误结果保留，并通过后续报告注明修复；不得为了“整理”而把历史记录改成全成功。公共归档只经过格式选择和凭据模式扫描，没有重写原始数据、指标或命令。环境日志包含历史机器路径和硬件信息；它们不是新机器配置。

## 下载来源与校验

模型URL、第三方固定commit、checkpoint SHA统一见 [configs/model_sources.json](../configs/model_sources.json)。

- CosPlace：`gmberton/CosPlace`，commit `52b56e95ea62245281281f3bafd7b9390d19a0fd`，R18/512。
- DINOv2：`facebookresearch/dinov2`，commit `7764ea0f912e53c92e82eb78a2a1631e92725fc8`，ViT-S/14无register的CLS/384。
- EigenPlaces：`gmberton/EigenPlaces`，commit `a2969f71d5ea31017443af490b15273ca4c50af1`，R50/512。
- 官方toy评测：`gmberton/VPR-methods-evaluation`，commit `9c8dfd496b49a49549323b94a6af204cbee91604`；递归子模块 `naver/deep-image-retrieval` commit `610247f721452393738690fc56d0f66f5823d581`。
- Nordland-Part-2020：[Zenodo 4016653](https://zenodo.org/records/4016653)，MD5 `3127c5965bd4d1f3a1ef8ee49285fbb9`；下载/校验脚本 `scripts/download_nordland_ranges.py`。
- Gardens Point：[原作者下载](https://www.tu-chemnitz.de/etit/proaut/datasets/GardensPoint_Walking.zip)。本地哈希在P1数据审计中；不是发布者公布的官方完整哈希。

重新获取第三方源码放在 `third_party/`，checkout上述精确commit，不修改其已被指纹记录的源码。权重保存到model_sources声明的 `weights/p0_torch/hub/checkpoints/`，按该JSON校验SHA后使用。不要复制原始照片到Git中。

## 环境与命令

原Ubuntu已有 `.venv-p0`，无需重新安装环境。跨机需先检查GPU/驱动，创建独立环境；有可用GPU才按原研究Torch 2.6.0/torchvision 0.21.0 cu124配对安装，否则选择CPU。安装范围为虚拟环境，保持系统Python/驱动不变。

`requirements-evaluated-cu124.txt`是在本次备份时从研究venv采集的完整pip快照；原始各run的安装命令和依赖记录在证据包中，后者是当时环境的权威证据。该快照含CUDA wheel和NVIDIA运行库，CPU环境不能直接当作同一安装清单。CPU/不同机器的新结果须单独记录环境身份，不宣称与原CUDA数值逐位一致。

证据恢复：

```bash
python3 scripts/repository_evidence.py verify
python3 scripts/repository_evidence.py restore
```

恢复不覆盖内容不同的既有证据，执行前检查路径/符号链接/每项SHA。现有原Ubuntu文件一致时恢复是幂等的。它不恢复官方数据、权重、描述子数组或匹配照片；完整图像实验仍需官方资产，详见各阶段报告和README。

全部恢复后，冻结包位于 `outputs/freeze_review_20261010_143800/selection.json`。已确认门限和参数只读保存；最终评测入口是 `scripts/run_p4_frozen_evaluation.sh`，没有为公开仓库重新拟合或运行最终测试。

## SSH与公开前检查

原Git历史已扫描常见私钥、GitHub/OpenAI/AWS token及URL凭据模式，未发现匹配；证据归档内573个UTF-8文件也通过同类检查。模式扫描不是所有秘密的形式化证明，任何新增认证文件都应保持忽略。

首次GitHub连接使用[GitHub官方Ed25519主机公钥/指纹](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints)。原Ubuntu只在本仓库 `.git/github_verified_known_hosts` 保存公共主机公钥，并用仓库局部 `core.sshCommand` 引用它。原私钥权限由0664收紧为0600以满足OpenSSH，密钥内容未读取或修改，SSH/FlClash/Codex配置未修改。这些 `.git` 局部设置不会随仓库克隆传播；新机器按其正常GitHub SSH认证使用。
