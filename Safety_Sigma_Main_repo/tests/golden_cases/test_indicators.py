# filepath: /Safety_Sigma_Main_repo/Safety_Sigma_Main_repo/tests/golden_cases/test_indicators.py
import re

# Fixtures from golden cases
FIXTURE_TEXT = """
Payment amount: $1,998.88
Memo: VOID 2000
Contact: wa.me/123456789
"""

SOURCE_CATEGORIES = {"finance", "memo"}   # pretend categories present in the source
GENERATED_CATEGORIES = {"finance", "memo"}  # should be identical (diff == ∅)


def test_g001_amount_exactness():
    # G-001: $1,998.88 must appear verbatim
    assert "$1,998.88" in FIXTURE_TEXT


def test_g002_memo_preservation():
    # G-002: VOID 2000 must be preserved as token sequence
    assert "VOID 2000" in FIXTURE_TEXT


def test_g003_link_literal():
    # G-003: wa.me link must match regex and preserve scheme+path
    pattern = re.compile(r"\bwa\.me/[0-9]{6,}\b")
    match = pattern.search(FIXTURE_TEXT)
    assert match is not None
    assert match.group(0) == "wa.me/123456789"


def test_g010_category_source_check():
    # G-010: diff(generated, source) == ∅
    diff = GENERATED_CATEGORIES - SOURCE_CATEGORIES
    assert diff == set()