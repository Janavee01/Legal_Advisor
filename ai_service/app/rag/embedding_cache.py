"""
embedding_cache.py — Disk cache for derived embeddings.

Stores model output vectors keyed by a hash of the exact inputs they
were computed from. A cache hit returns the identical array that would
have been produced by recomputing, so retrieval behavior is unchanged.

The signature includes the full input text, so any change to
intent_index.json or category_prototypes.py automatically invalidates.
"""

import hashlib
import json
from pathlib import Path

import numpy as np

CACHE_DIR = Path(__file__).resolve().parents[1] / "data"


def _signature(*parts) -> str:
    h = hashlib.sha256()
    for part in parts:
        h.update(json.dumps(part, sort_keys=True).encode("utf-8"))
    return h.hexdigest()


def load_array(cache_name: str, *signature_parts):
    sig_path = CACHE_DIR / f"{cache_name}.sig"
    arr_path = CACHE_DIR / f"{cache_name}.npy"

    if (
        sig_path.exists()
        and arr_path.exists()
        and sig_path.read_text().strip() == _signature(*signature_parts)
    ):
        return np.load(arr_path)

    return None


def save_array(cache_name: str, arr, *signature_parts) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    np.save(CACHE_DIR / f"{cache_name}.npy", arr)
    (CACHE_DIR / f"{cache_name}.sig").write_text(_signature(*signature_parts))


def load_json(cache_name: str, *signature_parts):
    sig_path = CACHE_DIR / f"{cache_name}.sig"
    json_path = CACHE_DIR / f"{cache_name}.json"

    if (
        sig_path.exists()
        and json_path.exists()
        and sig_path.read_text().strip() == _signature(*signature_parts)
    ):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    return None


def save_json(cache_name: str, obj, *signature_parts) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_DIR / f"{cache_name}.json", "w", encoding="utf-8") as f:
        json.dump(obj, f)
    (CACHE_DIR / f"{cache_name}.sig").write_text(_signature(*signature_parts))