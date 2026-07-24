# 论文核心文本草稿

## 确定题目（日文）

**感情語に対する意味的評価と映像によって喚起された情動体験とのVAD次元別対応関係の検討**

## 英文工作题目

**From Emotion Words to Elicited Experience: Dimension-Specific Cross-Context Alignment Between NRC-VAD and DREAMER**

## 摘要草稿

### 中文摘要

效价、唤醒度和支配感（VAD）既用于描述词语的情感意义，也用于记录刺激后的主观情绪体验，但相同的维度名称并不保证两类评分可以直接互换。本研究检验词汇VAD常模向影片诱发体验的跨情境可迁移性，并区分全局量尺差异与情绪类别特异偏差。我们将NRC-VAD v2.1中九个英文情绪名词的坐标，与DREAMER数据库23名参与者观看18段影片后获得的414个VAD评分进行对齐。核心推断以九个情绪类别为单位，采用全部362,880种标签排列的精确检验、Holm校正、参与者与影片双层bootstrap、逐类删除分析以及留一情绪仿射校准。Valence表现出稳定的跨情境对应（r=.875，Holm p=.018），Arousal具有线性对应（r=.832，Holm p=.034）但排序和类别影响较不稳定，Dominance未显示对应（r=-.121，Holm p=.792）。整体三维构型显著高于随机排列（C=.529，p=.0058），但DREAMER的V和A范围相对词汇常模明显压缩。校准后calmness具有最大的残差点估计，但类别区间广泛重叠。结果表明，词汇常模保留了部分诱发情绪结构，却不能被视为体验评分的直接替代；其可迁移性具有维度和类别特异性。

关键词：VAD；情绪词；情绪诱发；构念对齐；词汇常模；DREAMER

### English Abstract

Valence, arousal, and dominance (VAD) are used both to represent the affective meaning of words and to record self-reported experience after emotion elicitation. Shared dimension labels, however, do not guarantee that lexical norms and elicited ratings are interchangeable. This study examined the cross-context transportability of lexical VAD norms while separating global scale differences from emotion-specific discrepancy. NRC-VAD v2.1 coordinates for nine English emotion nouns were aligned with 414 post-film VAD ratings from 23 participants and 18 clips in DREAMER. Inference was conducted at the level of nine emotion categories using all 362,880 exact label permutations, Holm adjustment, a hierarchical participant-and-film bootstrap, leave-one-emotion-out influence analysis, and affine calibration. Valence showed robust cross-context correspondence (r=.875, Holm-adjusted p=.018). Arousal showed a linear association (r=.832, adjusted p=.034), although rank correspondence and category influence were less stable. Dominance showed no evidence of alignment (r=-.121, adjusted p=.792). The axis-preserving three-dimensional configuration was more congruent than expected under random label assignment (C=.529, p=.0058), while elicited valence and arousal were substantially compressed relative to lexical norms. Calmness had the largest calibrated residual point estimate, but uncertainty intervals overlapped broadly across categories. Lexical norms therefore preserve part of the structure of elicited affect but should not be treated as direct substitutes for experiential ratings. Transportability appears to be dimension- and category-dependent.

Keywords: VAD; emotion words; emotion elicitation; construct alignment; affective norms; DREAMER

## 1. 引言

### 1.1 共同坐标不等于共同测量

维度情绪模型使用Valence、Arousal和Dominance描述情感状态。Valence表示愉悦或不愉悦，Arousal表示低激活到高激活，Dominance通常涉及控制、力量或被情境支配的感受（Bradley & Lang, 1994）。VAD的优势在于它能够为词语、图片、影片和主观体验提供形式相似的连续坐标，因此成为心理语言学和情感计算之间的重要接口——研究者可以在同一个三维空间中标定词汇的情感意义、刺激的情绪属性以及参与者的主观体验。

然而，**维度名称相同不代表测量对象相同**。这一区分至关重要：NRC-VAD等词汇常模要求评分者判断词语通常具有的情感属性，主要反映共享语义和概念知识（Mohammad, 2018）；DREAMER等诱发数据库则要求参与者在观看具体影片后报告自身即时状态（Katsigiannis & Ramzan, 2018），评分会同时受到刺激内容、个体状态、情境因素和量表使用方式的影响。如果不检验这种跨情境可迁移性，研究者可能把词汇标签、刺激常模和体验评分直接合并使用——例如用词典VAD标注刺激材料，或用诱发数据库中的标签训练情感识别模型——却不知道观测到的差异来自情绪本身，还是来自任务、量尺和样本的差异。

Barrett（2004）表明，经验性情绪自评既与情绪词语义结构有关，又不能完全还原为词义知识：人们在报告自身情绪体验时，可能同时调用了当下的身体感受和长期积累的语义知识。Robinson和Clore（2002）的可及性模型进一步区分了即时体验信息（来自情景记忆）与一般情绪信念（来自语义知识），并预测二者在不同时间尺度和报告条件下对自评的贡献不同。因此，词汇VAD与诱发VAD既不是完全无关的对象，也不是同一测量的简单重复。

基于上述理论与测量背景，本研究的核心问题不是”哪一种VAD更真实”，而是**transportability**（可迁移性）：词汇常模所保存的情绪结构，能够在多大程度上迁移到刺激诱发后的体验空间？如果不能完全迁移，迁移的边界在哪里——哪些维度、哪些情绪类别更可靠，哪些需要校准或不可直接迁移？

### 1.2 跨情境迁移为何需要系统检验

已有跨域研究发现，文字、图片和面孔的情绪加工既有共同成分，也受刺激复杂度和任务要求影响（Schlochtermeier et al., 2013; Bayer & Schacht, 2014; Usée et al., 2020）。在共享语义内容的条件下，文字和图片可同时分析共同点和域差异，但刺激模态本身会系统影响效价和唤醒度评分。

具体而言，两个数据库即使使用相同的VAD维度标签，也可能产生至少三类差异：（1）**类别排序差异**：同一情绪概念在词汇和体验空间中的相对位置不同；（2）**全局量尺差异**：一套量尺相对另一套发生整体压缩或平移——例如体验评分可能比词汇常模更集中于中性区间；（3）**类别特异偏离**：某些具体情绪在去除全局变换后仍具有超出预期的残差，可能反映了概念知识与实际体验之间的系统性差异。

单独计算相关不能区分绝对坐标是否接近（高相关可以伴随大幅平移），单独计算欧氏距离又会把整体量尺压缩误认为特定情绪的特异差异（全局压缩会使所有类别看起来都”偏离”）。一个完整的跨情境审计因此需要同时检验：**维度层面的结构对应、全局量尺映射的参数估计、以及校准后的类别残差排序**。本研究正是按此三步框架展开。

### 1.3 维度特异性预期与生理探索

Valence通常是情绪词和刺激评价中最直接、最可靠的组织维度（Warriner et al., 2013），因而预期表现出最强的跨情境迁移。Arousal更容易受到刺激强度、时间动态（影片的节奏、声音、情节起伏）和参与者平均效应的影响，因此可能保留总体线性趋势但出现类别排序变化和范围压缩。Dominance的参照对象最不稳定：词汇评分可能反映某一情绪概念所包含的力量或控制程度，刺激后评分则可能反映参与者当时对环境或自身状态的控制感；两种参照对象的差异可能导致D缺乏跨情境对应。

在生理层面，本研究额外关注额叶alpha不对称（frontal alpha asymmetry, FAA）与Dominance的关系。大量文献表明，FAA与趋近/回避动机系统相关（Davidson, 1992; Harmon-Jones & Gable, 2018），左侧额叶活动增强与趋近倾向和掌控感有关，右侧增强与回避倾向有关。因此，FAA可能在概念上与Dominance（控制/支配感）存在特异性关联：如果参与者在观看影片后体验到更强的控制感（高Dominance），理论上可能伴随更大的左侧额叶alpha不对称。这一假设在已有的多模态情绪数据库中尚未被充分检验。DREAMER提供14通道EEG数据，包含AF3、F3、AF4、F4等额叶电极，允许从刺激前后基线变化中提取FAA，并检验其与Dominance体验偏差的特异性关系。

### 1.4 当前研究

本研究将NRC-VAD v2.1中的九个情绪名词与DREAMER中九类影片诱发VAD对齐，回答以下问题：（1）V、A、D各自是否呈现跨情境类别对应；（2）两套坐标的全局压缩和平移程度如何；（3）去除全局映射后，哪些情绪仍具有较大类别特异残差；（4）探索EEG/ECG特征——特别是FAA——是否与个体层面的VAD偏差有关。研究属于跨样本、类别级探索性二手数据分析，不检验个体内等价，也不判断哪一套VAD”更真实”。

## 2. 方法

### 2.1 数据来源

DREAMER v1.0.2包含23名参与者观看18段影音刺激时记录的EEG与ECG，以及每段刺激后的1-5分Valence、Arousal和Dominance自评。18段影片覆盖九个目标情绪，每类两段，共414个完整试次。NRC-VAD v2.1提供大规模英文词项的VAD常模。本研究使用与DREAMER目标类别同名的九个英文名词；对应状态形容词作为敏感性分析。

### 2.2 对齐与量尺

DREAMER评分使用 `(score - 3) / 2` 映射至[-1, 1]。在参与者与情绪内平均该类两段影片，随后在参与者间估计类别质心。核心相关的有效样本为九类情绪，而不是414个试次。

### 2.3 统计分析

主分析分别计算各维度的Pearson相关和Spearman秩相关。通过枚举九个类别标签的全部362,880种排列计算双侧精确p值，并分别对三条维度检验执行Holm校正。参与者和每类中的两段影片同时有放回重抽5,000次，用于估计DREAMER类别质心导致的相关、斜率和残差区间。

整体三维结构使用轴保持的标准化构型一致性：在两套数据中分别标准化V、A、D后，计算对应坐标向量的congruence。该指标不允许旋转坐标轴，避免用Valence和Arousal的线性组合人为提高拟合。

为描述量尺差异，逐维拟合 `DREAMER = intercept + slope x NRC`。为估计类别特异性偏离，对每个情绪使用其余八类拟合上述映射，再预测被留出的类别，并计算预测残差的VA和VAD欧氏长度。逐一删除情绪类别检查相关影响。名词/形容词和Dominance正向/反向编码均作敏感性分析。

### 2.4 探索性生理分析

从每段刺激及其基线的末60秒提取EEG theta、alpha、beta相对功率、额叶alpha不对称，以及ECG心率、RMSSD和SDNN变化。试次级模型控制18段影片固定效应，标准误按参与者聚类，并做Holm校正。该模型检验同一影片内个体差异，不将生理特征解释为客观VAD。

## 3. 结果

### 3.1 维度层面对齐

Valence呈现强相关，Pearson `r=.875`，精确 `p=.0061`，Holm校正 `p=.0184`，双层bootstrap 95% CI `[.762, .920]`；Spearman `rho=.895`，校正 `p=.0067`。删除任一类别后Pearson相关保持在`.848-.922`，说明该结果不依赖单一情绪。

Arousal的Pearson相关为`r=.832`，精确`p=.0169`，校正`p=.0339`，bootstrap 95% CI `[.370, .913]`；但Spearman `rho=.433`，校正`p=.500`。删除单一类别后的Pearson相关范围为`.482-.898`。这表明A保留总体线性关系，但具体类别顺序和效应大小较不稳定。

Dominance未呈现对应，Pearson `r=-.121`，校正`p=.792`，bootstrap 95% CI `[-.432, .280]`；Spearman `rho=-.417`，校正`p=.500`。删除单类后的相关范围为`-.574-.049`。反向编码只改变符号，不改善证据强度。

### 3.2 整体构型与量尺压缩

轴保持的三维构型一致性为`C=.529`，单侧精确置换`p=.0058`，bootstrap 95% CI `[.299, .651]`。因此两套空间整体上比随机标签更相似，但该结论不能替代逐维结果。

NRC到DREAMER的斜率为V `.520`（95% CI `[.423, .611]`）、A `.341`（`[.184, .501]`）和D `-.055`（`[-.272, .159]`）。V与A的斜率明显低于单位斜率，说明诱发类别均值的范围更集中。

### 3.3 校准后的类别残差

LOEO校准后的VAD残差依次为excitement `.212`、fear `.283`、anger `.320`、amusement `.360`、sadness `.433`、disgust `.448`、happiness `.492`、surprise `.497`和calmness `.759`。calmness的区间为`[.538, 1.036]`，点估计最大；然而多数组别区间重叠较多，故该排序只用于生成后续假设。

### 3.4 生理结果

七项EEG/ECG特征（theta/alpha/beta相对功率、额叶alpha不对称FAA、心率、RMSSD、SDNN的基线变化）对个体VAD总体对齐距离的关联在Holm校正后均为`p=1.000`。在补充分析中，FAA与Dominance偏差的单独检验同样未达到显著水平。因此，当前粗粒度特征——包括理论上与Dominance相关的FAA——没有解释控制影片后的个体线性差异。该空结果不否定生理反应与情绪的关系：DREAMER的14通道低密度EEG、每类仅两段影片和末60秒平均化处理可能不足以捕捉FAA与Dominance之间的细粒度关联。此问题需要在更高密度EEG、更多刺激重复和更精准的Dominance测量的实验设计中重新检验。

## 4. 讨论

### 4.1 主要发现

本研究发现，词汇VAD向诱发体验的迁移不是“全部成立”或“全部失效”，而是明显依赖维度。Valence在精确检验、多重比较、双层bootstrap和逐类删除中均保持稳定，是当前最可靠的跨情境桥梁。Arousal保留线性趋势，但秩相关和影响分析显示其具体类别结构更容易受刺激集合影响。Dominance则没有出现可识别的跨情境对应。

### 4.2 Valence为何更稳定

一种谨慎解释是，正负性既是情绪词语义的主要组织原则，也是观看影片后最容易报告的体验属性。该结果支持词汇常模保存了真实诱发空间的一部分结构，但不证明两者绝对坐标相同。V的斜率仅约`.52`，说明即使类别顺序相似，体验均值仍明显不如词汇常模极端。

### 4.3 Arousal的线性对应与排序不稳定

Arousal的Pearson相关较高、Spearman相关较弱，说明类别大体沿同一方向变化，却不能稳定复现逐项排序。影片的节奏、声音、时长和情节强度可能影响诱发A；参与者和两段影片平均也会压缩极端值。calmness对A相关的影响尤其明显，因此未来复现需要增加低唤醒刺激并扩大每类刺激数量。

### 4.4 Dominance：概念参照、测量方向与生理关联

D的空对应不能证明Dominance是纯认知的、无生理基础的或无效的。更有限的解释是，两套任务中的D可能具有不同参照对象，且DREAMER原始SAM图示的方向仍需最终核验。词汇中的力量或控制联想、观看影片时自身的控制感、以及影片角色的支配性可能被混合。当前结果因此暴露的是测量可迁移性风险，而不是D的本体论答案。

一个理论上值得进一步检验的方向是额叶alpha不对称（FAA）与Dominance的关系。FAA长期与趋近/回避动机系统关联（Davidson, 1992; Harmon-Jones & Gable, 2018），左侧额叶活动增强被认为反映趋近倾向和掌控感——这些概念与Dominance（控制/支配感）有天然的理论交集。本文在DREAMER数据上对FAA与Dominance偏差的检验未发现显著关联，但DREAMER的14通道低密度EEG和每类仅两段影片的刺激设计限制了该检验的敏感性。在未来的A2同一参与者实验中，若设备条件允许，应在更高密度EEG下将FAA→Dominance作为预设的探索性假设，并在试次层面检验FAA变化是否特异性地追踪Dominance体验而非Valence或Arousal。

### 4.5 原始距离与校准残差必须分开

原始欧氏距离回答两套绝对坐标相隔多远；LOEO残差回答在允许整体平移和压缩后，某类是否仍异常。fear的原始距离较大但校准残差较小，说明其差异主要符合全局变换。calmness在校准后仍偏大，更像类别特异候选。两类指标回答不同问题，不能合并为单一“重合度排名”。

### 4.6 限制

首先，九个类别不足以支持对全部情绪空间的推广。其次，每类仅两段影片，使刺激和类别难以分离，bootstrap区间仍不能代表广泛刺激总体。第三，NRC与DREAMER来自不同样本和任务，任何差异都可能混合文化、样本、量尺和情境因素。第四，无法获得NRC原始评分者数据，词典坐标的不确定性未传播。第五，类别残差分析是探索性的，应在另一数据库或同被试实验中复现。

### 4.7 结论

词汇VAD常模能够保留诱发情绪体验的部分结构，但不能作为其无条件替代。Valence表现出最可靠的迁移，Arousal需要考虑范围压缩与类别构成，Dominance在跨任务使用前必须重新确认参照对象和计分方向。跨数据库研究应同时报告结构对应、全局尺度映射和类别特异残差，而不是仅凭共同的VAD标签假定测量等价。

## 5. 数据与透明度声明草稿

- **Data availability**：DREAMER与NRC-VAD受各自许可约束，原始数据不随仓库重新分发。分析脚本、派生统计表和不含受限原始内容的图表保存在项目仓库。
- **Ethics**：本研究为已公开或经许可获得数据的二次分析，不新增招募或干预；原始研究伦理信息应按DREAMER论文补充。
- **Conflict of interest**：作者声明无利益冲突。
- **Funding**：待填写。
- **Author contributions**：待按CRediT填写。
- **AI assistance disclosure**：研究设计整理、代码检查和文稿语言编辑使用了生成式AI辅助；所有分析决策、统计输出、文献核验和最终表述由作者负责复核。
