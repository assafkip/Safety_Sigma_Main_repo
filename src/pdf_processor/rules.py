from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import copy
import re


class RuleCompileError(Exception):
    """Raised when the IR is missing required fields for compilation."""


@dataclass
class CompileOptions:
    targets: Optional[List[str]] = None  # ["regex","sql","json"]; None = all


# ---- internal helpers -------------------------------------------------------

def _escape_literal(s: str) -> str:
    # Literal, zero-inference escape with appropriate boundaries for exact matching
    escaped = re.escape(s)
    
    # For strings that start/end with word characters, use word boundaries
    # For strings with special characters, use more generic boundaries
    starts_with_word = s and s[0].isalnum()
    ends_with_word = s and s[-1].isalnum()
    
    if starts_with_word and ends_with_word:
        return f"\\b{escaped}\\b"
    elif starts_with_word:
        return f"\\b{escaped}(?!\\w)"
    elif ends_with_word:
        return f"(?<!\\w){escaped}\\b"
    else:
        # For special character patterns, use start/end of string or non-word boundaries
        return f"(?<!\\S){escaped}(?!\\S)"

def _required_fields(kind: str) -> List[str]:
    if kind == "amount":
        return ["kind", "verbatim", "numeric", "category_id", "span_id"]
    if kind == "link":
        return ["kind", "literal", "category_id", "span_id"]
    # "text" covers memo/markers with verbatim content
    if kind in ("text", "memo"):
        return ["kind", "verbatim", "category_id", "span_id"]
    # New types in schema v0.2: domain, phone, email, account, behavior
    if kind in ("domain", "phone", "email", "account", "behavior"):
        return ["kind", "verbatim", "category_id", "span_id"]
    # default: require verbatim if present; remain strict on span refs
    return ["kind", "category_id", "span_id"]

def _provenance_meta(cat: str, span: str) -> Dict[str, Any]:
    return {
        "source_span": {"category_id": cat, "span_id": span},
        "provenance": {"stage": "compile", "version": "v0.2"},
    }

def _targets_all(options: Optional[CompileOptions]) -> List[str]:
    wanted = (options.targets if options and options.targets else ["regex", "sql", "json"])
    # maintain stable order
    order = ["regex", "sql", "json"]
    return [t for t in order if t in wanted]


# ---- public API -------------------------------------------------------------

def compile_rules(ir: Dict[str, Any], options: Optional[CompileOptions] = None) -> Dict[str, Any]:
    """
    Compile IR into rule artifacts (regex / SQL / JSON) without mutating IR.

    Guardrails:
      - Zero-inference, exact indicator preservation (amounts, tokens, links).
      - Category grounding: compiled categories must equal IR categories set.
      - Audit completeness: every artifact carries span refs + provenance.

    IR shapes supported:
      - Preferred: {"indicators":[...], "categories": {...}}
      - Also tolerated: {"extractions":[...]}  (best-effort mapping to indicators)

    Raises:
      RuleCompileError on missing required fields or category set mismatch.
    """
    # Append-only: never mutate caller IR
    ir_in = copy.deepcopy(ir)

    # Collect indicators from "indicators" (preferred) or map from "extractions"
    indicators: List[Dict[str, Any]] = []
    if isinstance(ir_in.get("indicators"), list):
        indicators = ir_in["indicators"]
    elif isinstance(ir_in.get("extractions"), list):
        # Best-effort mapping for common types; zero inference on values
        for x in ir_in["extractions"]:
            k = x.get("type")
            if k == "amount":
                indicators.append({
                    "kind": "amount",
                    "verbatim": x.get("value"),
                    "numeric": (x.get("norm") or {}).get("amount"),
                    "category_id": x.get("category_id", "UNSPECIFIED"),
                    "span_id": x.get("span_id", "UNSPECIFIED"),
                })
            elif k == "link":
                indicators.append({
                    "kind": "link",
                    "literal": x.get("value"),
                    "category_id": x.get("category_id", "UNSPECIFIED"),
                    "span_id": x.get("span_id", "UNSPECIFIED"),
                })
            elif k in ("memo", "text"):
                indicators.append({
                    "kind": "text",
                    "verbatim": x.get("value"),
                    "category_id": x.get("category_id", "UNSPECIFIED"),
                    "span_id": x.get("span_id", "UNSPECIFIED"),
                })
            # ignore other types for compiler scope
    else:
        indicators = []

    categories: Dict[str, Any] = ir_in.get("categories", {}) or {}

    # Validate required fields per indicator kind
    missing_total: List[Dict[str, Any]] = []
    for idx, ind in enumerate(indicators):
        req = _required_fields(ind.get("kind", ""))
        missing = [f for f in req if f not in ind]
        if missing:
            missing_total.append({"index": idx, "missing": missing, "indicator": ind})
    if missing_total:
        raise RuleCompileError(f"Missing required fields: {missing_total}")

    # Build artifacts according to requested targets
    artifacts: Dict[str, Any] = {}
    for target in _targets_all(options):
        if target == "regex":
            regex_rules: List[Dict[str, Any]] = []
            for ind in indicators:
                kind = ind["kind"]
                cat, span = ind["category_id"], ind["span_id"]
                if kind == "amount":
                    lit = ind["verbatim"]
                elif kind == "link":
                    lit = ind["literal"]
                elif kind in ("text", "memo", "domain", "phone", "email", "account", "behavior"):
                    lit = ind.get("verbatim")
                else:  # fallback for other types
                    lit = ind.get("verbatim")
                if not isinstance(lit, str):
                    # Skip impossible cases; unit tests expect strict failure on missing before this point.
                    continue
                pattern = _escape_literal(lit)
                rule = {
                    "pattern": pattern,
                    "meta": {"name": lit, "kind": kind, **_provenance_meta(cat, span)},
                }
                regex_rules.append(rule)
            artifacts["regex"] = regex_rules

        elif target == "sql":
            rows: List[Dict[str, Any]] = []
            for ind in indicators:
                row = {
                    "kind": ind["kind"],
                    "category_id": ind["category_id"],
                    "span_id": ind["span_id"],
                }
                # Preserve exact fields; do not invent/rename
                if "verbatim" in ind:
                    row["verbatim"] = ind["verbatim"]
                if "numeric" in ind:
                    row["numeric"] = ind["numeric"]
                if "literal" in ind:
                    row["literal"] = ind["literal"]
                # embed minimal audit meta
                row.update(_provenance_meta(ind["category_id"], ind["span_id"]))
                rows.append(row)
            artifacts["sql"] = {"table": "indicators", "rows": rows}

        elif target == "json":
            # Mirror categories and keep indicators with preserved fields
            inds_out: List[Dict[str, Any]] = []
            for ind in indicators:
                kept = {
                    "kind": ind["kind"],
                    "category_id": ind["category_id"],
                    "span_id": ind["span_id"],
                }
                if "verbatim" in ind:
                    kept["verbatim"] = ind["verbatim"]
                if "numeric" in ind:
                    kept["numeric"] = ind["numeric"]
                if "literal" in ind:
                    kept["literal"] = ind["literal"]
                kept.update(_provenance_meta(ind["category_id"], ind["span_id"]))
                inds_out.append(kept)
            json_output = {"categories": categories, "indicators": inds_out}
            
            # If input IR had links, carry them through untouched
            if "links" in ir_in:
                json_output["links"] = ir_in["links"]
            
            artifacts["json"] = json_output

    # Category diff ==  (compiled JSON vs IR)
    if "json" in artifacts:
        compiled_cats = set((artifacts["json"].get("categories") or {}).keys())
        ir_cats = set(categories.keys())
        if compiled_cats != ir_cats:
            raise RuleCompileError(
                f"Category set mismatch: compiled={sorted(compiled_cats)} ir={sorted(ir_cats)}"
            )

    return artifacts