import hashlib
import json

import pytest

from src.promote import promote_model


def _write_fixture(tmp_path):
    model_path = tmp_path / "model.joblib"
    model_path.write_bytes(b"immutable-model-bytes")
    digest = hashlib.sha256(model_path.read_bytes()).hexdigest()

    manifest_path = tmp_path / "deployment_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "model_name": "extra_trees",
                "model_version": "test-v1",
                "model_sha256": digest,
            }
        ),
        encoding="utf-8",
    )

    metrics_path = tmp_path / "test_metrics.json"
    metrics_path.write_text(
        json.dumps(
            {
                "phishing_recall": 0.93,
                "phishing_f2": 0.91,
                "roc_auc": 0.95,
                "average_precision": 0.94,
            }
        ),
        encoding="utf-8",
    )
    return model_path, manifest_path, metrics_path


def test_promote_model_creates_immutable_release(tmp_path):
    model_path, manifest_path, metrics_path = _write_fixture(tmp_path)
    registry = tmp_path / "registry"

    promotion = promote_model(
        model_path=model_path,
        deployment_manifest_path=manifest_path,
        test_metrics_path=metrics_path,
        registry_dir=registry,
        stage="staging",
        approved_by="ci",
        minimum_phishing_recall=0.90,
        minimum_phishing_f2=0.90,
    )

    release = registry / "test-v1" / "staging"
    assert promotion["stage"] == "staging"
    assert (release / "model.joblib").exists()
    assert (release / "deployment_manifest.json").exists()
    assert (release / "test_metrics.json").exists()
    assert (release / "promotion.json").exists()

    with pytest.raises(FileExistsError):
        promote_model(
            model_path=model_path,
            deployment_manifest_path=manifest_path,
            test_metrics_path=metrics_path,
            registry_dir=registry,
            stage="staging",
            approved_by="ci",
        )


def test_promote_model_rejects_tampered_artifact(tmp_path):
    model_path, manifest_path, metrics_path = _write_fixture(tmp_path)
    model_path.write_bytes(b"tampered")

    with pytest.raises(ValueError, match="SHA-256"):
        promote_model(
            model_path=model_path,
            deployment_manifest_path=manifest_path,
            test_metrics_path=metrics_path,
            registry_dir=tmp_path / "registry",
            stage="production",
            approved_by="release-manager",
        )
