import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from src.pipeline import (
    PHISHING_LABEL,
    build_preprocessor,
    clean_dataset,
    phishing_probability,
    select_threshold,
    threshold_predict,
)


def synthetic_data(n: int = 80) -> pd.DataFrame:
    rows = []
    for i in range(n):
        phishing = 0 if i % 2 == 0 else 1
        rows.append(
            {
                "Unnamed: 0": i,
                "NoOfImage": -3 if i == 0 else (2 + i % 7),
                "DomainAgeMonths": 2 + (i % 30),
                "LargestLineLength": 50 + i,
                "Industry": "finance" if i % 3 == 0 else "retail",
                "HostingProvider": "A" if i % 4 < 2 else "B",
                "label": phishing,
            }
        )
    return pd.DataFrame(rows)


def test_clean_dataset_drops_index_and_invalid_negative() -> None:
    X, y = clean_dataset(synthetic_data())
    assert "Unnamed: 0" not in X.columns
    assert pd.isna(X.loc[0, "NoOfImage"])
    assert set(y.unique()) == {0, 1}


def test_model_probability_and_threshold_selection() -> None:
    X, y = clean_dataset(synthetic_data())
    model = Pipeline(
        [
            ("preprocess", build_preprocessor(X)),
            ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )
    model.fit(X, y)
    probs = phishing_probability(model, X)
    threshold, metrics = select_threshold(y, probs)
    preds = threshold_predict(probs, threshold)
    assert len(preds) == len(y)
    assert PHISHING_LABEL in preds
    assert 0 < threshold < 1
    assert "average_precision" in metrics


def test_threshold_validation() -> None:
    probs = np.array([0.1, 0.9])
    try:
        threshold_predict(probs, 1.0)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected invalid threshold to raise ValueError")
