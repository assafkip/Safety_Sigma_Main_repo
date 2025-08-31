Principles

Lossless for indicators and categories.

Every field carries provenance (doc id + span offsets).

Zero inference: only source-grounded categories.

Extraction Object
{
  "type": "amount|memo|link|category|entity|date|range|platform",
  "value": "<verbatim>",
  "norm": {"currency": "USD", "amount": 1998.88},
  "provenance": {"page": 3, "start": 1043, "end": 1052},
  "confidence": 0.98
}

Rules

C-001: Amounts MUST keep original string in value and numeric in norm.

C-002: Links MUST be literal; no normalization.

C-003: Categories MUST map to source spans; include span ids.

Examples

✅ Good:

{"type": "amount", "value": "$1,998.88", "norm": {"currency":"USD","amount":1998.88}, ...}


❌ Bad:

{"type": "amount", "value": "1998.88 USD"}  // lost original string
