import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from src.inference import predict_records, validate_records
from src.pipeline import build_preprocessor, clean_dataset


def _bundle():
    raw = pd.DataFrame(
        {
            "NoOfImage": [1, 12, 2, 15, 3, 18],
            "Industry": ["finance", "retail", "finance", "retail", "finance", "retail"],
            "label": [0, 1, 0, 1, 0, 1],
        }
    )
    X, y = clean_dataset(raw)
    model = Pipeline(
        [
            ("preprocess", build_preprocessor(X)),
            ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )
    model.fit(X, y)
    return {
        "model_name": "logistic_regression",
        "model_version": "test-v1",
        "threshold": 0.5,
        "feature_columns": ["NoOfImage", "Industry"],
        "feature_schema": {"NoOfImage": "numeric", "Industry": "categorical"},
        "model": model,
    }


def test_validate_records_enforces_exact_schema():
    bundle = _bundle()
    frame = validate_records([{"NoOfImage": 3, "Industry": "finance"}], bundle)
    assert list(frame.columns) == bundle["feature_columns"]

    try:
        validate_records([{"NoOfImage": 3}], bundle)
    except ValueError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("Missing feature should fail schema validation")


def test_predict_records_uses_bundle_threshold_and_version():
    bundle = _bundle()
    result = predict_records([{"NoOfImage": 3, "Industry": "finance"}], bundle)[0]
    assert 0.0 <= result["phishing_probability"] <= 1.0
    assert result["predicted_label"] in {"phishing", "legitimate"}
    assert result["threshold"] == 0.5
    assert result["model_version"] == "test-v1"
