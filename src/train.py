from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from .pipeline import (
    build_preprocessor,
    clean_dataset,
    phishing_probability,
    select_threshold,
    split_data,
)


def fit_candidate(name: str, classifier, X_train, y_train, X_val, y_val):
    model = Pipeline(
        [
            ("preprocess", build_preprocessor(X_train)),
            ("classifier", classifier),
        ]
    )
    model.fit(X_train, y_train)
    probs = phishing_probability(model, X_val)
    threshold, metrics = select_threshold(y_val, probs, beta=2.0)
    return name, model, threshold, metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and compare phishing classifiers.")
    parser.add_argument("--data", required=True, help="Path to the phishing CSV dataset.")
    parser.add_argument("--target", default="label", help="Target column name.")
    parser.add_argument(
        "--model-out",
        default="artifacts/best_model.joblib",
        help="Output path for the selected model artifact.",
    )
    parser.add_argument(
        "--metrics-out",
        default="artifacts/validation_metrics.json",
        help="Output path for validation metrics JSON.",
    )
    parser.add_argument("--outputs-dir", default="outputs", help="Generated report directory.")
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args()

    raw = pd.read_csv(args.data)
    X, y = clean_dataset(raw, target=args.target)
    splits = split_data(X, y, random_state=args.random_state)

    candidates = [
        (
            "logistic_regression",
            LogisticRegression(
                max_iter=2000,
                class_weight="balanced",
                random_state=args.random_state,
            ),
        ),
        (
            "random_forest",
            RandomForestClassifier(
                n_estimators=300,
                class_weight="balanced_subsample",
                random_state=args.random_state,
                n_jobs=-1,
            ),
        ),
        (
            "extra_trees",
            ExtraTreesClassifier(
                n_estimators=300,
                class_weight="balanced",
                random_state=args.random_state,
                n_jobs=-1,
            ),
        ),
    ]

    results = [
        fit_candidate(
            name,
            classifier,
            splits.X_train,
            splits.y_train,
            splits.X_val,
            splits.y_val,
        )
        for name, classifier in candidates
    ]

    best_name, best_model, best_threshold, best_metrics = sorted(
        results,
        key=lambda item: (
            item[3]["average_precision"],
            item[3]["phishing_f2"],
            item[3]["phishing_recall"],
        ),
        reverse=True,
    )[0]

    artifact = {
        "model_name": best_name,
        "threshold": best_threshold,
        "target": args.target,
        "random_state": args.random_state,
        "feature_columns": list(splits.X_train.columns),
        "model": best_model,
    }

    model_out = Path(args.model_out)
    model_out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, model_out)

    metrics_out = Path(args.metrics_out)
    metrics_out.parent.mkdir(parents=True, exist_ok=True)
    metrics_payload = {
        name: {"threshold": threshold, **metrics}
        for name, _, threshold, metrics in results
    }
    metrics_out.write_text(json.dumps(metrics_payload, indent=2), encoding="utf-8")

    outputs_dir = Path(args.outputs_dir)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for name, _, threshold, metrics in results:
        rows.append(
            {
                "model": name,
                "threshold": threshold,
                "phishing_precision": metrics["phishing_precision"],
                "phishing_recall": metrics["phishing_recall"],
                "phishing_f1": metrics["phishing_f1"],
                "phishing_f2": metrics["phishing_f2"],
                "roc_auc": metrics["roc_auc"],
                "average_precision": metrics["average_precision"],
            }
        )
        (outputs_dir / f"validation_report_{name}.txt").write_text(
            metrics["classification_report"], encoding="utf-8"
        )

    pd.DataFrame(rows).sort_values(
        ["average_precision", "phishing_f2"], ascending=False
    ).to_csv(outputs_dir / "validation_model_comparison.csv", index=False)

    summary = {
        "rows": int(len(X)),
        "features": int(X.shape[1]),
        "best_model": best_name,
        "selected_threshold": best_threshold,
        "selection_metric": "validation average precision; phishing F2 tie-break",
        "best_validation_metrics": {
            key: value
            for key, value in best_metrics.items()
            if key != "classification_report"
        },
    }
    (outputs_dir / "training_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    print(json.dumps(summary, indent=2))
    print(f"Saved model artifact: {model_out}")


if __name__ == "__main__":
    main()
