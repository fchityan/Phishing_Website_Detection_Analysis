# Solution Design & Implementation Guide — Phishing Website Detection

This guide preserves the detailed implementation, model workflow, evaluation, deployment notes, and run commands previously included in the root README. Commands and file paths are relative to the repository root. For a concise summary, see the [project overview](../../README.md).

---

A production-grade reference implementation for classifying phishing websites versus legitimate websites from engineered website, HTML, metadata, and hosting features.

The original exploratory notebook, `data-discovery-and-insights/phishing-risk-feature-profiling.ipynb`, is preserved. The repository now separates experimentation, training, locked evaluation, monitoring, inference, and deployment concerns so the project can be reviewed as an end-to-end ML service architecture rather than a notebook-only exercise.

## Problem framing

The project uses the original target convention:

- `0` = phishing
- `1` = legitimate

Missed phishing sites are treated as the higher-cost error. Candidate models therefore use validation-only threshold tuning that maximizes phishing-class F2, weighting recall more heavily than precision while still penalizing false positives.

## Production-style lifecycle

```text
Source data
    ↓
Data-quality cleaning + schema checks
    ↓
Stratified train / validation / locked test
    ↓
Logistic Regression / Random Forest / Extra Trees
    ↓
Validation average precision + phishing F2 threshold tuning
    ↓
Immutable model bundle + SHA-256 fingerprint
    ↓
Locked test evaluation
    ↓
Authenticated FastAPI online / batch inference
    ↓
Prometheus service metrics + feature-drift checks
    ↓
Docker / Kubernetes deployment controls
    ↓
Rollback to previous immutable image + model artifact
```

## What the project demonstrates

- Data-quality handling for unnamed index columns, missing values, invalid negative count-like values, and non-finite values
- Numeric median imputation and standardization
- Categorical most-frequent imputation and one-hot encoding
- Reproducible 60/20/20 stratified train/validation/test splitting
- Logistic Regression, Random Forest, and Extra Trees comparison
- Validation-only phishing F2 threshold optimization
- Locked holdout evaluation separated from model and threshold selection
- Versioned model bundles containing feature schema and a training monitoring profile
- SHA-256 artifact fingerprinting and deployment manifests
- Strict online/batch inference schema validation
- Optional API-key authentication
- Liveness, readiness, metadata, and Prometheus metrics endpoints
- Structured request logging and request IDs without logging feature payloads
- Numeric PSI and categorical total-variation drift checks
- Non-root Docker serving
- Kubernetes probes, resource limits, HPA, and PodDisruptionBudget template
- Automated tests and CI container builds
- Production runbook and security guidance

## Repository structure

```text
.
├── app.py
├── data-discovery-and-insights/phishing-risk-feature-profiling.ipynb
├── Dockerfile
├── requirements.txt
├── src/
│   ├── pipeline.py
│   ├── train.py
│   ├── evaluate.py
│   ├── inference.py
│   ├── monitor.py
│   └── production.py
├── tests/
│   ├── test_pipeline.py
│   ├── test_inference.py
│   └── test_monitor.py
├── deployment-architecture/
│   └── kubernetes.yaml
└── docs/
    ├── business-analysis/
    │   └── business-requirements-and-solution-design.md
    ├── ai-enablement/
    │   └── ai-readiness-and-model-governance-assessment.md
    ├── solution-design/
    │   └── solution-design-and-implementation-guide.md
    └── operational-readiness/
        └── service-transition-and-operations-runbook.md
```

## Input data

The dataset is not committed. Supply the CSV used by the original notebook or another dataset with the same target convention.

The training pipeline expects a `label` column by default. Change it with `--target` if needed.

## Train and compare models

```bash
pip install -r requirements.txt

python -m src.train \
  --data path/to/phishing_dataset.csv \
  --model-out artifacts/best_model.joblib \
  --outputs-dir outputs
```

Training writes validation comparison outputs plus `outputs/deployment_manifest.json`, which records the selected model, threshold, model version, creation time, and SHA-256 fingerprint.

## Locked evaluation

```bash
python -m src.evaluate \
  --data path/to/phishing_dataset.csv \
  --model-path artifacts/best_model.joblib \
  --outputs-dir outputs
```

The test split is untouched until model and threshold selection are complete.

## Drift monitoring

The bundle stores a reference profile from the training split. Compare a later scoring batch with:

```bash
python -m src.monitor \
  --data path/to/current_batch.csv \
  --model-path artifacts/best_model.joblib \
  --output outputs/drift_report.json
```

Numeric features use population stability index (PSI); categorical features use total-variation distance. Included alert thresholds are engineering defaults for demonstration and should be calibrated against actual production distributions.

## Serve the model

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

Endpoints:

- `GET /live` — process liveness
- `GET /ready` — model readiness
- `GET /metrics` — Prometheus-format runtime metrics
- `GET /metadata` — authenticated model/version/schema/fingerprint metadata
- `POST /predict` — authenticated single-record inference
- `POST /predict/batch` — authenticated bounded-batch inference

For production, set `REQUIRE_API_KEY=true`, provide `API_KEY` through the hosting platform's secret manager, and set `MODEL_SHA256` to the fingerprint of the promoted artifact.

## Container and deployment

```bash
docker build -t phishing-detection-api .
```

The container runs as a non-root user and expects the model artifact to be mounted read-only. The Kubernetes reference adds multiple replicas, readiness/liveness probes, CPU and memory controls, autoscaling, a PodDisruptionBudget, dropped Linux capabilities, and a read-only root filesystem.

See `deployment-architecture/kubernetes.yaml`, `docs/operational-readiness/service-transition-and-operations-runbook.md`, `.env.example`, and `SECURITY.md`.

## Tests

```bash
pytest -q
```

GitHub Actions compiles the service, runs the tests, checks installed dependencies, and builds the production container.
