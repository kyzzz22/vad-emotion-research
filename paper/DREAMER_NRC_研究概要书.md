# 研究概要书

## 研究题目

**词汇情感常模能否迁移至诱发情绪体验：NRC-VAD与DREAMER的跨情境对齐研究**

英文题目：*Are Lexical VAD Norms Transportable to Elicited Emotion? A Cross-Context Alignment Study of NRC-VAD and DREAMER*

## 一句话概要

本研究不预设“情绪词的VAD坐标”和“观看影片后的VAD体验”可以互换，而是检验二者在多大程度上共享结构，并区分整体量尺差异与特定情绪的额外偏离。

## 研究出发点与必要性

Valence、Arousal和Dominance（VAD）同时存在于词汇情感常模、情绪诱发实验和情感计算数据库中，因此常被当作一种跨任务的共同坐标。然而，坐标名称相同不代表测量对象相同。NRC-VAD描述词语通常具有的情感意义；DREAMER的SAM评分描述参与者观看特定影片后报告的即时状态。前者更接近共享的语义知识，后者同时受到刺激内容、个体状态、情境和量表使用方式影响。

如果不检验这种跨情境可迁移性，研究者可能把词汇标签、刺激常模和体验评分直接合并，却不知道差异来自情绪本身，还是来自任务、量尺和样本。这不是简单的“两个数据库做相关”，而是一个测量边界问题：**语言中的情绪坐标能否作为体验坐标的代理，若只能部分代理，其失效发生在哪些维度和类别？**

Barrett（2004）指出，经验性情绪自评既包含当下体验信息，也会受到情绪词语义结构影响；Robinson和Clore（2002）进一步区分了即时体验信息与一般情绪信念。Bradley和Lang（1994）的SAM测量刺激后的愉悦、唤醒和控制体验，而Mohammad（2018）的NRC-VAD测量词义的VAD属性。现有理论因此支持“相关但不等价”的预期，却仍需要可量化的跨数据检验。

## 研究目的

1. 检验九类情绪的词汇VAD与影片诱发VAD在各维度上的结构对应。
2. 估计DREAMER相对NRC是否存在整体平移或压缩，避免把全局量尺差异误认为某一情绪的特殊差异。
3. 在去除整体线性映射后，识别仍具有较大残差的情绪类别，作为后续直接实验的优先对象。
4. 评估上述结论对单一情绪、词形选择和Dominance计分方向是否敏感。
5. 探索粗粒度EEG/ECG特征是否解释同一影片内个体VAD偏差，但不将生理信号视为VAD真值。

## 研究问题

- **RQ1**：词汇常模与诱发体验在V、A、D三个维度上的类别结构是否对应？
- **RQ2**：两套坐标的偏差有多少表现为全局量尺压缩，有多少是类别特异残差？
- **RQ3**：哪些情绪在校准后仍值得优先复核？该排序的不确定性有多大？
- **RQ4（探索性）**：EEG/ECG基线变化是否与个体层面对齐距离相关？

## 数据与设计

- DREAMER v1.0.2：23名参与者、18段影片、414个完整试次。
- 九类目标情绪：amusement、anger、calmness、disgust、excitement、fear、happiness、sadness、surprise。
- 每类情绪由两段影片表示，参与者在每段影片后使用1-5分SAM报告VAD。
- DREAMER评分按 `(score - 3) / 2` 映射至[-1, 1]。
- NRC-VAD v2.1提供对应英文情绪名词的词汇坐标；名词为主分析，状态形容词为敏感性分析。
- 核心统计推断单位是九个情绪类别。414个试次用于估计DREAMER类别质心和不确定性，不用于虚增跨数据库检验样本量。

## 分析策略

1. 分别计算V、A、D的Pearson和Spearman相关。
2. 枚举全部 `9! = 362,880` 种类别标签排列，获得精确p值，并对三维检验做Holm校正。
3. 同时重抽参与者与每类中的影片，执行5,000次双层bootstrap。
4. 以保持V/A/D轴含义的标准化构型一致性检验整体三维结构，不允许通过旋转交换维度含义。
5. 拟合NRC到DREAMER的逐维仿射映射，描述整体压缩与平移。
6. 对每类情绪执行leave-one-emotion-out校准，用其他八类预测被留出的类别，计算VA和VAD残差。
7. 逐一删除情绪类别，检查相关结论是否由单一类别驱动。
8. 报告名词/形容词和Dominance反向编码敏感性。

## 已获得的主要结果

| 维度 | Pearson r | 精确p | Holm p | 双层bootstrap 95% CI | 结论 |
|---|---:|---:|---:|---|---|
| Valence | .875 | .0061 | .0184 | [.762, .920] | 强且稳定的跨情境结构对应 |
| Arousal | .832 | .0169 | .0339 | [.370, .913] | 存在线性对应，但排序和类别影响较不稳定 |
| Dominance | -.121 | .7923 | .7923 | [-.432, .280] | 未发现跨情境对应 |

保持维度轴不旋转的整体构型一致性为 `C=.529`，单侧精确置换 `p=.0058`，双层bootstrap 95% CI为 `[.299, .651]`。这说明三维空间总体并非随机对应，但一致性主要由V和A贡献，不能用整体显著掩盖D的失配。

NRC到DREAMER的斜率分别为V `.520`、A `.341`、D `-.055`。V和A明显低于1，说明DREAMER类别均值相对词汇常模更集中。该压缩可能来自多名参与者和两段影片的平均、刺激强度、任务参照及量尺差异，不能归因于单一机制。

校准后的VAD残差从小到大为excitement、fear、anger、amusement、sadness、disgust、happiness、surprise、calmness。calmness点估计最大（`.759`，95% CI `[.538, 1.036]`），但多数类别区间广泛重叠，因此只能将其称为优先复核对象，不能建立确定的普遍排行榜。

逐类删除后，Valence相关保持在`.848-.922`，显示结论稳定；Arousal为`.482-.898`，更依赖类别构成；Dominance为`-.574-.049`，始终没有稳定正对应。名词和形容词分析给出相同的维度模式。Dominance反向仅改变相关符号，不改变其不显著性。

七项粗粒度EEG/ECG特征在控制影片固定效应、按参与者聚类标准误并做Holm校正后均不显著。其含义是当前特征未解释同一影片内的个体对齐偏差，而不是“生理与情绪无关”。

## 预期贡献

### 理论贡献

将“词义理解和诱发体验是否可比”的争论转化为可检验的跨情境迁移问题。结果支持二者相关但不等价，并显示这种关系具有维度特异性。

### 方法贡献

提出一套区分结构相关、绝对坐标距离、全局尺度映射和类别特异残差的分析流程。它比单独报告相关或欧氏距离更能避免错误解释。

### 应用贡献

为使用词汇VAD标注刺激、训练情感模型或连接异质情绪数据库提供边界证据：Valence可能较适合作为跨情境桥梁；Arousal需要校准；Dominance不应在未核对参照对象和计分方向时直接迁移。

## 研究限制

1. 核心检验只有九个类别，不能推广到全部复杂情绪。
2. 每类只有两段影片，刺激与类别部分混淆，影片总体误差估计不足。
3. NRC与DREAMER来自不同参与者、任务和时间，不支持个体内预测或因果归因。
4. 词典坐标被视为固定值，当前数据无法传播NRC原始评分者层面的测量误差。
5. Dominance的具体解释仍依赖DREAMER原始SAM界面方向和题干核验。
6. 情绪特异残差为探索性结果，其排序需要外部数据库或新实验复现。

## 当前论文定位

本研究适合定位为**探索性二手数据研究、方法短文或预印本**，核心表述为cross-context alignment或transportability，而不是validation或measurement invariance。当前证据足以形成边界清楚的论文，但不足以证明语义VAD和体验VAD可以互换。

## 后续直接验证

下一阶段最强的设计是在同一参与者内，对同一情绪概念获得词汇联想、典型体验和影片诱发后的VAD评分，并统一量尺、题干和Dominance参照对象。当前结果可用于选择重点类别、估计效应范围并预注册分析，而不是替代该直接实验。

## 核心参考文献

- Barrett, L. F. (2004). Feelings or words? *Journal of Personality and Social Psychology, 87*(2), 266-281. https://doi.org/10.1037/0022-3514.87.2.266
- Bradley, M. M., & Lang, P. J. (1994). Measuring emotion: The Self-Assessment Manikin and the Semantic Differential. *Journal of Behavior Therapy and Experimental Psychiatry, 25*(1), 49-59. https://doi.org/10.1016/0005-7916(94)90063-9
- Katsigiannis, S., & Ramzan, N. (2018). DREAMER. *IEEE Journal of Biomedical and Health Informatics, 22*(1), 98-107. https://doi.org/10.1109/JBHI.2017.2688239
- Mohammad, S. M. (2018). Obtaining reliable human ratings of valence, arousal, and dominance for 20,000 English words. *ACL 2018*, 174-184. https://doi.org/10.18653/v1/P18-1017
- Robinson, M. D., & Clore, G. L. (2002). Belief and feeling. *Psychological Bulletin, 128*(6), 934-960. https://doi.org/10.1037/0033-2909.128.6.934

