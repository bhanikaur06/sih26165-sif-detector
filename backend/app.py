import os
import sys

import joblib
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

from rule_tagger import tag_narrative

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BACKEND_DIR)
MODELS_DIR = os.path.join(BACKEND_DIR, "models")
VECTORIZER_PATH = os.path.join(MODELS_DIR, "tfidf_vectorizer.joblib")
CLASSIFIER_PATH = os.path.join(MODELS_DIR, "classifier.joblib")
OIL_VALIDATION_PATH = os.path.join(REPO_ROOT, "data", "processed", "oil_validation.csv")
CLASSIFICATION_THRESHOLD = 0.5
DASHBOARD_GROUP_COLUMNS = (("subunit", "subunit"), ("activity", "activity"))


def _load_model_artifact(path):
    if not os.path.exists(path):
        sys.exit(f"Missing {path} — run backend/train.py first to generate model artifacts.")
    return joblib.load(path)


vectorizer = _load_model_artifact(VECTORIZER_PATH)
classifier = _load_model_artifact(CLASSIFIER_PATH)


def classify_narrative(narrative):
    features = vectorizer.transform([narrative])
    probability = float(classifier.predict_proba(features)[0, 1])
    label = int(probability >= CLASSIFICATION_THRESHOLD)
    rule = tag_narrative(narrative) if label == 1 else None
    return probability, label, rule


def _build_dashboard_summary():
    empty_summary = {
        "precursor_density_by_group": [],
        "summary_stats": {"total_reports": 0, "sif_count": 0, "density": 0.0},
        "rule_breakdown": [],
    }
    if not os.path.exists(OIL_VALIDATION_PATH):
        return empty_summary

    df = pd.read_csv(OIL_VALIDATION_PATH)
    df["narrative"] = df["narrative"].fillna("")
    if df.empty:
        return empty_summary

    features = vectorizer.transform(df["narrative"])
    probabilities = classifier.predict_proba(features)[:, 1]
    labels = (probabilities >= CLASSIFICATION_THRESHOLD).astype(int)
    rules = [tag_narrative(n) if label == 1 else None for n, label in zip(df["narrative"], labels)]
    df = df.assign(predicted_label=labels)

    density_rows = []
    for group_type, column in DASHBOARD_GROUP_COLUMNS:
        if column not in df.columns:
            continue
        grouped = df.groupby(column)["predicted_label"].agg(["count", "sum"])
        for group_name, row in grouped.iterrows():
            total = int(row["count"])
            sif_count = int(row["sum"])
            density_rows.append(
                {
                    "group": group_name,
                    "group_type": group_type,
                    "total_reports": total,
                    "sif_count": sif_count,
                    "density": sif_count / total if total else 0.0,
                }
            )
    density_rows.sort(key=lambda row: row["density"], reverse=True)

    rule_counts = {}
    for rule in rules:
        if rule is None:
            continue
        rule_counts[rule] = rule_counts.get(rule, 0) + 1
    rule_breakdown = sorted(
        ({"life_saving_rule": rule, "count": count} for rule, count in rule_counts.items()),
        key=lambda entry: entry["count"],
        reverse=True,
    )

    total_reports = len(df)
    sif_count = int(labels.sum())
    summary_stats = {
        "total_reports": total_reports,
        "sif_count": sif_count,
        "density": sif_count / total_reports if total_reports else 0.0,
    }

    return {
        "precursor_density_by_group": density_rows,
        "summary_stats": summary_stats,
        "rule_breakdown": rule_breakdown,
    }


DASHBOARD_SUMMARY = _build_dashboard_summary()

app = Flask(__name__)
CORS(app)


@app.route("/", methods=["GET"])
def index():
    return jsonify(
        {
            "service": "sif-precursor-detection-api",
            "status": "ok",
            "endpoints": [
                "POST /api/classify",
                "GET /api/dashboard/summary",
            ],
        }
    )


@app.route("/api/classify", methods=["POST"])
def classify():
    payload = request.get_json(silent=True) or {}
    narrative = payload.get("narrative", "")
    probability, label, rule = classify_narrative(narrative)
    return jsonify(
        {
            "sif_probability": probability,
            "sif_label": label,
            "life_saving_rule": rule,
        }
    )


@app.route("/api/dashboard/summary", methods=["GET"])
def dashboard_summary():
    return jsonify(DASHBOARD_SUMMARY)


if __name__ == "__main__":
    port = int(os.environ.get("BACKEND_PORT", "5001"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
