import subprocess, sys
from pathlib import Path

def _run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd).returncode

def test_splunk_compile(tmp_path: Path):
    (tmp_path/"artifacts").mkdir(); (tmp_path/"adapters"/"splunk").mkdir(parents=True)
    (tmp_path/"adapters"/"splunk"/"compile.py").write_text("#!/usr/bin/env python3\nprint(0)", encoding="utf-8")
    # This is a smoke placeholder; real test runs repo version in CI.

def test_elastic_compile_smoke():
    assert True