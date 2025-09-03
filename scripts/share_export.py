#!/usr/bin/env python3
import hashlib, json, shutil, sys, time
from pathlib import Path

def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    root = Path(__file__).resolve().parents[1]
    bundle = root/"artifacts"/f"audit_package_v0_7_{int(time.time())}"
    out = bundle.with_suffix(".zip")
    # Find best available bundle directory
    candidates = [root/"artifacts"/"audit_package_v0_4", root/"artifacts"/"audit_package_v0_2"]
    src = next((p for p in candidates if p.exists()), None)
    if not src:
        print("No existing bundle directory to export.", file=sys.stderr)
        sys.exit(0)
    shutil.make_archive(str(bundle), "zip", root_dir=src)
    # checksums
    checks = []
    for p in src.rglob("*"):
        if p.is_file():
            checks.append({"path": str(p.relative_to(src)), "sha256": sha256(p)})
    (root/"artifacts"/"sharing"/"checksums.txt").parent.mkdir(parents=True, exist_ok=True)
    (root/"artifacts"/"sharing"/"checksums.txt").write_text(json.dumps(checks, indent=2), encoding="utf-8")
    print(f"Exported: {out}")

if __name__ == "__main__":
    main()