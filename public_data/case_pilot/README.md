# CASE × NRC-VAD feasibility pilot

This directory keeps third-party source data separate from derived outputs.

## Sources

- `case_dataset/`: official CASE GitLab repository clone.
- `nrc_vad/`: NRC-VAD v2.1 downloaded from the official project page. The
  lexicon is restricted to non-commercial research/educational use and must
  not be redistributed.

## Run

From the project root:

```powershell
.\.venv\Scripts\python.exe analysis\case_nrc_pilot.py
```

The default run analyzes all 30 participants' annotations and uses the first
three participants only to verify raw physiological parsing, calibration,
segmentation, and baseline correction. Outputs are written to `results/`.

To extend the engineering check to all subjects:

```powershell
.\.venv\Scripts\python.exe analysis\case_nrc_pilot.py --physiology-subjects 30
```

The source datasets are never modified by the script.
