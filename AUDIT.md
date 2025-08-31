Purpose

Guarantee append-only auditability for all outputs.

Requirements

Append-only log (no mutation/deletion).

Each entry must include:

module_version

inputs (PDF id, file hash)

spans (offsets, page)

decisions (kept/dropped)

validation_scores

test_results

timestamp

Example Entry
{
  "module_version": "pdf_processor_v0.1",
  "doc_id": "123e4567-e89b-12d3-a456-426614174000",
  "spans": [{"page":3,"start":1043,"end":1052}],
  "decision": "keep",
  "validation_scores": {"indicator_preservation": 1.0},
  "test_results": {"G-001": "pass", "G-010": "pass"},
  "timestamp": "2025-09-01T12:34:56Z"
}
