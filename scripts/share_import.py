#!/usr/bin/env python3
import json, sys, zipfile
from pathlib import Path

def main():
    ap = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if not ap or not ap.exists():
        print("Usage: share_import.py <bundle.zip>", file=sys.stderr); sys.exit(2)

    target = Path("artifacts/imported")
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ap, "r") as z:
        z.extractall(target)
    manifest = next(target.rglob("manifest.json"), None)
    if not manifest:
        print("Import error: manifest.json missing", file=sys.stderr); sys.exit(1)
    try:
        json.loads(manifest.read_text(encoding="utf-8"))
        print("Import dry-run OK")
    except Exception as e:
        print(f"Import error: {e}", file=sys.stderr); sys.exit(1)

if __name__ == "__main__":
    main()