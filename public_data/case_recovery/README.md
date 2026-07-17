# CASE recovery analysis

This directory contains derived outputs for direction B. The official CASE raw
data remain under `public_data/case_pilot/case_dataset` and are never modified.

Run the first-week pilot from the project root:

```powershell
.\.venv\Scripts\python.exe analysis\case_recovery_pilot.py --subjects 1 2
```

Expected outputs under `results/`:

- `trial_index.csv`: all 240 emotional trials reconstructed from metadata.
- `annotation_blue_screen_audit.csv`: participant-level evidence about joystick
  behavior during blue screens.
- `pilot_recovery_bins.csv`: 10-second HR/SCL recovery bins for the selected
  pilot participants.
- `pilot_trial_features.csv`: baseline, reactivity, residual, slope and AUC
  features.
- `pilot_signal_qc.csv`: ECG detection and signal-coverage checks.
- `pilot_ecg_qc_sub*.png`: R-peak overlays from the beginning, middle and end
  of each pilot recording.
- `pilot_recovery_curves.png`: subject-level engineering-check curves.
- `first_week_manifest.json`: reproducibility manifest.

The pilot ECG detector is an engineering check. Waveform inspection and a
mature-tool cross-check are required before confirmatory analysis.

## Week-two full-sample analysis

```powershell
.\.venv\Scripts\python.exe analysis\case_recovery_week2.py
```

Full-sample outputs are written to `week2/`. The script validates the ECG
detector against HeartPy, processes all 30 participants, audits ECG/EDA quality,
draws individual and participant-bootstrap curves, fits mixed models and three
sensitivity variants, and estimates cross-condition participant consistency.
