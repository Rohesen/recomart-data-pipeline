"""Central logging: human-readable log files + a machine-readable JSONL audit trail."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

from .config import LOG_DIR

_FMT = "%(asctime)s | %(levelname)-7s | %(name)-22s | %(message)s"


def get_logger(name: str, logfile: str = "pipeline.log") -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(f"recomart.{name}")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        fh = RotatingFileHandler(LOG_DIR / logfile, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
        fh.setFormatter(logging.Formatter(_FMT))
        logger.addHandler(fh)
        if logfile != "pipeline.log":           # every stage also lands in the combined pipeline log
            ph = RotatingFileHandler(LOG_DIR / "pipeline.log", maxBytes=5_000_000, backupCount=3, encoding="utf-8")
            ph.setFormatter(logging.Formatter(_FMT))
            logger.addHandler(ph)
        sh = logging.StreamHandler()
        sh.setFormatter(logging.Formatter(_FMT))
        sh.setLevel(logging.WARNING)
        logger.addHandler(sh)
        logger.propagate = False
    return logger


def audit(event: str, **fields) -> None:
    """Append one structured audit record (who/what/when) to logs/audit.jsonl."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    rec = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "event": event, **fields}
    with open(LOG_DIR / "audit.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, default=str) + "\n")


def read_audit(limit: int = 500) -> list[dict]:
    p = LOG_DIR / "audit.jsonl"
    if not p.exists():
        return []
    lines = p.read_text(encoding="utf-8").splitlines()[-limit:]
    return [json.loads(x) for x in lines if x.strip()]
