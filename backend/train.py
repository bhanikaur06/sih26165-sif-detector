import os
import sys

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BACKEND_DIR)
MSHA_PATH = os.path.join(REPO_ROOT, "data", "processed", "msha_labeled.csv")
OIL_VALIDATION_PATH = os.path.join(REPO_ROOT, "data", "processed", "oil_validation.csv")
MODELS_DIR = os.path.join(BACKEND_DIR, "models")
REQUIRED_COLUMNS = {"doc_id", "narrative", "sif_label", "source_code", "split"}


def load_csv(path):
    if not os.path.exists(path):
        sys.exit(f"Missing {path} — run the data track pipeline first.")
    df = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        sys.exit(f"{path} is missing expected columns: {sorted(missing)}")
    df["narrative"] = df["narrative"].fillna("")
    return df


def print_metrics(label, y_true, y_pred):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    print(f"\n{label} (n={len(y_true)})")
    print(f"  TP: {tp}  FP: {fp}  TN: {tn}  FN: {fn}")
    print(f"  accuracy:  {accuracy_score(y_true, y_pred):.4f}")
    print(f"  precision: {precision_score(y_true, y_pred, zero_division=0):.4f}")
    print(f"  recall:    {recall_score(y_true, y_pred, zero_division=0):.4f}")
    print(f"  f1:        {f1_score(y_true, y_pred, zero_division=0):.4f}")


def main():
    msha_df = load_csv(MSHA_PATH)

    train_df = msha_df[msha_df["split"] == "train"]
    test_df = msha_df[msha_df["split"] == "test"]

    if train_df.empty:
        sys.exit(f"No rows with split == 'train' in {MSHA_PATH}")
    if test_df.empty:
        sys.exit(f"No rows with split == 'test' in {MSHA_PATH}")

    vectorizer = TfidfVectorizer()
    X_train = vectorizer.fit_transform(train_df["narrative"])
    y_train = train_df["sif_label"]

    classifier = LogisticRegression(class_weight="balanced", max_iter=1000)
    classifier.fit(X_train, y_train)

    X_test = vectorizer.transform(test_df["narrative"])
    y_test = test_df["sif_label"]
    y_test_pred = classifier.predict(X_test)
    print_metrics("MSHA test split", y_test, y_test_pred)

    oil_df = load_csv(OIL_VALIDATION_PATH)
    X_oil = vectorizer.transform(oil_df["narrative"])
    y_oil = oil_df["sif_label"]
    y_oil_pred = classifier.predict(X_oil)
    print_metrics("Oil validation set (domain transfer, not part of MSHA split)", y_oil, y_oil_pred)

    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(vectorizer, os.path.join(MODELS_DIR, "tfidf_vectorizer.joblib"))
    joblib.dump(classifier, os.path.join(MODELS_DIR, "classifier.joblib"))
    print(f"\nSaved vectorizer and classifier to {MODELS_DIR}")


if __name__ == "__main__":
    main()
