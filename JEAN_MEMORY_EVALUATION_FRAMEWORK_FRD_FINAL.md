# **Jean Memory Performance Evaluation & Testing Framework - Final FRD**

## **1. What**

Build a streamlined evaluation system for the Jean Memory context engineering algorithm that measures memory retrieval accuracy, reasoning capabilities, and conversation consistency using LoCoMo benchmarks. The system wraps the Python SDK as a black-box testing framework, leveraging existing instrumentation for zero-impact production monitoring.

## **2. Why**

Jean Memory's sophisticated context engineering system currently operates without systematic evaluation, making it impossible to measure improvements, detect regressions, or validate performance claims against research benchmarks. With LoCoMo research showing RAG systems perform best for long-term memory (exactly what Jean Memory is), we need evaluation to demonstrate competitive advantage and guide optimization efforts. This unblocks our ability to confidently iterate on the algorithm and prove Jean Memory's superiority over existing solutions.

## **3. Scope**

### **In Scope:**

- LoCoMo framework integration (5 reasoning types: single-hop, multi-hop, temporal, commonsense, adversarial)
- Extended conversation testing (5-35 message sequences)
- Python SDK wrapper-based evaluation (black-box testing approach)
- OAuth 2.1 PKCE authentication flow for real user testing
- Analysis and documentation of Python SDK functionality during implementation
- Evaluation of all three decision paths (New Conversation, Generic Knowledge, Contextual Conversation)
- Memory retrieval accuracy measurement via existing decorators
- Synthetic test data generation using LLMs
- JSON file-based dataset storage
- Markdown-based reporting with performance analysis
- CLI-based test orchestration for easy execution
- CI/CD integration support with manual authentication step

### **Out of Scope:**

- React SDK testing (Python SDK only)
- Automatic test user creation or authentication bypass
- Web-based dashboards or UI components
- Database storage (using JSON files)
- Gold standard human annotations
- Modifying core jean_memory tool logic
- Modifying Python SDK code
- Real-time evaluation during production
- User-facing evaluation features
- Integration with external evaluation platforms
- Evaluation of non-memory features (OAuth, UI, etc.)
- Performance optimization implementation (only measurement)

## **4. Acceptance Criteria**

### **Core Evaluation Infrastructure** ✅ (Task 1 - Complete)

- [x] Evaluation system can be toggled on/off via environment variable with zero production impact
- [x] Decorator pattern applied to key functions requires <10 lines of core code changes
- [x] System captures metrics at all identified evaluation points: AI planning, memory search, context formatting
- [x] Async evaluation processing without blocking main flow
- [x] Memory overhead <50MB when evaluation active

### **LLM Judge & Scoring System** ✅ (Task 2 - Complete)

- [x] Multi-provider LLM integration (Gemini, OpenAI GPT-5)
- [x] Consensus judging with outlier detection
- [x] All five LoCoMo reasoning types evaluated
- [x] 0-10 scoring scale with detailed explanations
- [x] Evaluation completes within 5-10 seconds per query

### **Synthetic Test Data Generation** ✅ (Task 3 - Complete)

- [x] LLM-powered test case generation across all LoCoMo types
- [x] Quality validation of generated test cases
- [x] Persona-based conversation generation
- [x] Difficulty level variation (easy, medium, hard)
- [x] Batch generation capability

### **Conversation Dataset Management** (Task 4)

- [ ] JSON file-based storage in `./test_datasets/` folder
- [ ] Generate conversations of configurable length (5-35 messages)
- [ ] Control LoCoMo type distribution (uniform or mixed)
- [ ] CLI interface for dataset generation
- [ ] Metadata tracking for each dataset
- [ ] Leverage Task 3 synthetic generator for test case creation

### **Python SDK Testing Harness** (Task 5)

- [ ] SDK wrapper approach (no SDK modifications)
- [ ] OAuth 2.1 PKCE authentication flow integration
- [ ] Manual user authentication support for testing
- [ ] Analysis and documentation of SDK behavior during implementation
- [ ] Testing of SDK error handling and edge cases
- [ ] Load and execute test datasets sequentially
- [ ] Call `client.get_context()` for each conversation turn
- [ ] Verification of jean_memory tool invocation
- [ ] Automatic metric capture via existing Task 1 decorators
- [ ] No modifications to production code required

### **Performance Reporting** (Task 6)

- [ ] Markdown report generation with LoCoMo breakdown
- [ ] LLM Judge scores for each conversation turn
- [ ] Response time analysis (average, P50, P95)
- [ ] Export to `./evaluation_reports/` folder
- [ ] Score breakdown by reasoning type
- [ ] Pass/fail determination based on thresholds

### **CLI Test Orchestration** (Task 7)

- [ ] Single command evaluation execution: `./run_evaluation.py`
- [ ] Configurable via command-line arguments (length, type)
- [ ] OAuth authentication flow guidance for users
- [ ] Progress indicators during execution
- [ ] Automatic report generation
- [ ] CI/CD compatible with proper exit codes (0 for pass, 1 for fail)
- [ ] Clear instructions for manual authentication step

### **LoCoMo Performance Targets**

- [ ] Single-hop reasoning: >90% accuracy (9.0/10 score)
- [ ] Multi-hop reasoning: >80% accuracy (8.0/10 score)
- [ ] Temporal reasoning: >75% accuracy (7.5/10 score)
- [ ] Adversarial handling: >70% accuracy (7.0/10 score)
- [ ] Commonsense integration: >75% accuracy (7.5/10 score)
- [ ] Overall average: >7.0/10 for passing grade

### **System Performance Requirements**

- [ ] Evaluation mode disabled by default in production
- [ ] Zero measurable latency impact when disabled
- [ ] Response latency P50 <1000ms, P95 <3000ms when enabled
- [ ] Support for 100+ test cases across all reasoning types
- [ ] Full conversation test (20 turns) completes within 5 minutes

## **5. Implementation Architecture**

### **SDK Wrapper Approach (Verified)**

The evaluation framework treats the Python SDK as a black box:

```python
# How it works:
1. Generate test conversation (Task 3 synthetic generator)
2. Create SDK client: JeanMemoryClient(api_key)
3. For each turn: client.get_context(user_token, message)
   → SDK makes MCP request to backend
   → jean_memory tool is called (already decorated)
   → Task 1 decorators capture metrics automatically
4. Task 2 LLM Judge evaluates response quality
5. Generate markdown report with results
```

### **Authentication Flow**

```python
# Production Mode (Required for all testing)
from jean_memory import JeanMemoryClient, JeanMemoryAuth

# Initialize with API key
client = JeanMemoryClient("jean_sk_your_key")
auth = JeanMemoryAuth("jean_sk_your_key")

# OAuth authentication flow
print("Opening browser for authentication...")
user_info = auth.authenticate()  # Opens browser for OAuth login
user_token = user_info['access_token']

# Use authenticated token for all requests
context = client.get_context(
    user_token=user_token,
    message="What were we discussing?"
)

# SDK Analysis during implementation:
# - Verify MCP request format
# - Confirm jean_memory tool invocation
# - Test error handling scenarios
# - Document response structure
```

## **6. Technical Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                  Evaluation Framework                        │
│                  (External SDK Wrapper)                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │    Task 4: Conversation Dataset Generator            │  │
│  │    • Uses Task 3 synthetic generator                 │  │
│  │    • Creates JSON conversation datasets              │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │    Task 5: Python SDK Test Harness                   │  │
│  │    • Wraps JeanMemoryClient (no modifications)       │  │
│  │    • OAuth authentication with manual login          │  │
│  │    • Analyzes SDK behavior during implementation     │  │
│  │    • Calls client.get_context() for each turn        │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│         [SDK calls jean_memory tool via MCP]                │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │    Existing Infrastructure (Automatic)               │  │
│  │    • Task 1 decorators capture metrics               │  │
│  │    • jean_memory tool processes request              │  │
│  │    • Response returned to SDK                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │    Task 2: LLM Judge Evaluation                      │  │
│  │    • Scores response quality (0-10)                  │  │
│  │    • Evaluates reasoning type accuracy               │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │    Task 6: Performance Report Generator              │  │
│  │    • Aggregates metrics and scores                   │  │
│  │    • Generates markdown report                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │    Task 7: CLI Test Runner                           │  │
│  │    • Single command orchestration                    │  │
│  │    • CI/CD integration support                       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## **7. Success Metrics**

- **Coverage**: All 5 LoCoMo reasoning types evaluated
- **Scale**: 100+ test cases across conversation lengths
- **Performance**: Meeting latency targets (P50 <1s, P95 <3s)
- **Quality**: LLM Judge scores >7/10 average
- **Automation**: Single CLI command for complete evaluation
- **Safety**: Zero production impact (external wrapper only)

## **8. Deliverables**

### **Code Components**

- ✅ Evaluation infrastructure with decorators (Task 1)
- ✅ LLM Judge service with consensus (Task 2)
- ✅ Synthetic data generator (Task 3)
- ⏳ Conversation dataset generator (Task 4)
- ⏳ Python SDK test harness wrapper (Task 5)
- ⏳ Markdown report generator (Task 6)
- ⏳ CLI orchestration script (Task 7)

### **Usage Interface**

```bash
# Standard evaluation run (OAuth authentication required)
./run_evaluation.py --api-key jean_sk_your_key \
                   --length 20 \
                   --type mixed
# Browser will open for OAuth login
# After authentication, tests will run automatically

# Uniform reasoning type test
./run_evaluation.py --api-key jean_sk_your_key \
                   --length 30 \
                   --type uniform \
                   --reasoning MULTI_HOP

# CI/CD integration (requires pre-authenticated token)
export JEAN_USER_TOKEN="<oauth_token_from_previous_auth>"
./run_evaluation.py --api-key $JEAN_API_KEY \
                   --user-token $JEAN_USER_TOKEN \
                   --length 10 \
                   --type mixed \
                   --ci-mode
```

### **Output Format**

```markdown
# Jean Memory Performance Evaluation Report

**Date**: 2025-08-16T10:30:00
**Conversation Length**: 20 turns
**Mode**: test

## Overall Performance
- **Average Score**: 8.2/10 ✅
- **P50 Latency**: 450ms
- **P95 Latency**: 1200ms

## LoCoMo Reasoning Breakdown
| Type | Avg Score | Pass Rate |
|------|-----------|-----------|
| Single-hop | 9.1/10 | 95% ✅ |
| Multi-hop | 7.8/10 | 78% ⚠️ |
| Temporal | 8.5/10 | 85% ✅ |
| Adversarial | 7.2/10 | 72% ✅ |
| Commonsense | 8.4/10 | 84% ✅ |

## Detailed Results
[Turn-by-turn analysis...]
```

## **9. Implementation Timeline**

### **Completed** (Weeks 1-2)
- ✅ Task 1: Core Evaluation Infrastructure
- ✅ Task 2: LLM Judge & Scoring System
- ✅ Task 3: Synthetic Test Data Generator

### **Remaining** (3 days)
- **Day 1**: Task 4 (Dataset Generator) + Task 5 (SDK Harness)
- **Day 2**: Task 6 (Report Generator) + Task 7 (CLI Runner)
- **Day 3**: Integration testing and documentation

## **10. Key Design Decisions**

### **SDK Wrapper Approach**
- **Decision**: Treat Python SDK as black box, no modifications
- **Rationale**: Zero production risk, authentic user experience testing
- **Benefit**: Existing decorators capture metrics automatically

### **OAuth Authentication Only**
- **Decision**: Require OAuth authentication for all testing
- **Rationale**: Tests real user experience, avoids authentication bypass complexity
- **Benefit**: Production-identical testing, security compliance

### **SDK Analysis During Implementation**
- **Decision**: Document SDK behavior as part of Task 5
- **Rationale**: Understand SDK internals for better testing
- **Benefit**: Creates documentation for future maintainers

### **JSON File Storage**
- **Decision**: Simple file-based dataset storage
- **Rationale**: No database complexity, easy versioning
- **Benefit**: Portable, debuggable, git-friendly

### **Markdown Reports**
- **Decision**: Plain markdown output instead of dashboards
- **Rationale**: Simple, readable, CI/CD friendly
- **Benefit**: No UI complexity, easy to share/review

## **11. Risk Mitigation**

| Risk | Mitigation | Impact |
|------|------------|---------|
| Production impact | External wrapper only, no core changes | Zero |
| OAuth authentication required | Clear documentation, manual step for CI/CD | Low |
| SDK changes break tests | Wrapper isolates changes, SDK analysis docs | Low |
| Timeout issues | Configurable timeouts, async processing | Low |
| CI/CD automation | Pre-authenticated tokens, clear instructions | Medium |

## **12. Success Criteria**

The evaluation framework is considered successful when:

1. **Functional**: Can run 20-turn conversations through SDK
2. **Accurate**: LLM Judge scores align with human assessment
3. **Performant**: Complete evaluation in <5 minutes
4. **Non-invasive**: Zero production code modifications
5. **Automated**: Single CLI command execution
6. **Reliable**: Consistent results across runs

---

**Status**: Ready for final implementation (Tasks 4-7)
**Effort**: 2-3 days remaining
**Risk**: Minimal (external wrapper only)
**Value**: Complete evaluation capability with zero production risk