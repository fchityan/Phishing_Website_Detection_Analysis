from __future__ import annotations

import json
import os

from locust import HttpUser, between, task


def _load_features() -> dict:
    raw = os.getenv("LOAD_TEST_FEATURES_JSON", "").strip()
    if not raw:
        return {"NoOfImage": 3, "Industry": "finance"}
    parsed = json.loads(raw)
    if not isinstance(parsed, dict) or not parsed:
        raise ValueError("LOAD_TEST_FEATURES_JSON must be a non-empty JSON object.")
    return parsed


class PhishingApiUser(HttpUser):
    wait_time = between(0.2, 1.0)

    def on_start(self) -> None:
        self.api_key = os.getenv("LOAD_TEST_API_KEY", "")
        self.features = _load_features()

    @task(9)
    def predict(self) -> None:
        headers = {"content-type": "application/json"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        self.client.post(
            "/predict",
            json={"features": self.features},
            headers=headers,
            name="/predict",
        )

    @task(1)
    def readiness(self) -> None:
        self.client.get("/ready", name="/ready")
