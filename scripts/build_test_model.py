from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from src.monitor import build_monitoring_profile
from src.pipeline import build_preprocessor, clean_dataset


def build_fixture(output: Path) -> None:
    raw = pd.DataFrame(
        {
            "NoOfImage": [1, 12, 2, 15, 3, 18, 4, 20],
            "Industry": [
                "finance",
                "retail",
                "finance",
                "retail",
                "finance",
                "retail",
                "finance",
                "retail",
            ],
            "label": [0, 1, 0, 1, 0, 1, 0, 1],
        }
    )
    X, y = clean_dataset(raw)
    model = Pipeline(
        [
            ("preprocess", build_preprocessor(X)),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )
    model.fit(X, y)

    artifact = {
        "model_name": "logistic_regression_ci_fixture",
        "model_version": "ci-fixture-v1",
        "created_at_utc": "1970-01-01T00:00:00+00:00",
        "threshold": 0.5,
        "target": "label",
        "random_state": 42,
        "feature_columns": list(X.columns),
        "feature_schema": {
            column: (
                "numeric"
                if pd.api.types.is_numeric_dtype(X[column])
                else "categorical"
            )
            for column in X.columns
        },
        "monitoring_profile": build_monitoring_profile(X),
        "model": model,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, output)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a deterministic CI-only model fixture.")
    parser.add_argument("--output", default="artifacts/best_model.joblib")
    args = parser.parse_args()
    output = Path(args.output)
    build_fixture(output)
    print(output)


if __name__ == "__main__":
    main()
