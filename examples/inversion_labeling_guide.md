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

Each dataset example in `examples/inversion_dataset.json` should contain:

- `source`: short identifier for the sounding
- `label`: one of the four allowed labels
- `sounding_text`: the text-only sounding description given to DSPy

## Notes For Phase 1

- Keep this first task mutually exclusive: one sounding, one inversion-strength label.
- If a sounding also contains a low-level jet, ignore that for this task unless it changes the inversion label under your written criteria.
- Keep the text representation consistent across examples. If you later standardize the wording, do it for the whole dataset rather than one example at a time.

## Future Expansion

Later tasks can add separate label guides for:

- low-level jet strength in the lowest 300 mb
- inversion break timing
- low-level jet descent or surface coupling likelihood