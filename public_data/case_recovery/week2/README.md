# CASE direction B: week-two outputs

These files are derived from the read-only official CASE raw data.

Reproduce every table and figure from the project root:

```powershell
.\.venv\Scripts\python.exe analysis\case_recovery_week2.py
```

Key files:

- `week2_manifest.json`: versions, counts, seed and completion gates.
- `ecg_heartpy_validation.csv`: peak-level independent validation.
- `participant_signal_qc.csv`: ECG and raw EDA audit metrics.
- `full_recovery_bins.csv`: all 2880 ten-second HR/SCL bins.
- `full_trial_features.csv`: all 240 trial-level recovery features.
- `model_input_bins.csv`: 1440 main-condition rows with model predictors.
- `mixed_model_coefficients.csv`: MixedLM and standardized GEE coefficients.
- `mixed_model_fit.csv`: convergence, variance and warning diagnostics.
- `sensitivity_key_terms.csv`: key terms across all model variants.
- `cross_condition_consistency.csv`: correlations, bootstrap CIs and BH q-values.
- `overall_curve_bootstrap_ci.csv`: participant-bootstrap trajectory estimates.
- `*.png`: individual curves, overall curves and consistency scatterplots.

The scientific interpretation and limitations are documented in
`protocol/B_第二周执行记录.md`.
