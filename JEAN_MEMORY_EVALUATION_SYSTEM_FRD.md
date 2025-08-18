# Jean Memory Evaluation System - Mini-FRD

## **Part 1 — Mini-FRD (What & Why)**

### 1. **What**
Build a comprehensive evaluation system for the Jean Memory context engineering algorithm that measures memory retrieval accuracy, reasoning capabilities, and long-term conversation consistency using modern AI memory benchmarks (LoCoMo, HotpotQA, Cognee) while maintaining zero impact on production performance.

### 2. **Why**
Jean Memory's sophisticated context engineering system currently operates without systematic evaluation, making it impossible to measure improvements, detect regressions, or validate performance claims against research benchmarks. With LoCoMo research showing RAG systems perform best for long-term memory (exactly what Jean Memory is), we need evaluation to demonstrate competitive advantage and guide optimization efforts. This unblocks our ability to confidently iterate on the algorithm and prove Jean Memory's superiority over existing solutions.

### 3. **Scope**

**In Scope:**
- LoCoMo framework integration (5 reasoning types: single-hop, multi-hop, temporal, commonsense, adversarial)
- Extended conversation testing (10-35 session sequences)
- Evaluation of all three decision paths (New Conversation, Generic Knowledge, Contextual Conversation)
- Memory retrieval accuracy measurement at key pipeline points
- Long-range conversation consistency evaluation
- **LLM-as-a-Judge evaluation using Gemini Flash** for relevance, completeness, and reasoning quality scoring
- **Synthetic test data generation** using LLMs to create diverse conversation scenarios, memory injection sequences, and adversarial test cases
- **Test dataset management suite** for creating, versioning, and maintaining evaluation datasets
- SDK-based evaluation environment using React/Python SDKs
- Minimal-invasive decorator pattern for production monitoring
- Automated reporting and trend analysis
- Performance regression detection

**Out of Scope:**
- Modifying core jean_memory tool logic (only add evaluation layers)
- Real-time evaluation during production (evaluation mode toggle only)
- User-facing evaluation features
- Integration with external evaluation platforms
- Evaluation of non-memory features (OAuth, UI, etc.)
- Performance optimization implementation (only measurement)

### 4. **Acceptance Criteria**

#### Core Evaluation Infrastructure
- [ ] Evaluation system can be toggled on/off via environment variable with zero production impact
- [ ] Decorator pattern applied to key functions requires <10 lines of core code changes
- [ ] System captures metrics at all identified evaluation points: AI planning, memory search, context formatting, background tasks

#### LoCoMo Framework Integration
- [ ] All five LoCoMo reasoning types implemented: single-hop, multi-hop, temporal, commonsense, adversarial
- [ ] Extended conversation testing supports 10-35 session sequences
- [ ] Long-range consistency evaluation measures narrative coherence across sessions
- [ ] Adversarial robustness testing handles conflicting information scenarios

#### SDK-Based Testing Environment
- [ ] React SDK evaluation harness runs extended conversation tests
- [ ] Python SDK can inject synthetic memories and measure retrieval accuracy
- [ ] Test environment simulates real user interactions through SDKs
- [ ] Synthetic data generator creates diverse test scenarios using LLMs

#### Evaluation Metrics & Reporting
- [ ] System measures all target metrics: relevance (>8.5/10), completeness (>80%), latency P50 (<1000ms), P95 (<3000ms)
- [ ] LoCoMo-specific targets tracked: single-hop (>95%), multi-hop (>85%), temporal (>80%), adversarial (>75%), long-range consistency (>90%)
- [ ] Automated markdown reports generated with trend analysis
- [ ] Performance regression detection alerts when metrics drop below thresholds

#### Production Safety & Performance
- [ ] Evaluation mode disabled by default in production
- [ ] When enabled, evaluation runs asynchronously without blocking responses
- [ ] Memory consumption increase <50MB when evaluation active
- [ ] No measurable latency impact on user requests when evaluation disabled

#### LLM-as-a-Judge Implementation
- [ ] Gemini Flash integration for automated relevance scoring (0-10 scale)
- [ ] LLM judges evaluate context completeness against query requirements
- [ ] Reasoning quality assessment for multi-hop and temporal queries
- [ ] Automated consistency scoring across extended conversation sessions
- [ ] LLM-based adversarial robustness evaluation (conflicting information handling)
- [ ] Judge reliability validation through human annotation comparison on subset

#### Synthetic Data Generation & Management
- [ ] LLM-powered synthetic conversation generator creates diverse test scenarios
- [ ] Automated memory injection sequence creation for multi-hop testing
- [ ] Adversarial scenario generator creates conflicting information test cases
- [ ] Temporal event sequence generator creates time-based reasoning tests
- [ ] Persona-based conversation generation for consistent character testing

#### Test Dataset Management Suite
- [ ] Version-controlled test dataset storage with metadata tracking
- [ ] Dataset creation tools for manual test case authoring
- [ ] Import/export functionality for standard evaluation formats (JSON, CSV)
- [ ] Test case categorization and tagging system (LoCoMo types, difficulty levels)
- [ ] Dataset validation tools ensure test case quality and coverage
- [ ] Automated dataset expansion using synthetic generation
- [ ] Performance benchmarking datasets for regression testing
- [ ] Human-annotated gold standard datasets for judge calibration

#### Data & Test Coverage
- [ ] 100+ synthetic test cases across all LoCoMo reasoning types
- [ ] Test cases cover all three Jean Memory decision paths
- [ ] Temporal event graph test scenarios validate time-based reasoning
- [ ] Multi-hop reasoning tests require 3-5 memory traversals
- [ ] Adversarial tests include conflicting memory scenarios
- [ ] Balanced dataset distribution across difficulty levels and reasoning types
- [ ] Gold standard human-annotated subset (20+ cases) for judge validation

#### Integration & Automation
- [ ] CI/CD integration for automated evaluation runs
- [ ] Weekly automated evaluation reports generated
- [ ] Evaluation results stored with timestamp for trend analysis
- [ ] System compatible with existing logging infrastructure

#### Validation Against Research Benchmarks
- [ ] Jean Memory performance measured against LoCoMo benchmark standards
- [ ] Comparison framework validates superiority claims over existing solutions
- [ ] Results demonstrate Jean Memory's competitive advantage as advanced RAG system
- [ ] Documentation provides clear performance comparison with research baselines