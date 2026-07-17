# Multimodal Emotion Fusion: Lexicon-Based Coordinate Validation

> **研究者**: Xixie Jiang (姜晰頡) — 芝浦工業大学 Doly Lab  
> **状态**: Phase 2 — 跨词典验证完成，正在设计人类实验  
> **最新更新**: 2026-07-09

---

## 项目概述

**核心问题**: 情绪词典（NRC VAD、ANEW）中的 VA(D) 坐标能否用于多模态情绪融合的计算建模？

**发现**: 两本独立词典的坐标都不能预测人类对"face × voice 情绪融合"的感知共识。但这不是噪声——两本词典之间高度一致（r=0.65, p=0.02），排列检验证实词典中存在真实但微弱的融合结构（p<0.001）。问题在于**词典测量的"孤立词汇语义"和融合感知测量的"多模态动态整合"是两个根本不同的空间**。

---

## 目录结构

```
multimodal-emotion-fusion/
├── README.md                    # 本文件
├── ROADMAP.md                   # 目标和计划
├── .gitignore
├── core/                        # 核心分析脚本
│   ├── train_dual_channel_extended.py  # 双通道融合模型（基础依赖）
│   ├── analyze_nrc_vs_consensus_3d.py  # 2D vs 3D NRC 分析
│   ├── cross_lexicon_validation.py     # NRC vs ANEW 跨词典验证
│   ├── nrc_fusion_correction.py        # 校正模型 + LOO + 49格预测
│   ├── audit_nrc_coverage.py           # NRC 覆盖率审计 + 排列检验
│   └── generate_progress_figures.py    # 图表生成
├── reports/                     # 报告和论文
│   ├── 进展报告_2026-07-09.md          # 综合进展报告（含图表）
│   ├── 新表结构设计方案_文献修正版.md    # 新10×12表设计（含文献）
│   ├── paper_draft_valence_arousal_dominance.md  # 英文论文草稿
│   ├── human_experiment_predictions.md # 可检验预测列表
│   ├── nrc_direct_story_完整叙事.md    # 方向C完整叙事
│   └── 新实验方案_纯NRC_人类验证.md    # 实验设计
├── figures/                     # 图表（PNG）
│   ├── fig1_lexicon_vs_consensus.png   # 两本词典 vs 人类共识
│   ├── fig1b_nrc_vs_anew.png           # 词典间互相一致 (r=0.65)
│   ├── fig2_dimension_contribution.png # V42% A28% D30%
│   ├── fig3_permutation_test.png       # 500次排列检验
│   ├── fig4_heatmaps.png               # 7×7 偏差热力图
│   ├── fig5_per_emotion.png            # 逐情绪 2D vs 3D
│   └── fig6_research_overview.png      # 四阶段研究路径图
├── data/                        # 词典数据
│   ├── NRC-VAD-Lexicon-v2.1.txt       # NRC VAD 词典（55000词）
│   └── ANEW/BRM-emot-submit.csv       # ANEW 词典（14000词）
├── results/                     # 分析结果（CSV）
│   ├── nrc_vs_consensus/              # 2D/3D 分析结果
│   ├── cross_lexicon/                 # NRC vs ANEW 对比
│   ├── nrc_fusion_correction/         # 校正模型 LOO 结果
│   └── story_analysis/                # 排列检验 + 几何错位分析
├── reference/                   # 参考文献
│   ├── MA24004_Jenish.doc             # Savaliya (2026) 硕士论文
│   ├── MA24004_Jenish_extracted.txt   # 论文文本提取
│   └── 文献综述_离散情绪维度情绪争论.md
└── ppt/                         # 演示文稿
    └── 汇报ppt_日语版本_3_三坐标最终版.pptx
```

---

## 核心发现速查

| 指标 | 值 | 含义 |
|------|:---:|------|
| NRC vs 共识 (Pearson r) | -0.17 (p=0.55) | 词典不能预测共识 |
| ANEW vs 共识 (Pearson r) | -0.20 (p=0.53) | 两本词典都不行 |
| **NRC vs ANEW 偏差相关** | **+0.65 (p=0.02)** | 词典间一致——问题是系统性的 |
| D 贡献占比 | 30% | Dominance 与 Arousal 同等重要 |
| 排列检验 p 值 | < 0.002 | 词典结构真实存在但弱 |
| 排列检验 Cohen's d | -2.50 | 效应量非常大 |

---

## 文献基础

- Savaliya, J. (2026). 7×7 Hierarchical Matrix for multimodal emotion fusion. Master's thesis.
- Mohammad, S. M. (2018). NRC VAD Lexicon (55,000 words, Best-Worst Scaling).
- Warriner et al. (2013). ANEW (14,000 words, SAM scale).
- Cowen & Keltner (2017, 2020). 27-28 facial expression categories.
- Cowen et al. (2019). 12 cross-cultural vocal emotion categories.
- Keltner et al. (2023). Semantic Space Theory (high-dimensional emotion).

---

## 如何复现

```bash
# 1. 安装依赖
pip install numpy scipy matplotlib

# 2. 下载 ANEW 词典
# 从 https://crr.ugent.be/archives/1003 下载 BRM-emot-submit.csv
# 放到 data/ANEW/ 下

# 3. 运行分析
python core/analyze_nrc_vs_consensus_3d.py     # 2D vs 3D 分析
python core/cross_lexicon_validation.py         # NRC vs ANEW 对比
python core/nrc_fusion_correction.py             # 校正模型
python core/generate_progress_figures.py         # 生成所有图表
```

---

## 当前状态 & 下一步

详见 [ROADMAP.md](ROADMAP.md)

1. ~~Phase 1: 主观坐标拟合（已废弃）~~
2. **Phase 2: NRC-only 分析 + 跨词典验证（已完成）** ← 当前
3. Phase 3: 人类实验验证预测（设计完成，待执行）
4. Phase 4: 新 10×12 非对称矩阵（方案完成，待候选词生成）

---

## 联系

- 研究者: Xixie Jiang
- 导师: Prof. Midori Sugaya
- 实验室: Doly Lab, Shibaura Institute of Technology
