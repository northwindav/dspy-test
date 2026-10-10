# DSPy Sounding Classification (Azure-only)

This project is an Azure-only DSPy workspace for text-based upper-air sounding classification, starting with inversion-strength classification in the lowest 150 mb.

The repo also now contains an initial raster-based pyrocumulonimbus classification path for sounding images. The older JSON-profile inversion workflow can remain in place as archived reference work, but it is no longer the primary direction.

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

Use the converter in `src/inversion_converter.py` to turn raw sounding rows into profile records, then label the stability profiles using `docs/inversion_labeling_guide.md`.

Before labeling a new batch, record any rule changes or boundary decisions in `docs/inversion_labeling_decisions.md`.

To convert a new multi-sounding text file to JSON, run:

```powershell
python scripts/convert_soundings_to_json.py --input path\to\your_soundings.txt --output path\to\your_profiles.json
```

Examples:

```powershell
python scripts/convert_soundings_to_json.py --input data\inversion\CYXY_2025060112_2025063012.txt --output data\inversion\CYXY_2025060112_2025063012_profiles.json
python scripts/convert_soundings_to_json.py --input data\inversion\CYXY_2025060112_2025063012.txt --output data\inversion\CYXY_2025060200_profiles.json --valid-utc "2025-06-02 00:00:00"
python scripts/convert_soundings_to_json.py --input data\inversion\CYXY_2025060112_2025063012.txt --output data\inversion\CYXY_2025060112_2025063012_profiles_700mb.json --top-pressure-mb 700
```

Recommended sequence for a new file:

- Convert the `.txt` file to a profile JSON file.
- If needed, create a stability-only labeling dataset with `scripts/prepare_inversion_labeling_dataset.py`.
- Label the stability profiles.
- Run `scripts/run_inversion_classification.py` against the labeled JSON.

Each labeled dataset example should include at minimum:

- `source`
- `label`
- `sounding_text`

The converter also emits useful optional fields such as:

- `case_name`
- `station`
- `validUTC`
- `profile_type`
- `levels`
- `top_pressure_mb`

For full-profile labeling review, the converter can retain all rows that have a real `pressure_mb` value and/or a real `height_m` value. A pressure cutoff should only be applied deliberately for a narrower experiment.

Each valid time may now produce two profile records:

- `profile_type="stability"` for thermodynamic sounding rows with real pressure values
- `profile_type="wind"` for hodograph-style rows with height and wind information

For inversion labeling, only the `stability` profiles should be labeled.

## 5) Run inversion classification

Once you have a labeled JSON dataset, run:

```powershell
python scripts/run_inversion_classification.py --dataset path\to\your_labeled_dataset.json --optimizer all
```

Current supported labels are:

- `none`
- `weak`
- `moderate`
- `strong`

Recommended workflow:

- Convert raw sounding files into case records.
- Label only the `stability` records using the inversion guide.
- Keep labels mutually exclusive for this first task.
- Compare baseline, `LabeledFewShot`, and `BootstrapFewShot` before trying heavier optimizers.

## 6) Project structure

- `src/config.py`: Azure DSPy runtime configuration.
- `src/inversion_converter.py`: raw sounding row conversion into labeled-case JSON format.
- `src/inversion_classification.py`: classification logic, evaluation helpers, and prompt-side optimizer entry points.
- `scripts/run_inversion_classification.py`: runnable CLI for baseline and optimized inversion classification.
- `scripts/convert_soundings_to_json.py`: runnable CLI for converting a multi-sounding text file into profile JSON.
- `docs/inversion_labeling_guide.md`: labeling contract for real datasets.
- `docs/inversion_labeling_decisions.md`: decision log for rule changes and applied case judgments.
- `tests/test_inversion_converter.py`: unit tests for the data conversion path.

## 7) Current project scope

- First task: inversion strength in the lowest 150 mb.
- Input: text-only soundings with user-supplied gold labels.
- Optimization sequence: baseline, `LabeledFewShot`, `BootstrapFewShot`, then only heavier prompt optimizers if needed.
- Deferred: multi-phenomenon classification, time-series reasoning, MCP, and fine-tuning.

## 8) PyroCb Raster Path

For the new raster workflow, see `docs/pyrocb_raster_workflow.md`.

Current assumptions:

- image-only sounding interpretation
- binary labels: `pyrocb` and `no_pyrocb`
- single Azure-hosted vision-capable model
- prompt optimization first, not multi-model comparison

For the current raster workflow, only the first two logical fields matter:

- `case-name` as the unique identifier
- `pyrocb-classification` as the binary label

The image filename is inferred as `<case-name>.png`. Any remaining CSV columns are ignored.

The runnable entry point is:

```powershell
python scripts/run_pyrocb_raster_classification.py --manifest path\to\manifest.csv --images-dir path\to\image_folder --train-size 12 --split-mode stratified --seed 0 --optimizer baseline
```

## Troubleshooting

- Missing dataset file:
  - `scripts/run_inversion_classification.py` requires an explicit `--dataset` path.
- Azure errors about model/deployment:
  - `AZURE_OPENAI_DEPLOYMENT` must be your Azure deployment name, not model family text.
- Azure auth or endpoint issues:
  - Verify endpoint shape: `https://<resource>.openai.azure.com`.
  - Verify API version supported by your deployment.
- DSPy import issues:
  - Confirm the `.venv` environment is active and packages were installed there.
  - Confirm `python --version` reports Python 3.11 or 3.12.
