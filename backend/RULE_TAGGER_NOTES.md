# Rule tagger notes — IOGP Life-Saving Rule keyword tagger

Produced by `rule_tagger.py`. Pure keyword/phrase matching against the nine
IOGP Life-Saving Rule categories — no model, no training, deliberately
separate from the classifier in `train.py` per `backend/CLAUDE.md`.

## Headline figure: 76% (73/96)

`tag_narrative()` was run against all 174 real narratives in
`data/processed/oil_validation.csv` and compared to each row's `source_code`.
96 of those 174 rows carry an `LSR_*` code that maps onto one of the nine
required categories (`LSR_GAS`, a tenth "general gas/leak" category the data
track added, doesn't map to any of the nine and is excluded from this count).
73 of those 96 were tagged to the expected category — **76%**.

This is **not accuracy against verified ground truth**. `source_code` is the
category the report was *written to represent* by the data track's generation
script, not a hand-labeled or independently verified tag — it's an
illustrative label, useful as a real-text sanity check on the tagger's
behavior, but not a benchmark to optimize against as if it were gold-standard
data. Several of the "misses" below are cases where the tagger's answer is
arguably as defensible as the intended one; see the multi-rule-sentence
bucket.

## Three concrete bugs found and fixed

Found by reading the full 174-row output, not by trusting the aggregate
score:

1. **Missing Driving vocabulary.** `"Vehicle brakes were reported as spongy...
   but the truck was driven anyway"` tagged `None`. The keyword list had
   `driver`/`driving` but never `vehicle`, `truck`, `drove`, or `driven`.
   Added all four.
2. **No plural matching.** `"Seatbelts were not worn by two passengers..."`
   tagged `None` — the regex only matched singular `seatbelt`. Every keyword
   pattern now tolerates an optional trailing `s`.
3. **Tiebreak order bug.** `"Operator stood directly under a suspended load
   while guiding a crane..."` tagged Safe Mechanical Lifting instead of Line
   of Fire, despite an exact `"suspended load"` hit — the tiebreak priority
   list ranked Lifting above Line of Fire, so a 1-1 tie went the wrong way.
   Reordered so Line of Fire outranks Lifting on ties. Isolating this one
   change against the full 174-row set (keywords and plural handling held
   fixed) showed it touched exactly 2 rows, both corrected, zero regressions
   elsewhere — a narrow, contained fix, not a source of new false positives.

Score before all three fixes: 63/96. After: 73/96.

## Two honest failure-mode buckets for what's still wrong

**Vocabulary gaps** — the narrative describes the violation in language the
keyword list doesn't cover, and a keyword tagger has no way to generalize
past what's enumerated:
- `"Relief valve on the flowline manifold was found gagged with a bolted
  flange"` → `None` (intended Bypassing Safety Controls) — "gagged" isn't
  vocabulary that was anticipated.
- `"A painter was observed standing on the handrail of the catwalk..."` →
  `None` (intended Working at Height) — no "harness"/"scaffold"/"ladder"/etc.
  present, just "handrail" and "catwalk."

**Genuine multi-rule sentences** — both the tagger's answer and the intended
answer are actually present in the text; no amount of better keywords fixes
this because it isn't a vocabulary problem, it's two real signals in one
sentence:
- `"Isolation of a heater's fuel gas line was confirmed verbally but... hot
  work began nearby"` → tagged Hot Work (literal `"hot work"` hit), data
  track intended Energy Isolation. The sentence genuinely describes both.
- `"High-level alarm... found silenced... with no corresponding work
  permit..."` → tagged Work Authorisation via `"work permit"`, intended
  Bypassing Safety Controls. Same story — a silenced alarm *and* a missing
  permit are both actually in the sentence.

## False-positive rate: 6/78, not chased further

6 of the 78 rows whose `source_code` is not an LSR category (72 `NONSIF_*`
rows plus the 6 `LSR_GAS` rows, both correctly out of scope for these nine
categories) still got tagged to one of the nine anyway — e.g. `"A driver
mentioned the seat cushioning..."` → Driving, `"A clerk... asked for a
rolling ladder..."` → Working at Height, `"A routine vehicle service
record..."` → Driving.

All six trace back to the same cause: single common words (`driver`,
`ladder`, `vehicle`) that are genuine, necessary keywords for their category
but also appear constantly in ordinary, non-hazard sentences. Tightening
those specific keywords to reduce false positives was not done, because the
fix that adding `vehicle` provided (closing two real Driving misses) came
paired with exactly this kind of false positive — the same word that catches
`"the truck was driven anyway"` also catches `"a routine vehicle service
record."` Removing the keyword to kill the false positive would reopen the
misses it fixed; tightening it to a longer, safer phrase would just recreate
the original vocabulary-gap problem. This is a structural limit of
keyword-only tagging, not a bug worth chasing with more keyword surgery.

It's also lower-stakes than the raw number suggests: `rule_tagger.py` doesn't
know about `sif_label` and never will (kept as a separate component from the
classifier by design). Once wired into `app.py`, `life_saving_rule` is only
meaningful alongside a positive SIF classification — and these 6 false
positives are all on reports the classifier should itself be scoring as
non-SIF, so the tag is unlikely to ever surface in practice for them.
