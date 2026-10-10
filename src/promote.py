from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VALID_STAGES = {"staging", "production"}


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def promote_model(
    *,
    model_path: str | Path,
    deployment_manifest_path: str | Path,
    test_metrics_path: str | Path,
    registry_dir: str | Path,
    stage: str,
    approved_by: str,
    minimum_phishing_recall: float | None = None,
    minimum_phishing_f2: float | None = None,
) -> dict[str, Any]:
    if stage not in VALID_STAGES:
        raise ValueError(f"stage must be one of {sorted(VALID_STAGES)}")
    if not approved_by.strip():
        raise ValueError("approved_by is required")

    model_path = Path(model_path)
    deployment_manifest_path = Path(deployment_manifest_path)
    test_metrics_path = Path(test_metrics_path)
    manifest = load_json(deployment_manifest_path)
    metrics = load_json(test_metrics_path)

    expected_sha = str(manifest.get("model_sha256", "")).strip().lower()
    actual_sha = sha256_file(model_path)
    if not expected_sha or not hmac.compare_digest(expected_sha, actual_sha):
        raise ValueError("Model artifact does not match deployment manifest SHA-256.")

    model_version = str(manifest.get("model_version", "")).strip()
    if not model_version:
        raise ValueError("deployment manifest is missing model_version")

    phishing_recall = float(metrics["phishing_recall"])
    phishing_f2 = float(metrics["phishing_f2"])
    if minimum_phishing_recall is not None and phishing_recall < minimum_phishing_recall:
        raise ValueError("Locked-test phishing recall is below the promotion gate.")
    if minimum_phishing_f2 is not None and phishing_f2 < minimum_phishing_f2:
        raise ValueError("Locked-test phishing F2 is below the promotion gate.")

    destination = Path(registry_dir) / model_version / stage
    if destination.exists():
        raise FileExistsError(
            f"Immutable promotion destination already exists: {destination}"
        )
    destination.mkdir(parents=True, exist_ok=False)

    artifact_destination = destination / "model.joblib"
    shutil.copy2(model_path, artifact_destination)
    shutil.copy2(deployment_manifest_path, destination / "deployment_manifest.json")
    shutil.copy2(test_metrics_path, destination / "test_metrics.json")

    promotion = {
        "model_name": manifest.get("model_name"),
        "model_version": model_version,
        "stage": stage,
        "approved_by": approved_by.strip(),
        "promoted_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_sha256": actual_sha,
        "locked_test": {
            "phishing_recall": phishing_recall,
            "phishing_f2": phishing_f2,
            "roc_auc": metrics.get("roc_auc"),
            "average_precision": metrics.get("average_precision"),
        },
        "promotion_gates": {
            "minimum_phishing_recall": minimum_phishing_recall,
            "minimum_phishing_f2": minimum_phishing_f2,
        },
    }
    (destination / "promotion.json").write_text(
        json.dumps(promotion, indent=2),
        encoding="utf-8",
    )
    return promotion


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Promote a verified immutable model artifact into a local release registry."
    )
    parser.add_argument("--model-path", default="artifacts/best_model.joblib")
    parser.add_argument(
        "--deployment-manifest",
        default="outputs/deployment_manifest.json",
    )
    parser.add_argument("--test-metrics", default="artifacts/test_metrics.json")
    parser.add_argument("--registry-dir", default="registry")
    parser.add_argument("--stage", choices=sorted(VALID_STAGES), required=True)
    parser.add_argument("--approved-by", required=True)
    parser.add_argument("--min-phishing-recall", type=float)
    parser.add_argument("--min-phishing-f2", type=float)
    args = parser.parse_args()

    promotion = promote_model(
        model_path=args.model_path,
        deployment_manifest_path=args.deployment_manifest,
        test_metrics_path=args.test_metrics,
        registry_dir=args.registry_dir,
        stage=args.stage,
        approved_by=args.approved_by,
        minimum_phishing_recall=args.min_phishing_recall,
        minimum_phishing_f2=args.min_phishing_f2,
    )
    print(json.dumps(promotion, indent=2))


if __name__ == "__main__":
    main()
