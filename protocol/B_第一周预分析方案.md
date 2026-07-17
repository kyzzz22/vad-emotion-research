# B方向第一周预分析方案

## 1. 研究定位

### 暂定题目

愉悦与恐惧刺激后的自主神经恢复轨迹及其个体一致性：基于CASE数据集的探索性分析

### 研究边界

- 本研究是公开数据二次分析，不进行新的人体数据采集。
- “恢复”指刺激结束后120秒内相对刺激前局部基线的生理变化。
- CASE蓝屏阶段的摇杆值主要为零，不能解释为连续的主观恢复报告。
- 刺激期间的主观Valence/Arousal用于描述前一情绪体验及解释后续生理恢复，不充当生理真值。
- 主要对比限定为amusing与scary，不推广为所有正性与负性情绪。

## 2. 研究问题

RQ1：amusing与scary视频之后，HR和SCL的120秒恢复轨迹是否不同？

RQ2：刺激末30秒的主观Arousal能否解释后续HR和SCL恢复幅度？

RQ3：同一个体在amusing与scary条件下的恢复特征是否具有跨条件一致性？

## 3. 数据与分析单位

- 数据：CASE，30名参与者，每人8个情绪视频，视频间隔120秒蓝屏。
- 主要条件：amusing（2个视频）与scary（2个视频）。
- 次要条件：boring与relaxed，仅用于描述和敏感性分析。
- 重复测量单位：trial；独立抽样层级：participant。
- 高频采样点和10秒bin不作为相互独立的样本。

## 4. 时间窗口

| 阶段 | 定义 | 用途 |
|---|---|---|
| local baseline | 情绪视频前蓝屏最后60秒 | 个体与trial局部校正 |
| stimulus end | 情绪视频最后30秒 | 反应幅度与主观体验 |
| recovery | 视频后蓝屏或endVid的0-120秒 | 主要恢复轨迹 |
| early recovery | 0-30秒 | 即刻残留 |
| middle recovery | 30-60秒 | 中段恢复 |
| late recovery | 90-120秒 | 晚期残留 |

每段恢复数据按10秒bin汇总。最后一个情绪视频后接endVid而非普通bluVid，该trial保留`recovery_is_endvid`标记，并在敏感性分析中排除。

## 5. 变量

### 主要结局

- `hr_delta_bpm`：每个恢复bin的平均HR减去局部baseline平均HR。
- `scl_delta_us`：每个恢复bin的平均SCL减去局部baseline平均SCL。

### 主要trial特征

- `reactivity`：刺激末30秒减去local baseline。
- `early_residual`：恢复0-30秒相对baseline的平均偏差。
- `late_residual`：恢复90-120秒相对baseline的平均偏差。
- `recovery_auc_abs`：120秒内绝对baseline偏差的时间积分。
- `recovery_slope`：恢复bin偏差对时间中点的普通最小二乘斜率。

`T50`不作为主要指标。它要求轨迹单调且真实跨越50%阈值，在噪声生理数据中可能大量缺失，仅在可识别trial中探索性报告。

### 刺激期解释变量

- 刺激末30秒连续主观Valence均值。
- 刺激末30秒连续主观Arousal均值。
- 视频类别、具体视频、呈现顺序。

## 6. 信号处理

### ECG与HR

1. 使用原始1000 Hz ECG。
2. 工程试跑采用5-20 Hz Butterworth带通、导数平方和150 ms移动积分检测候选QRS。
3. 在候选点附近回到带通信号定位R峰。
4. RR仅保留0.333-1.5秒（40-180 bpm），并记录有效RR比例。
5. 第一周算法用于验证数据链；第二周须抽查波形并与成熟工具实现交叉验证。

### EDA/SCL

1. 按CASE官方转换式：`SCL = 24 * GSR_voltage - 49.2`。
2. 第一周使用10秒bin均值分析tonic水平。
3. phasic分解不进入第一周主结果，第二周再决定是否加入。

## 7. 排除与质量规则

- 缺少完整前置蓝屏或后置恢复段的trial排除。
- HR bin少于5个有效心搏间期时设为缺失。
- trial有效RR比例低于80%时标记`hr_low_quality`，不自动删除原始记录。
- SCL非有限值或明显超出被试内分布时标记，阈值在全体QC后冻结。
- 普通bluVid和endVid恢复分别标记；主分析包含，敏感性分析排除endVid。
- 所有排除数量按participant、condition和video报告。

## 8. 计划模型

主要轨迹模型分别用于HR与SCL：

```text
delta ~ condition * time + condition * time^2
      + stimulus_end_arousal + presentation_order + recovery_is_endvid
      + (1 + time | participant)
```

若随机斜率模型不收敛，降级为participant随机截距，并报告降级原因。具体视频作为固定效应进行敏感性控制。

个体一致性分析：先在每名参与者内分别平均两个amusing和两个scary trial的AUC、slope及late residual，再计算Spearman相关和participant bootstrap 95%置信区间。该结果只解释为探索性跨条件一致性，不解释为稳定人格特质。

## 9. 预定图表

- 图1：CASE序列和baseline/stimulus/recovery窗口。
- 图2：amusing与scary条件的HR恢复曲线。
- 图3：amusing与scary条件的SCL恢复曲线。
- 图4：个体amusing-scary恢复特征散点图。
- 表1：样本、trial和QC。
- 表2：混合模型结果。
- 表3：个体一致性及bootstrap置信区间。

## 10. 第一周决策门

继续进入全体预处理，必须同时满足：

1. 240个情绪trial均能从官方序列和时长重建。
2. 被试1-2的ECG、GSR与annotation时间范围覆盖完整实验。
3. 每个情绪trial能连接前置baseline和后置recovery。
4. HR检测得到生理合理的中位值并通过波形抽查。
5. SCL在baseline、stimulus和recovery间可连续追踪。

若第4项失败，第二周优先改用BVP或成熟ECG工具；若蓝屏摇杆持续近零，则永久删除“主观恢复轨迹”表述。
