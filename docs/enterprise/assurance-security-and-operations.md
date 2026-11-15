# Security Assurance, Adversarial Testing & Operations — Phishing Risk

**Evidence boundary:** Implementation/test scaffolding and operations reference are documented. The original dataset is unavailable here; up-to-date held-out metrics, external red-team testing, SOC UAT and live monitoring are **not evidenced**.

## Verification and acceptance
| Gate | Test | Evidence needed |
|---|---|---|
| Labels | Confirm 0=phishing in model scoring and threshold selection | Negative/positive label fixtures |
| Dataset | Provenance, class imbalance, deduplication, domain leakage and contamination | Data approval + split manifest |
| Held-out evaluation | Recall, precision, PR-AUC, F2, confusion matrix at alert budget | Source-data report, independent reproduction |
| Robustness | Typosquatting, new hosting, unseen HTML patterns, adversarial and evasive sites | Threat simulation and post-change regression |
| API/security | Auth failures, invalid payloads, rate limiting, abuse, max-batch and injection | Test logs and assessment |
| SOC UAT | Analyst interpretation, false-positive resolution and escalation | Signed scenarios and audit history |
| Release | Image/artifact fingerprint, deploy smoke test, rollback | Environment evidence and owner signoff |

## Threat and model risk register
| Threat | Business harm | Proposed control |
|---|---|---|
| Adversarial feature manipulation | Missed malicious sites | Red-team benchmark and adversarial monitoring |
| Label contamination or site duplication | Overstated detection performance | Source provenance and temporal/domain separated evaluation |
| Legitimate-site false positives | Service disruption / reputation damage | Human review and configurable warn-only mode |
| Exposed scoring API | Abuse or information disclosure | Auth, TLS, request limits, logging and secret rotation |
| Drift / new attack campaigns | Falling recall | Drift review, delayed labels, retraining with approval |
| Unsafe auto-blocking | Unjustified enforcement | Separate rule authority and explicit SOC override |

## Data protection and security
Define legal source-collection rules, retention, access groups, log redaction, malicious-content sandboxing, isolation of downloaded artifacts, malware scanning, least-privilege service accounts, dependency/image scanning, TLS and protected model registry. These are **requirements**, not claims of completed controls.

## Proposed operating model
Security operations owner handles severity, triage and analyst decision; data steward owns sources and labels; ML owner tests performance/drift; platform security owns API and infrastructure; privacy/legal signs collection policy. Names/rotas and response SLOs remain unassigned.

**Incident workflow:** suspend score-driven enforcement; preserve request/model identifiers; triage false negative or false positive; isolate source/model change; roll back version; analyst clearance; document incident and requalification. Reference the [service runbook](../operational-readiness/service-transition-and-operations-runbook.md).

**Go/no-go:** approved datasets, externally verified metrics, adversarial tests, SOC UAT, security/privacy review, on-call ownership and rollback rehearsal. No live blocking or production readiness claim is made.
