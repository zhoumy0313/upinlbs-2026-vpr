# 论文工作稿引用核对

核对日期2026-10-10。此表核对目前8项引用的来源和书目信息，不代表完整相关工作综述或人类作者已经审阅所有论断。论文编译使用 `paper/main.tex` 的内联书目，`paper/references.bib` 是可复用库存。

| 引用 | 原始来源与目前核对状态 |
|---|---|
| Visual Place Recognition: A Tutorial | [作者大学主页](https://www.tu-chemnitz.de/etit/proaut/en/team/stefanSchubert.html)确认5位作者、2024年IEEE RAM 31(3):139–153和DOI；[官方代码](https://github.com/stschubert/VPR_Tutorial)的数据/评测语义另有P1审计 |
| CosPlace | [CVF出版页](https://openaccess.thecvf.com/content/CVPR2022/html/Berton_Rethinking_Visual_Geo-Localization_for_Large-Scale_Applications_CVPR_2022_paper.html)及[官方代码](https://github.com/gmberton/CosPlace)的题目、3作者、CVPR2022、4878–4888；直接浏览出版页曾403，检索索引和本地官方引用可核对，保留访问限制 |
| EigenPlaces | [CVF出版页](https://openaccess.thecvf.com/content/ICCV2023/html/Berton_EigenPlaces_Training_Viewpoint_Robust_Models_for_Visual_Place_Recognition_ICCV_2023_paper.html)及[官方代码](https://github.com/gmberton/EigenPlaces)的题目、4作者、ICCV2023、11080–11090；代码与权重实际使用版本见模型指纹 |
| DINOv2 | [arXiv作者提交元数据](https://arxiv.org/abs/2304.07193)确认题目、26作者与2023初稿/2024 v2；修正库存中的作者顺序以及Mahmoud Assran、Michael Rabbat姓名。内联书目保留M. Oquab et al.与2023预印本，不声称核实了正式期刊元数据；OpenReview访问返回浏览器验证，未通过认证绕过 |
| Through the Lens of Doubt | [作者机构仓储](https://repository.essex.ac.uk/43511/)与[正式DOI](https://doi.org/10.1109/LRA.2026.3674688)支持5作者、RA-L2026 11(5):5899–5906。读过预印本相关方法，但官方实现与完整数值约定未核实，排除数字比较，不能伪造官方SU |
| To Match or Not to Match | [CVF出版页](https://openaccess.thecvf.com/content/CVPR2025W/IMW/html/Sferrazza_To_Match_or_Not_to_Match_Revisiting_Image_Matching_for_CVPRW_2025_paper.html)支持4作者、CVPRW2025、2874–2885；[官方代码](https://github.com/gmberton/To-Match-or-Not-to-Match)README页码2849–2860不同，采用出版方信息，未把局部匹配方法宣称为本项目同输入对照 |
| Sequence-Matching Receptiveness Prediction | [arXiv v2](https://arxiv.org/abs/2503.06840)确认3作者、IROS2025接受信息；保留可核查预印本引用，最终会议页码未核实。该文已有纠错/误伤类别，不能声称本研究首次提出这种标签 |
| Nordland-Part-2020 | [Zenodo原始记录](https://zenodo.org/records/4016653)确认Sourav Garg、2020、v1.0.0、DOI与1750×2张summer/winter；本项目下载哈希另见P1。此引用支持所用子集来源，不等于独立新路线评测 |

DINOv2修正仅影响参考文献库存，未改变实验模型、预处理、门控或冻结哈希。内联参考文献的简称与库存条目对应；编译仍不依赖外部bib文件。

投稿前需要人类复核：引用是否支持具体句子、是否遗漏最接近研究、最终出版元数据和会议引用风格。方案目前为实证比较/失效分析，不能以未检索到相同论文为新颖性证明。
