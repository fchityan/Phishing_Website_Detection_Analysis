# Business Requirements & Solution Design Specification — Phishing Website Detection ML

This is a project-level **requirements traceability and solution-design artefact**, not a signed-off BRD or completed UAT.

## Business problem and process map

**Use case:** Detect possible phishing websites from website/HTML/metadata/hosting features. False negatives (missed phishing sites) and false positives (incorrect alerts) have different operational costs.

**Potential stakeholders:** threat analyst, security operations owner, business analyst and AI engineer.

**Possible As-Is → reference To-Be:** Manual investigation of suspicious website indicators → feature validation/preprocessing → training/validation/locked-test model comparison → phishing F2 threshold selection → API scoring and drift checks → proposed analyst review.

## Requirements Traceability Matrix

| ID | Requirement | Implementation evidence | Suggested acceptance check |
|---|---|---|---|
| BR-01 | Consistent classification meaning | Dataset convention | Verify **0 = phishing**, **1 = legitimate** |
| FR-01 | Clean invalid and missing features | `src/pipeline.py` | Check invalid-input handling |
| FR-02 | Evaluate candidate classifiers | `src/train.py` | Confirm Logistic Regression, Random Forest and Extra Trees comparison |
| FR-03 | Tune threshold without contaminating locked test | Training/evaluation | Confirm phishing-class F2 is tuned on validation data |
| FR-04 | Score records and inspect drift | `app.py`, `src/monitor.py` | Check single/batch API and monitoring output |
| NFR-01 | Reproducible evaluation and artefact integrity | Tests and model fingerprints | Review deterministic split and model metadata |

These checks are **proposed acceptance scenarios**, not evidence of stakeholder UAT.

## Digital transformation considerations

A deployed workflow would require defined alert owners, analyst escalation, risk appetite, labelled-outcome feedback, case retention, audit requirements and security/privacy controls. No measured detection accuracy is claimed without re-running the unavailable source dataset.

See [AI readiness](../ai-enablement/ai-readiness-and-model-governance-assessment.md).
