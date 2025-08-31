# Safety Sigma 2.0

Advanced threat intelligence detection system with modular architecture, agent-based processing, and comprehensive audit trails.

## Overview

Safety Sigma 2.0 is the evolution of the original Safety Sigma system, designed with:
- **Modular architecture** with pluggable tools and agents
- **Backward compatibility** with Safety Sigma 1.0
- **Feature toggles** for risk-free adoption
- **Comprehensive audit trails** and compliance guarantees
- **Zero-inference compliance** for regulatory requirements

## Quick Start

### Bootstrap the repository
```bash
make bootstrap
```

### Run with v1.0 parity (default)
```bash
safety-sigma --pdf report.pdf --instructions prompt.md
```

### Enable v2.0 features (optional)
```bash
# Copy and configure environment
cp .env.example .env
# Edit .env to enable desired features

# Run with tool abstraction
SS2_ENABLE_TOOLS=true safety-sigma --pdf report.pdf --instructions prompt.md
```

## Architecture

Safety Sigma 2.0 follows a staged evolution approach:

### Stage 0: Bootstrap & Parity Harness ✅
- Repository structure and dependency management
- Parity testing framework ensuring v1.0 compatibility
- CI/CD pipeline with regression testing

### Stage 1: Tool Abstraction (wrap, don't change) ✅
- `tools/base_tool.py` - Abstract tool interface with audit logging
- Tool wrappers for PDF processing and extraction  
- Sequential orchestration with execution logs
- **Toggle**: `SS2_ENABLE_TOOLS`

### Stage 2: Simple Agent Logic (deterministic)
- Basic agent with input analysis and workflow selection
- Hardcoded decision trees for document processing
- **Toggle**: `SS2_USE_AGENT`

### Stage 3: Claude Integration (documentation only)
- Documentation enhancement without changing rule logic
- Pre/post validation and compliance checking
- **Toggle**: `SS2_ENHANCE_DOCS`

### Stage 4: Dynamic Workflows
- Document analysis and threat classification
- Specialized processing templates per threat type
- **Toggle**: `SS2_DYNAMIC_WORKFLOWS`

### Stage 5: Multi-Agent System
- Specialized agents for extraction, validation, and compilation
- Agent coordination and communication
- **Toggle**: `SS2_MULTI_AGENT`

### Stage 6: Self-Improvement Loop
- Performance tracking and metrics collection
- Adaptive processing strategies
- **Toggle**: `SS2_SELF_IMPROVE`

## Build Ledger

| Stage | Documentation | Status |
|-------|---------------|--------|
| Stage 0 | [docs/stages/stage-0.md](docs/stages/stage-0.md) | ✅ Complete |
| Stage 1 | [docs/stages/stage-1.md](docs/stages/stage-1.md) | ✅ Complete |
| Stage 2 | [docs/stages/stage-2.md](docs/stages/stage-2.md) | ⏳ Pending |
| Stage 3 | [docs/stages/stage-3.md](docs/stages/stage-3.md) | ⏳ Pending |
| Stage 4 | [docs/stages/stage-4.md](docs/stages/stage-4.md) | ⏳ Pending |
| Stage 5 | [docs/stages/stage-5.md](docs/stages/stage-5.md) | ⏳ Pending |
| Stage 6 | [docs/stages/stage-6.md](docs/stages/stage-6.md) | ⏳ Pending |

## Development

### Make Targets
```bash
make bootstrap    # Initialize repository and dependencies
make test        # Run all tests including parity checks
make lint        # Run code formatting and linting
make demo        # Run demo with sample data
```

### Feature Toggles

All v2.0 features are disabled by default to maintain v1.0 parity:

- `SS2_ENABLE_TOOLS=false` - Tool abstraction layer
- `SS2_USE_AGENT=false` - Agent-based processing  
- `SS2_ENHANCE_DOCS=false` - Documentation enhancements
- `SS2_DYNAMIC_WORKFLOWS=false` - Threat-specific workflows
- `SS2_MULTI_AGENT=false` - Multi-agent coordination
- `SS2_SELF_IMPROVE=false` - Self-improvement loop

### Compliance Guarantees

- **Zero-inference mode**: Only extract literal data from source documents
- **Source traceability**: Every output spans back to original document sections
- **Audit trails**: Complete execution logs with timing and validation results
- **Validation gates**: Fail-closed validation on all synthetic content detection

## Testing

### Parity Testing
```bash
# Run parity tests against Safety Sigma 1.0
make test-parity

# Generate parity baseline 
python -m tests.test_parity_baseline --generate-baseline
```

### Stage-specific Testing
```bash
# Test specific stage with feature toggles
SS2_ENABLE_TOOLS=true make test-stage1
SS2_USE_AGENT=true make test-stage2
```

## License

MIT License - see LICENSE file for details.