# Inversion Smoke-Test Labeling Guide

This file is the gold-label contract for the first DSPy smoke test.

## Task

Classify inversion strength in the lowest 150 mb of the sounding.

Allowed labels:

- `none`
- `weak`
- `moderate`
- `strong`

## Fill In The Measurable Criteria

Record the exact thresholds you want used when assigning labels.

### `none`

- Definition:
- Thresholds:
- Borderline exclusions:

### `weak`

- Definition:
- Thresholds:
- Borderline exclusions:

### `moderate`

- Definition:
- Thresholds:
- Borderline exclusions:

### `strong`

- Definition:
- Thresholds:
- Borderline exclusions:

## Input Expectations

Each dataset example should contain:

- `source`: short identifier for the sounding, ideally derived from the source file and valid time
- `label`: one of the four allowed labels
- `sounding_text`: the text-only sounding description given to DSPy

Optional fields that fit the current repo workflow:

- `case_name`
- `station`
- `validUTC`
- `levels`
- `top_pressure_mb`

## Suggested Case Naming

For a file like `data/inversion/CYXY_2025060112_2025063012.txt`, a good case name is:

- `CYXY_2025060200`
- `CYXY_2025060212`

This keeps each sounding unique while preserving the station code and valid time.

## Suggested Conversion Workflow

1. Parse the raw file into one case per valid time.
2. Optionally apply a `top_pressure_mb` cutoff so only the lower portion of the sounding is included for the current task.
3. Generate `sounding_text` from the retained pressure-level rows.
4. Keep the retained structured rows in `levels` so the raw low-level profile is still available.
5. Assign a label from `none`, `weak`, `moderate`, or `strong`.
6. Write the labeled cases into a JSON dataset for DSPy.

Current repo support for this workflow:

- `src/inversion_converter.py` builds case records and writes JSON datasets.
- `tests/test_inversion_converter.py` validates the converter behavior.
- `examples/inversion_smoke_test.py` runs the DSPy baseline and first prompt-side optimizers against the labeled JSON dataset.

For inversion work, a cutoff such as `top_pressure_mb=850.0` can be a reasonable first pass because rows above that pressure are excluded.

## Notes For Phase 1

- Keep this first task mutually exclusive: one sounding, one inversion-strength label.
- If a sounding also contains a low-level jet, ignore that for this task unless it changes the inversion label under your written criteria.
- Keep the text representation consistent across examples. If you later standardize the wording, do it for the whole dataset rather than one example at a time.
- No placeholder dataset is tracked anymore. Create or supply a real labeled JSON dataset before running the smoke test.

## Future Expansion

Later tasks can add separate label guides for:

- low-level jet strength in the lowest 300 mb
- inversion break timing
- low-level jet descent or surface coupling likelihood