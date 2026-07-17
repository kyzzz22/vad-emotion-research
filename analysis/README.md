# A2 分析流程

## 文件

- `simulate_and_validate.py`：生成结构正确的模拟数据并执行键、范围和完整性检查。
- `run_analysis.py`：计算主要 VAD 距离、拟合主要混合模型并输出描述统计。
- `requirements.txt`：分析依赖。
- `power_sensitivity.py`：对参与者层平均 PI-LI 距离差做精确配对 t 功效敏感性分析。
- `analyze_pilot.py`：按预测试预定规则输出逐试次命中和逐刺激保留指标。
- `prepare_ratings.py`：按目标概念白名单移除 filler、验证键与评分并派生目标情绪强度。
- `validate_events.py`：验证场次与逐试次事件顺序、成对标记、时长和 marker hook 错误。
- `apply_exclusions.py`：统一执行参与者级注意、完整性和极快反应排除，输出逐人日志。
- `power_lmm_simulation.py`：按主要 `PI-LI` 配对差模型做参数化 Monte Carlo 功效分析。
- `make_figures.py`：生成概念质心、配对距离、逐维偏差和操纵检查表图。
- `prepare_physiology.py`：验证设备无关的试次级 EDA/HR 摘要并计算参与者内/间成分。
- `analyze_physiology.py`：拟合 induced A 与 prototype-induced A 偏差的预定探索模型。
- `run_pipeline.py`：串联主观/生理处理、排除、模型和表图，并记录输入 SHA-256 与运行环境。
- `run_secondary.py`：检验 D 相对 V 的标准化绝对跨条件偏差，并输出 Holm 校正结果。
- `summarize_instruction_checks.py`：汇总三种条件评分对象理解核对的首次正确率与错误选项分布，不据此排除参与者。

## 运行顺序

```powershell
python analysis/simulate_and_validate.py
python analysis/prepare_ratings.py --raw data/simulated/ratings_long.csv --output data/simulated/ratings_prepared.csv
python analysis/run_analysis.py --ratings data/simulated/ratings_prepared.csv --output results/simulated
```

模拟结果只用于验证数据和代码结构，绝不进入正式论文结果。

预测试完成后运行：

```powershell
python analysis/analyze_pilot.py --ratings data/processed/pilot_ratings_long.csv --output results/pilot
```

正式任务原始导出先处理为主分析长表：

```powershell
python analysis/prepare_ratings.py --raw data/raw/task_export.csv --output data/processed/ratings_long.csv
python analysis/validate_events.py --events data/raw/events_P001_S1.csv --output data/interim/events_P001_S1_qc.csv
python analysis/apply_exclusions.py --ratings data/processed/ratings_long.csv --output data/processed/ratings_analysis.csv --log results/participant_exclusions.csv
```

完整管线：

```powershell
python analysis/run_pipeline.py --ratings-raw data/raw/ratings_all.csv `
  --physiology data/interim/physiology_trials.csv `
  --processed-dir data/processed --output results/main
```

主要模型先在参与者 × 概念内计算 `PI-LI`，再拟合参与者随机截距 LMM；若两个优化器均不收敛或随机截距位于预定零边界，则降级为带有限样本校正的参与者聚类 OLS。原 source 随机斜率模型保留为敏感性分析。`primary_model.txt` 首行记录实际主要模型路径。

主分析另输出 `primary_effect.csv` 和 `model_metadata.json`，用于论文表格和复核，避免从终端文本手抄结果。

正式数据到位后：

```powershell
python analysis/run_analysis.py --ratings data/processed/ratings_long.csv --output results/main
```

## 主要输出

- `vad_distances.csv`：每名参与者、每个概念的 LI 和 PI 距离。
- `vad_distance_contrasts.csv`：每名参与者、每个概念的精确 `PI-LI` 配对差及顺序变量。
- `primary_model.txt`：主要混合模型结果。
- `source_model_sensitivity.txt`：原距离长表 source 模型的敏感性分析。
- `condition_summary.csv`：各条件和维度的描述统计。

## 环境状态

项目内 `.venv` 已安装依赖，模拟数据和主要混合模型已于 2026-07-14 跑通。当前模拟模型可收敛；由于模拟概念方差接近零，会出现边界警告，后续功效模拟将加入更真实的随机效应结构。

使用项目环境运行：

```powershell
.\.venv\Scripts\python.exe analysis\simulate_and_validate.py
.\.venv\Scripts\python.exe analysis\prepare_ratings.py --raw data\simulated\ratings_long.csv --output data\simulated\ratings_prepared.csv
.\.venv\Scripts\python.exe analysis\run_analysis.py --ratings data\simulated\ratings_prepared.csv --output results\simulated
```
