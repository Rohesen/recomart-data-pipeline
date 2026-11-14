"""Raw data-lake storage with a fixed, documented partition layout.

    data/lake/raw/source=<source>/type=<type>/date=YYYY-MM-DD/<file>
    data/lake/raw/_manifest.jsonl          one line per stored object (audit + lineage)
    data/lake/quarantine/...               rows rejected by validation

Backend is local by default; set `backend: s3` in configs/storage.yaml (and install boto3) to
mirror the same keys to an S3 bucket.

    python -m recomart.storage upload       # push the local lake to the configured backend
    python -m recomart.storage tree         # print the lake layout
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .config import CONFIG_DIR, RAW, ROOT

MANIFEST = RAW / "_manifest.jsonl"


def storage_root() -> Path:
    return RAW


def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def partition_key(source: str, dtype: str, date: str, filename: str) -> str:
    for part in (source, dtype, date, filename):
        if "/" in part or ".." in part or not part:
            raise ValueError(f"Unsafe partition component: {part!r}")
    return f"source={source}/type={dtype}/date={date}/{filename}"


class LakeStorage:
    def __init__(self, conf: dict | None = None):
        self.conf = conf or yaml.safe_load((CONFIG_DIR / "storage.yaml").read_text())
        self.backend = self.conf.get("backend", "local")

    def put_file(self, src: Path, key: str) -> Path:
        dest = RAW / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".part")       # atomic write: no half-written files
        shutil.copyfile(src, tmp)
        tmp.replace(dest)
        if self.backend == "s3":
            self._s3_put(dest, key)
        return dest

    def put_bytes(self, data: bytes, key: str) -> Path:
        dest = RAW / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        tmp.write_bytes(data)
        tmp.replace(dest)
        if self.backend == "s3":
            self._s3_put(dest, key)
        return dest

    def _s3_put(self, path: Path, key: str):
        import boto3                                          # optional dependency
        s3c = self.conf["s3"]
        boto3.client("s3", region_name=s3c.get("region")).upload_file(
            str(path), s3c["bucket"], f"{s3c['prefix']}/raw/{key}")

    @staticmethod
    def record(entry: dict):
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        entry = {"stored_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), **entry}
        with open(MANIFEST, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    @staticmethod
    def manifest() -> list[dict]:
        if not MANIFEST.exists():
            return []
        return [json.loads(x) for x in MANIFEST.read_text().splitlines() if x.strip()]

    @staticmethod
    def list_partition(source: str, dtype: str) -> list[Path]:
        return sorted((RAW / f"source={source}" / f"type={dtype}").glob("date=*/*"))


def tree(max_files: int = 2) -> str:
    lines = [str(RAW.relative_to(ROOT)) + "/"]
    for src in sorted(RAW.glob("source=*")):
        lines.append(f"  {src.name}/")
        for typ in sorted(src.glob("type=*")):
            dates = sorted(typ.glob("date=*"))
            lines.append(f"    {typ.name}/   ({len(dates)} date partitions)")
            for d in dates[:max_files]:
                files = sorted(d.iterdir())
                lines.append(f"      {d.name}/  " + ", ".join(f.name for f in files[:2]))
            if len(dates) > max_files:
                lines.append("      ...")
    return "\n".join(lines)


def upload_all():
    st = LakeStorage()
    n = 0
    for p in RAW.rglob("*"):
        if p.is_file() and p.name != "_manifest.jsonl":
            key = str(p.relative_to(RAW))
            if st.backend == "s3":
                st._s3_put(p, key)
            n += 1
    return {"backend": st.backend, "objects": n}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["upload", "tree"])
    a = ap.parse_args()
    print(json.dumps(upload_all()) if a.cmd == "upload" else tree())
