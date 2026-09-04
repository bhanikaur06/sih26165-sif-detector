# SIH26165 — SIF Precursor Detection Engine

AI/NLP system that classifies Oil India's unsafe-act/unsafe-condition and
near-miss reports as Serious Injury & Fatality (SIF) precursors, tags them to
IOGP Life-Saving Rules, and surfaces precursor density on a dashboard.

## Team and ownership

| Folder | Owner | Claude session runs from |
|---|---|---|
| `/data` | Person A | `data/` |
| `/backend` | Person B | `backend/` |
| `/frontend` | Person C | `frontend/` |

Each folder has its own `CLAUDE.md` with role-specific instructions. This root
file is the shared contract — read automatically by every session regardless of
which folder it's working in.

## Tech stack

- Data + backend: Python, pandas, numpy, scikit-learn, matplotlib
- Frontend: HTML, CSS, JavaScript (no framework)

## Data source

MSHA Accident Injuries Data Set (public, US mining, used as a labeled proxy for
SIF-precursor classification — see `data/CLAUDE.md` for acquisition details).
Definition file:
https://arlweb.msha.gov/opengovernmentdata/DataSets/Accidents_Definition_File.txt

## Interface contract — processed dataset

`data/processed/msha_labeled.csv`, produced by the data track, consumed by
backend. Columns:

| column | type | notes |
|---|---|---|
| doc_id | string | unique row id |
| narrative | string | free-text incident description |
| sif_label | int | 0 or 1, derived from IMMEDNOTIFYCD |
| source_code | string | original MSHA IMMEDNOTIFYCD, kept for traceability |
| split | string | "train", "val", or "test" |

Plus these grouping columns, added for the dashboard's
`precursor_density_by_group`. A missing value is written as an empty field —
never a placeholder like "NO VALUE FOUND" — so pandas reads it back as `NaN`
unless you pass `keep_default_na=False`. Read `source_code` and `mine_id` as
strings; they have leading zeros.

| column | type | fill | distinct | notes |
|---|---|---|---|---|
| mine_id | string | 100% | 8,634 | MSHA mine identifier |
| operator_name | string | 99.5% | 6,157 | too high-cardinality to chart directly |
| activity | string | 71.8% | 98 | what the person was doing |
| subunit | string | 100% | 10 | best default grouping — clean, low cardinality |

`data/processed/oil_validation.csv` — same columns, holds ~150-200 hand-written
Indian-oilfield-style reports for honest domain-transfer reporting. Never mix
this into the MSHA train/val/test split; its `split` value is always
`"oil_validation"`, so filtering on `split` cannot pull it in by accident. Its
`source_code` is an IOGP Life-Saving Rule category tag (`LSR_*` / `NONSIF_*`),
not an MSHA code, and its grouping columns use oilfield values
(`GGS-02`, `DRILLING RIG`, …) so the dashboard can be demoed on it.

## Interface contract — API

Backend serves these two endpoints. Frontend consumes them and never calls the
model directly.

**POST /api/classify**

Request:
```json
{ "narrative": "<text>" }
```

Response:
```json
{ "sif_probability": 0.0, "sif_label": 0, "life_saving_rule": "<string or null>" }
```

**GET /api/dashboard/summary**

Response:
```json
{
  "summary_stats": { "total_reports": 0, "sif_count": 0, "density": 0.0 },
  "precursor_density_by_group": [
    { "group": "<string>", "group_type": "<string>", "total_reports": 0, "sif_count": 0, "density": 0.0 }
  ],
  "rule_breakdown": [
    { "life_saving_rule": "<string>", "count": 0 }
  ]
}
```

`summary_stats` field names are confirmed with backend. Same field names as a
per-group entry, but computed directly over the whole report population — not
summed from `precursor_density_by_group`, since that array can mix multiple
`group_type` values and summing it would double-count reports.

Backend decides what "group" means (site, activity, etc.) based on what fields
survive in the processed data — frontend renders whatever groups come back.

If this contract needs to change, whoever changes it tells the other two before
pushing. Do not edit it silently.

## Code style — applies to all three folders

Do not write comments in code — no `#`, `//`, `/* */`, or docstrings — unless
explicitly asked for one in a specific case. Use clear function and variable
names to carry meaning instead.

## Problem statement summary (SIH26165)

Build a prototype that ingests OIL's free-text safety reports and: (a)
classifies each as SIF-potential vs non-SIF-potential, (b) tags it to the
relevant IOGP Life-Saving Rule, (c) surfaces recurring precursor patterns via a
dashboard that ranks sites/activities by SIF-precursor density.
