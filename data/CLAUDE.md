# Data track — CLAUDE.md

Scope: this folder owns acquiring, cleaning, and labeling the training data.
See the root `CLAUDE.md` for the shared schema and API contract — don't
duplicate it here, just follow it.

## Responsibilities

1. Download the MSHA Accident Injuries flat file from
   https://www.msha.gov/mine-data-retrieval-system
2. Keep raw downloads in `data/raw/` (gitignored — too large to commit, and
   refreshed weekly upstream anyway)
3. Map `IMMEDNOTIFYCD` to a binary `sif_label` — document the exact mapping
   used in `data/processed/LABEL_MAPPING.md`, since this is a judgment call an
   evaluator will ask about
4. Clean and split into train/val/test, output to
   `data/processed/msha_labeled.csv` matching the root contract's schema
   exactly
5. Hand-write or adapt 150-200 realistic Indian-oilfield-style UA/UC reports as
   `data/processed/oil_validation.csv` — this is the honest domain-transfer
   evidence, keep it separate from the MSHA split

## Out of scope

Model training and the life-saving-rule tagger belong to `/backend`. This
folder stops at producing the labeled CSV.
