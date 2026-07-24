# 研究概要书

## 研究题目

**感情語に対する意味的評価と映像によって喚起された情動体験とのVAD次元別対応関係の検討**

英文工作题目：
*From Emotion Words to Elicited Experience: Dimension-Specific Cross-Context Alignment Between NRC-VAD and DREAMER*

## 一句话概要

本研究不预设"情绪词的VAD坐标"和"观看影片后的VAD体验"可以互换，而是检验二者在多大程度上共享结构，并区分整体量尺差异与特定情绪的额外偏离。

## 研究背景与必要性

### 共同坐标不等于共同测量

Valence（愉悦度）、Arousal（激活度）和Dominance（支配感）三维度同时存在于词汇情感常模、情绪诱发实验和情感计算数据库中，因而常被当作一种跨任务的共同坐标。然而，**维度名称相同不代表测量对象相同**：

- NRC-VAD中，评分者判断一个词语通常具有的情感属性——这是共享语义知识。
- DREAMER中，参与者观看特定影片后报告自身即时状态——这是情境化主观体验。

如果不检验这种跨情境可迁移性，研究者可能把词汇标签、刺激常模和体验评分直接合并使用，却不知道差异来自情绪本身，还是来自任务、量尺和样本。这不仅是"两个数据库做相关"的技术问题，而是一个**测量边界问题**：语言中的情绪坐标能否作为体验坐标的代理？若只能部分代理，其失效发生在哪些维度和类别？

### 理论基础：相关但不等价

已有研究为"相关但不等价"的预期提供了理论支撑。Barrett（2004）指出，经验性情绪自评既包含当下体验信息，也会受到情绪词语义结构的影响——换言之，自评体验本身已经混合了语义知识。Robinson和Clore（2002）的可及性模型进一步区分了即时体验信息与一般情绪信念：前者来自情景记忆，后者来自语义知识，二者在不同时间尺度上对自我报告的贡献不同。Bradley和Lang（1994）的SAM可以同时测量刺激后的愉悦、唤醒和控制体验，但测量工具相同并不意味着被测对象相同。

### 跨情境检验的具体必要性

已有跨域研究（Schlochtermeier et al., 2013; Bayer & Schacht, 2014）发现，文字、图片和面孔的情绪加工既有共同成分，也受刺激复杂度和任务要求影响。这意味着两个数据库即使使用相同的VAD标签，也可能产生至少三类差异：（1）类别相对顺序不同；（2）一套量尺相对另一套发生整体压缩或平移；（3）某些具体情绪具有超出全局变换的额外偏离。单独计算相关无法区分绝对坐标是否接近，单独计算欧氏距离又会把整体量尺压缩误认为类别特异差异。

### 本研究填补的缺口

综上所述，现有理论支持"词汇VAD与诱发VAD既有关联又不等价"的预期，已有跨域研究也提示刺激模态和任务会系统影响情绪评分，但**尚无研究对同一组情绪概念的词汇常模和诱发体验进行系统的跨情境VAD审计**——即在统一尺度下同时检验维度结构、全局量尺映射和校准后的类别残差。本研究使用NRC-VAD v2.1和DREAMER两个公开数据库，对九类情绪完成这一审计，明确跨情境迁移的可行范围与失效边界。

## 研究目的与研究问题

### 研究目的

1. 检验九类情绪的词汇VAD与影片诱发VAD在各维度上的结构对应。
2. 估计DREAMER相对NRC是否存在整体平移或压缩，避免把全局量尺差异误认为某一情绪的特殊差异。
3. 在去除整体线性映射后，识别仍具有较大残差的情绪类别，作为后续直接实验的优先对象。
4. 评估上述结论对单一情绪、词形选择（名词/形容词）和Dominance计分方向是否敏感。
5. 探索粗粒度EEG/ECG特征是否解释同一影片内个体VAD偏差，但不将生理信号视为VAD真值。

### 研究问题

- **RQ1**：词汇常模与诱发体验在V、A、D三个维度上的类别结构是否对应？
- **RQ2**：两套坐标的偏差有多少表现为全局量尺压缩，有多少是类别特异残差？
- **RQ3**：哪些情绪在校准后仍值得优先复核？该排序的不确定性有多大？
- **RQ4（探索性）**：EEG/ECG基线变化是否与个体层面对齐距离相关？

## 数据来源：三个数据库的横向对比

本研究同时使用三个公开/许可数据库，它们在测量对象、任务类型和数据特性上有本质差异。下表总结其关键特征及在本研究中的角色：

| | DREAMER | CASE | NRC-VAD |
|---|---|---|---|
| **类型** | 影片诱发体验数据库 | 影片诱发体验数据库 | 大规模词汇情感常模 |
| **参与者** | 23人 | 30人 | 众包评分者（每词≥10人） |
| **刺激** | 18段影音片段（9类情绪×2段） | 8段情绪视频（4类情绪） | 20,000+英文词条 |
| **情绪类别** | 9类：amusement, anger, calmness, disgust, excitement, fear, happiness, sadness, surprise | 4类可命名：amusing, boring, relaxing, scary | 覆盖全部英文词，可任意选取 |
| **VAD维度** | V + A + D，1-5分SAM自评 | V + A连续标注（0.5-9.5），**无D** | V + A + D，0-1连续评分 |
| **任务** | 观看影片后即时SAM自评 | 观看影片后连续VA自评 | 判断词语本身的情感属性 |
| **生理信号** | 14ch EEG + 2ch ECG | GSR, BVP, 皮温, 呼吸, 面部EMG | 无 |
| **本研究角色** | **主数据**：三维VAD全维度对齐 | **方法试跑**：VA两维流程验证 + 恢复曲线支线 | **参照基准**：跨任务比较的词汇VAD标准 |
| **核心贡献** | 提供跨情境对齐的完整三维空间，回答V/A/D各自是否可迁移 | 验证分析流程可运行，提供恢复曲线候选方法，确认无D时的分析边界 | 提供词汇层面的VAD参照坐标，使"语义vs体验"的比较在操作上可行 |
| **核心局限** | 每类仅2段影片，刺激与类别部分混淆；N=23 | 仅4类、无Dominance；类别层面N=4 | 词汇评分不含即时体验信息；评分者不确定性无法传播到类别对比 |

### 三个数据库的一致性

- **Valence**：CASE和DREAMER的诱发VA均与NRC词义坐标呈现方向一致的正负效价对应（DREAMER Pearson r=.875，CASE四类VA质心方向一致）。
- **数据库间可复现**：CASE的二维VA试跑在四类情绪上复现了DREAMER主分析的分析流程和量尺转换方法，证明分析管线可跨数据库迁移。

### 三个数据库的关键差异

- **Dominance的缺失**：CASE无D自评，无法参与三维对齐；DREAMER有D但当前未发现跨情境对应（r=-.121），Dominance的测量可迁移性在三库中均为未解决问题。
- **类别覆盖**：CASE仅4类，不足以估计类别排序的稳定性；DREAMER的9类勉强支持相关分析但每类仅2段影片。
- **任务与量尺**：NRC-VAD是离线词汇判断，CASE和DREAMER是即时体验报告；三者的量尺范围和锚定方式各不相同，本研究的统一[-1,1]映射只是量尺对齐，不是构念等价声明。

## 分析策略

1. 分别计算V、A、D的Pearson和Spearman相关。核心推断单位是9个情绪类别，不是414个试次。
2. 枚举全部 `9! = 362,880` 种类别标签排列，获得精确p值，并对三维检验做Holm校正。
3. 同时重抽参与者与每类中的影片，执行5,000次双层bootstrap。
4. 以保持V/A/D轴含义的标准化构型一致性检验整体三维结构，不允许通过旋转交换维度含义。
5. 拟合NRC到DREAMER的逐维仿射映射，描述整体压缩与平移。
6. 对每类情绪执行leave-one-emotion-out校准，用其他八类预测被留出的类别，计算VA和VAD残差。
7. 逐一删除情绪类别，检查相关结论是否由单一类别驱动。
8. 报告名词/形容词和Dominance反向编码的敏感性分析。

## 已获得的主要结果

| 维度 | Pearson r | 精确p | Holm p | 双层bootstrap 95% CI | 结论 |
|---|---:|---:|---:|---|---|
| Valence | .875 | .0061 | .0184 | [.762, .920] | 强且稳定的跨情境结构对应 |
| Arousal | .832 | .0169 | .0339 | [.370, .913] | 存在线性对应，但排序和类别影响较不稳定 |
| Dominance | -.121 | .7923 | .7923 | [-.432, .280] | 未发现跨情境对应 |

保持维度轴不旋转的整体构型一致性为 `C=.529`，单侧精确置换 `p=.0058`，双层bootstrap 95% CI为 `[.299, .651]`。三维空间总体并非随机对应，但一致性主要由V和A贡献，不能用整体显著掩盖D的失配。

NRC到DREAMER的斜率分别为V `.520`、A `.341`、D `-.055`。V和A斜率明显低于1，说明DREAMER类别均值相对词汇常模更集中（全局量尺压缩）。

校准后的VAD残差从小到大为excitement、fear、anger、amusement、sadness、disgust、happiness、surprise、calmness。calmness点估计最大（`.759`，95% CI `[.538, 1.036]`），但多数类别区间广泛重叠，因此只能将其称为**优先复核对象**，不能建立确定的普遍排行榜。

### 敏感性分析摘要

- **逐类删除**：Valence相关保持在`.848-.922`（稳定），Arousal为`.482-.898`（依赖calmness），Dominance为`-.574-.049`（始终无正对应）。
- **名词/形容词**：维度模式一致，名词为主分析。
- **Dominance方向**：反向编码仅改变符号，不改变不显著性。
- **生理探索**：包括理论上与Dominance相关的额叶alpha不对称（FAA）在内，七项EEG/ECG特征在Holm校正后均不显著——当前粗粒度特征（14ch低密度EEG、末60s平均、每类仅2段影片）未解释同一影片内的个体对齐偏差，而非"生理与情绪无关"。FAA与Dominance的特异性关联需要在更高密度EEG和更精准Dominance测量的实验设计中重新检验。

## 预期贡献

### 理论贡献

将"词义理解和诱发体验是否可比"的争论转化为可检验的跨情境迁移问题。结果支持二者相关但不等价，并显示这种关系具有**维度特异性**：Valence可作为跨情境桥梁，Arousal需要校准，Dominance不应在未核对参照对象时直接迁移。

### 方法贡献

提出一套区分结构相关、绝对坐标距离、全局尺度映射和类别特异残差的分析流程。它比单独报告相关或欧氏距离更能避免错误解释。该流程已在DREAMER（三维）和CASE（二维）两个数据库上验证可运行。

### 应用贡献

为使用词汇VAD标注刺激、训练情感模型或连接异质情绪数据库提供**边界证据**：哪些维度可跨情境使用，哪些需要逐类校准，哪些在当前条件下无法可靠迁移。

## 研究限制

1. 核心检验只有九个类别，不能推广到全部复杂情绪。
2. 每类只有两段影片，刺激与类别部分混淆，影片总体误差估计不足。
3. NRC与DREAMER来自不同参与者、任务和时间——这是跨样本结构比较，不支持个体内预测或因果归因。
4. 词典坐标被视为固定值，当前数据无法传播NRC原始评分者层面的测量误差。
5. Dominance的具体解释仍依赖DREAMER原始SAM界面方向和题干核验（待完成）。
6. 情绪特异残差为探索性结果，其排序需要外部数据库或新实验复现。

## 当前论文定位

本研究适合定位为**探索性二手数据研究、方法短文或预印本**，核心表述为cross-context alignment或transportability，而不是validation或measurement invariance。当前证据足以形成边界清楚的论文，但不足以证明语义VAD和体验VAD可以互换。

## 未来工作

以下工作已设计完成但尚未开始执行，等待伦理审批、设备确认和参与者招募等前置条件：

### 第一优先级：A2同一参与者三层对齐实验（未开始）

当前DREAMER×NRC的跨样本比较无法区分"个体差异"和"任务差异"。下一阶段最强设计是在**同一参与者内**，对同一情绪概念获得三个层次的VAD评分：

- **词义联想VAD**：看到情绪词时的直接语义判断。
- **概念原型VAD**：对"典型处于该情绪的人"的判断。
- **诱发体验VAD**：观看影片后对当下体验的报告。

核心假设H1：概念原型与诱发体验的坐标距离小于词汇联想与诱发体验的距离（`|Delta_PE| < |Delta_LE|`）。

设计为被试内重复测量，两场次（语义+诱发），6个情绪概念（喜悦/被逗乐/温情/愤怒/悲伤/恐惧），同步采集EDA+ECG/PPG。目标36-45人。当前状态：实验任务（Web浏览器）、材料、随机表、分析管线、预测试方案、操作手册和伦理草案均已完成设计；**伦理审批、设备同步验证、预测试和正式招募尚未启动**（详见`A2_研究主方案.md`和`PROJECT_STATUS.md`）。

### 第二优先级：Dominance原始材料核验（待完成）

需回到DREAMER原始SAM材料，确认Dominance图示与编码方向。该核验直接影响对D维度的全部解释。

### 远期方向

- **FAA→Dominance特异性假设的高密度验证**：额叶alpha不对称（FAA）与趋近/回避动机系统的理论关联，使其成为Dominance的潜在生理标记。当前DREAMER的14通道低密度EEG和每类仅2段影片的限制使该检验敏感性不足。未来若设备条件允许，应在更高密度EEG下设FAA→Dominance为预设探索性假设，并在试次层面检验FAA变化是否特异性地追踪Dominance体验而非Valence或Arousal。
- 将情绪恢复曲线建模为峰值、恢复速度、曲线面积和正负情绪对称性（CASE上已有方法试跑，见`public_data/case_recovery/`）。
- 量化个体在正向与负向高唤醒情绪中的恢复特征是否稳定。
- 扩展到更复杂的情绪概念（但不从少量锚点直接宣称可以可靠推断全部坐标）。
- 建立经过许可、材料验证和充分样本支持的多模态情绪数据库。

## 核心参考文献

1. Barrett, L. F. (2004). Feelings or words? Understanding the content in self-report ratings of experienced emotion. *Journal of Personality and Social Psychology, 87*(2), 266-281. https://doi.org/10.1037/0022-3514.87.2.266
2. Bradley, M. M., & Lang, P. J. (1994). Measuring emotion: The Self-Assessment Manikin and the Semantic Differential. *Journal of Behavior Therapy and Experimental Psychiatry, 25*(1), 49-59. https://doi.org/10.1016/0005-7916(94)90063-9
3. Katsigiannis, S., & Ramzan, N. (2018). DREAMER: A database for emotion recognition through EEG and ECG signals from wireless low-cost off-the-shelf devices. *IEEE Journal of Biomedical and Health Informatics, 22*(1), 98-107. https://doi.org/10.1109/JBHI.2017.2688239
4. Mohammad, S. M. (2018). Obtaining reliable human ratings of valence, arousal, and dominance for 20,000 English words. In *Proceedings of ACL 2018* (pp. 174-184). https://doi.org/10.18653/v1/P18-1017
5. Robinson, M. D., & Clore, G. L. (2002). Belief and feeling: Evidence for an accessibility model of emotional self-report. *Psychological Bulletin, 128*(6), 934-960. https://doi.org/10.1037/0033-2909.128.6.934
6. Schlochtermeier, L. H., et al. (2013). Emotional picture and word processing: An fMRI study on effects of stimulus complexity. *PLoS ONE, 8*(2), e55619. https://doi.org/10.1371/journal.pone.0055619
7. Sharma, K., et al. (2019). A dataset of continuous affect annotations and physiological signals for emotion analysis. *Scientific Data, 6*, 196. https://doi.org/10.1038/s41597-019-0209-0
8. Bayer, M., & Schacht, A. (2014). Event-related brain responses to emotional words, pictures, and faces: A cross-domain comparison. *Frontiers in Psychology, 5*, 1106. https://doi.org/10.3389/fpsyg.2014.01106
