from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from .pipeline import clean_dataset


EPSILON = 1e-6


def _safe_probabilities(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    values = np.clip(values, EPSILON, None)
    return values / values.sum()


def build_monitoring_profile(frame: pd.DataFrame, max_numeric_bins: int = 10) -> dict[str, Any]:
    profile: dict[str, Any] = {"features": {}}

    for column in frame.columns:
        series = frame[column]
        if pd.api.types.is_numeric_dtype(series):
            non_null = pd.to_numeric(series, errors="coerce").dropna()
            if non_null.empty:
                profile["features"][column] = {
                    "kind": "numeric",
                    "bin_edges": [],
                    "reference_distribution": [1.0],
                    "missing_rate": 1.0,
                }
                continue

            quantiles = np.linspace(0.0, 1.0, min(max_numeric_bins, max(2, non_null.nunique())) + 1)
            edges = np.unique(np.quantile(non_null, quantiles))
            internal_edges = edges[1:-1].astype(float)
            bins = np.concatenate(([-np.inf], internal_edges, [np.inf]))
            counts, _ = np.histogram(non_null.to_numpy(dtype=float), bins=bins)
            distribution = _safe_probabilities(counts)
            profile["features"][column] = {
                "kind": "numeric",
                "bin_edges": internal_edges.tolist(),
                "reference_distribution": distribution.tolist(),
                "missing_rate": float(series.isna().mean()),
            }
        else:
            converted = series.astype("string")
            missing_rate = float(converted.isna().mean())
            counts = converted.dropna().astype(str).value_counts(normalize=True).head(20)
            profile["features"][column] = {
                "kind": "categorical",
                "reference_distribution": {str(k): float(v) for k, v in counts.items()},
                "missing_rate": missing_rate,
            }

    return profile


def compare_monitoring_profile(profile: dict[str, Any], frame: pd.DataFrame) -> dict[str, Any]:
    report: dict[str, Any] = {"features": {}, "alerts": []}

    for column, reference in profile.get("features", {}).items():
        if column not in frame.columns:
            report["alerts"].append({"feature": column, "reason": "missing_feature"})
            continue

        series = frame[column]
        missing_rate = float(series.isna().mean())
        missing_delta = abs(missing_rate - float(reference.get("missing_rate", 0.0)))

        if reference["kind"] == "numeric":
            non_null = pd.to_numeric(series, errors="coerce").dropna()
            internal_edges = np.asarray(reference.get("bin_edges", []), dtype=float)
            bins = np.concatenate(([-np.inf], internal_edges, [np.inf]))
            counts, _ = np.histogram(non_null.to_numpy(dtype=float), bins=bins)
            actual = _safe_probabilities(counts)
            expected = _safe_probabilities(np.asarray(reference["reference_distribution"], dtype=float))
            psi = float(np.sum((actual - expected) * np.log(actual / expected)))
            report["features"][column] = {
                "kind": "numeric",
                "psi": psi,
                "missing_rate": missing_rate,
                "missing_rate_delta": missing_delta,
            }
            if psi >= 0.20 or missing_delta >= 0.10:
                report["alerts"].append(
                    {"feature": column, "reason": "numeric_drift", "psi": psi, "missing_rate_delta": missing_delta}
                )
        else:
            reference_dist = dict(reference.get("reference_distribution", {}))
            converted = series.astype("string").dropna().astype(str)
            current = converted.value_counts(normalize=True).to_dict()
            keys = set(reference_dist) | set(current)
            tv_distance = 0.5 * sum(
                abs(float(reference_dist.get(key, 0.0)) - float(current.get(key, 0.0)))
                for key in keys
            )
            report["features"][column] = {
                "kind": "categorical",
                "total_variation_distance": float(tv_distance),
                "missing_rate": missing_rate,
                "missing_rate_delta": missing_delta,
            }
            if tv_distance >= 0.20 or missing_delta >= 0.10:
                report["alerts"].append(
                    {
                        "feature": column,
                        "reason": "categorical_drift",
                        "total_variation_distance": float(tv_distance),
                        "missing_rate_delta": missing_delta,
                    }
                )

    report["status"] = "alert" if report["alerts"] else "ok"
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare a scoring batch with the training reference profile.")
    parser.add_argument("--data", required=True, help="CSV containing current scoring features.")
    parser.add_argument("--model-path", default="artifacts/best_model.joblib")
    parser.add_argument("--output", default="outputs/drift_report.json")
    args = parser.parse_args()

    bundle = joblib.load(args.model_path)
    raw = pd.read_csv(args.data)
    target = bundle.get("target", "label")
    if target in raw.columns:
        frame, _ = clean_dataset(raw, target=target)
    else:
        unnamed = [c for c in raw.columns if str(c).lower().startswith("unnamed")]
        frame = raw.drop(columns=unnamed, errors="ignore")

    expected = list(bundle["feature_columns"])
    missing = sorted(set(expected) - set(frame.columns))
    if missing:
        raise ValueError(f"Monitoring batch is missing required features: {missing}")

    report = compare_monitoring_profile(bundle["monitoring_profile"], frame[expected])
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "alerts": len(report["alerts"])}, indent=2))


if __name__ == "__main__":
    main()
