# AI Readiness & Model Governance Assessment — Phishing Website Detection ML

## Data and evaluation readiness

The intended task uses **0 = phishing** and **1 = legitimate** labels. Website, HTML, metadata and hosting signals are transformed into classifier features. The source dataset is **not committed**; independent verification of updated model accuracy is therefore outstanding.

Candidate models are Logistic Regression, Random Forest and Extra Trees. The reference workflow separates train/validation/held-out test samples and chooses a threshold using phishing-class F2 on validation data.

## AI governance controls

| Control | Reference implementation | Operational requirement |
|---|---|---|
| Data quality | Input checks and preprocessing | Verified source provenance and label-quality checks |
| Model selection | Candidate comparison, validation F2 | Agree missed-threat versus false-positive costs |
| Evaluation | Locked holdout protocol | Reproduce metrics on actual source and independent test data |
| Traceability | Model bundle, feature contract, fingerprint | Model inventory and reviewer audit trail |
| Monitoring | Feature-drift and service metrics | Live monitoring, alert owner and incident process |
| Human oversight | Prediction API | Define escalation, overrides and feedback loops |

**Boundary:** This is a reference pipeline, not a verified live phishing-blocking service.

See [requirements and solution design](../business-analysis/business-requirements-and-solution-design.md).
