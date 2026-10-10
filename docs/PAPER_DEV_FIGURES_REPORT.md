# 开发集论文图表与来源审计

2026-10-10。此阶段只读取冻结审查包中的开发指标与既有验证计时记录，未访问最终测试图像、训练选择器或调整门限。最终测试仍未执行。新增 `scripts/plot_development_study.py`；修正 `paper/references.bib` 中 DINOv2 的作者姓名和顺序；补充引用审计与证据映射。现有冻结算法文件未改变，审查包 SHA-256 仍为 `5da3ca5eb3e80d2facf7e56017694bb437bda22c3fd6b8380f5e1c12a2602769`。

## 实际产物与检查

运行目录：`outputs/paper_dev_figures_20261010_150500/`。目录名称不是实际开始时间；以 `commands.jsonl` 中带时区的时间为准。

| 文件（均在该 run 的 figures/） | 内容与限制 |
|---|---|
| development_accuracy_invocation.pdf / .png | 两组模型的验证精度—真实调用率；随机对照报告全部五种子的均值和总体标准差，非置信区间 |
| development_complementarity.pdf / .png | A/B四类正确性：原始DINO纠错29、误伤88；Eigen纠错51、误伤15；各300张验证查询 |
| development_accuracy_latency.pdf / .png | 真实25%预算在线计时及A/B单模型；没有补造10%/50%的未测延迟；保留全部随机种子 |
| plot_points.csv | 全部100个可部署开发策略记录；未计时项的 mean_ms 留空 |
| figure_provenance.json | 审查包、输入JSON/逐查询CSV、脚本及输出文件SHA-256、绘图依赖版本 |

实际新建独立 `.venv-paper`，由实验环境的pip管理目标环境，未在 `.venv-p0` 中安装绘图库。Matplotlib 3.10.7、NumPy 2.2.6、Pillow 12.3.0及完整版本清单见 `plot_environment.txt`。

`generate_development_figures.log`：逐行核对两个模型对的 30,600 条真实在线计时记录，重算每策略均值、中位数、P95，核对900查询及实际A/B调用数，退出0。图中100个策略的Recall单调性和净增量恒等式通过检查。三张PNG均已实际目视检查。

`verify_figure_pdf_and_identity.log`：复核全部输出SHA-256、冻结包身份以及确认文件仍缺失；`pdfinfo` 确认三个PDF各1页，`pdffonts` 确认字体为嵌入的TrueType子集，退出0。`figure_acceptance.json` 状态 passed。图表PDF的页数不等于论文页数。

## 实际命令与退出码

精确argv、环境覆盖、耗时、日志和退出码均保存在 `commands.jsonl`。本阶段实际完成5条记录命令，均退出0：新建绘图环境、安装绘图依赖、生成图表、核查PDF/指纹、检查绘图环境依赖。

可复现命令（使用新的输出目录，禁止覆盖本run）：

```bash
.venv-paper/bin/python scripts/plot_development_study.py \
  --package outputs/freeze_review_20261010_143800/selection.json \
  --output outputs/paper_dev_figures_reproduction
```

原脚本会先验证冻结包文件哈希，并创建不存在的输出目录。精确环境安装命令已记录，而非宣称无需依赖即可运行。

开发结果：A验证R@1为71.33%；EigenPlaces为83.33%；25%预算净收益门控75.67%，错误预测器77.33%。对应同一次Eigen在线测试均值分别8.92、14.44、13.02、13.38ms。GPU时钟未锁定，不能从0.36ms差值声称稳定速度优势。更高准确率的单模型也必须进入最终比较。

## 图像输入到图表的8行解释

1. 输入照片先按固定规则转为224×224的RGB张量。
2. 冻结A模型输出512维归一化描述子，描述子不是地点坐标。
3. A描述子与夏季图库描述子逐一计算余弦相似度，再排序。
4. 在线选择器只看到A排名前列的五个分数统计，不看到真值或B结果。
5. 门限决定是否调用第二模型；调用时B独立检索并替换完整排名。
6. 评测器事后把检索图像ID与固定容差下的真值比较，统计正确、纠错和误伤。
7. 计时记录来自实际图像推理，缓存排名只用于核对结果，不能代替模型时延。
8. 绘图脚本读取这些已有记录并复算指标，输出PNG、PDF和每个点的CSV。

## 未完成与下一步

没有执行P4最终评测，也没有用开发结果填入论文的最终实验。原生LaTeX编译曾返回success；当前暴露工具支持编辑、编译和PDF预览，未提供独立PDF导出调用，因而论文PDF交付及最终≤6页仍未核实。没有安装TeX或LaTeX插件。

单一下一步：收到审查包的实际人工确认后，按既定入口运行完整冻结最终实验；原始DINO负结果与Eigen对照都保留，不再更换模型。作者顺序、通讯作者、匿名/截止时区等待定问题保留在论文审计中。
