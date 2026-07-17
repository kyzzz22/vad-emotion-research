# 多模态情绪融合：研究进展记录（从规则表到连续函数）

本文件用于记录本项目从“查表式 7×7 离散规则”到“可学习、可解释的连续函数模型”的完整思考与实验路径。

---

## 0. 问题定义与数据

### 0.1 VA 表示
- 每个情绪标签用二维连续坐标表示：Valence（愉悦/正负向）与 Arousal（激活度）。
- 两个模态输入：
  - 表情：\(F=(v_f,a_f)\)
  - 语音：\(V=(v_v,a_v)\)
- 输出（查表/目标）：\(E=(v_{out},a_{out})\)

### 0.2 两套数据集（训练/验证协议）
- **Full49（7×7 原表）**：7 个基础情绪两两组合，共 49 个输出坐标，代表“查表规则”。
- **Selected14（红框 14 条）**：从 Full49 中选出的关键监督样本，用于“少样本拟合 → 反向验证能否泛化到 Full49”。

这套协议的核心意义：把“离散规则”视为可学习目标，检验连续模型是否能用少量监督捕捉规律并泛化。

---

## 1. Step 1：标量冲突建模（距离 conflict）

### 1.1 初始设想
用一个标量描述模态冲突：
\[
conflict=\sqrt{(v_f-v_v)^2+(a_f-a_v)^2}
\]
权重（语音权重）：
\[
w=\sigma(a\cdot conflict+b)
\]
融合（单权重）：
\[
E=(1-w)\cdot F + w\cdot V
\]

### 1.2 做了什么
- 将 (F,V) → 查表输出 E 转成回归训练对
- 拟合 \(a,b\) 让预测 VA 尽量接近查表 VA

### 1.3 发现的问题
- conflict 是“长度”，丢失“方向”。同样的距离可能对应非常不同的输出方向。
- 单一权重 \(w\) 只能在 VA 平面上沿 F→V 直线做单调插值，很难复现一些表格中的非对称行为。

结论：需要把冲突从标量升级为“带方向的差值”，并允许 Valence/Arousal 分开建模。

---

## 2. Step 2：双通道权重（Valence / Arousal 分开）

### 2.1 模型升级
将冲突向量化为两个差值：
\[
dV=v_v-v_f,\quad dA=a_v-a_f
\]
两条权重函数：
\[
w^V=\sigma(a_v\cdot dV+b_v),\quad w^A=\sigma(a_a\cdot dA+b_a)
\]
输出：
\[
v_{out}=v_f+w^V\cdot (v_v-v_f),\quad a_{out}=a_f+w^A\cdot (a_v-a_f)
\]

### 2.2 得到的改进
- 允许 Valence 与 Arousal 在同一对输入下采取不同“信任权重”，能解释“只在某个维度偏向语音/表情”的现象。
- 训练目标自然变成回归（MSE），参数可解释：
  - \(a\)：对差值的敏感度（冲突增大时权重变化快慢）
  - \(b\)：基线偏置（d=0 时默认信谁）

---

## 3. Step 3：训练流程标准化（Selected14 → Full49）

### 3.1 训练与评估
训练：用 Selected14 拟合参数  
验证：冻结参数，在 Full49（原 7×7 表）上评估 MSE / R²

### 3.2 可视化与诊断
常用图：
- true vs pred 拟合散点（Valence / Arousal 分开）
- 49 格误差热力图（pred-true + L2 误差幅值）
- 权重曲线（w vs dV、w vs dA），用于解释“机制”

产物已按阶段整理在 [report_assets](file:///Users/mac/Documents/trae_projects/jenish/report_assets)。

---

## 4. Step 4：线性模型下的机制枚举（a,b 符号四象限）

### 4.1 为什么做这一步
线性 sigmoid 模型是单调的，机制差异主要来自：
- \(a\) 的符号：权重随差值是增还是减（倾向语音 vs 倾向表情）
- \(b\) 的符号：d=0 时基线更信语音还是表情

### 4.2 四种情况（线性）
- ap_bp：\(a>0,b>0\)
- ap_bn：\(a>0,b<0\)
- an_bp：\(a<0,b>0\)
- an_bn：\(a<0,b<0\)

结论（机制层面）：
- 线性模型只能表达“谁一直主导 + 基线偏置”，无法表达“策略反转”。

对应结果与图：
- 线性四象限汇总图：  
  [step04_linear_cases4_metrics.png](file:///Users/mac/Documents/trae_projects/jenish/report_assets/_legacy_before_table14_holdout35/04_linear_cases4/step04_linear_cases4_metrics.png)

---

## 5. Step 5：引入二次项（\(d^2\)）尝试“策略反转”

### 5.1 模型形式
\[
w=\sigma(a_1 d + a_2 d^2 + b)
\]
其中 \(a_2\) 决定曲率，从而在形式上允许非单调。

### 5.2 转折点与“是否反转”的判别
由于 sigmoid 单调，是否出现非单调由
\[
z(d)=a_1 d + a_2 d^2 + b
\]
的导数决定。转折点：
\[
d^\*=-\frac{a_1}{2a_2}
\]
若 \(d^\*\) 落在有效数据覆盖范围，理论上可出现“策略反转”。

### 5.3 发现的问题
- 由于 Selected14 样本很少（两通道共 6 参数），\(a_2\) 容易吸收噪声形成“假曲率”。
- 多数情况下转折点靠近 0 或落在缺少支持的区间，导致“形式上非单调，但行为上不显著/不稳定”。

阶段性结论：
- 当前数据不足以支持“策略反转（冲突反转）”机制，需要额外设计高冲突样本才能严谨检验该假设。

对应图在：
- [05_extended_quad](file:///Users/mac/Documents/trae_projects/jenish/report_assets/_legacy_before_table14_holdout35/05_extended_quad)

---

## 6. Step 6：最终选型（\(|d|\)）表达“方向 + 强度”解耦

### 6.1 模型形式
\[
w=\sigma(a_1 d + a_2 |d| + b)
\]
解释：
- \(d\)：方向（谁更强、哪边更高）
- \(|d|\)：冲突强度（不一致程度）

它不强行制造“同一侧的反转”，但允许 \(d>0\) 与 \(d<0\) 两侧呈现不同敏感度（分段线性），更贴合“整体近似单调但存在方向不对称”的观测。

### 6.2 关键结果（Selected14 拟合 → Full49 验证）
本阶段重点选择 **abs + ap_bp（约束：\(a_1>0,\ b>0\)）** 作为主结果（用 Selected14 学到参数，泛化评估 Full49）。

- eval_full（Full49）：
  - MSE ≈ **0.0296**
  - R²_valence ≈ **0.883**
  - R²_arousal ≈ **0.930**

对应图（已重命名）：
- 训练拟合（Selected14）：  
  [step06_abs_ap_bp_fit_train_selected14.png](file:///Users/mac/Documents/trae_projects/jenish/report_assets/_legacy_before_table14_holdout35/06_extended_abs/step06_abs_ap_bp_fit_train_selected14.png)
- 泛化拟合（Full49）：  
  [step06_abs_ap_bp_eval_fit_full49.png](file:///Users/mac/Documents/trae_projects/jenish/report_assets/_legacy_before_table14_holdout35/06_extended_abs/step06_abs_ap_bp_eval_fit_full49.png)
- 泛化误差热图（Full49）：  
  [step06_abs_ap_bp_eval_err_full49.png](file:///Users/mac/Documents/trae_projects/jenish/report_assets/_legacy_before_table14_holdout35/06_extended_abs/step06_abs_ap_bp_eval_err_full49.png)
- 权重曲线（|d| 形状）：  
  [step06_abs_ap_bp_weights_curve.png](file:///Users/mac/Documents/trae_projects/jenish/report_assets/_legacy_before_table14_holdout35/06_extended_abs/step06_abs_ap_bp_weights_curve.png)
- Selected14 样本清单：  
  [step06_abs_ap_bp_selected14_samples.txt](file:///Users/mac/Documents/trae_projects/jenish/report_assets/_legacy_before_table14_holdout35/06_extended_abs/step06_abs_ap_bp_selected14_samples.txt)

### 6.3 当前达成的预期
- 用少量监督（Selected14）拟合出一套连续函数
- 反向验证能在 Full49 规则表上取得较强泛化表现
- 输出可解释的机制图（权重曲线与误差结构）

对应全部 abs 结果汇总在：
- [06_extended_abs](file:///Users/mac/Documents/trae_projects/jenish/report_assets/_legacy_before_table14_holdout35/06_extended_abs)

---

## 7. 参考上限：直接用 Full49 训练（不是泛化实验）

为了知道“理论上能拟合到什么程度”，也跑过 “直接用 full49 训练并评估 full49” 的结果（相当于上限参考，不代表 14→49 泛化能力）。

对应产物：
- [99_full49_train_baseline](file:///Users/mac/Documents/trae_projects/jenish/report_assets/99_full49_train_baseline)

---

## 8. 代码索引（复现实验）

- 线性双通道 + 四象限符号约束：  
  [train_dual_channel.py](file:///Users/mac/Documents/trae_projects/jenish/train_dual_channel.py)
- 扩展模型（linear/abs/quad）+ full49 评估 + 表格导出：  
  [train_dual_channel_extended.py](file:///Users/mac/Documents/trae_projects/jenish/train_dual_channel_extended.py)
- VA 空间可视化：  
  [va_visualize.py](file:///Users/mac/Documents/trae_projects/jenish/va_visualize.py)
- 表格可视化/对比：  
  [visualize_fv_table.py](file:///Users/mac/Documents/trae_projects/jenish/visualize_fv_table.py)  
  [compare_tables.py](file:///Users/mac/Documents/trae_projects/jenish/compare_tables.py)
- 其他早期探索脚本：  
  [target.py](file:///Users/mac/Documents/trae_projects/jenish/target.py)
- NRC 最近邻标签建议（候选集内重标注）：  
  [suggest_labels_from_nrc.py](file:///Users/mac/Documents/trae_projects/jenish/suggest_labels_from_nrc.py)

---

## 9. 下一步建议（可直接落地的实验）

1) **Baseline 对照**：固定权重（0/0.5/1）在 Full49 上报告同样指标，量化提升幅度。  
2) **稳健性检验**：对 Selected14 做 bootstrap/多 seed，统计参数方差与性能方差，评估结论稳定性。  
3) **反转机制的可证伪实验**：若要讨论 \(d^2\) 的策略反转，需要补充“高冲突密集采样”的监督样本，否则转折点解释不成立。  

---

## 10. 使用 NRC VAD Lexicon 的坐标系复现实验（更权威的坐标来源）

### 10.1 为什么要做这一步
之前实验中的 VA 坐标来自“手工设定/查表坐标”，可复现实验流程，但坐标来源说服力有限。  
因此引入 **NRC-VAD-Lexicon-v2.1** 作为更权威的情感维度来源，并将本项目原有 7×7 表通过“7 个基础情绪锚点”对齐到 NRC 坐标系。

### 10.2 坐标对齐方法（关键）
- NRC VAD 提供的是词条（term）级别的 VA（本仓库版本为带符号分数，范围约为 \([-1,1]\)）。
- 为 7 个基础情绪选择对应的词条作为锚点：
  - Happy→happy，Sad→sad，Angry→angry，Fear→fear，Disgusted→disgust，Surprised→surprise，Neutral→neutral
- 用 7 个锚点拟合一个二维仿射变换 \(T(\cdot)\)，使得：
  \[
  T(\text{old\_base}(e)) \approx \text{NRC}(e)
  \]
- 将该 \(T\) 同时作用于 full49 表内所有输出坐标，得到 NRC 对齐后的 full49 表。

NRC 锚点坐标（已导出）：
- [nrc_base7.txt](file:///Users/mac/Documents/trae_projects/jenish/report_assets/_legacy_before_table14_holdout35/07_nrc_vad_rerun/nrc_base7.txt)

### 10.3 训练/验证协议（14 → 35）
为了对应“用 14 个复杂情绪拟合 → 反向拟合剩余 35 个”的设定：
- 训练集（Table14）：选择 image.png 中那 14 个“复杂情绪”对应的 (F,V) 格子（Nervous/Excited/…/Impartial）
- 测试集：full49 的其余 35 格

本次运行采用最终模型：\(w=\sigma(a_1 d + a_2|d| + b)\)（abs），并使用 \(a_1>0,b>0\)（ap\_bp）约束。

### 10.4 结果与产物（NRC 坐标系）
运行日志（含参数与指标）：
- [run_log.txt](file:///Users/mac/Documents/trae_projects/jenish/report_assets/_legacy_before_table14_holdout35/07_nrc_vad_rerun/run_log.txt)

主要指标（from run_log）：
- train（Table14）：MSE≈0.01575，R²\_V≈0.9616，R²\_A≈0.9601
- eval\_full（NRC 对齐后的 Full49）：MSE≈0.04425，R²\_V≈0.9216，R²\_A≈0.8100
- holdout35（Full49 剩余 35 格）：MSE≈0.05567，R²\_V≈0.9088，R²\_A≈0.7019

可视化：
- 训练拟合散点（Table14）：  
  [fit_table14_nrc_affine_abs_B_bpos.png](file:///Users/mac/Documents/trae_projects/jenish/report_assets/_legacy_before_table14_holdout35/07_nrc_vad_rerun/fit_table14_nrc_affine_abs_B_bpos.png)
- Full49 拟合散点：  
  [eval_fit_table14_nrc_affine_abs_B_bpos.png](file:///Users/mac/Documents/trae_projects/jenish/report_assets/_legacy_before_table14_holdout35/07_nrc_vad_rerun/eval_fit_table14_nrc_affine_abs_B_bpos.png)
- Full49 误差热力图：  
  [eval_err_table14_nrc_affine_abs_B_bpos.png](file:///Users/mac/Documents/trae_projects/jenish/report_assets/_legacy_before_table14_holdout35/07_nrc_vad_rerun/eval_err_table14_nrc_affine_abs_B_bpos.png)
- holdout35 拟合散点：  
  [holdout_fit_table14_nrc_affine_abs_B_bpos.png](file:///Users/mac/Documents/trae_projects/jenish/report_assets/_legacy_before_table14_holdout35/07_nrc_vad_rerun/holdout_fit_table14_nrc_affine_abs_B_bpos.png)
- holdout35 误差热力图：  
  [holdout_err_table14_nrc_affine_abs_B_bpos.png](file:///Users/mac/Documents/trae_projects/jenish/report_assets/_legacy_before_table14_holdout35/07_nrc_vad_rerun/holdout_err_table14_nrc_affine_abs_B_bpos.png)
- 权重曲线：  
  [weights_table14_nrc_affine_abs_B_bpos.png](file:///Users/mac/Documents/trae_projects/jenish/report_assets/_legacy_before_table14_holdout35/07_nrc_vad_rerun/weights_table14_nrc_affine_abs_B_bpos.png)

用拟合函数生成的 7×7 预测坐标表（CSV）：
- [pred_table_table14_nrc_affine_abs_B_bpos.csv](file:///Users/mac/Documents/trae_projects/jenish/report_assets/_legacy_before_table14_holdout35/07_nrc_vad_rerun/pred_table_table14_nrc_affine_abs_B_bpos.csv)

---

## 11. 使用 NRC VAD 直接重建 Full49（不做仿射对齐）

### 11.1 目标与含义
“不做仿射对齐”的意思是：Full49 的每一格输出坐标不再继承旧表的数值（再整体变换），而是**直接由该格子的输出情绪词**在 NRC VAD Lexicon 中查得（或由词组/近义词规则聚合得到）。

这样构造出来的 Full49 具备更强的“坐标来源权威性”（每一格都能追溯到 NRC）。

### 11.2 构造方法
- 输入（F,V）的 7 个基础情绪锚点仍来自 NRC：happy/sad/angry/fear/disgust/surprise/neutral。
- Full49 每格输出对应 image.png 中的词：
  - 例如：Happy×Happy→Joyful，Happy×Sad→Nostalgic，Disgusted×Angry→Fed up，…，Neutral×Neutral→Impartial
- 对 NRC 中不存在的输出词，使用可解释的回退策略（近义词/词根形式），例如：
  - disillusioned→disillusionment
  - repulsed→repulsion
  - nauseated→nausea
  - grossed out→gross

### 11.3 实验：用 14 个复杂情绪拟合 → 预测其余 35 格
产物与日志位于：
- [report_assets/08_nrc_direct_rerun](file:///Users/mac/Documents/trae_projects/jenish/report_assets/_legacy_before_table14_holdout35/08_nrc_direct_rerun)
- 关键日志：[run_log.txt](file:///Users/mac/Documents/trae_projects/jenish/report_assets/_legacy_before_table14_holdout35/08_nrc_direct_rerun/run_log.txt)
- 四象限对比日志：[run_log_cases4.txt](file:///Users/mac/Documents/trae_projects/jenish/report_assets/_legacy_before_table14_holdout35/08_nrc_direct_rerun/run_log_cases4.txt)

单次运行（abs + ap\_bp）结果（from run_log）：
- train（Table14）：MSE≈0.2124，R²\_V≈0.3656，R²\_A≈0.7258
- eval\_full（Full49）：MSE≈0.3600，R²\_V≈0.4665，R²\_A≈0.3802
- holdout35：MSE≈0.4196，R²\_V≈0.4913，R²\_A≈0.2353

四象限机制枚举（abs cases4）中，当前最优（按 eval\_full MSE）约为：
- an\_bp：eval\_full MSE≈0.3216，R²\_V≈0.5621，R²\_A≈0.4055（仍明显弱于仿射对齐方案）

对比图：
- [compare_table14_abs_cases4.png](file:///Users/mac/Documents/trae_projects/jenish/report_assets/_legacy_before_table14_holdout35/08_nrc_direct_rerun/compare_table14_abs_cases4.png)

### 11.4 阶段性结论
当 Full49 的输出坐标完全由“词典定义的情绪词 VA”直接给出时，原先假设的低维连续融合规律（基于输入差值的权重函数）在 14→35 的泛化上显著变弱。  
这通常意味着：要么需要更丰富的监督样本，要么需要更灵活的模型（例如更强的非线性/类别依赖项），或者需要重新审视“词典词条 VA 与查表融合机制”之间是否存在系统性偏差。

---

## 12. NRC 对齐方案下的机制枚举（abs 四象限）与结论稳定性

### 12.1 为什么要再做四象限
在 NRC 对齐（nrc_affine）坐标系下，仍然需要验证“机制结论”是否依赖某个特定的参数符号假设。  
因此对 abs 模型做四象限枚举（ap\_bp/ap\_bn/an\_bp/an\_bn），并以 holdout35 为主评估泛化。

### 12.2 四象限结果（nrc_affine）
日志与对比图：
- [run_log_cases4.txt](file:///Users/mac/Documents/trae_projects/jenish/report_assets/_legacy_before_table14_holdout35/07_nrc_vad_rerun/run_log_cases4.txt)
- [compare_table14_abs_cases4.png](file:///Users/mac/Documents/trae_projects/jenish/report_assets/_legacy_before_table14_holdout35/07_nrc_vad_rerun/compare_table14_abs_cases4.png)

关键结论（以 holdout35 MSE 更小、更稳为准）：
- ap\_bn 在 holdout35 上最好（from run_log_cases4）：
  - holdout35：MSE≈0.05209，R²\_V≈0.9089，R²\_A≈0.7363
- an\_bn 次之：
  - holdout35：MSE≈0.05272，R²\_V≈0.9118，R²\_A≈0.7225

解释：
- 在 nrc_affine 坐标系里，abs 模型的泛化（尤其 Arousal）仍保持较好水平；这与 nrc_direct（词典直接重建 Full49）形成对照，说明“旧表内部结构”更符合低维连续融合假设。

---

## 13. 基于 NRC 的 7×7 标签优化（方案 A：候选集内最近邻重标注）

### 13.1 目标
给定模型生成的 7×7 输出坐标表（在 nrc_affine 坐标系），希望把“输出情绪标签”优化得更符合 NRC 词典中的几何位置。  
注意：此处优化的是 VA 几何一致性，不保证语义一定正确，需人工审阅。

### 13.2 方法（方案 A）
- 先固定“候选标签集合”为原 7×7 表的 49 个输出情绪词（Joyful/Nostalgic/…/Impartial）。
- 对每个格子的预测坐标 \(E_{pred}\)，在候选集合中找 NRC 坐标最近的词作为建议标签（nearest\_in\_49labels）。
- 设定阈值（本次为 dist\_49 < 0.12），只对“非常接近”的格子执行自动替换，避免大范围改名导致语义崩坏。

### 13.3 产物与本次阈值结果
目录：
- [report_assets/09_nrc_affine_label_opt](file:///Users/mac/Documents/trae_projects/jenish/report_assets/09_nrc_affine_label_opt)

本次用于生成坐标表的模型（nrc_affine + abs + ap\_bn）日志：
- [run_log.txt](file:///Users/mac/Documents/trae_projects/jenish/report_assets/09_nrc_affine_label_opt/run_log.txt)

输出：
- 7×7 预测坐标表（CSV）：  
  [pred_table_table14_nrc_affine_abs_B_bneg.csv](file:///Users/mac/Documents/trae_projects/jenish/report_assets/09_nrc_affine_label_opt/pred_table_table14_nrc_affine_abs_B_bneg.csv)
- 每格的 NRC 最近邻建议（全词典最近邻 + 候选49最近邻）：  
  [suggested_labels_from_nrc.csv](file:///Users/mac/Documents/trae_projects/jenish/report_assets/09_nrc_affine_label_opt/suggested_labels_from_nrc.csv)
- 阈值 dist\_49 < 0.12 的自动重标注结果（改动 23/49）：  
  [optimized_labels_7x7_dist012.csv](file:///Users/mac/Documents/trae_projects/jenish/report_assets/09_nrc_affine_label_opt/optimized_labels_7x7_dist012.csv)

### 13.4 阶段性提醒
在全词典（5 万+词条）中做最近邻会频繁命中非情绪词，因此本阶段只推荐使用“候选集内最近邻”或自定义“情绪词候选集”。

---

## 14. 报告资产统一整理（Table14 → Holdout35，nrc_affine）

### 14.1 目的
为了便于写报告与横向对比，将所有“模型形式 × case”可视化统一使用同一协议：
- 训练：Table14
- 测试：Holdout35（Full49 剩余 35 格）
- 坐标系：nrc_affine（旧表输出坐标仿射对齐到 NRC）

### 14.2 统一目录（主入口）
- [report_assets/10_table14_holdout35_nrc_affine](file:///Users/mac/Documents/trae_projects/jenish/report_assets/10_table14_holdout35_nrc_affine)

其中按模型形式分为 4 组：
- Simple Average（baseline）：[01_simple_average](file:///Users/mac/Documents/trae_projects/jenish/report_assets/10_table14_holdout35_nrc_affine/01_simple_average)
- Linear（cases4）：[02_linear](file:///Users/mac/Documents/trae_projects/jenish/report_assets/10_table14_holdout35_nrc_affine/02_linear)
- Quadratic（cases4）：[03_quadratic](file:///Users/mac/Documents/trae_projects/jenish/report_assets/10_table14_holdout35_nrc_affine/03_quadratic)
- Abs（cases4）：[04_abs](file:///Users/mac/Documents/trae_projects/jenish/report_assets/10_table14_holdout35_nrc_affine/04_abs)

每个目录都包含：
- `fit_*`（Table14 拟合散点）
- `holdout_fit_*` / `holdout_err_*`（Holdout35 拟合与误差热力图）
- `weights_*`（权重曲线）
- `pred_table_*`（对应 case 的 7×7 预测坐标表）
- `compare_*_cases4.png`（四象限指标对比图）

---

## 14. Baseline 对照与少样本稳定性检验

### 14.1 为什么补这一步
前面主要证明了“14 个监督样本能否拟合并泛化到 49 格规则表”。  
但要形成更稳的研究结论，还需要回答两个问题：

1) 可解释连续模型相比简单规则到底提升多少？  
2) 14 个样本是否太少，结论会不会对样本扰动非常敏感？

因此新增脚本：
- [analyze_model_evidence.py](file:///Users/mac/Documents/trae_projects/jenish/analyze_model_evidence.py)

输出目录：
- [10_model_evidence](file:///Users/mac/Documents/trae_projects/jenish/report_assets/10_model_evidence)

主要产物：
- [baseline_model_comparison.csv](file:///Users/mac/Documents/trae_projects/jenish/report_assets/10_model_evidence/baseline_model_comparison.csv)
- [stability_abs_ap_bn_nrc_affine.csv](file:///Users/mac/Documents/trae_projects/jenish/report_assets/10_model_evidence/stability_abs_ap_bn_nrc_affine.csv)
- [summary.md](file:///Users/mac/Documents/trae_projects/jenish/report_assets/10_model_evidence/summary.md)

### 14.2 Baseline 与模型对照
本次统一比较：
- 固定权重 baseline：face only、voice only、0.25/0.5/0.75 融合
- linear 四象限：ap\_bp/ap\_bn/an\_bp/an\_bn
- abs 四象限：ap\_bp/ap\_bn/an\_bp/an\_bn

统一评估：
- train14
- full49
- holdout35

关键结果（按 holdout35 MSE 排名）：

**native 坐标系**
- 最强 baseline 是 simple average：holdout35 MSE≈0.0148，R²\_V≈0.9506，R²\_A≈0.9460
- linear ap\_bp/ap\_bn 与 simple average 很接近

**nrc\_affine 坐标系**
- linear ap\_bn 最优：holdout35 MSE≈0.0509，R²\_V≈0.9102，R²\_A≈0.7439
- simple average 非常接近：holdout35 MSE≈0.0516，R²\_V≈0.9137，R²\_A≈0.7287
- abs ap\_bp/ap\_bn 仍能保持较好泛化，但本次排序中不再明显优于 linear/average

**nrc\_direct 坐标系**
- 最优仍明显更差：linear an\_bp 的 holdout35 MSE≈0.3592
- 这继续支持前面的判断：NRC 词典直接重建 Full49 后，低维融合结构明显变弱。

### 14.3 稳定性检验：nrc\_affine + abs + ap\_bn
对 nrc\_affine 下的 abs + ap\_bn 做了两类稳定性检验：
- bootstrap：对 14 个训练样本有放回重采样 80 次
- leave-one-out：每次去掉 1 个训练样本，共 14 次

结果摘要：
- leave-one-out 较稳定：
  - holdout35 MSE mean≈0.0591，sd≈0.0053
  - holdout35 R²\_V mean≈0.9052
  - holdout35 R²\_A mean≈0.6786
- bootstrap 波动较大：
  - holdout35 MSE mean≈0.1036，sd≈0.0571
  - holdout35 R²\_A 的 2.5% 分位数为负，说明 Arousal 通道在重采样下存在不稳定风险
  - 参数 \(a_2^A\) 波动尤其大，说明 abs 模型的强度项容易被少量样本牵动

### 14.4 新的写作结论
这一步让结论更清楚：

1) **低维连续融合结构确实存在**：native 与 nrc\_affine 都能用很简单的函数取得较好泛化。  
2) **simple average 是强 baseline**：论文/报告中不应只强调模型 MSE，而应强调机制可解释性、坐标系对照和误差结构。  
3) **nrc\_direct 是重要反证**：当每格输出完全来自词典词条 VA，14→35 泛化明显下降，说明词典几何与原规则表融合几何不是同一个东西。  
4) **abs 模型可解释，但稳定性需要谨慎**：\(|d|\) 项能表达“方向 + 强度”解耦，但在 14 样本下参数方差较大，适合写成机制候选，而不是过度宣称唯一最优模型。

因此，当前最稳妥的主叙事应调整为：

> 7×7 多模态情绪融合表的内部结构可以被低维连续融合函数近似重建；这种结构在 NRC 仿射对齐坐标系下仍然保留，但在 NRC 词典直接重建坐标系下显著减弱。模型价值主要体现在可解释机制与结构检验，而不仅是相对 simple average 的数值提升。

---

## 15. 完整中文报告整理

基于第 14 步的 baseline 对照和稳定性检验，已整理出一版中文主报告：

- [研究报告_中文版.md](file:///Users/mac/Documents/trae_projects/jenish/研究报告_中文版.md)

报告结构：
- Introduction：从离散规则表到连续函数的问题定义
- Method：VA 表示、Table14→Holdout35 协议、simple average、linear、abs 模型
- Experiments：native、nrc\_affine、nrc\_direct 三套坐标系
- Results：最佳方法对照、simple average/linear/abs 对照、稳定性检验
- Discussion：simple average 为什么强、nrc\_direct 为什么弱、abs 模型的价值与限制
- Conclusion：原规则表存在低维融合几何，但词典词条 VA 与规则表融合几何存在偏差

该报告已按新的写作口径处理：
- simple average 被定位为强参照基线，而不是弱 baseline
- nrc\_direct 被定位为“词典坐标不自动保留融合几何”的反证
- abs 模型被定位为机制扩展，不宣称稳定最优
- 标签优化被放在附加分析位置，不作为主线核心

---

## 16. nrc_direct 性能突破尝试：低维残差修正与半解释模型

### 16.1 为什么做这一步

前面的结果显示，nrc\_direct 下所有低维插值模型都明显变弱。  
为了确认问题是否只是“当前 linear/abs 权重函数不够好”，新增了一组 nrc\_direct 性能突破实验。

核心假设：

> 当前 linear/abs 模型只能在表情 F 与语音 V 的连线上插值，但 nrc\_direct 的目标点来自词典情绪词，很多目标可能并不在 F-V 线段附近。因此可以尝试加入低维残差修正，让输出离开 F-V 直线。

新增脚本：

- [analyze_nrc_direct_breakthrough.py](file:///Users/mac/Documents/trae_projects/jenish/analyze_nrc_direct_breakthrough.py)

输出目录：

- [report_assets/11_nrc_direct_breakthrough](file:///Users/mac/Documents/trae_projects/jenish/report_assets/11_nrc_direct_breakthrough)

### 16.2 新增模型

本次保持 Table14 -> Holdout35 协议，不使用测试格子的输出标签作为输入。

比较方法包括：

- 当前旧模型族：linear 四象限、abs 四象限
- residual\_ridge：在旧融合模型预测结果上学习低维残差修正
- feature\_ridge：使用 F、V、d、|d|、conflict 和简单交互项做正则化回归
- kernel\_residual：用 Table14 中相似输入组合的残差，对新样本做平滑修正

正则化参数与 kernel 参数只基于 Table14 的 leave-one-out 选择，没有用 Holdout35 调参。

### 16.3 几何诊断：目标点到 F-V 线段距离

新增诊断图：

- [segment_distance_diagnostics.png](file:///Users/mac/Documents/trae_projects/jenish/report_assets/11_nrc_direct_breakthrough/segment_distance_diagnostics.png)
- [segment_distance_diagnostics.csv](file:///Users/mac/Documents/trae_projects/jenish/report_assets/11_nrc_direct_breakthrough/segment_distance_diagnostics.csv)

关键数值：

- nrc\_direct 目标点到 F-V 线段的平均距离 ≈ **0.2552**
- 最大距离 ≈ **1.3900**
- 8/49 个目标点落在 F-V 线段外侧

距离最大的若干格子：

- Happy|Surprised：dist≈1.3900，raw t≈-2.4574
- Surprised|Sad：dist≈0.9529
- Surprised|Neutral：dist≈0.8150
- Neutral|Angry：dist≈0.8006，raw t≈-0.4340
- Disgusted|Angry：dist≈0.6016

这说明 nrc\_direct 中确实存在一些目标点远离“表情-语音插值线”的情况，因此单纯调整权重函数很难完全解决。

### 16.4 性能突破结果

模型对照表：

- [model_comparison.csv](file:///Users/mac/Documents/trae_projects/jenish/report_assets/11_nrc_direct_breakthrough/model_comparison.csv)
- [model_comparison_holdout35.png](file:///Users/mac/Documents/trae_projects/jenish/report_assets/11_nrc_direct_breakthrough/model_comparison_holdout35.png)

Holdout35 排名：

| rank | method | Holdout35 MSE | R²_V | R²_A |
|---:|---|---:|---:|---:|
| 1 | linear\_an\_bp | 0.3592 | 0.5370 | 0.3763 |
| 2 | kernel\_residual | 0.3639 | 0.5371 | 0.3613 |
| 3 | residual\_ridge | 0.3757 | 0.5221 | 0.3406 |
| 4 | abs\_an\_bp | 0.4044 | 0.5714 | 0.1938 |
| 11 | feature\_ridge | 2.1701 | -2.7705 | -1.6750 |

结论：

> 本次半解释残差模型没有突破旧的最佳 linear\_an\_bp。  
> 最好的新模型 kernel\_residual 只接近旧 best，但没有超过它。

### 16.5 最优新模型稳定性

最优新模型是 kernel\_residual，但仍未超过旧 linear\_an\_bp。

稳定性结果：

- [stability_kernel_residual_leave_one_out.csv](file:///Users/mac/Documents/trae_projects/jenish/report_assets/11_nrc_direct_breakthrough/stability_kernel_residual_leave_one_out.csv)

leave-one-out 摘要：

- holdout35 MSE mean≈0.3686，sd≈0.0170
- holdout35 R²\_V mean≈0.5336
- holdout35 R²\_A mean≈0.3503

说明 kernel\_residual 相对稳定，但性能没有达到突破标准。

### 16.6 本阶段结论

本次实验是一个有价值的负结果：

1. nrc\_direct 的弱表现不是简单由 abs/linear 权重函数太弱导致的。
2. 低维残差修正、正则化特征回归、相似样本残差平滑都没有明显改善 Holdout35。
3. nrc\_direct 的词典坐标很可能需要额外信息才能更好预测，例如输出语义、类别先验、更多训练样本，或更强但较不解释的模型。

因此，当前更稳的结论是：

> 在只使用 face/voice 基础情绪 VA 坐标、且只用 Table14 监督的条件下，nrc\_direct 的词典几何难以被当前低维输入空间解释。  
> 这进一步支持”词典词条情绪几何”和”多模态融合表几何”之间存在系统性差异。

---

## 17. NRC 仿射标签解释（nrc_affine 坐标 + NRC 最近邻）

### 17.1 目的

在已确定 nrc_affine 为建模主线的前提下，对 nrc_affine 坐标附近的 NRC 候选情绪词做标签一致性审查。  
核心原则：不自动改标签，只标注”原标签与 VA 几何是否一致”。

新增脚本：
- [analyze_nrc_affine_label_interpretation.py](file:///Users/mac/Documents/trae_projects/jenish/analyze_nrc_affine_label_interpretation.py)

输出目录：
- [report_assets/12_nrc_affine_label_interpretation](file:///Users/mac/Documents/trae_projects/jenish/report_assets/12_nrc_affine_label_interpretation)

### 17.2 主要产物与结论

一致性分类（49 格，按原标签至 nrc_affine 坐标的距离）：
- aligned（dist ≤ 0.20）：5 格
- weakly_aligned（0.20 < dist ≤ 0.35）：13 格
- review（dist > 0.35）：31 格

关键统计：
- 原标签平均距离：0.5173
- 原标签距离中位数：0.4610
- 原标签最大距离：1.4434（Happy|Surprised = Calm）

代表性案例：
- Happy|Surprised 原标签 Calm，dist=1.443，附近候选 Amused/Amazed/Excited（高 V 高 A 情绪词群）
- 说明 Calm 与 nrc_affine 坐标在 VA 空间中差异显著，适合复查

### 17.3 定位

NRC 最近邻不是自动改名工具，而是：
1) 检查原标签与当前 VA 几何是否一致
2) 人工审阅标签的辅助依据
3) 后续优化 7×7 表标签集的起点

---

## 18. 7×7 源表审查与最终文件整理

### 18.1 源表审查矩阵

针对 7×7 原始标签表，生成了多维审查矩阵：

脚本：
- [generate_source_table_review.py](file:///Users/mac/Documents/trae_projects/jenish/generate_source_table_review.py)
- [generate_source_table_review_pngs.py](file:///Users/mac/Documents/trae_projects/jenish/generate_source_table_review_pngs.py)

输出目录：
- [report_assets/14_source_table_review](file:///Users/mac/Documents/trae_projects/jenish/report_assets/14_source_table_review)

主要文件：
- `source_table_7x7_matrix.md`：原始 7×7 标签矩阵
- `label_alignment_review_matrix.md`：NRC 一致性 7×7 矩阵
- `label_alignment_review_summary.md`：标签一致性数量统计和 top review 候选
- `error_based_review_top15.md`：nrc_direct 误差最大的 15 个格子
- `error_priority_matrix.md`：误差复查优先级 7×7 矩阵

### 18.2 文件清理与项目整理（2026-05-11）

**PPT 版本清理**：
- 最新版保留：`ppt/汇报ppt 日语版本 3_三坐标最终版.pptx`（29 页，主線已改为三坐标对比）
- 9 個旧版移至 `_archive/old_ppts/`

**過時腳本清理**：
- `patch_ppt3_*.py`（5 個臨時修補腳本）→ `_archive/old_scripts/`
- `generate_*_ppt.mjs`（4 個旧版 PPT 生成腳本）→ `_archive/old_scripts/`
- `generate_progress_ppt.py` → `_archive/old_scripts/`

**新增文件**：
- [汇报ppt_日语版本_3_最終修改建議_2026-05-11.md](汇报ppt_日语版本_3_最終修改建議_2026-05-11.md)：基於實際 PPT 內容的逐頁修改建議
- [汇报ppt_日语讲稿.md](汇报ppt_日语讲稿.md)：已更新為匹配 33 頁新版 PPT 的完整日語講稿（含質疑応答想定）

### 18.3 当前文件索引（精簡後）

**研究记录**：
- `research_progress.md`：完整实验过程记录（本文件）
- `研究报告_中文版.md`：正式中文论文草稿
- `研究报告_日本語版.md`：日語版論文草稿
- `notion_研究进展自我记录.md`：白話版自我記錄
- `notion_latest_update_2026-05-06.md`：最新主線整理

**PPT相關**：
- `ppt/汇报ppt 日语版本 3_三坐标最终版.pptx`：唯一保留的最新版
- `汇报ppt_日语版本_3_最終修改建議_2026-05-11.md`：逐頁修改建議
- `汇报ppt_日语讲稿.md`：新版 15-20 分講稿
- `ppt3_修改优化建议_2026-05-06.md`：旧版优化建议（参考用）
- `汇报ppt_优化补充内容_2026-05-06.md`：旧版补充文案（参考用）

**核心實驗腳本**：
- `train_dual_channel.py`：線性雙通道 + 四象限基礎訓練
- `train_dual_channel_extended.py`：擴展模型（linear/abs/quad）+ full49 評估
- `analyze_model_evidence.py`：baseline 對照 + 穩定性檢驗
- `analyze_nrc_direct_breakthrough.py`：nrc_direct 突破嘗試 + 線段距離診斷
- `analyze_nrc_affine_label_interpretation.py`：NRC 最近鄰標籤解釋
- `generate_source_table_review.py`：7×7 源表審查矩陣
- `summarize_table14_holdout35_results.py`：Table14 Holdout35 結果匯總
- `make_coord_compare_3coords.py`：三坐標系比較

**關鍵結果目錄**：
- `report_assets/10_model_evidence`：baseline 對照和穩定性檢驗
- `report_assets/11_nrc_direct_breakthrough`：nrc_direct 突破嘗試
- `report_assets/12_nrc_affine_label_interpretation`：NRC 最近鄰標籤解釋
- `report_assets/14_source_table_review`：7×7 源表審查

---

## 19. 下一步行動清單（2026-05-11 更新）

### 本周必須完成
- [ ] 根據 `汇报ppt_日语版本_3_最終修改建議_2026-05-11.md` 修改 PPT
  - [ ] 修正 Slide 24, 27 的數值錯誤
  - [ ] 填補 Slide 21 空白頁
  - [ ] 充填 Slide 20, 22 內容
  - [ ] 新增 nrc_direct 追加實驗頁
  - [ ] 新增 F-V 線分距離診斷頁
  - [ ] 新增 NRC 最近傍標籤解釋頁
  - [ ] 新增安定性検証頁
  - [ ] 拡充結論頁
- [ ] PPT 修改完成後，對照新版講稿練習一次（15-20分）

### 中期
- [ ] review 候補セル 31 個を人工的に確認
- [ ] nrc_direct の誤差上位 15 セルを事例分析
- [ ] 必要に応じてラベル候補リストを再設計

### 長期
- [ ] 日本語 / 英語で論文原稿を作成
- [ ] NRC 以外の辞書や実データで再検証
- [ ] 追加サンプルで abs の安定性を再検証
