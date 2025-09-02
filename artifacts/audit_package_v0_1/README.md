# Audit Package v0.1

This bundle contains:

- `input/` - Source PDF document
- `rules/` - Compiled rules and reports (AUTHORITATIVE)
- `tests/` - JUnit test results for validation gates
- `advisory/` - NON-AUTHORITATIVE analyst narrative
- `manifest.json` - Bundle metadata and gate status

## Advisory Disclaimer

The `advisory/` folder contains NON-AUTHORITATIVE content for analyst convenience.
It is derived from quoted spans in the rules/IR but should not be treated as
a source of truth. Always refer to the authoritative artifacts in `rules/` and
the validation results in `tests/`.

## Validation Gates

- V-001: Indicator preservation
- V-002: Category grounding  
- V-003: Audit completeness
- V-004: Practitioner readiness
- V-005: Execution guarantees

See manifest.json for current gate status.
