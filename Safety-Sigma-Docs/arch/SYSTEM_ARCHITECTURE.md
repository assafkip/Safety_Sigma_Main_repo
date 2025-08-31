# Safety Sigma: System Architecture

**Version**: 2.0  
**Last Updated**: August 2025  
**Status**: MVP → Agent Evolution  

---

## Executive Summary

Safety Sigma employs a **compliance-first, agent-based architecture** designed specifically for Trust & Safety intelligence processing. The system transforms unstructured threat intelligence into operational detection rules while maintaining complete source traceability and zero-hallucination guarantees.

### Core Design Principles

1. **Compliance as Infrastructure**: Critical requirements enforced at system level, not prompt level
2. **Zero-Tolerance Policy**: Hard failures on any synthetic data generation or hallucination
3. **Complete Traceability**: Every extracted element linked to exact source location
4. **Incremental Evolution**: Maintain backward compatibility while adding agent capabilities
5. **Customer-Driven Development**: Regular validation with T&S professionals

---

## System Architecture Overview

### High-Level Data Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   INGESTION     │    │   PROCESSING    │    │   COMPILATION   │
│                 │    │                 │    │                 │
│ • PDF Parser    │───▶│ • Document      │───▶│ • SQL Generator │
│ • URL Fetcher   │    │   Analysis      │    │ • Python Rules  │
│ • Text Input    │    │ • Pattern       │    │ • Unit21 JSON   │
│                 │    │   Extraction    │    │ • Custom Format │
└─────────────────┘    │ • Validation    │    └─────────────────┘
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  AUDIT SYSTEM   │
                       │                 │
                       │ • Event Logs    │
                       │ • Compliance    │
                       │   Tracking      │
                       │ • Provenance    │
                       │   Records       │
                       └─────────────────┘
```

### Agent Architecture

```
                    ┌─────────────────┐
                    │  MASTER AGENT   │
                    │                 │
                    │ • Orchestration │
                    │ • Decision      │
                    │   Making        │
                    │ • Error         │
                    │   Recovery      │
                    └─────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ EXTRACTION  │    │ VALIDATION  │    │COMPILATION  │
│   AGENT     │    │   AGENT     │    │   AGENT     │
│             │    │             │    │             │
│ • Pattern   │    │ • Compliance│    │ • Multi-    │
│   Detection │    │   Checking  │    │   Target    │
│ • Source    │    │ • Quality   │    │   Rules     │
│   Citation  │    │   Assurance │    │ • Template  │
└─────────────┘    └─────────────┘    └─────────────┘
```

---

## Component Architecture

### 1. Document Processing Layer

**Purpose**: Convert various input formats to structured, span-aware text

**Components**:
```python
# PDF Processing with Span Preservation
class PDFProcessor:
    def extract_with_spans(self, pdf_path: str) -> DocumentData:
        # Extract text while maintaining character-level position tracking
        # Generate document hash for integrity verification
        # Preserve page/paragraph structure for citations
        
# Web Content Fetcher  
class WebFetcher:
    def fetch_with_metadata(self, url: str) -> DocumentData:
        # Retrieve web content with source attribution
        # Handle various content types (HTML, PDF, etc.)
        # Maintain URL provenance for audit trails

# Text Input Processor
class TextProcessor:
    def process_raw_text(self, text: str) -> DocumentData:
        # Structure raw text for processing
        # Generate synthetic spans for citation purposes
        # Validate text encoding and format
```

**Key Features**:
- **Span Preservation**: Character-level position tracking for exact citations
- **Document Hashing**: SHA-256 integrity verification for tamper detection
- **Multi-Format Support**: PDF (priority), HTML, plain text, URLs
- **Metadata Extraction**: Title, author, date, classification extraction

### 2. Intelligence Extraction Layer

**Purpose**: Extract threat patterns with zero-inference guarantee

**Components**:
```python
# Core Extraction Engine
class IntelligenceExtractor:
    def extract_patterns(self, document: DocumentData) -> ExtractionResult:
        # Zero-inference extraction using AI models
        # Pattern-specific extractors for different threat types
        # Complete source citation for every extracted element
        
# Specialized Pattern Extractors
class TemporalExtractor:
    def extract_time_patterns(self, text: str, spans: SpanData) -> List[TemporalPattern]
    
class FinancialExtractor:
    def extract_financial_indicators(self, text: str, spans: SpanData) -> List[FinancialPattern]
    
class InfrastructureExtractor:  
    def extract_technical_indicators(self, text: str, spans: SpanData) -> List[InfraPattern]
```

**Extraction Schema**:
```python
@dataclass
class ThreatPattern:
    pattern_id: str
    pattern_type: str
    confidence_level: str
    
    # Core pattern data with citations
    temporal_data: Optional[TemporalPattern]
    financial_data: Optional[FinancialPattern] 
    infrastructure_data: Optional[InfraPattern]
    behavioral_data: Optional[BehavioralPattern]
    
    # Complete provenance
    source_citations: List[SourceCitation]
    extraction_metadata: Dict[str, Any]
    
@dataclass  
class SourceCitation:
    page: int
    start_char: int
    end_char: int
    quoted_text: str
    context_before: str
    context_after: str
```

### 3. Compliance & Validation Layer

**Purpose**: Enforce zero-hallucination guarantee through architectural constraints

**Components**:
```python
# Compliance Engine - Zero Tolerance
class ComplianceEngine:
    def validate_extraction(self, result: ExtractionResult, source: DocumentData) -> ComplianceResult:
        violations = []
        
        # Check 1: All data must cite source spans
        violations.extend(self._verify_source_citations(result, source))
        
        # Check 2: No synthetic or inferred content
        violations.extend(self._detect_inference_violations(result, source))
        
        # Check 3: No hallucinated information
        violations.extend(self._detect_hallucinations(result, source))
        
        # Zero tolerance - any violations = hard failure
        return ComplianceResult(
            passed=len(violations) == 0,
            violations=violations,
            attestation=self._generate_attestation(violations)
        )

# Hallucination Detection
class HallucinationDetector:
    def detect_synthetic_content(self, extracted: str, source: str) -> List[Violation]:
        # Advanced detection of AI-generated content not in source
        # Pattern matching for common AI hallucination signatures
        # Cross-reference all claims against source material
        
# Citation Validator
class CitationValidator:
    def verify_citations(self, citations: List[Citation], source: DocumentData) -> ValidationResult:
        # Verify every citation refers to actual source content
        # Check quote accuracy and span correctness
        # Validate context preservation
```

### 4. Rule Compilation Layer

**Purpose**: Transform validated patterns into platform-specific detection rules

**Components**:
```python
# Multi-Target Rule Compiler
class RuleCompiler:
    def compile_for_platform(self, patterns: List[ThreatPattern], platform: str) -> RuleSet:
        compiler = self._get_platform_compiler(platform)
        return compiler.compile_rules(patterns)

# Platform-Specific Compilers
class SQLCompiler:
    def compile_rules(self, patterns: List[ThreatPattern]) -> SQLRuleSet:
        # Generate optimized SQL queries for threat detection
        # Include source comments and metadata
        # Multiple variants (high precision, high recall, balanced)
        
class PythonCompiler:
    def compile_rules(self, patterns: List[ThreatPattern]) -> PythonRuleSet:
        # Generate executable Python detection scripts
        # Include proper error handling and logging
        # Maintain source attribution in comments
        
class Unit21Compiler:
    def compile_rules(self, patterns: List[ThreatPattern]) -> Unit21RuleSet:
        # Generate Unit21-compatible JSON rule definitions
        # Map threat patterns to Unit21 rule structure
        # Include appropriate action specifications
```

### 5. Agent Coordination Layer

**Purpose**: Orchestrate specialized agents for optimal results

**Components**:
```python
# Master Agent - Coordination Logic
class MasterAgent:
    def process_intelligence(self, input_data: InputData) -> ProcessingResult:
        # Analyze document and select optimal processing strategy
        analysis = self.document_analyzer.analyze(input_data)
        
        # Coordinate specialized agents based on analysis
        extraction_result = self.extraction_agent.extract(input_data, analysis.strategy)
        validation_result = self.validation_agent.validate(extraction_result, input_data)
        
        if validation_result.passed:
            compilation_result = self.compilation_agent.compile(extraction_result, analysis.targets)
            return self._build_success_result(extraction_result, compilation_result)
        else:
            return self._build_failure_result(validation_result)

# Specialized Agents
class ExtractionAgent:
    def extract(self, document: DocumentData, strategy: ExtractionStrategy) -> ExtractionResult:
        # Specialized extraction based on threat type and complexity
        # Dynamic tool selection based on document characteristics
        # Optimized processing workflows for different scenarios

class ValidationAgent:
    def validate(self, extraction: ExtractionResult, source: DocumentData) -> ValidationResult:
        # Comprehensive validation using multiple compliance engines
        # Quality assurance checks beyond basic compliance
        # Performance optimization based on validation history

class CompilationAgent:
    def compile(self, extraction: ExtractionResult, targets: List[str]) -> CompilationResult:
        # Multi-target rule generation with optimization
        # Template management and version control
        # Rule effectiveness testing and validation
```

---

## Data Architecture

### Core Data Models

```python
# Document Data Model
@dataclass
class DocumentData:
    content: str
    spans: List[Span]  # Character-level position tracking
    metadata: DocumentMetadata
    document_hash: str
    processing_timestamp: datetime

# Span Data Model for Citations
@dataclass  
class Span:
    start_char: int
    end_char: int
    page: Optional[int]
    paragraph: Optional[int]
    text: str

# Processing Result Model
@dataclass
class ProcessingResult:
    success: bool
    extraction_data: Optional[ExtractionResult]
    validation_data: ValidationResult
    compilation_data: Optional[CompilationResult] 
    audit_trail: AuditTrail
    performance_metrics: PerformanceMetrics
```

### State Management

```python
# Processing State Tracking
class ProcessingState:
    def __init__(self, request_id: str):
        self.request_id = request_id
        self.current_stage = ProcessingStage.INITIALIZED
        self.stage_results = {}
        self.error_history = []
        self.performance_data = {}
        
    def transition_to_stage(self, stage: ProcessingStage, result: Any):
        # Record stage transition with timing and result data
        # Maintain complete processing history for audit
        # Enable rollback to previous stages if needed
```

---

## Security Architecture

### Data Security

- **Encryption**: AES-256 at rest, TLS 1.3 in transit
- **Access Control**: Role-based permissions with audit logging
- **PII Handling**: Automatic detection, redaction, and secure handling
- **Key Management**: Secure key rotation and escrow procedures

### Processing Security

- **Input Validation**: Comprehensive sanitization of all inputs
- **Output Validation**: All outputs verified before delivery
- **Sandboxing**: AI model calls isolated from system resources
- **Rate Limiting**: Protection against abuse and resource exhaustion

### Compliance Security

- **Audit Trails**: Cryptographically signed, immutable event logs
- **Data Provenance**: Complete lineage from input to output
- **Regulatory Compliance**: SOC 2, GDPR, financial services standards
- **Zero Trust**: Validation at every processing stage

---

## Performance Architecture

### Scalability Design

```python
# Horizontal Scaling Components
class LoadBalancer:
    def distribute_requests(self, request: ProcessingRequest) -> WorkerNode:
        # Route requests based on document type, size, complexity
        # Balance load across available worker nodes
        # Handle node failures with automatic failover

class WorkerNode:
    def process_document(self, document: DocumentData) -> ProcessingResult:
        # Independent processing capability
        # Local caching for performance optimization
        # Resource monitoring and automatic scaling
```

### Performance Optimization

- **Caching Strategy**: Document hash-based result caching
- **Parallel Processing**: Multi-threaded extraction for large documents  
- **Resource Management**: Dynamic allocation based on document complexity
- **Performance Monitoring**: Real-time metrics and alerting

### Current Performance Targets

- **Latency**: p95 ≤ 5 minutes per document (50-page FBI report)
- **Throughput**: 10-50 documents per day per node
- **Accuracy**: ≥95% extraction accuracy vs human expert
- **Uptime**: ≥99% availability during customer operations

---

## Evolution Architecture

### Phase 1 → Agent Migration Strategy

```python
# Backward Compatibility Layer
class CompatibilityLayer:
    def __init__(self):
        self.phase1_script = Phase1Script()  # Original working script
        self.agent_system = AgentSystem()     # New agent-based system
        
    def process_with_fallback(self, input_data: Any) -> ProcessingResult:
        try:
            # Try agent system first
            result = self.agent_system.process(input_data)
            
            # Validate agent result meets Phase 1 quality standards
            if self._validate_agent_result(result):
                return result
            else:
                # Fallback to Phase 1 script if quality issues
                return self.phase1_script.process(input_data)
                
        except Exception:
            # Hard fallback to Phase 1 for any agent system failures
            return self.phase1_script.process(input_data)
```

### Configuration Management

```yaml
# config/evolution_config.yaml
evolution_settings:
  current_step: 3  # Claude integration step
  enabled_features:
    - tool_abstraction
    - simple_agent_logic
    - claude_enhancement
  disabled_features:
    - dynamic_workflows
    - multi_agent_system
    - self_improvement
    
fallback_settings:
  enable_phase1_fallback: true
  fallback_threshold: 0.95  # Quality threshold for agent vs script
  max_agent_retries: 2
```

---

## Deployment Architecture

### Container Architecture

```dockerfile
# Multi-stage build for security and performance
FROM python:3.11-slim as base
# Install dependencies and security updates

FROM base as safety-sigma
# Copy application code and configuration
# Set up non-root user for security
# Configure health checks and monitoring
```

### Infrastructure Components

- **Application Server**: FastAPI with async processing
- **Background Processing**: Celery with Redis for task management
- **Data Storage**: PostgreSQL for structured data, S3 for documents
- **Monitoring**: Prometheus metrics, Grafana dashboards
- **Logging**: Structured logging with ELK stack integration

### Deployment Strategies

- **Development**: Local Docker Compose stack
- **Staging**: Single-node deployment with full monitoring
- **Production**: Multi-node with load balancing and auto-scaling
- **Customer Deployment**: Containerized on-premises option

---

## Monitoring & Observability

### Key Metrics

**Processing Metrics**:
- Document processing latency (p50, p95, p99)
- Extraction accuracy rates
- Compliance violation rates
- System resource utilization

**Business Metrics**:
- Customer satisfaction scores
- Rule deployment success rates
- Time-to-value measurements
- Feature adoption rates

**Operational Metrics**:
- System uptime and availability
- Error rates and types
- Performance degradation alerts
- Security event monitoring

### Alerting Strategy

```python
# Alert Configuration
class AlertManager:
    def configure_alerts(self):
        # Critical: Compliance violations (immediate escalation)
        # High: Performance degradation >2x baseline
        # Medium: Error rate increase >5%
        # Low: Resource utilization >80%
```

---

## Future Architecture Considerations

### Network Effects Platform

- **Cross-Customer Intelligence**: Privacy-preserving threat pattern sharing
- **Collective Defense**: Industry-wide threat correlation
- **Intelligence Marketplace**: Verified threat pattern exchange

### Advanced Capabilities

- **Real-Time Processing**: Stream processing for live threat feeds  
- **Advanced Analytics**: ML-based threat evolution prediction
- **Integration Ecosystem**: Native platform integrations and APIs
- **Enterprise Features**: SSO, RBAC, advanced compliance reporting

---

This architecture document provides the technical foundation for Safety Sigma's evolution from MVP script to enterprise-grade agent system while maintaining the core compliance and quality guarantees that differentiate the platform.