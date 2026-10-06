from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    fbeta_score,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

PHISHING_LABEL = 0
LEGITIMATE_LABEL = 1


@dataclass
class DatasetSplits:
    X_train: pd.DataFrame
    X_val: pd.DataFrame
    X_test: pd.DataFrame
    y_train: pd.Series
    y_val: pd.Series
    y_test: pd.Series


def clean_dataset(df: pd.DataFrame, target: str = "label") -> tuple[pd.DataFrame, pd.Series]:
    """Clean common data-quality issues while preserving the source feature set."""
    data = df.copy()
    unnamed = [c for c in data.columns if str(c).lower().startswith("unnamed")]
    if unnamed:
        data = data.drop(columns=unnamed)

    if target not in data.columns:
        raise ValueError(f"Target column '{target}' not found.")

    for col in data.columns:
        if col == target or not pd.api.types.is_numeric_dtype(data[col]):
            continue
        normalized = str(col).lower().replace("_", "")
        if normalized.startswith("noof") or normalized in {"domainagemonths", "largestlinelength"}:
            data.loc[data[col] < 0, col] = np.nan

    data = data.replace([np.inf, -np.inf], np.nan)
    data = data[data[target].isin([PHISHING_LABEL, LEGITIMATE_LABEL])].copy()
    if data.empty or data[target].nunique() < 2:
        raise ValueError("Dataset must contain both phishing (0) and legitimate (1) labels.")

    X = data.drop(columns=[target])
    y = data[target].astype(int)
    if X.shape[1] == 0:
        raise ValueError("No feature columns remain after cleaning.")
    return X, y


def split_data(X: pd.DataFrame, y: pd.Series, random_state: int = 42) -> DatasetSplits:
    """Create reproducible 60/20/20 stratified splits."""
    X_train, X_temp, y_train, y_temp = train_test_split(
        X,
        y,
        test_size=0.40,
        random_state=random_state,
        stratify=y,
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp,
        y_temp,
        test_size=0.50,
        random_state=random_state,
        stratify=y_temp,
    )
    return DatasetSplits(X_train, X_val, X_test, y_train, y_val, y_test)


def build_preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    numeric = list(X.select_dtypes(include=np.number).columns)
    categorical = [c for c in X.columns if c not in numeric]

    numeric_pipe = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipe = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    transformers = []
    if numeric:
        transformers.append(("num", numeric_pipe, numeric))
    if categorical:
        transformers.append(("cat", categorical_pipe, categorical))
    return ColumnTransformer(transformers=transformers)


def phishing_probability(model: Pipeline, X: pd.DataFrame) -> np.ndarray:
    classes = list(model.named_steps["classifier"].classes_)
    if PHISHING_LABEL not in classes:
        raise ValueError(f"Phishing label {PHISHING_LABEL} not present in model classes: {classes}")
    return model.predict_proba(X)[:, classes.index(PHISHING_LABEL)]


def threshold_predict(probs: np.ndarray, threshold: float) -> np.ndarray:
    if not 0 < threshold < 1:
        raise ValueError("threshold must be between 0 and 1")
    return np.where(probs >= threshold, PHISHING_LABEL, LEGITIMATE_LABEL)


def evaluate_predictions(y_true: pd.Series, y_pred: np.ndarray, probs: np.ndarray) -> dict:
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=[PHISHING_LABEL],
        average=None,
        zero_division=0,
    )
    y_binary = (np.asarray(y_true) == PHISHING_LABEL).astype(int)
    pred_binary = (np.asarray(y_pred) == PHISHING_LABEL).astype(int)
    return {
        "classification_report": classification_report(y_true, y_pred, digits=4, zero_division=0),
        "phishing_precision": float(precision[0]),
        "phishing_recall": float(recall[0]),
        "phishing_f1": float(f1[0]),
        "phishing_f2": float(fbeta_score(y_binary, pred_binary, beta=2, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_binary, probs)),
        "average_precision": float(average_precision_score(y_binary, probs)),
        "confusion_matrix": confusion_matrix(
            y_true, y_pred, labels=[PHISHING_LABEL, LEGITIMATE_LABEL]
        ).tolist(),
    }


def select_threshold(
    y_true: pd.Series,
    probs: np.ndarray,
    *,
    beta: float = 2.0,
    minimum: float = 0.10,
    maximum: float = 0.90,
    step: float = 0.01,
) -> tuple[float, dict]:
    """Choose a validation threshold that maximizes phishing F-beta."""
    if minimum <= 0 or maximum >= 1 or minimum >= maximum or step <= 0:
        raise ValueError("Invalid threshold search range.")

    y_binary = (np.asarray(y_true) == PHISHING_LABEL).astype(int)
    best: tuple[float, float, float] | None = None
    best_metrics: dict | None = None

    for threshold in np.arange(minimum, maximum + 1e-9, step):
        y_pred = threshold_predict(probs, float(threshold))
        pred_binary = (y_pred == PHISHING_LABEL).astype(int)
        score = float(fbeta_score(y_binary, pred_binary, beta=beta, zero_division=0))
        recall = float(
            precision_recall_fscore_support(
                y_true,
                y_pred,
                labels=[PHISHING_LABEL],
                average=None,
                zero_division=0,
            )[1][0]
        )
        candidate = (score, recall, -abs(float(threshold) - 0.5))
        if best is None or candidate > best:
            best = candidate
            best_metrics = evaluate_predictions(y_true, y_pred, probs)
            best_metrics["threshold"] = float(round(threshold, 4))

    assert best_metrics is not None
    return float(best_metrics["threshold"]), best_metrics
