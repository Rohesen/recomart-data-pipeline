"""Recommendation inference API.

    uvicorn serving.api:app --port 8000      # docs at http://127.0.0.1:8000/docs
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi import FastAPI, HTTPException, Query  # noqa: E402

from recomart.recommend import champion_info, recommend, similar_items  # noqa: E402

app = FastAPI(title="RecoMart Recommendation API", version="1.0",
              description="Personalised recommendations from the MLflow @champion model + feature store")
UID, PID = re.compile(r"^U\d{5}$"), re.compile(r"^P\d{5}$")


@app.middleware("http")
async def headers(request, call_next):
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/model-info")
def model_info():
    try:
        return champion_info()
    except Exception:
        raise HTTPException(503, "No champion model - run the pipeline first")


@app.get("/recommend/{user_id}")
def recommend_endpoint(user_id: str, k: int = Query(10, ge=1, le=50)):
    if not UID.match(user_id):
        raise HTTPException(422, "user_id must look like U20001")
    try:
        return recommend(user_id, k)
    except Exception:
        raise HTTPException(503, "Recommendation service unavailable")


@app.get("/similar/{product_id}")
def similar_endpoint(product_id: str, k: int = Query(10, ge=1, le=20)):
    if not PID.match(product_id):
        raise HTTPException(422, "product_id must look like P10001")
    return similar_items(product_id, k)
