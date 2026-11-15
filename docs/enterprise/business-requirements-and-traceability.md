# Security Use Case & Requirements Traceability — Phishing Risk

**Status:** Proposed control requirements; no security-operations owner or risk committee approval asserted.

## Business/security objective
Prioritise potentially malicious websites for a security analyst using engineered URL/HTML/metadata/hosting signals. In the source task, **0 denotes phishing and 1 denotes legitimate**. The model is not an independently validated site-blocking authority.

**Potential stakeholders:** SOC lead, threat analyst, website/security engineer, business analyst, data steward and model-risk reviewer.

**Reference As-Is:** inconsistent manual assessment of structured website signals. **Proposed To-Be:** approved feature capture → validated classifier → calibrated phishing alert → security analyst disposition → feedback/label correction → monitoring and incident response.

**Candidate metrics (not measured):** missed phishing cases, legitimate false alarms, analyst triage time, precision at fixed alert budget, time from detection to review, recovery time and drift-related incidents.

## Requirements traceability (proposed)
| ID | Priority | Requirement | Repository evidence | Proposed acceptance |
|---|---|---|---|---|
| BR-01 | Must | Preserve label mapping 0=phishing, 1=legitimate | README; `src/pipeline.py` | Hand-check representative labels and scores |
| FR-01 | Must | Validate website/HTML/metadata/hosting inputs | Preprocessing pipeline | Invalid and missing feature tests |
| FR-02 | Must | Compare Logistic Regression, Random Forest and Extra Trees | `src/train.py` | Reproduce held-out comparison on approved dataset |
| FR-03 | Must | Tune phishing-class F2 on validation only | Training/evaluation workflow | Test isolation and positive-class orientation |
| FR-04 | Should | Provide structured, authenticated single/batch scoring | `app.py` | Access/negative-path/size-limit tests |
| FR-05 | Should | Record model fingerprint and drift status | Monitoring and model metadata | Integrity/restart tests |
| NFR-01 | Must | Prevent unsafe automated blocking without review | **Human-override process not evidenced** | Analyst UAT and override protocol |
| NFR-02 | Must | Audit source provenance and label verification | Not evidenced as approved operational process | Data signoff and label-quality report |

## Key design and policy decisions still open
Detection risk appetite; acceptable false-positive rate; incident triage authority; sample sources/licensing; adversarial tests; retention of suspicious URL/user data; block versus warn decision; legal/security review. Proposed controls require sponsor, SOC, security/privacy and model owner approval before pilot.
