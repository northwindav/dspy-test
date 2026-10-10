# Inversion Labeling Guide

This file documents decisions and changes on labeling of inversions from text-based stability profiles.

## Task

Determine presence or absence of an inversion in the lower atmosphere. 'Lower' is subjectively defined as within approximately 150 mb of the surface at the site of the sounding. 

Labels:

- `none`
- `weak`
- `moderate`
- `strong`

## Current Rule Set: Version 0.1 (04 Aug 2026)

Applies to any evaluations done from 04 Aug until the next revision is applied.

### General Rules

- If a file contains both stability and wind profiles, only the stability portion is labeled for evaluation.
- Updates to rules are recorded in docs/inversion_labeling_decisions.md
- If multiple inversions are present in the lower atmopshere, the profile is classified based on the strongest inversion.

### `none`

- Definition: No portion of the lower atmosphere has a measured increase in temperature with height. This includes isothermal sections.

### `weak`

- Definition: At least one vertical interval in the lower atmosphere shows a measurable increase in temperature with height, but does not meet the threshold for moderate.
- The subjective evaluation will take into account the depth and magnitude of this increase. 
- The 'weak' classifier will be used for thin and/or small magnitudes. Specifics are noted in the labeling decisions document.

### `moderate`

- Definition: More than 1 adjacent vertical layer has an increase in temperature with height AND the magnitude of the increase with height is >= 2 degrees C over a vertical pressure change of <= 50 mb

### `strong`

- Definition: Strong and/or thicker inversions. At least 2 adjacent layers record an increase in temperature with elevation AND the magnitude of this increase is >= 5 degrees C over a vertical pressure change of <= 50 mb. 

## Input fields

Each sample stability profile must include:

- `source`: short, unique identifier for the sounding. Format <STN>_<YYYYMMDDHH_valid>
- `label`: one of the four allowed labels
- `sounding_text`: the text-only sounding description given to DSPy. The text is what is actually evaluated.

Additional fields included for readability, but not included in the DSPy evaluation.

- `case_name`
- `station`
- `validUTC`
- `levels`
- `top_pressure_mb`

## Conversion Workflow

1. Parse the raw file into one case per valid time. Current workflow supports conversion of data files retrieved from Iowa Environmental Mesonet.
2. For full-profile review, retain all rows that contain a real pressure value and/or a real `height_m` value.
3. Only apply a pressure cutoff if you explicitly want a reduced profile for a specific experiment.
4. Generate `sounding_text` from the retained pressure-level rows.
5. Keep the retained structured rows in `levels` so the raw profile remains available during labeling.
6. Assign a label from `none`, `weak`, `moderate`, or `strong`.
7. Write the labeled cases into a JSON dataset for DSPy.

Current files to apply this workflow:

- `src/inversion_converter.py` builds case records and writes JSON datasets based on input txt files, containing multiple stability and wind profiles, from Iowa Environmental Mesonet.
- `scripts/convert_soundings_to_json.py` is the recommended CLI wrapper for converting a new multi-sounding txt file to JSON.
- `tests/test_inversion_converter.py` validates the converter behavior.
- `scripts/run_inversion_classification.py` runs the DSPy baseline and first prompt-side optimizers against the labeled JSON dataset.

### Converting a new file

Basic conversion:

```powershell
python scripts/convert_soundings_to_json.py --input path\to\your_soundings.txt --output path\to\your_profiles.json
```

Single sounding only:

```powershell
python scripts/convert_soundings_to_json.py --input path\to\your_soundings.txt --output path\to\single_case.json --valid-utc "2025-06-02 00:00:00"
```

Optional pressure-limited export:

```powershell
python scripts/convert_soundings_to_json.py --input path\to\your_soundings.txt --output path\to\profiles_700mb.json --top-pressure-mb 700
```

Current converter behavior for this workflow:

- rows are retained when they contain a real `pressure_mb` value and/or a real `height_m` value
- rows with neither are excluded
- `levelcode` is dropped from the output because it is not used for labeling
- single-sounding export is supported by filtering on `validUTC`

## Notes For Phase 1

- Keep this first task mutually exclusive: one sounding, one inversion-strength label.
- Keep the text representation consistent across examples. If you later standardize the wording, do it for the whole dataset rather than one example at a time.

## Future Expansion

Later tasks can add separate label guides for:

- low-level jet strength in the lowest 300 mb
- inversion break timing
- low-level jet descent or surface coupling likelihood