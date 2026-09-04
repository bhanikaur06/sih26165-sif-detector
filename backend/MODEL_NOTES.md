# Model notes — TF-IDF + logistic regression classifier

Produced by `train.py`. Trained on the `train` split of
`data/processed/msha_labeled.csv`, evaluated separately on the MSHA `test`
split and on `data/processed/oil_validation.csv` (174 hand-written Indian
oilfield reports, held fully out of the MSHA train/val/test split).

## Confusion matrix

| | MSHA test split (n=13708) | Oil validation (n=174) |
|---|---|---|
| TP | 4336 | 82 |
| FP | 525 | 48 |
| TN | 7790 | 24 |
| FN | 1057 | 20 |

## Metrics

| Metric | MSHA test split | Oil validation |
|---|---|---|
| Accuracy | 0.8846 | 0.6092 |
| Precision | 0.8920 | 0.6308 |
| Recall | 0.8040 | 0.8039 |
| F1 | 0.8457 | 0.7069 |

## Recall holds, precision collapses

Recall is nearly identical across domains — 0.8040 on MSHA test vs. 0.8039 on
oil validation. Precision is where the domain gap actually lives: 0.8920 on
MSHA test, down to 0.6308 on oil validation. The model isn't failing to
recognize danger in oilfield text at a meaningfully different rate than in
mining text; it's failing to *rule out* safe oilfield text at a much higher
rate.

## Why: vocabulary blindness, not just domain drift

TF-IDF's feature space is fixed at fit time to the vocabulary observed in the
MSHA training narratives. A term that never appears in that training corpus
has no column in the vectorizer's output at all — it isn't down-weighted, it
is **absent as a feature**. Oilfield-specific vocabulary for real precursors
(drilling/well-servicing/rig terminology, IOGP Life-Saving-Rule-adjacent
phrasing that doesn't overlap with MSHA's mining narratives) is invisible to
the classifier in this sense: those words contribute nothing to the decision,
positive or negative, no matter how strongly they'd signal risk to a human
reader. The classifier is left leaning on whatever MSHA-vocabulary overlap
happens to exist in an oilfield narrative, which is a weaker and noisier
signal than the domain-specific language actually driving the report.

## Failure mode: over-flagging, not under-flagging

The oil validation confusion matrix shows the model erring toward false
positives over false negatives — 48 FP vs. 20 FN. For a safety-precursor
triage tool, that's the safer direction to be wrong in: an over-flagged
report costs someone a few minutes of review; an under-flagged one is a real
SIF precursor going unreviewed.

That said, this isn't a free pass — 20 of the 102 real-positive oilfield
reports (FN + TP) were missed, a ~19.6% miss rate on genuine precursors,
i.e. roughly **1 in 5 real oilfield SIF precursors still slip through**
uncaught. The over-flagging tendency reduces the cost of the model's
mistakes; it does not eliminate the cost of the ones it still makes.

## This is a ranking failure, not a calibration one

Two real predictions from the live `/api/dashboard/summary` output, both on
`oil_validation.csv` narratives:

- `NONSIF_ADM`, *"A minor formatting error was found in the weekly
  non-operational activity report."* — **0.888**, the single highest-confidence
  positive prediction in the whole set.
- `LSR_LOF`, *"A wire rope sling parted under load during a pipe-handling job
  on the catwalk, sending the pipe rolling toward the crew."* — **0.251**,
  called negative.

A formatting error outranks a sling failure that sent a pipe rolling toward a
crew. No single decision threshold fixes this: the two scores are on the
wrong sides of each other, not just the wrong side of some cutoff. Moving the
threshold up to reject the formatting-error false positive (0.888) would only
push the sling-failure false negative (0.251) further from being caught, not
closer — they'd both still be wrong, and the true positive would be wronger.
The 0.5 cutoff isn't miscalibrated on this pair; the model's underlying
ranking of the two narratives is inverted. That's the vocabulary-blindness
problem above showing up directly in a live response rather than staying
implicit in an aggregate metric — worth reading as a concrete instance of it,
not a separate issue.
