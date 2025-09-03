# Policy Encoding (v0)

**Problem:** Policies live in wikis, not enforcement.  
**Goal:** Encode policy clauses into Sigma rules with provenance.

## Policy → Rule mapping
- Identify exact policy text → extract clauses as literal spans.
- Map to canonical rule forms (regex/SQL/JSON) using policy tokens and ranges explicitly present.
- Attach policy version, owner/team, and review date as rule metadata.

## Acceptance
- Each policy-derived rule includes: policy_id, excerpt (quote), owner, review_date
- HTML "Policy" section lists derived rules with citations