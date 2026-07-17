# VAD 情绪研究：词义、诱发体验与生理信号

本仓库用于持续记录和同步 VAD 情绪研究的研究设计、文献、数据分析、论文写作、实验材料和可视化工具。

## 当前研究主线

核心问题是：**情绪词的规范化 VAD 坐标，与影片诱发后参与者实际报告的 VAD 体验，在多大程度上共享结构，又在哪些维度和情绪类别上发生偏离？**

长期目标是在同一批参与者中比较三个层次：

1. 词义联想 VAD：看到情绪词时的直接判断。
2. 概念原型 VAD：对“典型处于该情绪的人”的判断。
3. 诱发体验 VAD：接受影片刺激后对当下体验的判断。

当前一个月研究采用公开数据库完成类别级探索性分析，主数据为 DREAMER，词义坐标来自 NRC-VAD v2.1；CASE 用于早期方法试跑和情绪恢复曲线支线验证。

## 当前主要发现

- **Valence**：NRC 与 DREAMER 的九类情绪结构高度对应，名词主分析 Pearson `r=.875`。
- **Arousal**：线性对应较强，但类别排序不稳定，诱发体验相对词义坐标存在明显压缩。
- **Dominance**：目前未发现可靠对应，需要继续核实评分方向、任务理解与构念差异。
- **距离解释**：原始三维距离混合了整体尺度压缩与情绪特异性偏离，因此同时报告留一情绪校准残差。
- **生理信号**：当前粗粒度 EEG/ECG 特征尚未稳定解释 VAD 对齐距离，该结果仅属于探索性空结果。

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

## 快速查看

### 阅读研究进展

- [研究进展报告](paper/研究进展报告_DREAMER_NRC.md)
- [论文数据前稿](paper/A2_论文数据前稿.md)
- [论文详细提纲](paper/A2_论文详细提纲.md)
- [审稿人视角评估](paper/A2_审稿人视角评估.md)
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
git clone <private-repository-url>
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

## 研究边界

当前结果属于跨样本、跨任务、九类情绪的探索性比较。它支持讨论情绪词与诱发体验的群体结构对应，但不能证明同一个人的词义判断能够预测其实际诱发体验，也不能据此断言 Dominance 是纯认知维度。

