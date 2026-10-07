# Production Runbook

This project models the application and MLOps controls of a production phishing-detection service. It becomes a live production system only after deployment with real threat data, security controls, and operational ownership.

## Release flow

1. Train against the approved immutable source dataset.
2. Review validation comparison and the phishing-class F2 operating threshold.
3. Evaluate the selected model and threshold on the locked test split.
4. Review `outputs/deployment_manifest.json`.
5. Promote an immutable `artifacts/best_model.joblib` and record its SHA-256.
6. Store the API key and promoted model fingerprint in the platform secret manager.
7. Deploy the immutable container image and model artifact behind TLS ingress/API gateway.
8. Verify `/live`, `/ready`, `/metrics`, authenticated metadata, and a known-good scoring request before routing traffic.

Never overwrite a promoted model artifact in place.

## Runtime controls

- `/live`: process liveness.
- `/ready`: model-loaded readiness.
- `/metrics`: Prometheus request count, latency, and model-info metrics.
- `/metadata`: authenticated model version, threshold, schema, and fingerprint.
- `/predict`: authenticated single-record inference.
- `/predict/batch`: authenticated bounded-batch inference.
- Each HTTP response gets `X-Request-ID`.
- Logs are structured JSON and intentionally omit raw features and predictions.
- `MODEL_SHA256` can enforce exact artifact integrity.
- `ENABLE_DOCS=false` removes Swagger/OpenAPI endpoints in production.

## Suggested SLO targets

These are engineering targets to validate after deployment, not measured claims:

- 99.9% monthly API availability.
- p95 single-record service latency below 150 ms under normal load.
- 5xx rate below 0.5% over 15 minutes.
- zero traffic to replicas that fail model readiness.

## Model monitoring

Run `python -m src.monitor` against recent scoring batches. Numeric PSI >= 0.20, categorical total-variation distance >= 0.20, or missing-rate movement >= 0.10 are example alert thresholds, not universal production standards.

A real deployment should additionally monitor calibration, phishing recall/precision at the active threshold, adversarial/evasion patterns, analyst false-positive overturn rates, delayed confirmed labels, and feature availability.

## Alerting

Create an incident when:

- all replicas fail readiness;
- 5xx rate or p95 latency breaches the service threshold;
- model SHA-256 verification fails;
- schema rejection rate changes materially;
- drift alerts persist;
- confirmed phishing recall deteriorates;
- false-positive review burden breaches an agreed operational threshold.

## Rollback

Keep immutable image digests and immutable model versions. Roll back both image and model to the previously verified release. Retain the prior deployment manifest and fingerprint for audit.

## Security boundary

The reference architecture assumes TLS termination and gateway controls outside the repository. A real deployment should add cloud IAM, managed secrets, private networking as appropriate, WAF/rate limiting, centralized logs/traces, dependency and image scanning, image signing, model-registry access control, and on-call escalation.
