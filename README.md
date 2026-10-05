# VAD 情绪研究：词义、诱发体验与生理信号

更新日期：2026-10-03。当前新增工作为 Dominance 测量含义的可行性验证；原三级 A2 方案保留为后续候选，尚未冻结。

本仓库用于持续记录和同步 VAD 情绪研究的研究设计、文献、数据分析、论文写作、实验材料和可视化工具。

## 已确定的研究顺序

先完成路线2（日语D测量含义与控制机会验证），再开展路线1（同人词义—体验比较）。路线3（解释／重评）暂由用户继续调查。详见[阶段验收计划](protocol/A2_研究顺序与阶段验收.md)。当前完成的是准备材料，尚无新访谈或实验数据。

## 当前研究主线

当前确定题目：

**感情語に対する意味的評価と映像によって喚起された情動体験とのVAD次元別対応関係の検討**

核心问题是：**情绪词的规范化 VAD 坐标，与影片诱发后参与者实际报告的 VAD 体验，在多大程度上共享结构，又在哪些维度和情绪类别上发生偏离？**

后续候选是在同一批参与者中比较三个层次；是否进入正式采集，先通过指令审计、认知访谈和预测试决策门槛：

1. 词义联想 VAD：看到情绪词时的直接判断。
2. 概念原型 VAD：对“典型处于该情绪的人”的判断。
3. 诱发体验 VAD：接受影片刺激后对当下体验的判断。

现有研究采用公开数据库完成类别级探索性分析，主数据为 DREAMER，词义坐标来自 NRC-VAD v2.1；CASE 用于早期方法试跑和情绪恢复曲线支线验证。

## 下一步：先验证可行性

- 固定自身评价对象，开放检查 D 的理解，包括情境控制、能力／力量、情绪调节及其他含义。
- 不把自身/人物评分不同直接当作测量失败，也不把更一致当作更有效。
- 暂缓扩大正式 A2 样本和新增生理采集；先产出指令审计、访谈编码、预测试结果及继续/转向决定。
- [文献调查与证据边界](literature/2026-09-28_Dominance评价对象与测量迁移_调查建议.md)
- [可行性验证与决策门槛](protocol/A2_可行性验证与决策门槛.md)

## 日语控制任务验证项目

当前以单一控制机会操纵为候选，暂不采用“外部控制×调节指令”2×2。

- [六周验证计划](protocol/A2_六周验证计划.md)
- [日语访谈稿](protocol/A2_日语访谈稿.md)
- [日语SAM来源核查](literature/A2_日语SAM来源核查.md)：已核对两份论文的问卷原页。
- [材料审阅与访谈执行卡](protocol/A2_材料审阅与访谈执行卡.md)：下一步的人员、步骤和决策规则。
- [两条件技术演练原型](experiment/control-pilot/README.md)：尚未实现表现匹配，评分不是SAM，不用于正式采集。

- [Google Forms日语表单完整搭建稿](materials/cognitive-interview/GoogleForms_日语访谈设计_v0.1.md)与[假设结果解读](materials/cognitive-interview/假设结果与决策示例.md)：模拟示例与实际数据严格分开。

## 已备好的下一步材料

- [评分指令审计（含待核实项）](literature/A2_评分指令审计.md)
- [认知访谈提纲与编码模板](protocol/A2_认知访谈提纲与编码.md)
- [导师讨论一页说明](paper/A2_导师讨论一页说明.md)

## 当前主要发现

- **Valence**：NRC 与 DREAMER 的九类情绪结构高度对应，名词主分析 Pearson `r=.875`。
- **Arousal**：线性对应较强，但类别排序不稳定，诱发体验相对词义坐标存在明显压缩。
- **Dominance**：目前未发现可靠对应，需要继续核实评分方向、任务理解与构念差异。
- **距离解释**：原始三维距离混合了整体尺度压缩与情绪特异性偏离，因此同时报告留一情绪校准残差。
- **生理信号**：当前粗粒度 EEG/ECG 特征尚未稳定解释 VAD 对齐距离，该结果仅属于探索性空结果。

稳健性复核进一步完成了全部 `9! = 362,880` 种类别置换、5,000 次参与者与影片双层 bootstrap 和逐类删除分析。Holm 校正后 Valence 与 Arousal 的 Pearson 对应仍显著，Dominance 不显著；但 Arousal 的秩相关和类别影响不稳定。

完整报告见：[研究进展报告](paper/研究进展报告_DREAMER_NRC.md)。

## 仓库结构

| 路径 | 内容 |
|---|---|
| `analysis/` | DREAMER、CASE、恢复曲线和计划实验的分析脚本 |
| `paper/` | 论文数据稿、详细提纲、评估、报告和汇报文件 |
| `literature/` | 文献矩阵、检索记录、综述与研究缺口 |
| `protocol/` | 正式实验、预测试、样本量和执行记录 |
| `experiment/` | 实验 Web 任务、配置和材料验证工具 |
| `materials/` | 情绪概念、评分项目、刺激清单和事件码 |
| `public_data/` | 数据获取说明及允许同步的派生汇总结果 |
| `visualization/` | DREAMER × NRC 的交互式 VAD 3D 模型 |
| `docs/` | 项目进展日志和数据管理政策 |
| `archive/` | 已停止维护但仍有方法和历史价值的旧研究分支 |

## 快速查看

### 阅读研究进展

- [研究进展报告](paper/研究进展报告_DREAMER_NRC.md)
- [论文数据前稿](paper/A2_论文数据前稿.md)
- [论文详细提纲](paper/A2_论文详细提纲.md)
- [审稿人视角评估](paper/A2_审稿人视角评估.md)
- [DREAMER × NRC-VAD 研究概要书](paper/DREAMER_NRC_研究概要书.md)
- [论文核心文本草稿](paper/DREAMER_NRC_论文核心文本草稿.md)
- [稳健性分析报告](results/dreamer_nrc_robustness/robustness_report_zh.md)
- [后续路线图](ROADMAP.md)

### 启动 3D VAD 模型

进入 `visualization/dreamer-vad-3d/`：

- macOS：双击 `start_demo.command`，或运行 `bash start_demo.command`。
- Windows：双击 `start_demo.bat`。
- 通用方式：运行 `python -m http.server 8765`，然后访问 `http://127.0.0.1:8765/`。

### 重新运行 DREAMER 分析

先按 [DREAMER 数据说明](public_data/licensed/dreamer/README.md) 获取并放置受限数据，再根据脚本参数运行：

```bash
python analysis/dreamer_nrc_pilot.py --help
```

NRC-VAD 原词典也需要由使用者根据官方许可自行下载。仓库不分发 DREAMER、CASE 原始信号或 NRC-VAD 完整词典。

## 跨平台同步

首次在另一台电脑使用：

```bash
git clone https://github.com/kyzzz22/vad-emotion-research.git
cd vad-emotion-research
```

日常同步：

```bash
git pull
git add -A
git commit -m "记录本次研究进展"
git push
```

原始数据需要在每台电脑单独获取和放置，不通过 GitHub 同步。具体边界见 [数据政策](docs/DATA_POLICY.md)。

## 历史研究分支

早期的“情绪词典坐标能否解释面部×声音融合标签”项目已停止独立维护，其分析代码、派生结果、图表、报告和实验预测保存在：

- [Multimodal Emotion Fusion 历史归档](archive/multimodal-emotion-fusion-2026/README.md)

该分支提供了语义 VAD 不能直接替代多模态感知空间的早期证据，但样本点少、部分共识率来自定性估算，因此不作为当前 DREAMER × NRC 论文的确认性结果。

## 研究边界

当前结果属于跨样本、跨任务、九类情绪的探索性比较。它支持讨论情绪词与诱发体验的群体结构对应，但不能证明同一个人的词义判断能够预测其实际诱发体验，也不能据此断言 Dominance 是纯认知维度。
