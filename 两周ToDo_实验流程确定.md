# 两周 ToDo：确定虚拟 AI 面试压力任务实验流程

## 总目标

接下来两周的目标不是完成整个研究，而是锁定一个可执行、可向老师说明、可进入 pilot study 的最小可行实验流程。

当前最终收窄方向：

```text
大学生虚拟 AI 面试任务后的多模态生理恢复过程个体差异量化
```

核心任务：

```text
确定虚拟 AI 面试任务形式
确定中性说话对照任务
确定 trial 结构
确定主观评分项目
确定 MyBeat 与 Muse 指标
确定 recovery 阶段动态特征
确定 pilot 检查流程
```

## 第 1 阶段：锁定研究设计，第 1-2 天

- [ ] 确定最终题目暂定版。
- [ ] 确定研究问题 RQ1-RQ5。
- [ ] 确定研究对象：健康大学生 / 研究生。
- [ ] 确定实验情境：实验室内标准化虚拟 AI 面试任务。
- [ ] 确定主条件：中性说话任务 vs 虚拟 AI 面试压力任务。
- [ ] 确定主分析窗口：回答结束后的 recovery 阶段。
- [ ] 明确回答阶段不作为 EEG 的主要解释窗口。
- [ ] 决定暂时不做复杂实时 AI 交互、Transformer、复杂情绪预测。

建议题目：

```text
大学生虚拟 AI 面试任务后的多模态生理恢复过程个体差异量化
——基于个体 baseline 校正的心拍与 EEG 指标分析
```

建议研究问题：

```text
RQ1：
与中性说话任务相比，虚拟 AI 面试压力任务是否引起更明显的心拍与 EEG 反应及恢复过程变化？

RQ2：
虚拟 AI 面试任务后，不同个体在恢复速度和残留反应上是否存在差异？

RQ3：
这些个体差异是否可以通过反应强度、峰值时间、恢复速度、残留反应和模态差异等动态特征进行量化？

RQ4：
这些动态特征是否与主观 stress、arousal、evaluation threat、confidence 评分相关？

RQ5：
心拍相关指标与 EEG 指标在虚拟 AI 面试任务后的恢复过程中是否表现出不同时间模式？
```

## 第 2 阶段：设计任务材料，第 3-5 天

- [ ] 设计中性说话任务问题 6-8 个。
- [ ] 设计 AI 面试压力任务问题 6-8 个。
- [ ] 确保两类任务问题长度相近、回答时间一致。
- [ ] 确保中性任务无明显评价威胁。
- [ ] 确保面试任务具有自我表现和评价压力，但不过度冒犯。
- [ ] 决定正式 pilot 中每类使用的问题数量：建议每类 3-5 个。

中性说话任务问题示例：

```text
请用一分钟描述你今天来实验室的路线。
请用一分钟描述你平时使用的学习工具。
请用一分钟描述一个普通的教室或图书馆。
请用一分钟说明你平时如何整理书包或电脑文件。
```

AI 面试压力任务问题示例：

```text
请用一分钟介绍你自己。
请说明你最大的弱点。
请说明一次失败经历，以及你如何应对。
为什么我们应该选择你？
如果你在团队中被否定，你会怎么处理？
```

任务材料记录表建议字段：

```text
问题编号
条件
问题文本
预计难度
评价威胁程度
自我相关程度
伦理风险
备注
```

## 第 3 阶段：设计虚拟 AI 面试呈现方式，第 6 天

- [ ] 决定使用 Level 1 或 Level 2 方案。
- [ ] 准备虚拟面试官头像或简单界面。
- [ ] 准备问题呈现页面。
- [ ] 准备计时器提示。
- [ ] 准备评价压力提示语。
- [ ] 准备中性任务说明语。

推荐先采用 Level 1 或 Level 2：

```text
Level 1：
屏幕显示虚拟面试官头像 + 文字问题 + 计时器。

Level 2：
预录 AI 音声读问题 + 虚拟头像 + 计时器。

Level 3：
实时语音识别 + LLM 追问 + 自动反馈。
当前阶段不建议采用。
```

AI 面试压力提示语：

```text
你的回答将用于分析面试场景中的表达方式和应答内容。
请尽量像真实面试一样回答。
```

日文版：

```text
あなたの回答は、面接場面における話し方や応答内容の評価研究に使用されます。
できるだけ実際の面接のつもりで回答してください。
```

伦理边界：

```text
回答过程可能被记录用于实验分析，但不会对个人能力作出实际评价。
```

## 第 4 阶段：设计 Pilot 检查，第 7-8 天

- [ ] 确定 pilot 人数：3-5 名即可起步。
- [ ] 检查中性任务与面试任务的主观 stress 差异。
- [ ] 检查面试任务是否引发足够 evaluation threat。
- [ ] 检查问题是否过难、过尴尬或过度冒犯。
- [ ] 检查回答后 recovery 期间是否能保持安静不动。
- [ ] 检查 Muse 与 MyBeat 数据是否可同步和可记录。

pilot 后评分项目：

```text
stress：1-9
arousal：1-9
valence：1-9
evaluation threat：1-9
confidence：1-9
self-relevance：1-9
任务真实感：1-9
```

筛选标准：

```text
面试压力任务的 stress 与 evaluation threat 应高于中性任务。
问题不能引起过度不适或伦理风险。
中性任务不应明显引发压力。
回答后 recovery 阶段参与者能够保持相对静止。
```

## 第 5 阶段：确定正式实验流程，第 9-10 天

- [ ] 确定每个 trial 的结构。
- [ ] 确定 pre-baseline：60 秒。
- [ ] 确定问题呈现：15 秒。
- [ ] 确定回答准备：30 秒。
- [ ] 确定口头回答：60 秒。
- [ ] 确定 recovery：120 秒。
- [ ] 确定主观评分：20-30 秒。
- [ ] 确定 trial 间休息：60 秒。
- [ ] 确定总 trial 数：6-10 个起步。
- [ ] 检查总实验时长是否可接受。

建议 trial 结构：

```text
pre-baseline：60 秒
问题呈现：15 秒
回答准备：30 秒
口头回答：60 秒
recovery：120 秒
主观评分：20-30 秒
trial 间休息：60 秒
```

建议总量：

```text
最低：中性 3 trial + 面试压力 3 trial = 6 trial。
较好：中性 5 trial + 面试压力 5 trial = 10 trial。
```

主分析窗口：

```text
pre-baseline
anticipation / preparation
recovery early：0-30 秒
recovery middle：30-60 秒
recovery late：60-120 秒
```

## 第 6 阶段：确定测量与预处理，第 11 天

- [ ] 确定 MyBeat 指标：RRI / HR / RMSSD / pNN50 / activity。
- [ ] 确定 Muse 指标：alpha / beta / beta-alpha ratio。
- [ ] 确定主观评分：stress / arousal / valence / evaluation threat / confidence。
- [ ] 写出 RRI 异常值排除规则。
- [ ] 写出 EEG artifact 处理原则。
- [ ] 明确回答阶段不作为 EEG 主解释窗口。
- [ ] 确定 baseline 校正方式：delta 或 z-score。

MyBeat 指标：

```text
RRI
HR
RMSSD
pNN50
activity
```

Muse S Gen2 指标：

```text
EEG alpha power
EEG beta power
beta / alpha ratio
信号质量指标，如果可导出
```

RRI 异常值规则草案：

```text
RRI < 400 ms 或 RRI > 1500 ms
局部中位数偏离过大的点
```

baseline 校正：

```text
delta = phase_value - baseline_value
```

或：

```text
z = (phase_value - baseline_mean) / baseline_sd
```

## 第 7 阶段：确定动态特征与分析框架，第 12 天

- [ ] 定义 Stress Reactivity。
- [ ] 定义 Peak Latency。
- [ ] 定义 Recovery Slope。
- [ ] 定义 Residual Activation。
- [ ] 定义 Modality Dominance。
- [ ] 定义 Subjective-Physiological Gap。
- [ ] 定义 Consistency Index。
- [ ] 确定可视化方式：每个被试、每个条件的 recovery 轨迹图。
- [ ] 确定主观评分相关分析方式。

动态特征定义：

```text
Stress Reactivity：
压力任务相对 baseline 的最大变化量或平均变化量。

Peak Latency：
任务开始或回答结束后达到最大变化的时间。

Recovery Slope：
回答结束后向 baseline 回归的速度或斜率。

Residual Activation：
recovery late 阶段仍然偏离 baseline 的程度。

Modality Dominance：
心拍反应和 EEG 反应哪个更明显。

Subjective-Physiological Gap：
主观压力评分与生理反应强度之间的不一致程度。

Consistency Index：
同一条件下个体反应模式是否稳定。
```

主分析：

```text
每个被试、每个 trial 的 recovery 轨迹可视化
中性 vs AI 面试压力任务的动态特征比较
个体间恢复速度与残留反应差异比较
动态特征与主观 stress / evaluation threat / confidence 的相关分析
```

## 第 8 阶段：准备给老师汇报，第 13-14 天

- [ ] 整理 6-8 页 PPT。
- [ ] 第 1 页：研究背景与问题。
- [ ] 第 2 页：为什么选择 AI / 虚拟面试压力任务。
- [ ] 第 3 页：研究目的与研究问题。
- [ ] 第 4 页：实验条件：中性说话 vs AI 面试压力。
- [ ] 第 5 页：正式 trial 流程。
- [ ] 第 6 页：测量指标与主观评分。
- [ ] 第 7 页：recovery 动态特征。
- [ ] 第 8 页：预期贡献与当前边界。

建议流程图：

```text
任务材料设计
↓
pilot 检查压力强度
↓
正式实验
↓
MyBeat + Muse 同步记录
↓
回答后 recovery 分析
↓
baseline 校正
↓
动态特征提取
↓
个体差异量化
↓
与主观评分关系分析
```

## 两周后应完成的成果

- [ ] 研究题目暂定版。
- [ ] 更新版开题报告草稿。
- [ ] 研究问题 RQ1-RQ5。
- [ ] 中性说话任务问题列表。
- [ ] AI 面试压力任务问题列表。
- [ ] 虚拟面试界面方案。
- [ ] pilot 评分表。
- [ ] 正式实验流程图。
- [ ] 测量指标列表。
- [ ] 预处理规则草案。
- [ ] recovery 动态特征定义表。
- [ ] 给老师汇报用 PPT。

## 优先级最高的 5 件事

1. 确定中性说话任务和 AI 面试压力任务的问题列表。
2. 确定虚拟 AI 面试的呈现方式。
3. 设计 pilot，确认压力任务是否真的提高 stress / evaluation threat。
4. 确定正式 trial 流程，尤其是 recovery 120 秒。
5. 明确回答阶段不作 EEG 主解释，主分析聚焦 recovery。

## 当前边界

当前两周内不扩展以下内容为主线：

- 复杂实时 AI 对话。
- LLM 自动追问。
- Transformer 主模型。
- 复杂情绪预测。
- 七种基础情绪分解。
- 行为日志。
- 更多传感器融合。

当前核心任务是：

```text
把虚拟 AI 面试压力任务、对照任务、recovery 分析窗口和动态特征定义锁定下来。
```

