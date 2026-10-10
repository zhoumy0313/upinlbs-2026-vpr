# P1 数据与投稿来源核查

核查日期：2026-10-10。只阅读数据说明、加载与评测实现；没有查看作者发布的模型测试成绩，也没有计算本项目最终成绩。原始 PLAN.md、AGENTS.md 和 protocol.yaml 保留。

## Nordland-Part-2020

[作者发布页](https://zenodo.org/records/4016653) 明确该子集有 summer/winter 两个目录，各1750张图像，并指向 DeltaDescriptors 作者代码；官方 ZIP 的 MD5 为 `3127c5965bd4d1f3a1ef8ee49285fbb9`。

固定作者仓库版本 `oravus/DeltaDescriptors@5511bdba9afc5eaa107943d176fbe3fb7959f774`。README.md 第25–36行指定该归档，第69行说明支持 Nordland 的逐帧一对一对应。`src/outFuncs.py` 第55–68行以两个序列的排序索引作为对应位置，计算匹配帧索引绝对差；第47–51行使用包含边界的 `dists <= radius`。这些索引不是米制 GPS/UTM 坐标。

本项目根据解析文件名得到的数字 ID 排序，先验证两序列 ID 完全相同，才生成从1开始的顺序 frame_index。主指标正样本为顺序索引差≤5；1和10为预先约定敏感性。训练/验证/缓冲/留出使用 protocol 中固定区段，同一参考图库用于全部区段，因此只能主张同一路线地图上的区段留出。

## Gardens Point

[教程作者代码](https://github.com/stschubert/VPR_Tutorial/blob/e4c7cffec5322d0aab1b08ad1bf2d479b52d577f/datasets/load_dataset.py) 固定版本 `e4c7cffec5322d0aab1b08ad1bf2d479b52d577f`。加载器第43–62行将 day_right 用作图库、night_right 用作查询，按文件名排序，以单位矩阵作为 GThard；GTsoft 是单位矩阵沿图库轴的17格卷积。

同版本 `evaluation/metrics.py` 第57–60行在 PR 评估时把 `GTsoft & ~GThard` 的分数降至最小值，使这些位置被忽略；单最佳匹配分支不支持 GTsoft。第145行起的 recallAtK 则要求调用者直接提供希望使用的 GT，且采用 database×query 矩阵，并丢弃没有正样本的查询。

本项目不会把 GTsoft 冒充主指标正样本：主指标严格对应，±8仅作为另行标记的自定义正样本敏感性；使用 query×database 矩阵和固定图库顺序稳定打破并列；无正样本应报错，不删查询。day_left 为 inspection_only，不能进入 day_right 图库。

归档来自教程指定的 [TU Chemnitz 下载地址](https://www.tu-chemnitz.de/etit/proaut/datasets/GardensPoint_Walking.zip)。没有找到该地址提供的发布者校验值；本地 SHA-256/MD5 只固定所获取的文件身份，不能声称验证了官方完整哈希。夜间 Image179.jpg 与 Image183.jpg 字节相同，保持原有数量与对应标签，记录重复，不删除或调整容差。

代表性原始配对图用于检查序列对应和视角差异，不是模型预测、最终成绩或新选择器输入。标签与 frame_index 不进入在线门控。

## 投稿与作者

[会议官网](https://upinlbs2026.com/) 的 HTML 为 Vue 外壳。官方前端资源 `assets/index-DYUnbZvC.js` 中 `/submission` 的静态作者说明确认英文 PDF、最多6页、IEEE conference format；资源快照、SHA-256 与已确认/未确认字段见本阶段 `conference_requirements.json`。

模板指向 [IEEE template selector](https://template-selector.ieee.org/secure/templateSelector/articleType?publicationTypeId=3&titleId=1)，投稿入口为 [UPINLBS2026 CMT](https://cmt3.research.microsoft.com/UPINLBS2026)。10月15日为初稿/摘要截止，10月26日通知，11月15日最终稿。尚未核实参考文献是否计页、匿名、截止时刻/时区与纸张规格；按全稿含引用≤6页、10月14日完成进行安排。

第一作者 Mingyang Zhou（周明杨），其他作者待定。[学校官网](https://english.ucas.edu.cn/) 标准英文名为 University of Chinese Academy of Sciences。通讯作者/邮箱待定，不自动投稿或决定作者。

## 下一阶段的文献边界

当前只读了以下候选近邻工作的摘要，尚未核对完整公式与代码：[Through the Lens of Doubt](https://arxiv.org/abs/2510.13464)、[Sequence-Matching Receptiveness Prediction](https://arxiv.org/abs/2503.06840)、[To Match or Not to Match](https://arxiv.org/abs/2504.06116)。在核查完整来源前不实现并命名“官方 SU”，不声称本项目的净收益监督目标具有已证实的新颖性。

第三方代码仅做来源审计，保留原许可证；未复制教程 GPL 实现到本项目，也未运行其发布成绩或安装旧依赖。各 Git 提交、代码文件 SHA-256 与日志在阶段产物中保存。
