import argparse
import csv
import hashlib
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"

SIF_TRUE_CODES = {f"{i:02d}" for i in range(1, 13)}
SIF_FALSE_CODES = {"13", "NOT_MARKED"}

REQUIRED_COLUMNS = ["DOCUMENT_NO", "NARRATIVE", "IMMED_NOTIFY_CD"]
OPTIONAL_COLUMNS = ["DEGREE_INJURY_CD", "DEGREE_INJURY"]

PASSTHROUGH_COLUMNS = {
    "MINE_ID": "mine_id",
    "OPERATOR_NAME": "operator_name",
    "ACTIVITY": "activity",
    "SUBUNIT": "subunit",
}

MISSING_PLACEHOLDERS = {"", "?", "NO VALUE FOUND"}

TRAIN_FRAC = 0.70
VAL_FRAC = 0.15
TEST_FRAC = 0.15
RANDOM_SEED = 42
MIN_NARRATIVE_CHARS = 15


def find_raw_table(raw_dir):
    zips = sorted(raw_dir.glob("*.zip"))
    for zip_path in zips:
        with zipfile.ZipFile(zip_path) as zf:
            candidates = [n for n in zf.namelist() if not n.endswith("/")]
            candidates = [n for n in candidates if "definition" not in n.lower()]
            if not candidates:
                continue
            best = max(candidates, key=lambda n: zf.getinfo(n).file_size)
            extract_dir = raw_dir / zip_path.stem
            extract_dir.mkdir(exist_ok=True)
            zf.extract(best, extract_dir)
            return extract_dir / best

    flat_candidates = []
    for pattern in ("*.txt", "*.csv", "*.tsv"):
        flat_candidates.extend(raw_dir.glob(pattern))
    flat_candidates = [p for p in flat_candidates if "definition" not in p.name.lower()]
    if flat_candidates:
        return max(flat_candidates, key=lambda p: p.stat().st_size)

    return None


def sniff_delimiter(path):
    with open(path, "r", encoding="latin-1", errors="replace") as f:
        sample = f.read(65536)
    counts = {d: sample.count(d) for d in ["|", ",", "\t"]}
    return max(counts, key=counts.get)


def load_raw_table(path):
    delimiter = sniff_delimiter(path)
    header = pd.read_csv(path, delimiter=delimiter, dtype=str, encoding="latin-1", nrows=0)
    normalised = {col: col.strip().upper() for col in header.columns}

    missing = [c for c in REQUIRED_COLUMNS if c not in normalised.values()]
    if missing:
        raise ValueError(
            f"Raw file {path} is missing expected columns {missing}. "
            f"Columns found: {sorted(normalised.values())}"
        )

    wanted = set(REQUIRED_COLUMNS) | set(OPTIONAL_COLUMNS) | set(PASSTHROUGH_COLUMNS)
    usecols = [orig for orig, norm in normalised.items() if norm in wanted]

    df = pd.read_csv(
        path,
        delimiter=delimiter,
        dtype=str,
        encoding="latin-1",
        usecols=usecols,
        quoting=csv.QUOTE_MINIMAL,
        on_bad_lines="skip",
        low_memory=False,
    )
    df.columns = [normalised[c] for c in df.columns]
    return df


def clean_passthrough(value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    value = " ".join(str(value).split())
    return "" if value.upper() in MISSING_PLACEHOLDERS else value


def clean_narrative(text):
    if text is None or (isinstance(text, float) and np.isnan(text)):
        return None
    text = " ".join(str(text).split())
    return text if text else None


def make_doc_id(mine_id, document_no, index):
    key = f"{mine_id}|{document_no}|{index}".encode("utf-8")
    digest = hashlib.sha1(key).hexdigest()[:10]
    return f"msha_{digest}"


def label_row(code):
    if code in SIF_TRUE_CODES:
        return 1
    if code in SIF_FALSE_CODES:
        return 0
    return None


def apply_blank_code_policy(df, policy):
    is_blank = df["_code_clean"].isna()
    if policy == "negative":
        df.loc[is_blank, "_code_clean"] = "NOT_MARKED"
        return df, 0
    return df[~is_blank].copy(), int(is_blank.sum())


def stratified_split(df, label_col, seed):
    rng = np.random.default_rng(seed)
    parts = []
    for _, group in df.groupby(label_col):
        idx = group.index.to_numpy().copy()
        rng.shuffle(idx)
        n = len(idx)
        n_train = int(round(n * TRAIN_FRAC))
        n_val = int(round(n * VAL_FRAC))
        n_train = min(n_train, n)
        n_val = min(n_val, n - n_train)
        train_idx, val_idx, test_idx = np.split(idx, [n_train, n_train + n_val])
        parts.append((train_idx, val_idx, test_idx))

    split = pd.Series(index=df.index, dtype=object)
    for train_idx, val_idx, test_idx in parts:
        split.loc[train_idx] = "train"
        split.loc[val_idx] = "val"
        split.loc[test_idx] = "test"
    return split


def build(raw_path, out_path, report_path, blank_code_policy):
    raw = load_raw_table(raw_path)
    n_raw = len(raw)

    raw["_narrative_clean"] = raw["NARRATIVE"].map(clean_narrative)
    raw["_code_clean"] = raw["IMMED_NOTIFY_CD"].fillna("").str.strip()
    raw["_code_clean"] = raw["_code_clean"].replace({"": None, "?": None})

    raw, dropped_no_code = apply_blank_code_policy(raw, blank_code_policy)

    dropped_short_narrative = raw["_narrative_clean"].isna().sum() + (
        raw["_narrative_clean"].str.len().fillna(0) < MIN_NARRATIVE_CHARS
    ).sum()
    raw = raw[raw["_narrative_clean"].notna()].copy()
    raw = raw[raw["_narrative_clean"].str.len() >= MIN_NARRATIVE_CHARS].copy()

    before_dedupe = len(raw)
    raw = raw.drop_duplicates(subset=["_narrative_clean"]).copy()
    dropped_duplicates = before_dedupe - len(raw)

    raw["sif_label"] = raw["_code_clean"].map(label_row)
    dropped_unmapped_code = raw["sif_label"].isna().sum()
    raw = raw[raw["sif_label"].notna()].copy()
    raw["sif_label"] = raw["sif_label"].astype(int)

    mine_id_col = raw["MINE_ID"] if "MINE_ID" in raw.columns else pd.Series(["NA"] * len(raw), index=raw.index)
    raw = raw.reset_index(drop=True)
    raw["doc_id"] = [
        make_doc_id(mine_id_col.iloc[i], raw["DOCUMENT_NO"].iloc[i], i) for i in range(len(raw))
    ]

    raw["split"] = stratified_split(raw, "sif_label", RANDOM_SEED)

    out = pd.DataFrame(
        {
            "doc_id": raw["doc_id"],
            "narrative": raw["_narrative_clean"],
            "sif_label": raw["sif_label"],
            "source_code": raw["_code_clean"],
            "split": raw["split"],
        }
    )

    for raw_name, out_name in PASSTHROUGH_COLUMNS.items():
        if raw_name in raw.columns:
            out[out_name] = raw[raw_name].map(clean_passthrough)
        else:
            out[out_name] = ""

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)

    report = {
        "raw_rows": int(n_raw),
        "blank_code_policy": blank_code_policy,
        "dropped_missing_immed_notify_cd": int(dropped_no_code),
        "dropped_missing_or_short_narrative": int(dropped_short_narrative),
        "dropped_duplicate_narrative": int(dropped_duplicates),
        "dropped_unmapped_code": int(dropped_unmapped_code),
        "final_rows": int(len(out)),
        "label_balance_overall": out["sif_label"].value_counts().to_dict(),
        "label_balance_by_split": {
            split_name: out.loc[out["split"] == split_name, "sif_label"]
            .value_counts()
            .to_dict()
            for split_name in ["train", "val", "test"]
        },
        "rows_per_split": out["split"].value_counts().to_dict(),
        "source_code_distribution": out["source_code"].value_counts().to_dict(),
        "grouping_columns": {
            out_name: {
                "populated_rows": int((out[out_name] != "").sum()),
                "fill_rate_pct": round(100 * float((out[out_name] != "").mean()), 1),
                "distinct_values": int(out.loc[out[out_name] != "", out_name].nunique()),
            }
            for out_name in PASSTHROUGH_COLUMNS.values()
        },
    }

    if "DEGREE_INJURY" in raw.columns:
        qa = (
            raw.groupby(["sif_label", raw["DEGREE_INJURY"].fillna("NO VALUE")])
            .size()
            .unstack(fill_value=0)
        )
        report["qa_sif_label_vs_degree_injury"] = {
            str(label): row.to_dict() for label, row in qa.iterrows()
        }
    report_path.write_text(json.dumps(report, indent=2, default=str))

    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-path", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=PROCESSED_DIR / "msha_labeled.csv")
    parser.add_argument("--report", type=Path, default=PROCESSED_DIR / "build_report.json")
    parser.add_argument(
        "--blank-code-policy",
        choices=["drop", "negative"],
        default="drop",
        help="how to treat rows whose IMMED_NOTIFY_CD is '?' / NO VALUE FOUND",
    )
    args = parser.parse_args()

    raw_path = args.raw_path or find_raw_table(RAW_DIR)
    if raw_path is None or not raw_path.exists():
        print(
            f"No raw MSHA table found under {RAW_DIR}. "
            "Download Accidents.zip from "
            "https://arlweb.msha.gov/opengovernmentdata/DataSets/Accidents.zip "
            "and place it there (or pass --raw-path).",
            file=sys.stderr,
        )
        sys.exit(1)

    report = build(raw_path, args.out, args.report, args.blank_code_policy)
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
