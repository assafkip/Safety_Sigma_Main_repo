![Golden Tests](https://github.com/assafkip/Safety_Sigma_Main_repo/actions/workflows/golden.yml/badge.svg)
![Golden Tests](https://github.com/assafkip/Safety_Sigma_Main_repo/actions/workflows/golden.yml/badge.svg)

# docs# Safety Sigma: AI-Powered Threat Intelligence to Detection Rules

[![Status](https://img.shields.io/badge/Status-MVP%20Development-yellow)](https://github.com/safety-sigma)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-Proprietary-red)](LICENSE)

## Overview

Safety Sigma transforms threat intelligence reports into operational detection rules with zero hallucinations and complete source traceability. Built specifically for Trust & Safety teams who need to rapidly deploy threat intelligence without manual rule creation.

### The Problem

Trust & Safety teams receive threat intelligence daily (FBI alerts, CISA advisories, industry reports) but struggle to operationalize it:
- **Translation bottleneck**: Analysts understand threats but can't code detection rules
- **Engineering dependency**: Rule creation requires engineering sprints (2-4 weeks typical)
- **Context loss**: Critical threat narrative lost during handoffs
- **Reinvention**: Every platform rebuilds the same defenses independently

### The Solution

**AI agent system that converts threat intelligence → operational detection rules in hours, not weeks.**

Key differentiators:
- **Zero hallucinations**: Only extracts explicitly stated information with source citations
- **Compliance-first**: Built-in audit trails and regulatory compliance features
- **Multi-target**: Generates rules for SQL, Python, Unit21, Sift, and custom platforms
- **Institutional memory**: Preserves complete threat context and decision rationale

---

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   INPUT LAYER   │    │  AGENT SYSTEM   │    │  OUTPUT LAYER   │
│                 │    │                 │    │                 │
│ • PDF Reports   │────│ • Document      │────│ • SQL Queries   │
│ • Web URLs      │    │   Analysis      │    │ • Python Rules  │
│ • Text Input    │    │ • Pattern       │    │ • Unit21 JSON   │
│                 │    │   Extraction    │    │ • Audit Trails  │
└─────────────────┘    │ • Rule          │    └─────────────────┘
                       │   Compilation   │
                       │ • Validation    │
                       └─────────────────┘
```

### Core Components

- **Document Processor**: PDF/text parsing with span preservation for citations
- **Intelligence Extractor**: Zero-inference pattern extraction with Claude/GPT-4
- **Multi-Agent System**: Specialized agents for extraction, validation, compilation
- **Compliance Engine**: Hard validation against hallucination and synthetic data
- **Rule Compiler**: Multi-target rule generation (SQL, Python, Unit21, etc.)
- **Audit System**: Complete processing provenance and decision trails

---

## Current Status: MVP Phase 1 → Agent Evolution

### Phase 1 MVP (✅ Complete)
**Working script-based system**:
- PDF processing with PyPDF2 ✅
- Zero-inference extraction with GPT-4 ✅  
- Multi-format rule generation ✅
- Compliance validation ✅
- Basic audit trails ✅

**Key Phase 1 Learnings**:
- Compliance must be architectural, not prompt-based
- User feedback integration essential for accuracy
- Source traceability critical for enterprise adoption
- Clear separation needed between extraction and analysis

### Phase 2: Agent Evolution (🚧 In Progress)
**Goal**: Transform Phase 1 script into agent-based system through 6 incremental steps

Current evolution plan:
1. **Tool Abstraction** (Week 1): Wrap existing functions as tools
2. **Simple Agent Logic** (Week 2): Add basic decision-making
3. **Claude Integration** (Week 3): Safe AI enhancement capabilities
4. **Dynamic Workflows** (Week 4): Threat-specific processing strategies
5. **Multi-Agent System** (Week 5): Specialized agent collaboration
6. **Self-Improvement** (Week 6): Performance learning and optimization

Each step maintains backward compatibility while adding new capabilities.

---

## Technical Specifications

### Requirements
- **Python**: 3.8+
- **AI Models**: Claude 3.5 (primary), GPT-4 (backup)
- **Dependencies**: PyPDF2, anthropic, openai, pydantic
- **Deployment**: Single machine, Docker containerized

### Performance Targets
- **Processing Time**: ≤2× Phase 1 baseline (~2-5 minutes per document)
- **Accuracy**: ≥95% compared to human expert extraction
- **Compliance**: 100% zero-hallucination guarantee
- **Throughput**: 10-50 documents/day (sufficient for current market)

### Security & Compliance
- **Zero-inference policy**: No AI-generated data not present in source
- **Complete traceability**: Every extraction linked to source spans
- **Audit trails**: Immutable processing logs with cryptographic integrity
- **PII handling**: Automatic detection and redaction
- **TLP compliance**: Traffic Light Protocol classification support

---

## Market Validation

### Target Customers
- **Primary**: Trust & Safety teams at Series B+ companies
- **Secondary**: Fraud teams at fintech/payments companies  
- **Tertiary**: Security operations centers needing threat operationalization

### Validated Pain Points
- 67% of T&S teams report 2+ week delays converting intel to detection rules
- Engineering capacity consistently bottlenecks threat response
- Critical threat context lost in analyst → engineer handoffs
- Industry lacks standardized approach to threat intelligence operationalization

### Competitive Advantage
- **Only solution**: AI designed specifically for T&S intelligence processing
- **Compliance-first**: Zero tolerance for hallucinations (critical for regulatory environments)
- **Source preservation**: Complete threat narrative maintained through pipeline
- **Multi-platform**: Works with existing detection infrastructure

---

## Development Roadmap

### Next 30 Days: Agent Evolution Completion
- Complete 6-step evolution from script to agent system
- Customer validation demos after Steps 2, 4, and 6
- Performance benchmarking against Phase 1 baseline

### Next 60 Days: Customer Pilots
- 3-5 pilot customer deployments
- Production hardening based on customer feedback
- Initial revenue generation ($1-5K MRR target)

### Next 90 Days: Platform Integration
- Native integrations with Sift, Unit21, Datadog
- API development for custom platform connections
- Self-service customer onboarding

### 6+ Months: Scale & Network Effects
- Cross-customer intelligence sharing (privacy-preserving)
- Advanced threat correlation capabilities
- Enterprise security certifications (SOC 2, etc.)

---

## Repository Structure

```
safety-sigma/
├── README.md                    # This file
├── docs/                        # Technical documentation
│   ├── ARCHITECTURE.md          # System architecture details
│   ├── DEVELOPMENT.md           # Development setup and guidelines
│   ├── EVOLUTION_PLAN.md        # Phase 1 → Agent evolution details
│   └── COMPLIANCE.md            # Compliance framework documentation
├── src/                         # Source code
│   ├── phase1_script/           # Current MVP implementation
│   ├── agents/                  # Agent-based system (in development)
│   ├── tools/                   # Processing tools and abstractions
│   └── tests/                   # Test suites and validation
├── config/                      # Configuration files
├── data/                        # Sample data and golden datasets
└── scripts/                     # Utility and deployment scripts
```

---

## Key Metrics & KPIs

### Technical Metrics
- **Processing latency**: p95 ≤ 5 minutes per document
- **Extraction accuracy**: ≥95% vs human expert baseline
- **Compliance pass rate**: 100% (zero tolerance for violations)
- **System uptime**: ≥99% during customer pilots

### Business Metrics  
- **Customer validation**: ≥80% of demos result in pilot interest
- **Time to value**: ≤2 hours from document to deployed rules
- **Customer satisfaction**: ≥4.5/5.0 rating from pilot customers
- **Revenue growth**: $10K MRR within 6 months

### Strategic Metrics
- **Market positioning**: Recognition as category leader in T&S AI tools
- **Customer retention**: ≥95% pilot → paid conversion rate
- **Competitive moat**: Technical capabilities 6+ months ahead of competitors
- **Network effects**: Cross-customer intelligence sharing platform

---

## Getting Started

### For Development
```bash
git clone https://github.com/safety-sigma/safety-sigma
cd safety-sigma
pip install -r requirements.txt
python scripts/setup_dev_environment.py
```

### For CTO Review
Key files to examine:
1. `docs/ARCHITECTURE.md` - Technical system design
2. `docs/EVOLUTION_PLAN.md` - Phase 1 → Agent transformation details  
3. `docs/COMPLIANCE.md` - Zero-hallucination framework
4. `src/phase1_script/` - Current working implementation
5. `tests/` - Validation and compliance test suites

---

## Contact & Support

**Founder**: Assaf Kipnis  
**Role**: Technical Lead & Product Owner  
**Background**: 10+ years Trust & Safety operations  

**Technical Questions**: Create GitHub issue or see `docs/DEVELOPMENT.md`  
**Business Inquiries**: Contact through company channels  
**Customer Pilots**: See pilot program documentation in `docs/`

---

*Safety Sigma is in active development. This README reflects current state and immediate roadmap. Technical specifications and timelines subject to change based on customer feedback and technical validation.*
