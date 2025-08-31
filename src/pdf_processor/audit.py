# src/pdf_processor/audit.py
import json, time, os
def append_jsonl(record, path="logs/audit.jsonl"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    record.setdefault("timestamp", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
