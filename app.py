from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from src.inference import load_model_bundle, predict_records
from src.production import (
    configure_logging,
    configure_tracing,
    install_observability,
    metrics_response,
    register_model_metrics,
    require_api_key,
    verify_model_artifact,
)

MODEL_PATH = Path(os.getenv("MODEL_PATH", "artifacts/best_model.joblib"))
MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "100"))
DOCS_ENABLED = os.getenv("ENABLE_DOCS", "true").lower() in {"1", "true", "yes", "on"}

configure_logging()


class PredictionRequest(BaseModel):
    features: dict[str, Any] = Field(..., min_length=1)


class PredictionResponse(BaseModel):
    phishing_probability: float = Field(ge=0.0, le=1.0)
    predicted_class: int
    predicted_label: str
    threshold: float = Field(gt=0.0, lt=1.0)
    model_name: str
    model_version: str


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.bundle = None
    application.state.load_error = None
    application.state.model_sha256 = None
    try:
        application.state.model_sha256 = verify_model_artifact(MODEL_PATH)
        application.state.bundle = load_model_bundle(MODEL_PATH)
        register_model_metrics(
            application.state.bundle["model_name"],
            application.state.bundle["model_version"],
        )
    except Exception as exc:
        application.state.load_error = str(exc)
    yield


app = FastAPI(
    title="Phishing Website Detection API",
    version="2.1.0",
    lifespan=lifespan,
    docs_url="/docs" if DOCS_ENABLED else None,
    redoc_url="/redoc" if DOCS_ENABLED else None,
    openapi_url="/openapi.json" if DOCS_ENABLED else None,
)
install_observability(app)
app.state.tracing_enabled = configure_tracing(app)


def _require_bundle(request: Request) -> dict[str, Any]:
    bundle = request.app.state.bundle
    if bundle is None:
        raise HTTPException(status_code=503, detail=request.app.state.load_error or "Model not loaded")
    return bundle


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "phishing-website-detection", "version": app.version}


@app.get("/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready(request: Request) -> dict[str, str]:
    bundle = _require_bundle(request)
    return {
        "status": "ready",
        "model_version": bundle["model_version"],
        "service_env": os.getenv("SERVICE_ENV", "development"),
    }


@app.get("/metrics")
def metrics():
    return metrics_response()


@app.get("/metadata", dependencies=[Depends(require_api_key)])
def metadata(request: Request) -> dict[str, Any]:
    bundle = _require_bundle(request)
    return {
        "model_name": bundle["model_name"],
        "model_version": bundle["model_version"],
        "threshold": bundle["threshold"],
        "feature_columns": bundle["feature_columns"],
        "feature_schema": bundle["feature_schema"],
        "created_at_utc": bundle.get("created_at_utc"),
        "model_sha256": request.app.state.model_sha256,
        "service_env": os.getenv("SERVICE_ENV", "development"),
        "tracing_enabled": bool(getattr(request.app.state, "tracing_enabled", False)),
    }


@app.post("/predict", response_model=PredictionResponse, dependencies=[Depends(require_api_key)])
def predict(payload: PredictionRequest, request: Request):
    bundle = _require_bundle(request)
    try:
        return predict_records([payload.features], bundle)[0]
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/predict/batch", response_model=list[PredictionResponse], dependencies=[Depends(require_api_key)])
def predict_batch(payloads: list[PredictionRequest], request: Request):
    if not payloads:
        raise HTTPException(status_code=400, detail="At least one record is required.")
    if len(payloads) > MAX_BATCH_SIZE:
        raise HTTPException(status_code=413, detail=f"Batch exceeds MAX_BATCH_SIZE={MAX_BATCH_SIZE}.")
    bundle = _require_bundle(request)
    try:
        return predict_records([payload.features for payload in payloads], bundle)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
