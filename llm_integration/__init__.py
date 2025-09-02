"""
Safety Sigma LLM Integration Layer v0.1

Minimal, testable LLM integration that:
- Consumes PDF-derived text/spans from existing extractor
- Uses LLM only to structure extractions into IR Schema v0.4
- Generates practitioner narratives with verbatim quoted spans
- Assembles deployable rules preserving indicators exactly
- Maintains zero-inference, cite-or-omit guardrails
"""

__version__ = "0.1.0"