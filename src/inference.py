from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from .pipeline import phishing_probability, threshold_predict


REQUIRED_BUNDLE_KEYS = {
    "model_name",
    "model_version",
    "threshold",
    "feature_columns",
    "feature_schema",
    "model",
}


def load_model_bundle(path: str | Path) -> dict[str, Any]:
    bundle = joblib.load(path)
    missing = REQUIRED_BUNDLE_KEYS - set(bundle)
    if missing:
        raise ValueError(f"Model bundle missing required keys: {sorted(missing)}")
    return bundle


def validate_records(records: list[dict[str, Any]], bundle: dict[str, Any]) -> pd.DataFrame:
    if not records:
        raise ValueError("At least one record is required.")

    expected = list(bundle["feature_columns"])
    expected_set = set(expected)
    schema = dict(bundle["feature_schema"])
    normalized: list[dict[str, Any]] = []

    for index, record in enumerate(records):
        received = set(record)
        missing = sorted(expected_set - received)
        unexpected = sorted(received - expected_set)
        if missing or unexpected:
            raise ValueError(
                f"Record {index} schema mismatch: missing={missing}, unexpected={unexpected}"
            )

        row: dict[str, Any] = {}
        for column in expected:
            value = record[column]
            if value is None:
                row[column] = None
                continue

            if schema.get(column) == "numeric":
                try:
                    numeric = float(value)
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"Record {index} feature '{column}' must be numeric or null."
                    ) from exc
                if not math.isfinite(numeric):
                    raise ValueError(f"Record {index} feature '{column}' must be finite or null.")
                row[column] = numeric
            else:
                row[column] = str(value)

        normalized.append(row)

    return pd.DataFrame(normalized, columns=expected)


def predict_records(records: list[dict[str, Any]], bundle: dict[str, Any]) -> list[dict[str, Any]]:
    frame = validate_records(records, bundle)
    probabilities = phishing_probability(bundle["model"], frame)
    predictions = threshold_predict(probabilities, float(bundle["threshold"]))

    output = []
    for probability, prediction in zip(probabilities, predictions):
        output.append(
            {
                "phishing_probability": float(probability),
                "predicted_class": int(prediction),
                "predicted_label": "phishing" if int(prediction) == 0 else "legitimate",
                "threshold": float(bundle["threshold"]),
                "model_name": str(bundle["model_name"]),
                "model_version": str(bundle["model_version"]),
            }
        )
    return output
