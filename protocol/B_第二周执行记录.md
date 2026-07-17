# B方向第二周执行记录

记录日期：2026-07-15

## 1. 第二周结论

第二周七项任务已完成：成熟ECG工具交叉验证、30人全样本预处理、ECG/EDA质控、个体及总体曲线、简化混合模型、三项预设敏感性分析和跨条件个体一致性分析均已形成可复现产物。

目前证据最强的是SCL：scary刺激后SCL相对局部基线的升高明显大于amusing，并在120秒内缓慢缩小。HR也存在条件平均差异，但恢复形状不如SCL稳定。刺激末主观Arousal的系数不能通过全部敏感性检验，因此RQ2暂不支持。个体一致性方面，SCL的绝对恢复AUC和恢复斜率有中等正相关；HR绝对AUC没有可靠跨条件一致性。

所有结果均限定于CASE数据集中amusing与scary视频，不推广为所有正负情绪，也不解释为因果效应。

## 2. 完成情况

| 第二周任务 | 证据 | 判定 |
|---|---|---|
| 成熟ECG工具交叉验证 | `ecg_heartpy_validation.csv` | 通过 |
| 全30人预处理 | 240 trial、2880 bin | 通过 |
| ECG/EDA质控 | `participant_signal_qc.csv` | 通过，P17保留审查标记 |
| 个体与总体曲线 | 3张曲线图及bootstrap CI表 | 通过 |
| 简化混合模型 | 7个MixedLM全部无警告收敛 | 通过 |
| 三项预设敏感性分析 | endVid、previous condition、within-person z | 通过 |
| 个体一致性 | 6个指标、participant bootstrap、BH-FDR | 通过 |

## 3. ECG交叉验证

正式处理使用第一周工程检测器，但在冻结规则前，用HeartPy独立检测完整记录并进行峰级匹配。HeartPy方法依据van Gent等人的同行评议算法论文（DOI：10.1016/j.trf.2019.09.015）。

| 参与者 | 工程检测峰数 | HeartPy峰数 | 工程峰匹配率 | HeartPy峰匹配率 | 匹配峰中位差 |
|---|---:|---:|---:|---:|---:|
| P1 | 3083 | 3086 | 100.00% | 99.90% | 0 ms |
| P2 | 2659 | 2660 | 100.00% | 99.96% | 0 ms |

预设门槛为两侧匹配率均不低于98%，因此通过。全样本HR中位数范围为54.25–85.71 bpm，最低有效RR比例为99.66%；每个10秒恢复箱至少有7个有效RR，没有trial触发`hr_low_quality`。

NeuroKit2 0.2.13虽已安装，但其依赖的下载版scikit-learn DLL被本机Windows应用控制策略阻止加载，因此没有把NeuroKit2写成已运行工具，也没有绕过系统策略。最终使用可正常运行且有方法论文支持的HeartPy。

## 4. 全样本与质控

| 层级 | 数量 |
|---|---:|
| 参与者 | 30 |
| 全部情绪trial | 240 |
| 主分析trial（amusing/scary） | 120 |
| 全部10秒恢复箱 | 2880 |
| 主分析恢复箱 | 1440 |
| 主结局缺失箱 | 0 |
| 参与者排除 | 0 |

EDA原始信号用于异常审计，正式SCL窗口值采用“每秒中位数，再在分析窗内求均值”，降低极少数单采样点跳变的影响。全样本最大大跳变比例为0.0145%，没有参与者超过0.1%的审查阈值。P17首尾60秒中位SCL相差-26.62 uS，保留`eda_qc_flag`，但局部基线设计能够降低全程漂移影响；剔除P17后的SCL结果单独复算。

P17不被自动排除的原因是：信号有限值比例合格、异常点比例极低、每个分析窗均有数据，而且预先定义的是局部trial基线。将其保留并报告剔除敏感性比事后直接删除更严谨。

## 5. 总体恢复曲线

总体曲线使用参与者作为bootstrap单位，重复2000次，避免把1440个时间箱当作独立样本。

- scary的SCL在第5秒为+10.44 uS（95% CI 7.94–13.04），第115秒仍为+8.10 uS（6.07–10.26）。
- amusing的SCL在第5秒为+0.46 uS（-1.07–1.99），第115秒为+1.03 uS（-0.25–2.30）。
- HR两条件的逐点置信区间更宽，且轨迹非单调，提示HR恢复的trial与个体差异较大。

这些逐点区间用于描述曲线，不替代混合模型推断。

## 6. 混合模型结果

主模型为参与者随机截距加时间随机斜率：

```text
delta ~ condition * time_linear + condition * time_quadratic
      + stimulus_end_arousal_z + order_z + recovery_is_endvid
      + (1 + time_linear | participant)
```

时间以60秒为中心并除以60，因此`condition_scary`表示恢复窗中点附近的scary-amusing差异。

### HR

- scary-amusing：-2.71 bpm，95% CI -3.88至-1.53，p<0.001。
- condition × linear time：+0.56 bpm，p=0.254，不支持两条件具有稳定不同的线性恢复速度。
- condition × quadratic time：+1.12 bpm，p=0.247，不支持稳定的曲率差异。
- Arousal：+0.59 bpm，p=0.038，但在剔除endVid和个体内标准化版本中不稳定。

解释：HR支持条件平均水平差异，不足以支持明确不同的恢复曲线形状。

### SCL

- scary-amusing：+9.53 uS，95% CI 8.26–10.81，p<0.001。
- condition × linear time：-1.37 uS，95% CI -2.34至-0.39，p=0.006。
- condition × quadratic time：+0.53 uS，p=0.589。
- Arousal：-0.82 uS，p=0.012，但不能通过全部敏感性分析。

解释：scary后的SCL残留显著更高，而且两条件差距随时间缓慢缩小；没有证据支持额外的二次曲率差异。

## 7. 敏感性分析

| 分析 | HR scary差异 | SCL scary差异 | 判定 |
|---|---:|---:|---|
| 主模型 | -2.71 bpm | +9.53 uS | 基准 |
| 剔除endVid | -2.92 bpm | +8.71 uS | 方向一致 |
| 控制前一情绪 | -3.01 bpm | +6.90 uS | 方向一致，SCL幅度减小 |
| 个体内标准化GEE | -0.39 SD | +1.04 SD | 方向一致 |
| SCL剔除P17 | 不适用 | +9.54 uS | 与主模型近乎相同 |

全部MixedLM均收敛、AIC有限且无优化警告。个体内标准化会按定义消除参与者随机截距，因此该版本使用参与者聚类、交换型相关结构的GEE，而不是报告一个必然落在零边界的随机截距模型。

前一情绪控制使SCL条件差异从9.53降至6.90 uS，说明序列残留确实重要；但方向、置信区间和主要时间交互均保持，因此主结论不是由序列顺序单独造成。

## 8. 主观Arousal判定

RQ2暂判定为不支持或证据不足。HR和SCL主模型中的Arousal系数达到名义显著，但剔除endVid后分别为p=0.071和p=0.719，个体内标准化GEE中也不显著。不能依据单一主模型声称主观唤醒稳定预测生理恢复。

这也说明“主观体验”和“自主神经恢复”不应被当成同一个测量层面。

## 9. 跨条件个体一致性

每个参与者在每个条件只有2个trial，因此以下结果明确标记为探索性。相关系数使用Spearman rho，置信区间使用参与者bootstrap 2000次，并对6个指标做Benjamini-Hochberg FDR校正。

- SCL绝对恢复AUC：rho=0.467，95% CI 0.088–0.759，原始p=0.009，BH q=0.019。
- SCL恢复斜率：rho=0.550，95% CI 0.197–0.789，原始p=0.002，BH q=0.009。
- HR绝对恢复AUC：rho=0.222，95% CI -0.146–0.586，p=0.238。
- HR晚期残留：rho=-0.523，95% CI -0.734至-0.205，p=0.003，BH q=0.009。由于指标有正负方向，这表示两条件下晚期HR偏离方向可能相反，不应解释为稳定的“恢复能力”。

正式引用显著性时以`cross_condition_consistency.csv`中的BH校正q值为准。SCL结果提示可能存在跨情绪条件的稳定个体排序，但两trial/条件不足以估计高可靠性的trait，应使用“初步证据”而不是“量化出稳定人格特征”。

## 10. 第二周后的论文判断

### 可以写入论文主结果

1. scary与amusing之后的SCL残留幅度存在明显差异；
2. SCL条件差距在120秒内缓慢缩小；
3. 上述结果对endVid、前一情绪、个体标准化和EDA审查参与者具有稳健性；
4. HR存在平均条件差异，但轨迹形状证据较弱。

### 只能作为探索性结果

1. SCL AUC和斜率的跨条件个体一致性；
2. HR晚期残留的负相关；
3. 个体分面曲线中的特殊恢复模式。

### 当前不能声称

1. 主观Arousal稳定预测生理恢复；
2. 生理信号可以转换成VAD坐标；
3. 蓝屏期有连续的主观恢复曲线；
4. 结果适用于所有正性和负性情绪；
5. 观察到的相关关系是因果关系。

## 11. 可复现产物

- 正式脚本：`analysis/case_recovery_week2.py`
- 环境版本：`requirements_b.txt`
- 运行清单：`public_data/case_recovery/week2/week2_manifest.json`
- 全量时间箱：`full_recovery_bins.csv`
- trial特征：`full_trial_features.csv`
- ECG/EDA质控：`participant_signal_qc.csv`
- HeartPy验证：`ecg_heartpy_validation.csv`
- 模型输入：`model_input_bins.csv`
- 模型系数与拟合：`mixed_model_coefficients.csv`、`mixed_model_fit.csv`
- 敏感性关键项：`sensitivity_key_terms.csv`
- 一致性结果：`cross_condition_consistency.csv`
- 曲线与散点图：`*.png`

完整复现命令：

```powershell
.\.venv\Scripts\python.exe analysis\case_recovery_week2.py
```
