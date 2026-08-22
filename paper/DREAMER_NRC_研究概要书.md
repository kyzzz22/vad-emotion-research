# 研究概要书

## 研究题目

**感情語に対する意味的評価と映像によって喚起された情動体験とのVAD次元別対応関係の検討**

英文工作题目：

*From Semantic Evaluation of Emotion Words to Video-Elicited Experience: Dimension-Specific VAD Alignment*

## 一句话概要

本研究比较两类评价。一类是感情词的意义评价。另一类是影片诱发后的情动体验评价。研究分别检查V、A、D三个维度。结果表明，Valence的类别顺序较为相似，但数值范围不同。Arousal存在正相关，但稳定性仍需确认。Dominance目前没有明确对应。

## 1. 背景与研究问题

VAD由三个维度构成。Valence表示快与不快。Arousal表示心理活跃程度。Dominance表示对情境的控制感。

VAD可以评价感情词的一般意义。VAD也可以评价观看影片后的情动体验。但是，两类评价的对象不同：

- 感情词评价回答“这个词通常表示怎样的感情”；
- 影片后评价回答“这段影片使我实际产生了怎样的体验”。

因此，即使使用相同的VAD名称，也不能预设两类数值一致。

本研究只讨论感情类别名称这一限定的单词单位，不把一个类别标签解释为整个词典。

> 本研究的中心问题是：意义评价与情动体验评价的对应强度及数值范围，是否因V、A、D维度而不同？

为回答这个问题，本研究区分两个方面：

1. 感情类别的排列顺序是否相似。本研究称其为“相对结构”。
2. 数值的分布范围是否相同。本研究称其为“尺度差”。

## 2. 研究目的

本研究不是判定两类评价是否相同。本研究以9个感情类别标签为对象，依次检查线性对应、排序对应和数值范围。目的在于明确VAD各维度的对应特性。

## 3. 数据的角色

| 数据库 | 测量对象 | 本研究中的角色 | 证据边界 |
|---|---|---|---|
| NRC-VAD v2.1 | 感情词的一般VAD意义 | DREAMER以名词形式标示感情类别，因此以同名英语名词1词作为主参照；对应形容词用于敏感性分析 | 是类别标签层面的操作化，不代表整个词典或全部近义词 |
| DREAMER v1.0.2 | 23人观看18段影片后的VAD评价 | 9类感情的主分析 | 每类仅2段影片 |
| CASE | 30人观看8段影片时的连续VA评价 | VA处理方法的补充确认 | 仅4类感情且无Dominance |

三套数据不在试次层面合并。NRC-VAD提供意义评价的参照。DREAMER提供主要结论。CASE只补充确认分析步骤。CASE不被解释为DREAMER的独立复现。本轮不纳入DEAP。

## 4. 分析方法

- 各数据的量尺范围不同。因此，先将它们转换到 `[-1, 1]`。
- 转换只统一数值范围。它不表示两类评价在心理意义上相同。
- 以9个感情类别为推断单位。414个试次不作为独立样本。
- 研究问题包含线性对应，因此用Pearson相关进行检查。
- 用Spearman相关检查类别排序。
- 用精确置换检验判断相关是否可能由偶然产生。
- 对Pearson和Spearman各自的V、A、D三个检验进行Holm校正。
- 用5,000次层级bootstrap估计DREAMER类别均值的不确定性。每次有放回地抽取23名参与者，并在每个感情类别内有放回地抽取2段影片。
- 用回归斜率近似“尺度差”。斜率1表示相同的数值范围。斜率小于1表示向中性点压缩。该指标不能分离量尺、刺激和样本差异。

## 5. 主要结果

| 指标 | Valence | Arousal | Dominance |
|---|---:|---:|---:|
| Pearson r（Holm p） | .875（.018） | .832（.034） | -.121（.792） |
| Spearman ρ（Holm p） | .895（.007） | .433（.500） | -.417（.500） |
| r的双层bootstrap 95% CI | [.762, .920] | [.370, .913] | [-.432, .280] |
| 回归斜率 | .520 | .341 | -.055 |
| 探索性判断 | 观察到线性与排序对应 | 仅观察到线性对应 | 未确认对应 |

Valence的回归斜率为`.520`。Arousal为`.341`。两者都小于1。因此，情动体验评价比意义评价更集中在中性点附近。也就是说，类别顺序可以相似，但具体数值并不一致。

Arousal的Pearson相关较高。但是，Spearman相关没有通过Holm校正。因此，Arousal只显示线性对应，不能说明类别排序稳定。

将名词参照改为对应形容词后，Valence（Pearson `r=.868`，Holm `p=.019`）与Arousal（`r=.829`，`p=.040`）仍呈线性对应。Dominance（`r=-.096`，`p=.850`）仍未确认对应。该结果降低了结论完全由名词/形容词形式决定的可能性，但不能证明单个标签代表整个词典。

## 6. 考察

现阶段的答案是：两类评价的对应形式因VAD维度而异。

- **Valence：** 感情类别的排列顺序较为相似。但是，情动体验评价的数值范围更窄。因此，“对应”不等于“数值一致”。
- **Arousal：** 存在线性关联。但是，结果可能受到刺激强度和类别构成影响。因此，还需要外部验证。
- **Dominance：** 目前没有明确对应。意义评价反映词语一般含有的支配感。情动体验评价可能受到具体场景中的可控制性、主体性与自我决定感影响。这种语境依赖性可能削弱跨数据库对应，但现有数据不能检验作用机制。

因此，本研究不把VAD作为一个整体来判断。研究分别说明V、A、D中的对应程度和尺度差异。

## 7. 现阶段的学术意义

本研究区分“对应”和“一致”。Pearson相关表示线性对应。Spearman相关表示排序对应。回归斜率表示数值的分布范围。Valence的两种相关都较高，但斜率小于1。因此，高相关不能单独证明数值一致。

本研究的创新点不是再次说明“词语与体验不同”，而是在同一分析框架内显示两类评价的对应程度因V、A、D而异。因此，在情感计算中将词典VAD直接作为情动体验模型的教师值或正解值时，需要逐维度验证其妥当性。

跨数据库比较VAD时，可按以下顺序检查：

1. 确认评价对象、指导语和时间窗；
2. 统一数值范围；
3. 分维度检验相对结构；
4. 在目标数据中重新估计尺度变换。

## 8. 限制

- 推断单位只有9类感情。每类以1个英语名词和2段影片操作化，因此不能推广到整个词典、全部近义词或更广泛的感情类别。
- NRC-VAD与DREAMER的参与者和任务不同。结果只表示类别层面的对应，不能说明同一个人的语义评价能够预测其情动体验。
- CASE只有4类感情且没有Dominance，不能构成充分的外部复现。
- DREAMER的Dominance原始SAM画面方向和指导语仍需最终核对。但是，符号反转的敏感性分析没有改变“无明确对应”的结论。
- 本研究是探索性二次数据分析，不构成测量不变性或因果关系的证明。

## 9. 结论与下一步

意义评价与情动体验评价的对应因VAD维度而异。Valence的相对结构较为稳定，但数值向中性点压缩。Arousal存在正相关，但稳定性仍需确认。Dominance目前没有明确对应。

下一步使用共同感情、影片数和近义词更多的外部数据复核。随后让同一参与者评价多个感情词及影片后的情动体验，检验个体内对应。

## 核心参考文献

1. Bradley, M. M., & Lang, P. J. (1994). Measuring emotion: The Self-Assessment Manikin and the Semantic Differential. *Journal of Behavior Therapy and Experimental Psychiatry, 25*(1), 49-59.
2. Katsigiannis, S., & Ramzan, N. (2018). DREAMER: A database for emotion recognition through EEG and ECG signals. *IEEE Journal of Biomedical and Health Informatics, 22*(1), 98-107.
3. Mohammad, S. M. (2025). NRC VAD Lexicon v2. *arXiv:2503.23547*.
4. Sharma, K., et al. (2019). A dataset of continuous affect annotations and physiological signals for emotion analysis. *Scientific Data, 6*, 196.
5. Barrett, L. F. (2004). Feelings or words? Understanding the content in self-report ratings of experienced emotion. *Journal of Personality and Social Psychology, 87*(2), 266-281.
6. Robinson, M. D., & Clore, G. L. (2002). Belief and feeling: Evidence for an accessibility model of emotional self-report. *Psychological Bulletin, 128*(6), 934-960.
