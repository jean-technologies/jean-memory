# **Jean Memory Performance Evaluation & Testing Framework - Updated FRD**

**Document Version:** 2.0.0  
**Date:** August 16, 2025  
**Status:** Tasks 1-4 Complete, Task 5 Redesigned

---

## **Updated Task Description**

Create comprehensive evaluation system to measure and validate Jean Memory's context engineering performance against research benchmarks (LoCoMo, HotpotQA) with automated testing, LLM-as-a-judge scoring, and regression detection capabilities.

### **Completed Tasks (1-4):**
1. ✅ Core Evaluation Infrastructure
2. ✅ LLM Judge & Scoring System  
3. ✅ Synthetic Test Data Generator
4. ✅ Conversation Dataset Generator

### **Redesigned Task (5):**
5. ⏳ **Minimal SDK Test Harness** (replacing Python SDK Test Harness)
   - Direct MCP endpoint testing without SDK dependencies
   - OAuth token reuse from Claude Desktop authentication
   - Log parsing for performance metrics extraction
   
### **Remaining Tasks (6-7):**
6. ⏳ Basic Performance Report Generator
7. ⏳ CLI Test Runner

---

## **1. What**

Build a streamlined evaluation system for the Jean Memory context engineering algorithm that measures memory retrieval accuracy, reasoning capabilities, and conversation consistency using LoCoMo benchmarks. The system uses **direct MCP endpoint calls** to test the stable jean_memory tool, bypassing the evolving Python SDK, while leveraging existing instrumentation for zero-impact production monitoring.

## **2. Why**

Jean Memory's sophisticated context engineering system currently operates without systematic evaluation, making it impossible to measure improvements, detect regressions, or validate performance claims against research benchmarks. With LoCoMo research showing RAG systems perform best for long-term memory (exactly what Jean Memory is), we need evaluation to demonstrate competitive advantage and guide optimization efforts. The Python SDK's ongoing development makes it unstable for testing, so **direct MCP testing provides a reliable evaluation path** using the stable jean_memory tool interface.

## **3. Scope**

### **In Scope:**

- LoCoMo framework integration (5 reasoning types: single-hop, multi-hop, temporal, commonsense, adversarial)
- Extended conversation testing (5-35 message sequences)
- **Direct MCP endpoint testing (stable jean_memory tool)**
- **OAuth token reuse from Claude Desktop sessions**
- **Render log parsing for performance metrics**
- Evaluation of all three decision paths (New Conversation, Generic Knowledge, Contextual Conversation)
- Memory retrieval accuracy measurement via existing decorators
- Synthetic test data generation using LLMs
- JSON file-based dataset storage
- Markdown-based reporting with performance analysis
- CLI-based test orchestration for easy execution

### **Out of Scope:**

- Python SDK modifications or testing
- React SDK testing
- Full OAuth 2.1 PKCE flow implementation
- Mock user creation
- Web-based dashboards or UI components
- Database storage (using JSON files)
- Gold standard human annotations
- Modifying core jean_memory tool logic
- Real-time evaluation during production
- User-facing evaluation features
- Integration with external evaluation platforms

## **4. Acceptance Criteria**

### **Core Evaluation Infrastructure ✅ (Task 1 - Complete)**

- [x] Evaluation system can be toggled on/off via environment variable with zero production impact
- [x] Decorator pattern applied to key functions requires <10 lines of core code changes
- [x] System captures metrics at all identified evaluation points: AI planning, memory search, context formatting
- [x] Async evaluation processing without blocking main flow
- [x] Memory overhead <50MB when evaluation active

### **LLM Judge & Scoring System ✅ (Task 2 - Complete)**

- [x] Multi-provider LLM integration (Gemini, OpenAI GPT-5)
- [x] Consensus judging with outlier detection
- [x] All five LoCoMo reasoning types evaluated
- [x] 0-10 scoring scale with detailed explanations
- [x] Evaluation completes within 5-10 seconds per query

### **Synthetic Test Data Generation ✅ (Task 3 - Complete)**

- [x] LLM-powered test case generation across all LoCoMo types
- [x] Quality validation of generated test cases
- [x] Persona-based conversation generation
- [x] Difficulty level variation (easy, medium, hard)
- [x] Batch generation capability

### **Conversation Dataset Management ✅ (Task 4 - Complete)**

- [x] JSON file-based storage in `./test_datasets/` folder
- [x] Generate conversations of configurable length (5-35 messages)
- [x] Control LoCoMo type distribution (uniform or mixed)
- [x] CLI interface for dataset generation
- [x] Metadata tracking for each dataset
- [x] Leverage Task 3 synthetic generator for test case creation

### **Minimal SDK Test Harness (Task 5 - Redesigned)**

- [ ] **Direct MCP endpoint calls** (no SDK dependency)
- [ ] **OAuth token extraction** from Claude Desktop session
- [ ] **Token reuse mechanism** for automated testing
- [ ] Load and execute test datasets sequentially
- [ ] Call jean_memory tool via MCP for each turn
- [ ] **Log parsing** for performance metrics extraction
- [ ] Automatic metric capture via existing Task 1 decorators
- [ ] No modifications to production code required

### **Performance Reporting (Task 6)**

- [ ] Markdown report generation with LoCoMo breakdown
- [ ] LLM Judge scores for each conversation turn
- [ ] **Log-based performance metrics** (orchestration time, cache hits)
- [ ] Response time analysis (average, P50, P95)
- [ ] Export to `./evaluation_reports/` folder
- [ ] Score breakdown by reasoning type
- [ ] Pass/fail determination based on thresholds

### **CLI Test Orchestration (Task 7)**

- [ ] Single command evaluation execution: `./run_evaluation.py`
- [ ] **Token setup wizard** for first-time configuration
- [ ] Configurable via command-line arguments (length, type, mode)
- [ ] Progress indicators during execution
- [ ] Automatic report generation
- [ ] Support for saved authentication tokens
- [ ] **Log file input option** for offline analysis

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

## **5. Implementation Architecture (Updated)**

### **Direct MCP Testing Approach**

The evaluation framework bypasses the Python SDK entirely:

```python
# How it works:
1. Generate test conversation (Task 4 datasets)
2. Extract OAuth token from Claude Desktop session
3. For each turn: 
   → Direct POST to /mcp/v2/claude/{user_id}
   → jean_memory tool is called (already decorated)
   → Task 1 decorators capture metrics automatically
   → Parse logs for performance metrics
4. Task 2 LLM Judge evaluates response quality
5. Generate markdown report with results
```

### **Authentication Flow (Simplified)**

```python
# One-time token extraction
auth_helper = JeanMemoryAuth()
token = auth_helper.extract_token_from_browser()
auth_helper.save_token(".jean_memory_token")

# Automated testing
client = MinimalMCPClient(
    user_id="fa97efb5-410d-4806-b137-8cf13b6cb464",
    token=token
)
response = await client.call_jean_memory("What are my hobbies?")
```

## **6. Technical Architecture (Updated)**

```
┌─────────────────────────────────────────────────────────────┐
│                  Evaluation Framework                        │
│                  (Direct MCP Testing)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │    Task 4: Conversation Dataset Generator ✅         │  │
│  │    • Uses Task 3 synthetic generator                 │  │
│  │    • Creates JSON conversation datasets              │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │    Task 5: Minimal MCP Test Harness (NEW)            │  │
│  │    • Direct HTTP calls to MCP endpoint               │  │
│  │    • OAuth token reuse from Claude Desktop           │  │
│  │    • No Python SDK dependency                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│         [Direct MCP call to jean_memory tool]               │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │    Existing Infrastructure (Automatic)               │  │
│  │    • Task 1 decorators capture metrics               │  │
│  │    • jean_memory tool processes request              │  │
│  │    • Response returned via MCP                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │    Log Parser (NEW)                                  │  │
│  │    • Extract [PERF] metrics from Render logs         │  │
│  │    • Parse context strategies and cache hits         │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │    Task 2: LLM Judge Evaluation ✅                   │  │
│  │    • Scores response quality (0-10)                  │  │
│  │    • Evaluates reasoning type accuracy               │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │    Task 6: Performance Report Generator              │  │
│  │    • Aggregates metrics, scores, and logs            │  │
│  │    • Generates comprehensive markdown report         │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │    Task 7: CLI Test Runner                           │  │
│  │    • Single command orchestration                    │  │
│  │    • Token setup wizard                              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## **7. Success Metrics**

- **Coverage**: All 5 LoCoMo reasoning types evaluated
- **Scale**: 100+ test cases across conversation lengths
- **Performance**: Meeting latency targets (P50 <1s, P95 <3s)
- **Quality**: LLM Judge scores >7/10 average
- **Automation**: Single CLI command for complete evaluation
- **Safety**: Zero production impact (direct MCP calls only)
- **Reliability**: No SDK dependencies, stable MCP interface

## **8. Deliverables**

### **Code Components**

- ✅ Evaluation infrastructure with decorators (Task 1)
- ✅ LLM Judge service with consensus (Task 2)
- ✅ Synthetic data generator (Task 3)
- ✅ Conversation dataset generator (Task 4)
- ⏳ **Minimal MCP test harness** (Task 5 - Redesigned)
  - `auth_helper.py` - Token extraction and management
  - `minimal_mcp_client.py` - Direct MCP endpoint client
  - `minimal_test_runner.py` - Test orchestration
  - `log_parser.py` - Performance metrics extraction
- ⏳ Markdown report generator (Task 6)
- ⏳ CLI orchestration script (Task 7)

### **Usage Interface (Updated)**

```bash
# First-time setup (extract token from Claude Desktop)
./run_evaluation.py --setup

# Run evaluation with saved token
./run_evaluation.py --user-id fa97efb5-410d-4806-b137-8cf13b6cb464 \
                   --length 20 \
                   --type mixed

# Parse existing logs
./run_evaluation.py --user-id fa97efb5-410d-4806-b137-8cf13b6cb464 \
                   --log-file render_logs.txt \
                   --type uniform \
                   --reasoning MULTI_HOP

# Quick test (5 turns)
./run_evaluation.py --quick-test
```

### **Output Format**

```markdown
# Jean Memory Performance Evaluation Report

**Date**: 2025-08-16T10:30:00
**Conversation Length**: 20 turns
**Evaluation Method**: Direct MCP Testing
**User ID**: fa97efb5-410d-4806-b137-8cf13b6cb464

## Overall Performance
- **Average Score**: 8.2/10 ✅
- **P50 Latency**: 450ms (from logs)
- **P95 Latency**: 1200ms (from logs)
- **Total Orchestration Time**: 12.33s
- **Cache Hit Rate**: 85%

## LoCoMo Reasoning Breakdown
| Type | Avg Score | Pass Rate | Avg Latency |
|------|-----------|-----------|-------------|
| Single-hop | 9.1/10 | 95% ✅ | 320ms |
| Multi-hop | 7.8/10 | 78% ⚠️ | 580ms |
| Temporal | 8.5/10 | 85% ✅ | 410ms |
| Adversarial | 7.2/10 | 72% ✅ | 490ms |
| Commonsense | 8.4/10 | 84% ✅ | 380ms |

## Performance Metrics (from logs)
- **AI Plan Creation**: 3.84s average
- **Context Execution**: 8.49s average
- **Memory Searches**: 3 per request
- **Context Strategy**: deep_understanding (60%), standard (40%)

## Detailed Results
[Turn-by-turn analysis with log excerpts...]
```

## **9. Implementation Timeline (Updated)**

### **Completed (Weeks 1-2)**

- ✅ Task 1: Core Evaluation Infrastructure
- ✅ Task 2: LLM Judge & Scoring System
- ✅ Task 3: Synthetic Test Data Generator
- ✅ Task 4: Conversation Dataset Generator

### **Remaining (1 week)**

- **Day 1**: Task 5 Subtask 1 - Authentication Token Management (5 hours)
- **Day 2**: Task 5 Subtask 2 - MCP Client Implementation (6 hours)
- **Day 3**: Task 5 Subtask 3 - Test Orchestration System (7 hours)
- **Day 4**: Task 5 Subtask 4 - Log Collection Integration (7 hours)
- **Day 5**: Task 5 Subtask 5 - Report Generation + Tasks 6-7 (7 hours)

## **10. Key Design Decisions (Updated)**

### **Direct MCP Testing**

- **Decision**: Bypass Python SDK, call MCP endpoints directly
- **Rationale**: SDK instability, frequent changes
- **Benefit**: Stable interface, authentic tool testing

### **OAuth Token Reuse**

- **Decision**: Extract and reuse tokens from Claude Desktop
- **Rationale**: Avoid complex OAuth implementation
- **Benefit**: Real user authentication without OAuth flow

### **Log-Based Metrics**

- **Decision**: Parse Render logs for performance data
- **Rationale**: Rich metrics not available in MCP responses
- **Benefit**: Complete performance visibility

### **Minimal Implementation**

- **Decision**: 200 lines of code vs full SDK harness
- **Rationale**: Faster development, easier maintenance
- **Benefit**: 1 week implementation vs 3+ weeks

## **11. Risk Mitigation (Updated)**

| Risk | Mitigation | Impact |
| --- | --- | --- |
| Token expiry | Clear error messages, refresh guide | Low |
| MCP API changes | Version locking, monitoring | Low |
| Log format changes | Flexible regex patterns | Low |
| No SDK testing | Direct tool testing more accurate | None |
| Manual token setup | One-time process, detailed guide | Low |

## **12. Success Criteria**

The evaluation framework is considered successful when:

1. **Functional**: Can run 20-turn conversations via MCP
2. **Accurate**: LLM Judge scores align with human assessment
3. **Performant**: Complete evaluation in <5 minutes
4. **Non-invasive**: Zero production code modifications
5. **Automated**: Single CLI command execution
6. **Reliable**: Consistent results across runs
7. **Comprehensive**: Log metrics provide full visibility

## **13. Task 5 Subtask Breakdown**

### **Subtask 5.1: Authentication Token Management (5 hours)**
- Token extraction helper script
- Secure local storage
- Validation and refresh detection

### **Subtask 5.2: MCP Client Implementation (6 hours)**
- Direct HTTP client for MCP v2
- Retry logic and error handling
- Request/response logging

### **Subtask 5.3: Test Orchestration System (7 hours)**
- Dataset loading and execution
- Conversation state management
- Integration with Tasks 1-2

### **Subtask 5.4: Log Collection Integration (7 hours)**
- Render log parsing
- Performance metric extraction
- Aggregate statistics

### **Subtask 5.5: Report Generation (7 hours)**
- Markdown and JSON reports
- LoCoMo breakdowns
- Summary statistics

---

**Status**: Tasks 1-4 Complete, Task 5 Redesigned for Minimal Implementation  
**Effort**: 1 week remaining (32 hours)  
**Risk**: Minimal (direct MCP testing, no SDK dependencies)  
**Value**: Complete evaluation capability with improved reliability

**Key Improvement**: Switching from SDK testing to direct MCP testing eliminates SDK instability issues while maintaining full evaluation capabilities through the stable jean_memory tool interface.