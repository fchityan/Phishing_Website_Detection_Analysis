#!/usr/bin/env bash
set -euo pipefail

IMAGE="${1:-phishing-detection-api:ci}"
CONTAINER="phishing-api-ci"
API_KEY="ci-secret"
ARTIFACT="artifacts/best_model.joblib"

cleanup() {
  docker rm -f "${CONTAINER}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

python scripts/build_test_model.py --output "${ARTIFACT}"
MODEL_SHA256="$(python - <<'PY'
import hashlib
from pathlib import Path
p = Path("artifacts/best_model.joblib")
print(hashlib.sha256(p.read_bytes()).hexdigest())
PY
)"

docker run -d   --name "${CONTAINER}"   -p 8000:8000   -v "$PWD/artifacts:/app/artifacts:ro"   -e REQUIRE_API_KEY=true   -e API_KEY="${API_KEY}"   -e MODEL_SHA256="${MODEL_SHA256}"   "${IMAGE}" >/dev/null

for _ in {1..30}; do
  if curl -fsS http://127.0.0.1:8000/live >/dev/null; then
    break
  fi
  sleep 1
done

curl -fsS http://127.0.0.1:8000/live
curl -fsS http://127.0.0.1:8000/ready

status="$(curl -sS -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/metadata)"
test "${status}" = "401"

curl -fsS   -H "x-api-key: ${API_KEY}"   http://127.0.0.1:8000/metadata >/dev/null

curl -fsS   -H "content-type: application/json"   -H "x-api-key: ${API_KEY}"   -d '{"features":{"NoOfImage":3,"Industry":"finance"}}'   http://127.0.0.1:8000/predict >/dev/null

echo "Container smoke test passed."
