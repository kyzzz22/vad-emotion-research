# A2 数据目录与数据字典

本目录不保存任何直接身份信息。参与者联系方式、知情同意和实验数据必须分开保存。

## 目录约定

```text
data/
  raw/          # 原始导出，只读保存
  interim/      # 同步、切段和质量标记后的中间数据
  processed/    # 可复现分析使用的匿名长表
```

正式分析的主表命名为 `processed/ratings_long.csv`。每行是一名参与者在一个情绪概念、一个条件和一个刺激上的一条评分。

语义任务原始导出还包含 `materials/semantic_fillers.csv` 中的 filler。处理脚本必须按目标 `concept_id` 白名单移除 filler，并在处理日志中报告数量；不得根据评分结果决定是否保留。

## ratings_long.csv

| 字段 | 类型 | 允许值/说明 |
|---|---|---|
| participant_id | string | 匿名编号，例如 P001 |
| sequence_id | integer | 1-8，三个平衡因素的正交序列编号 |
| concept_id | string | 与 `materials/emotion_concepts.csv` 完全一致 |
| condition | category | lexical, prototype, induced |
| stimulus_id | string | induced 条件必填；其余为空 |
| session_id | string | S1, S2 等 |
| session_order | integer | 1 = semantic 先，2 = induced 先 |
| block_order | integer | 场次内区块顺序 |
| item_order | integer | 区块内呈现顺序 |
| valence | integer | 1-9，越高越愉悦 |
| arousal | integer | 1-9，越高越激活 |
| dominance | integer | 1-9，越高越有控制感 |
| target_emotion_intensity | integer | 1-9 |
| intensity_joy ... intensity_fear | integer | induced 条件的六类目标/非目标情绪，1-9；语义条件为空 |
| intensity_disgust | integer | 1-9，用于检查愤怒材料的混合情绪 |
| discomfort | integer | 1-9，预测试和安全监测 |
| familiarity | integer | 1-9 |
| self_relevance | integer | 1-9 |
| response_time_ms | number | 评分总反应时或逐题反应时 |
| attention_check | integer | 0 = 未通过，1 = 通过 |
| attention_check_rate | number | 每场两个明确指令检查的正确比例：0, 0.5, 1 |
| instruction_check_correct | integer | 当前条件开始前的评分对象理解核对首次答案：0 = 错，1 = 对；仅作操纵证据，不用于排除 |
| instruction_check_response | category | lexical, prototype, induced；参与者首次选择的评分对象 |
| subjective_qc | category | prepare 脚本生成：pass, attention_fail, technical_fail |
| notes | string | 不含身份信息的异常说明 |

## physiology_trials.csv

每行是一名参与者在一个视频试次中的生理摘要。

| 字段 | 类型 | 说明 |
|---|---|---|
| participant_id | string | 与主观评分表一致 |
| concept_id | string | 目标情绪概念 |
| stimulus_id | string | 视频 ID |
| baseline_start_s | number | 原始连续记录中的时间戳 |
| baseline_end_s | number | 原始连续记录中的时间戳 |
| stimulus_start_s | number | 事件标记时间戳 |
| stimulus_end_s | number | 事件标记时间戳 |
| recovery_end_s | number | 事件标记时间戳 |
| eda_baseline | number | 基线摘要 |
| eda_stimulus | number | 刺激期摘要 |
| eda_delta | number | stimulus - baseline |
| hr_baseline | number | bpm |
| hr_stimulus | number | bpm |
| hr_delta | number | stimulus - baseline |
| ibi_baseline | number | ms |
| ibi_stimulus | number | ms |
| signal_qc_eda | category | pass, partial, fail |
| signal_qc_ecg_ppg | category | pass, partial, fail |
| exclusion_reason | string | 预定义规则产生的原因 |

## 合并约束

主观和生理数据只允许通过以下键连接：

```text
participant_id + concept_id + stimulus_id
```

禁止根据视频名称、行号或呈现顺序做模糊连接。正式采集前必须用模拟数据完成一次从原始导出到合并主表的全流程测试。

## 计分约束

- 所有 V/A/D 评分统一为 1-9 且方向一致。
- `target_emotion_intensity` 必须由 `concept_id` 对应的原始离散情绪列复制或在处理脚本中生成，不得手工填写。
- 不在原始数据中反向计分；转换只发生在可复现处理脚本中。
- 原始时间戳、设备采样率、事件标记和掉线记录必须保留。
- 原始数据永不手工覆盖；所有修正写入处理脚本或质量控制日志。
- 技术失败的空评分行保留在处理结果中并标记 `technical_fail`；主模型只读取 `subjective_qc=pass`，不得无记录地删除。
