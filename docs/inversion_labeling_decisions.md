# Inversion Labeling Decisions

This file records labeling decisions before they are applied broadly to the dataset.

## Decision Log

### 2026-08-04 — D001

- Scope: inversion labeling workflow
- Decision: only `profile_type="stability"` records are labeled for inversion strength. `profile_type="wind"` records are excluded from inversion labeling.
- Reason: the wind profile is hodograph-oriented and should not be mixed into the thermodynamic inversion task.

### 2026-08-04 — D002

- Scope: Stability strength labels have 4 possibilities:
    - none
    - weak
    - moderate
    - Strong
- Rationale: This is intended only to test Agent's ability to discern the presence of an inversion and to classify it as strong or weak.

