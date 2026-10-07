from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from .monitor import build_monitoring_profile
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    parser.add_argument(
        "--model-version",
        default="",
        help="Optional immutable model version. Defaults to a UTC timestamp.",
    )
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

    created_at = datetime.now(timezone.utc).isoformat()
    model_version = args.model_version.strip() or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    feature_schema = {
        column: ("numeric" if pd.api.types.is_numeric_dtype(splits.X_train[column]) else "categorical")
        for column in splits.X_train.columns
    }

    artifact = {
        "model_name": best_name,
        "model_version": model_version,
        "created_at_utc": created_at,
        "threshold": float(best_threshold),
        "target": args.target,
        "random_state": args.random_state,
        "feature_columns": list(splits.X_train.columns),
        "feature_schema": feature_schema,
        "monitoring_profile": build_monitoring_profile(splits.X_train),
        "model": best_model,
    }

    model_out = Path(args.model_out)
    model_out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, model_out)
    model_sha256 = sha256_file(model_out)

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

    deployment_manifest = {
        "model_name": best_name,
        "model_version": model_version,
        "model_sha256": model_sha256,
        "created_at_utc": created_at,
        "threshold": float(best_threshold),
        "stage": "candidate",
        "selection_metric": "validation average precision; phishing F2 tie-break",
        "promotion_note": "Review validation metrics and locked-test results before promoting this immutable artifact.",
    }
    (outputs_dir / "deployment_manifest.json").write_text(
        json.dumps(deployment_manifest, indent=2), encoding="utf-8"
    )

    summary = {
        "rows": int(len(X)),
        "features": int(X.shape[1]),
        "best_model": best_name,
        "model_version": model_version,
        "model_sha256": model_sha256,
        "selected_threshold": best_threshold,
        "selection_metric": "validation average precision; phishing F2 tie-break",
        "best_validation_metrics": {
            key: value
            for key, value in best_metrics.items()
            if key != "classification_report"
        },
        "deployment_manifest": str(outputs_dir / "deployment_manifest.json"),
    }
    (outputs_dir / "training_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    print(json.dumps(summary, indent=2))
    print(f"Saved model artifact: {model_out}")


if __name__ == "__main__":
    main()
