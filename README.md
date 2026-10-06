# Phishing Website Detection ML

A reproducible binary-classification project for distinguishing phishing websites from legitimate websites using engineered website, HTML, metadata, and hosting features.

The original exploratory notebook, `phishing_website_detection.ipynb`, is preserved. The repository now adds a scriptable machine-learning pipeline with preprocessing, model comparison, threshold tuning, artifact persistence, evaluation, and tests.

## Problem framing

The target convention used by the original notebook is:

- `0` = phishing
- `1` = legitimate

Because missed phishing sites are costly, the upgraded pipeline treats phishing detection as the positive-risk case and reports phishing precision, recall, F1, F2, ROC-AUC, and average precision. The validation threshold is tuned with F2 to give recall more weight than precision.

## What the project demonstrates

- Data-quality cleaning for unnamed index columns, missing values, and invalid negative count-like values
- Numeric median imputation and standardization
- Categorical most-frequent imputation and one-hot encoding
- Stratified 60/20/20 train/validation/test splitting
- Comparison of Logistic Regression, Random Forest, and Extra Trees
- Validation-only decision-threshold tuning
- Reproducible model artifacts and machine-readable metrics
- Holdout test evaluation separated from model selection
- Unit tests for preprocessing and threshold behavior

## Repository structure

```text
.
├── phishing_website_detection.ipynb
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── pipeline.py
│   ├── train.py
│   └── evaluate.py
└── tests/
    └── test_pipeline.py
```

## Input data

The dataset is not committed to this repository. Supply the CSV used by the notebook or another dataset with the same target convention.

The training pipeline expects a `label` column by default. You can change the target name with `--target`.

## Train and compare models

```bash
pip install -r requirements.txt
python -m src.train \
  --data path/to/phishing_dataset.csv \
  --model-out artifacts/best_model.joblib \
  --outputs-dir outputs
```

Training writes:

```text
artifacts/
├── best_model.joblib
└── validation_metrics.json

outputs/
├── training_summary.json
├── validation_model_comparison.csv
└── validation_report_<model>.txt
```

## Evaluate the locked model

```bash
python -m src.evaluate \
  --data path/to/phishing_dataset.csv \
  --model-path artifacts/best_model.joblib \
  --outputs-dir outputs
```

Evaluation writes a holdout classification report, probability-level metrics, confusion matrix data, and row-level test predictions.

## Model selection

Each candidate model is fitted only on the training split. Its phishing probability threshold is selected on the validation split by maximizing F2 across a bounded threshold grid. The best candidate is selected by validation average precision, with phishing F2 as the tie-break.

The test split is not used for model or threshold selection.

## Tests

```bash
pytest -q
```

## Limitations

- The source dataset is not included, so exact published metrics should only be added after rerunning the pipeline on the intended dataset.
- Website-threat distributions can drift as attackers change tactics.
- Engineered URL/HTML/hosting features can become stale and should be monitored in production.
- A production detector would also require latency, calibration, adversarial robustness, drift monitoring, and false-positive review.
