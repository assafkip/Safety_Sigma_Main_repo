# Safety Sigma Roadmap & Release Planning

## Version History & Planning

### v0.9b: Behavioral Slice (CURRENT)
- **Status**: Implementation Complete
- **Features**: 
  - Behavioral indicators as first-class entities (`type=behavior`)
  - Literal behavioral extraction (redirects, spoofing, urgency, payment methods)
  - EDAP expansions for behavioral enumerations (advisory)
  - Memory integration showing behavioral families across cases
  - HTML behavioral analysis and behavioral families sections
  - Golden tests G-060, G-061, G-062 for compliance
- **Compliance**: Preserves V-001..V-005, zero-inference principle
- **Target**: Enhanced behavioral context without authority mutation

### v0.10: Faithfulness Gate (PLANNED)
- **Status**: Not Started
- **Features**:
  - A-806 faithfulness gate (non-blocking)
  - Enhanced validation for LLM outputs
  - Consistency checks across lanes
- **Target**: Improved quality assurance for advisory outputs

### v1.0: Campaign Context (FUTURE)
- **Status**: Concept Phase
- **Features**:
  - Infrastructure overlaps detection
  - Victimology pattern analysis
  - Campaign-level context (advisory)
- **Target**: Strategic threat intelligence integration

## Release Principles
- **Authority Preservation**: Scripted lane (V-001..V-005) remains unmodified
- **Advisory Expansion**: New features are NON-AUTHORITATIVE unless explicitly validated
- **Zero Inference**: No behavioral or contextual guessing
- **Memory Safe**: Cumulative features don't influence authoritative decisions

## Quality Gates
- **V-001..V-005**: Scripted lane validation (authoritative)
- **V-006**: Deployment adapters
- **V-007**: Sharing and export integrity  
- **A-801..A-805**: Agentic decision validation (advisory)
- **A-806**: Faithfulness validation (planned v0.10)

## Testing Strategy
- **Golden Tests**: G-060+ for behavioral compliance
- **Unit Tests**: Component-level validation
- **Integration Tests**: End-to-end pipeline validation
- **Memory Tests**: Cross-case consistency validation