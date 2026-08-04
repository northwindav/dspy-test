# DSPy Sounding Classifier (Azure-only)

This project is an Azure-only DSPy workspace for text-based upper-air sounding classification, starting with inversion-strength classification in the lowest 150 mb.

## 1) Install a supported Python version

Use a standard CPython installation from python.org, not a Conda-managed interpreter.
This project is currently validated for Python 3.11 or 3.12. The current DSPy dependency stack does not install cleanly on Python 3.13 in this workspace.
If `python` still resolves to Conda on your machine, invoke the CPython 3.12 executable explicitly when creating the environment.

## 2) Create a native virtual environment (PowerShell)

```powershell
$env:LocalAppData\Programs\Python\Python312\python.exe -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, allow local scripts for the current user and retry:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## 3) Configure environment variables

Copy the template and edit values:

```powershell
Copy-Item .env.example .env
```

Edit `.env`:

- Set `AZURE_OPENAI_API_KEY`
- Set `AZURE_OPENAI_ENDPOINT`
- Set `AZURE_OPENAI_DEPLOYMENT` to your deployment name
- Keep/update `AZURE_OPENAI_API_VERSION`

This repo is intentionally Azure-only so the setup matches the larger sounding-interpretation project.

## 4) Build a labeled inversion dataset

Use the converter in `src/inversion_converter.py` to turn raw sounding rows into one JSON case per valid time, then label those cases using `examples/inversion_labeling_guide.md`.

Each labeled dataset example should include at minimum:

- `source`
- `label`
- `sounding_text`

The converter also emits useful optional fields such as:

- `case_name`
- `station`
- `validUTC`
- `levels`
- `top_pressure_mb`

For the current inversion task, a `top_pressure_mb=850.0` cutoff is a reasonable first pass because it keeps the low-level profile while excluding higher-level rows.

## 5) Run the sounding classification smoke test

Once you have a labeled JSON dataset, run:

```powershell
python examples/inversion_smoke_test.py --dataset path\to\your_labeled_dataset.json --optimizer all
```

Current supported labels are:

- `none`
- `weak`
- `moderate`
- `strong`

Recommended workflow:

- Convert raw sounding files into case records.
- Apply labels using the inversion guide.
- Keep labels mutually exclusive for this first task.
- Compare baseline, `LabeledFewShot`, and `BootstrapFewShot` before trying heavier optimizers.

## 6) Current project scope

- First task: inversion strength in the lowest 150 mb.
- Input: text-only soundings with user-supplied gold labels.
- Optimization sequence: baseline, `LabeledFewShot`, `BootstrapFewShot`, then only heavier prompt optimizers if needed.
- Deferred: multi-phenomenon classification, time-series reasoning, MCP, and fine-tuning.

## Troubleshooting

- Missing dataset file:
  - `examples/inversion_smoke_test.py` now requires an explicit `--dataset` path.
- Azure errors about model/deployment:
  - `AZURE_OPENAI_DEPLOYMENT` must be your Azure deployment name, not model family text.
- Azure auth or endpoint issues:
  - Verify endpoint shape: `https://<resource>.openai.azure.com`.
  - Verify API version supported by your deployment.
- DSPy import issues:
  - Confirm the `.venv` environment is active and packages were installed there.
  - Confirm `python --version` reports Python 3.11 or 3.12.
