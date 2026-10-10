# PyroCb Raster Workflow

This document defines the starting workflow for pyrocumulonimbus classification from sounding rasters.

## Scope

- Input format: raster sounding images only
- Label set: `pyrocb`, `no_pyrocb`
- Optimization target: prompt optimization with a single Azure-hosted vision-capable LLM
- Secondary target: reduce operational token usage after correctness is established

## Dataset Format

Use a folder of image files plus a CSV manifest.

Required CSV columns:

- Either:
	- `filename` and `label`, or
	- `case-name` and `pyrocb-classification`

Optional CSV columns:

- none required for the current workflow

Example:

```csv
filename,label,source
case_001.png,pyrocb,case_001
case_002.png,no_pyrocb,case_002
```

The loader also supports your current field layout directly:

```csv
case-name,pyrocb-classification,...
dspy-pcb-001a,y,...
dspy-pcb-002,n,...
```

In that format:

- the image filename is inferred as `<case-name>.png`
- `case-name` is also used as the unique example identifier
- `y` maps to `pyrocb`
- `n` maps to `no_pyrocb`
- only the classification columns are used; all other columns are ignored
- rows with blank classification are skipped

Labels must be exactly:

- `pyrocb`
- `no_pyrocb`

## Runner

Run the raster classifier with:

```powershell
python scripts/run_pyrocb_raster_classification.py --manifest path\to\manifest.csv --images-dir path\to\image_folder --train-size 12 --split-mode stratified --seed 0 --optimizer baseline
```

Then compare prompt-side optimizers in this order:

```powershell
python scripts/run_pyrocb_raster_classification.py --manifest path\to\manifest.csv --images-dir path\to\image_folder --train-size 12 --split-mode stratified --seed 0 --optimizer labeled
python scripts/run_pyrocb_raster_classification.py --manifest path\to\manifest.csv --images-dir path\to\image_folder --train-size 12 --split-mode stratified --seed 0 --optimizer bootstrap
```

## Important Constraints

- The Azure deployment must be vision-capable.
- The current implementation uses DSPy image inputs directly; no OCR or JSON-profile conversion is involved.
- Classification is exact-match against the labels in the CSV manifest.
- The current signature is intentionally minimal. Domain-specific pyroCb guidance should be added to the signature prompt only after you provide the initial expert prompt text.