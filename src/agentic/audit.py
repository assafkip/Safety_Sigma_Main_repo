from __future__ import annotations
import hashlib, json, time
from pathlib import Path
from typing import Any, Optional

class AuditLog:
    def __init__(self, outdir: Path):
        self.out = outdir / "agentic" / "audit.log.jsonl"
        self.out.parent.mkdir(parents=True, exist_ok=True)
        self._prev_hash = None

    def append(self, event_type: str, payload: dict[str, Any]):
        rec = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "event": event_type,
            "payload": payload,
            "prev_hash": self._prev_hash,
        }
        line = json.dumps(rec, sort_keys=True)
        curr_hash = hashlib.sha256(line.encode("utf-8")).hexdigest()
        rec["hash"] = curr_hash
        self.out.write_text(self.out.read_text() + json.dumps(rec) + "\n" if self.out.exists() else json.dumps(rec) + "\n", encoding="utf-8")
        self._prev_hash = curr_hash