from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd

from .pipeline import (
    clean_dataset,
    evaluate_predictions,
    phishing_probability,
    split_data,
    threshold_predict,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a locked phishing model on the test split.")
    parser.add_argument("--data", required=True, help="Path to the phishing CSV dataset.")
    parser.add_argument(
        "--model-path",
        default="artifacts/best_model.joblib",
        help="Path to the saved model artifact.",
    )
    parser.add_argument("--outputs-dir", default="outputs")
    parser.add_argument(
        "--metrics-out",
        default="artifacts/test_metrics.json",
        help="Path to test metrics JSON.",
    )
    args = parser.parse_args()

    artifact = joblib.load(args.model_path)
    target = artifact.get("target", "label")
    random_state = int(artifact.get("random_state", 42))
    threshold = float(artifact["threshold"])
    model = artifact["model"]

    raw = pd.read_csv(args.data)
    X, y = clean_dataset(raw, target=target)
    splits = split_data(X, y, random_state=random_state)

    probs = phishing_probability(model, splits.X_test)
    y_pred = threshold_predict(probs, threshold)
    metrics = evaluate_predictions(splits.y_test, y_pred, probs)
    metrics["threshold"] = threshold
    metrics["model_name"] = artifact.get("model_name", "unknown")

    metrics_out = Path(args.metrics_out)
    metrics_out.parent.mkdir(parents=True, exist_ok=True)
    metrics_out.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    outputs_dir = Path(args.outputs_dir)
    outputs_dir.mkdir(parents=True, exist_ok=True)
    (outputs_dir / "test_classification_report.txt").write_text(
        metrics["classification_report"], encoding="utf-8"
    )

    predictions = pd.DataFrame(
        {
            "y_true": splits.y_test.reset_index(drop=True),
            "phishing_probability": probs,
            "y_pred": y_pred,
        }
    )
    predictions.to_csv(outputs_dir / "test_predictions.csv", index=False)

    printable = {k: v for k, v in metrics.items() if k != "classification_report"}
    print(json.dumps(printable, indent=2))


if __name__ == "__main__":
    main()
