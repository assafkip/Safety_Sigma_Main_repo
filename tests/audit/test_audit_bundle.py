import json, os
from pathlib import Path
import pytest

def test_audit_bundle_manifest_exists(tmp_path):
    # Only checks structure; build script is run by demo/Make targets in CI
    out = Path("artifacts/audit_package_v0_1/manifest.json")
    if not out.exists():
        pytest.skip("bundle not built in this run")
    m = json.loads(out.read_text(encoding="utf-8"))
    assert "gates" in m and all(k in m["gates"] for k in ["V-001","V-002","V-003","V-004","V-005"])
    assert "rules_json" in m["artifacts"]