# Backend track — CLAUDE.md

Scope: this folder owns the classifier, the life-saving-rule tagger, and the
API server. See root `CLAUDE.md` for the schema and API contract this must
satisfy.

## Responsibilities

1. Read `data/processed/msha_labeled.csv` — do not modify it, that file
   belongs to the data track
2. Train a TF-IDF + logistic regression (or linear SVM) classifier on
   `narrative` -> `sif_label`. Use `class_weight='balanced'` given the
   expected class imbalance
3. Build a keyword/rule-based tagger mapping narratives to IOGP Life-Saving
   Rules (energy isolation, hot work, confined space, line of fire, etc.) as a
   separate component from the classifier — don't force one model to do both
   jobs
4. Report accuracy separately on the MSHA test split and on
   `data/processed/oil_validation.csv` — the gap between them is the real
   result, not something to hide
5. Serve `POST /api/classify` and `GET /api/dashboard/summary` exactly
   matching the root contract's request/response shapes
6. Save trained artifacts to `backend/models/` (gitignored — regenerate via
   `backend/train.py`, don't commit binaries)

## Suggested framework

Flask is the simplest fit for a small sklearn-backed API. If FastAPI is
preferred instead, decide before frontend starts hitting real endpoints and
note the choice here.
