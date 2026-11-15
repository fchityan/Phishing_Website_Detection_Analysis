# Security Analytics Architecture & Feature Contract — Phishing Risk

**Status:** Reference model/API design, not attested production integration.

```text
Approved labeled website-feature dataset (not in repository)
  → data cleaning, missing and invalid feature checks
  → label 0=phishing, 1=legitimate; leakage exclusions
  → train / validation / held-out test partitions
  → LR / Random Forest / Extra Trees; validation F2 threshold
  → versioned artifact + fingerprint
  → authenticated FastAPI score, single/batch
  → analyst interpretation and alert triage (proposed)
  → service/feature drift review → incident & retraining gate
```

## Data and decision contract
| Field/domain | Documented role | Required operational decision |
|---|---|---|
| Website/HTML attributes | Classifier features in source pipeline | Capture method, permission, freshness and normalization |
| DNS/hosting/metadata signals | Input feature families | Feature timing, provenance, valid ranges and missingness |
| Ground-truth label | 0 malicious, 1 legitimate | Independent label quality and timestamp audit |
| Prediction output | Classification/score and threshold | Meaning of phishing score, calibrated confidence and user warning |
| Trace | Model/feature version and request id | Log retention, redaction and incident correlation |
| Analyst disposition | Future feedback for errors/false alarms | Human override, review status and feedback integrity |

The actual feature schema must be extracted from `src/pipeline.py` and serving validators. The categories above are not a certified list of field names or data types.

## Architecture decision records
- **ADR-PH-01:** Threshold selection targets phishing-class F2 because missing malicious sites can be costly; revise with SOC risk appetite and analyst capacity.
- **ADR-PH-02:** Held-out data is not used to choose features or threshold.
- **ADR-PH-03:** Classifier output is evidence for human triage, not automatic enforcement authority.
- **ADR-PH-04:** Version and fingerprint artifacts and permit rollback.
- **ADR-PH-05:** Current Docker/Kubernetes manifests are **reference deployment artefacts**, not proof of a deployed security platform.

Before integration, specify source event contract, latency/timeout and fail-open/fail-closed behaviour, score semantics, batch caps, SIEM/ticketing interface, alert deduplication and review response SLAs.
