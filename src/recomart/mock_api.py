"""Mock of RecoMart's product-catalog service and an external popularity/sentiment provider.

It deliberately fails a fraction of requests with HTTP 503 (MOCK_API_FAILURE_RATE) so that the
ingestion layer's retry/backoff and logging can be demonstrated.

    python -m recomart.mock_api            # serves on 127.0.0.1:8765
"""
from __future__ import annotations

import json
import math
import os
import random
import threading
import time

from fastapi import FastAPI, HTTPException, Query

from .config import DATA, cfg

app = FastAPI(title="RecoMart Catalog & Popularity API (mock)", version="1.0")
SRC = DATA / "sources"
_rand = random.Random(7)


def _maybe_fail():
    rate = float(os.environ.get("MOCK_API_FAILURE_RATE", cfg()["ingestion"]["api_failure_rate"]))
    if _rand.random() < rate:
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")


def _load(name):
    return json.loads((SRC / name).read_text())


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/products")
def products(page: int = Query(1, ge=1, le=10_000), size: int = Query(100, ge=1, le=500)):
    _maybe_fail()
    items = _load("catalog.json")
    pages = max(1, math.ceil(len(items) / size))
    return {"page": page, "size": size, "total_pages": pages, "total": len(items),
            "items": items[(page - 1) * size: page * size]}


@app.get("/popularity")
def popularity():
    _maybe_fail()
    return {"as_of": time.strftime("%Y-%m-%dT%H:%M:%S"), "items": _load("popularity.json")}


def serve_in_background(host: str = "127.0.0.1", port: int = 8765) -> bool:
    """Start the mock API in a daemon thread (used by the pipeline / Prefect flow)."""
    import requests
    import uvicorn
    try:
        if requests.get(f"http://{host}:{port}/health", timeout=1).ok:
            return True
    except Exception:
        pass
    server = uvicorn.Server(uvicorn.Config(app, host=host, port=port, log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(50):
        try:
            if requests.get(f"http://{host}:{port}/health", timeout=1).ok:
                return True
        except Exception:
            time.sleep(0.1)
    return False


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)
