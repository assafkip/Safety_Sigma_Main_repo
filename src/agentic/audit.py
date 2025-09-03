from __future__ import annotations
import hashlib, json, time
from pathlib import Path
from typing import Any

class AuditLog:
    def __init__(self, repo_root: Path):
        self._prev_hash = None
        self.path = repo_root / "agentic" / "audit.log.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: str, payload: dict[str, Any]):
        rec = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "event": event,
            "payload": payload,
            "prev_hash": self._prev_hash
        }
        s = json.dumps(rec, sort_keys=True)
        h = hashlib.sha256(s.encode("utf-8")).hexdigest()
        rec["hash"] = h
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        self._prev_hash = h