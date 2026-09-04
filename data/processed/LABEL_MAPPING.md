# Label mapping — IMMED_NOTIFY_CD → sif_label

Source field: `IMMED_NOTIFY_CD` in the raw MSHA Accidents table. Kept verbatim
in the processed output as `source_code` for traceability. Produced by
`data/scripts/build_dataset.py`; every number below comes from the run
recorded in `data/processed/build_report.json`.

## Code reference (from MSHA's own definition file)

`IMMED_NOTIFY_CD` records whether the accident was one of the 12 categories
mine operators must **immediately** report to MSHA, because each one carries
real death/serious-injury potential regardless of how the specific event
happened to turn out.

| code | meaning | rows in raw file |
|---|---|---|
| 01 | Death | 1,207 |
| 02 | Serious injury | 8,531 |
| 03 | Entrapment | 842 |
| 04 | Inundation | 447 |
| 05 | Gas or dust ignition | 1,034 |
| 06 | Mine fire | 1,738 |
| 07 | Explosives | 117 |
| 08 | Roof fall | 17,306 |
| 09 | Outburst | 197 |
| 10 | Impounding dam | 59 |
| 11 | Hoisting | 4,423 |
| 12 | Offsite | 336 |
| 13 | Not marked — met none of the 12 criteria | 55,851 |
| ? | "NO VALUE FOUND" — field never populated | 182,479 |

Raw file: 274,567 rows.

## Mapping used

```
sif_label = 1  if IMMED_NOTIFY_CD in {01 … 12}
sif_label = 0  if IMMED_NOTIFY_CD == 13
row dropped    if IMMED_NOTIFY_CD == "?"      (default; see policy below)
```

## Rationale for the positive class

The root contract fixes `sif_label` as a binary field derived from
`IMMED_NOTIFY_CD` alone, so the decision is which values count as "1".

The 12 immediate-notification categories are exactly the accident *types*
MSHA itself has already judged to carry high fatality/serious-injury
potential — that is what "immediately reportable" means under 30 CFR Part 50.
That is functionally the same judgment SIF classification makes: was this a
type of event that plausibly could have killed or seriously injured someone,
independent of how it actually turned out. Roof falls, gas/dust ignitions,
entrapments and hoisting failures are the mining analogues of the incident
types IOGP's Life-Saving Rules target. Code 13 means the accident met none of
those criteria — the natural negative class.

We deliberately did **not** gate on `DEGREE_INJURY_CD` (realised outcome).
SIF-precursor detection is about *potential* severity: a roof fall that hurt
nobody is still a precursor, and that near-miss signal is the whole point of
the engine. Folding in realised harm would train the model to detect injuries
rather than precursors.

## The `?` rows — the real judgment call

Two thirds of the raw file (182,479 rows, 66.5%) carry `?` / "NO VALUE
FOUND" rather than an explicit code. How these are treated changes the
dataset more than anything else in this pipeline, so it is a switchable flag
rather than a silent decision.

**What the evidence says.** Cross-tabulating against `DEGREE_INJURY` shows
the `?` group behaves like an ordinary-accident population, not an ambiguous
one:

| group | rows | fatalities | fatality rate |
|---|---|---|---|
| coded 01–12 | 36,434 | 1,128 | 3.1% |
| coded 13 | 55,851 | 1 | 0.002% |
| `?` | 182,479 | 7 | 0.004% |

The `?` group is statistically indistinguishable from code 13 and three
orders of magnitude below the coded-SIF group. The most likely reading is
that operators simply left the field blank when no immediate notification
applied — i.e. `?` is a de facto negative.

**Why we still drop it by default.** "Probably a negative" is an inference,
not a recorded determination, and 182k inferred labels would dominate the
55k recorded ones. Dropping keeps every label in the training set traceable
to something a human actually recorded, and yields a workable 61/39 class
balance instead of 87/13.

**The alternative is one flag away:**

```bash
python3 data/scripts/build_dataset.py --blank-code-policy negative
```

Treats `?` as `sif_label = 0` (written to `source_code` as `NOT_MARKED`, so
these rows stay distinguishable from true code-13 rows downstream).

| policy | rows | label 0 | label 1 | balance | file size |
|---|---|---|---|---|---|
| `drop` (default) | 91,386 | 55,433 | 35,953 | 61 / 39 | 19 MB |
| `negative` | 272,711 | 236,769 | 35,942 | 87 / 13 | 59 MB |

Worth `/backend` trying both: `negative` is closer to the real-world base
rate (SIF precursors genuinely are rare), so a model trained on `drop` will
tend to over-predict SIF on live data and inflate the dashboard's density
numbers. `drop` is the easier baseline to get working under hackathon time.

## Sanity check on the shipped labels

Within the 91,386 labelled rows, `sif_label = 1` captures **1,128 of the
1,129 fatalities** (99.9%). The label was derived without ever looking at
`DEGREE_INJURY`, so this is an independent confirmation that the positive
class really is tracking severe outcomes.

## Other rows removed

| reason | rows |
|---|---|
| `?` code (default policy) | 182,479 |
| narrative missing or under 15 characters | 130 |
| duplicate narrative text | 574 |

Deduplication is on exact narrative text and runs *before* the split, so the
same narrative can't appear in both train and test.

## Split

70 / 15 / 15 train/val/test, stratified on `sif_label`, seed 42. Per-split balance is in `build_report.json` and matches the overall
61/39 to within a row.

## Grouping columns

Four raw fields are carried through alongside the five contract columns, so
`/backend` can compute `precursor_density_by_group` without going back to the
raw file. `?` and "NO VALUE FOUND" are normalised to an empty field, which
pandas reads back as `NaN` unless you pass `keep_default_na=False` — so
filter with `.notna()`, not `!= ""`.

| column | fill | distinct | good for grouping? |
|---|---|---|---|
| `subunit` | 100% | 10 | **yes — the default choice** |
| `activity` | 71.8% | 98 | yes, if you handle the 28% blanks |
| `mine_id` | 100% | 8,634 | only after a top-N cut |
| `operator_name` | 99.5% | 6,157 | only after a top-N cut |

Density by `subunit` on the shipped file, as a figure to check the API
against:

| subunit | reports | sif | density |
|---|---|---|---|
| UNDERGROUND | 43,006 | 24,781 | 0.576 |
| SURFACE AT UNDERGROUND | 3,661 | 1,988 | 0.543 |
| STRIP, QUARY, OPEN PIT | 22,639 | 5,172 | 0.228 |
| DREDGE | 1,211 | 254 | 0.210 |
| MILL OPERATION/PREPARATION PLANT | 19,951 | 3,545 | 0.178 |

Underground work carrying roughly triple the precursor density of surface
work is the expected shape, and mostly reflects roof falls (code 08) being
the largest single positive category.

## Gotcha for downstream consumers

`source_code` and `mine_id` keep their leading zeros (`"01"`, `"0100003"`).
Read them as strings or pandas will silently turn them into integers:

```python
pd.read_csv(
    "data/processed/msha_labeled.csv",
    dtype={"source_code": str, "mine_id": str},
)
```
