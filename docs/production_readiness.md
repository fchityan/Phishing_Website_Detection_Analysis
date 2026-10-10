# Production Readiness

This branch closes several gaps between a production-oriented reference implementation and a deployable ML service. It does not claim live production traffic or enterprise operations.

## Controls now implemented

- Optional OpenTelemetry tracing over OTLP, alongside existing Prometheus metrics and structured request logging.
- Immutable model promotion through `python -m src.promote`, with SHA-256 verification, locked-test evidence, reviewer identity, and optional phishing-recall/F2 gates.
- Container-level CI smoke testing that starts the real image with a deterministic CI-only model fixture and verifies liveness, readiness, authentication, metadata, and inference.
- Dependency auditing, Trivy filesystem scanning, and CycloneDX SBOM generation.
- Version-tagged GHCR release workflow with build provenance, SBOM metadata, and keyless cosign signing.
- Kubernetes deployment template that requires an immutable image digest and disables automatic service-account token mounting.
- Locust load-test harness for concurrency and latency validation.

## Model promotion

Run locked evaluation first, then promote an immutable artifact:

```bash
python -m src.promote \
  --stage staging \
  --approved-by reviewer-name \
  --min-phishing-recall 0.90 \
  --min-phishing-f2 0.90
```

The numeric thresholds above are examples only. They are not model-performance claims.

Promotion copies the model, deployment manifest, locked-test metrics, and a promotion record into an immutable version/stage path. A second promotion to the same path fails rather than overwriting the existing release.

## Tracing

Set:

```text
ENABLE_TRACING=true
OTEL_SERVICE_NAME=phishing-website-detection-api
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=https://collector.example/v1/traces
```

Raw feature payloads are not added to spans by this implementation. Protect telemetry backends with the hosting platform's identity and secret controls.

## Supply-chain workflow

The security workflow audits Python dependencies, scans the repository, and emits a CycloneDX SBOM. A version tag such as `v2.1.0` triggers the signed-container release workflow. Deploy the resulting digest rather than a mutable tag.

## Load validation

Install development tooling:

```bash
pip install -r requirements-dev.txt
```

Then run:

```bash
LOAD_TEST_API_KEY=replace-me \
LOAD_TEST_FEATURES_JSON='{"NoOfImage":3,"Industry":"finance"}' \
locust -f load/locustfile.py --host http://127.0.0.1:8000
```

Replace the example feature object with one matching the promoted model schema. Record p50, p95, p99 latency, error rate, throughput, and saturation. Suggested SLOs should not be presented as achieved until they are measured under representative traffic.

## Still required for a real production claim

- Actual deployment to a cloud or managed Kubernetes environment.
- Managed secrets and least-privilege cloud IAM.
- A managed log/trace backend and alert routing.
- Ingress/API gateway controls including TLS, rate limiting, and WAF policy.
- Real phishing feature ingestion and representative live traffic.
- Production data retention/privacy controls.
- Adversarial/evasion testing and analyst false-positive review.
- Outcome feedback, confirmed-label monitoring, and retraining governance.
- Canary or blue/green rollout with demonstrated rollback.
- Sustained operating history, incident response, and on-call ownership.

Until those are demonstrated, the correct positioning remains **production-grade reference implementation** rather than live enterprise production system.
