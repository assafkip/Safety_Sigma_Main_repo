import subprocess, sys
from pathlib import Path

def test_import_help_message(tmp_path: Path):
    cmd = [sys.executable, "scripts/share_import.py"]
    p = subprocess.run(cmd, cwd=Path.cwd())
    assert p.returncode != 0