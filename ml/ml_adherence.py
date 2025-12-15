
import json
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REPORT = ROOT / "report"
REPORT.mkdir(parents=True, exist_ok=True)

events_path = DATA / "events.csv"
if not events_path.exists():
    raise SystemExit("[ml] data/events.csv missing. Run the app seed or perceive step first.")

df = pd.read_csv(events_path)

# ---- Features (simple + explainable) ----
# completed is the label (0/1)
# Use columns that exist in your events.csv
needed_cols = ["est_min", "done_min", "reminders", "completed", "subject"]
missing = [c for c in needed_cols if c not in df.columns]
if missing:
    raise SystemExit(f"[ml] Missing columns in events.csv: {missing}")

# Feature engineering (keep it minimal)
df["effort_ratio"] = np.where(df["est_min"] > 0, df["done_min"] / df["est_min"], 0.0)
df["reminders_norm"] = df["reminders"].fillna(0).astype(float)
df["est_min"] = df["est_min"].fillna(0).astype(float)

X = df[["est_min", "effort_ratio", "reminders_norm"]].values
y = df["completed"].astype(int).values

unique = np.unique(y)

def baseline_predict_proba(row):
    """
    Very simple baseline:
    - if effort_ratio >= 0.9 -> high chance
    - else if reminders >= 2 -> medium
    - else -> low
    """
    est, ratio, rem = row
    if ratio >= 0.9:
        return 0.85
    if rem >= 2:
        return 0.60
    return 0.35

results = {}

# ---- Case A: Not enough class diversity -> baseline ----
if len(unique) < 2:
    p_hat = np.array([baseline_predict_proba(r) for r in X], dtype=float)
    pred = (p_hat >= 0.5).astype(int)

    results["mode"] = "baseline_fallback_single_class"
    results["reason"] = f"Training labels have only one class: {int(unique[0])}. Need both 0 and 1."
    results["overall_positive_rate"] = float(np.mean(y))
    results["baseline_accuracy_on_seen"] = float(np.mean(pred == y))
else:
    # ---- Case B: Train Logistic Regression ----
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    clf = LogisticRegression(max_iter=500)
    clf.fit(X_train, y_train)

    p_test = clf.predict_proba(X_test)[:, 1]
    pred_test = (p_test >= 0.5).astype(int)

    results["mode"] = "logistic_regression"
    results["test_accuracy"] = float(np.mean(pred_test == y_test))
    results["coef"] = {
        "est_min": float(clf.coef_[0][0]),
        "effort_ratio": float(clf.coef_[0][1]),
        "reminders_norm": float(clf.coef_[0][2]),
        "intercept": float(clf.intercept_[0]),
    }

    # For reporting, compute probs for all rows too
    p_hat = clf.predict_proba(X)[:, 1]

# ---- Per-subject aggregation (nice for your ISD demo) ----
df["p_complete"] = p_hat
by_subject = (
    df.groupby("subject")[["p_complete", "completed"]]
      .agg(p_pred_mean=("p_complete", "mean"),
           actual_completion_rate=("completed", "mean"),
           n=("completed", "count"))
      .reset_index()
)

results["per_subject"] = by_subject.to_dict(orient="records")

out_path = REPORT / "ml_adherence_report.json"
out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

print("[ml] wrote report/rl_adherence_report.json" if False else "[ml] wrote report/ml_adherence_report.json")
print(json.dumps(results, indent=2))

