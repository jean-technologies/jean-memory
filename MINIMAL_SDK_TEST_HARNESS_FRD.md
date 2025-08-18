# **Jean Memory Minimal Evaluation Harness - Complete Implementation FRD/EDD**

**Document Version:** 1.0.0  
**Date:** August 16, 2025  
**Priority:** P0  
**Total Implementation Time:** 1 week (5 subtasks)

---

## **Executive Summary**

This document defines the implementation plan for a minimal SDK test harness that evaluates the jean_memory MCP tool without modifying the Python SDK or backend systems. The harness will use real user authentication and leverage existing evaluation infrastructure from Tasks 1-4.

---

## **Main Task: Minimal SDK Test Harness**

### **What**
Build a minimal test harness that directly calls the jean_memory MCP tool using real user authentication to evaluate context engineering performance without modifying the Python SDK or backend systems.

### **Why**
Current manual evaluation via Claude Desktop is time-consuming and not scalable. We need automated evaluation to measure jean_memory performance against LoCoMo benchmarks while the Python SDK is still evolving, using the stable MCP interface.

### **Overall Scope**

**In Scope:**
- Direct MCP endpoint calls mimicking Claude Desktop
- OAuth token reuse from existing authentication
- Integration with Tasks 1-4 evaluation infrastructure
- Basic performance metrics extraction
- Report generation using existing LLM judge

**Out of Scope:**
- Python SDK modifications
- Full OAuth flow implementation
- Mock user creation
- Real-time log streaming
- GUI or web interface

### **Overall Acceptance Criteria**
- [ ] Complete authentication without implementing OAuth flow
- [ ] Execute test conversations via MCP endpoint
- [ ] Evaluate responses with LLM judge
- [ ] Extract performance metrics from logs
- [ ] Generate comprehensive evaluation reports

---

## **Subtask 1: Authentication Token Management**

**Name:** Secure Token Capture and Storage  
**Description:** Implement a secure system to capture and reuse OAuth tokens from Claude Desktop sessions  
**Estimated Time:** 5 hours  
**Dependencies:** None

### **Mini-FRD**

#### **What**
Create a secure token management system that captures and reuses OAuth tokens from Claude Desktop authentication sessions for automated testing.

#### **Why**
We need real user authentication to access production Qdrant, Neo4j, and Supabase services. Creating mock users would require extensive backend changes and wouldn't test real performance.

#### **Scope**

**In Scope:**
- Token extraction helper script
- Secure local token storage (.gitignored)
- Token validation and refresh detection
- Manual one-time setup documentation

**Out of Scope:**
- Full OAuth 2.1 PKCE flow implementation
- Automatic token refresh
- Cloud-based token storage
- Multi-user token management

#### **Acceptance Criteria**
- [ ] Token extraction script guides user through manual process
- [ ] Token stored securely in `.jean_memory_token` file
- [ ] Token file automatically added to .gitignore
- [ ] Token validation endpoint confirms authentication works
- [ ] Clear error messages when token expires

### **Mini-EDD**

#### **Chosen Approach**
Manual token extraction from browser session after Claude Desktop authentication, stored locally in encrypted file. This avoids OAuth complexity while maintaining security.

#### **Key Components**
- `app/evaluation/auth_helper.py` - Token extraction and management
- `.jean_memory_token` - Local token storage (gitignored)
- `app/evaluation/config.py` - Authentication configuration

#### **Implementation Steps**
1. Create interactive token extraction script (2 hours)
2. Implement secure local storage with encryption (1 hour)
3. Add token validation endpoint check (1 hour)
4. Write setup documentation with screenshots (1 hour)

#### **Risks & Mitigation**
- Token expiry during tests → Detection and clear user messaging
- Token leakage → Encryption at rest, .gitignore enforcement
- Manual process friction → Detailed guide with troubleshooting

#### **Testing Plan**
- Test token extraction on Chrome, Firefox, Safari
- Verify token works with MCP endpoint
- Test expired token handling
- Validate .gitignore prevents commits

---

## **Subtask 2: MCP Client Implementation**

**Name:** Direct MCP Endpoint Client  
**Description:** Build HTTP client that calls jean_memory tool via MCP v2 endpoint  
**Estimated Time:** 6 hours  
**Dependencies:** Subtask 1 (Authentication)

### **Mini-FRD**

#### **What**
Build a minimal HTTP client that directly calls the jean_memory MCP tool endpoint, mimicking Claude Desktop's exact request format without using the Python SDK.

#### **Why**
The Python SDK is still evolving and adds complexity. Direct MCP calls to the stable jean_memory tool provide consistent, reliable evaluation without SDK dependencies.

#### **Scope**

**In Scope:**
- Direct HTTP calls to MCP v2 endpoint
- Exact Claude Desktop request format replication
- Response parsing and error handling
- Retry logic for network failures
- Request/response logging for debugging

**Out of Scope:**
- Python SDK wrapper
- WebSocket connections
- Streaming responses
- Multi-tool support (only jean_memory)

#### **Acceptance Criteria**
- [ ] Successfully calls `/mcp/v2/claude/{user_id}` endpoint
- [ ] Handles jean_memory tool responses correctly
- [ ] Implements 3-retry logic with exponential backoff
- [ ] Logs all requests/responses for debugging
- [ ] Returns structured response matching Claude Desktop format

### **Mini-EDD**

#### **Chosen Approach**
Pure httpx async client making POST requests to MCP endpoint with exact payload structure observed in logs. No SDK dependencies ensures stability.

#### **Key Components**
- `app/evaluation/minimal_mcp_client.py` - Core MCP client
- `app/evaluation/mcp_types.py` - Request/response type definitions
- Existing httpx for async HTTP calls

#### **Implementation Steps**
1. Define MCP request/response types (1 hour)
2. Implement core HTTP client with retry logic (2 hours)
3. Add request/response logging (1 hour)
4. Create error handling for common failures (1 hour)
5. Test against production endpoint (1 hour)

#### **Risks & Mitigation**
- MCP API changes → Version lock to v2, monitor for deprecation
- Network timeouts → Configurable timeout with retry logic
- Rate limiting → Exponential backoff, request throttling

#### **Testing Plan**
- Test with valid jean_memory requests
- Test error handling (invalid token, network errors)
- Verify retry logic with mock failures
- Compare responses with Claude Desktop logs

---

## **Subtask 3: Test Orchestration System**

**Name:** Conversation Test Runner  
**Description:** Orchestrate test execution using Task 4 datasets with metrics collection  
**Estimated Time:** 7 hours  
**Dependencies:** Subtasks 1-2, Tasks 1-4 infrastructure

### **Mini-FRD**

#### **What**
Create a test runner that loads conversation datasets from Task 4, executes them via the MCP client, and collects evaluation metrics using Tasks 1-2 infrastructure.

#### **Why**
We need to systematically evaluate jean_memory performance using the scientific test cases already generated, leveraging existing evaluation decorators and LLM judges.

#### **Scope**

**In Scope:**
- Load Task 4 conversation datasets
- Sequential test execution with progress tracking
- Integration with Task 1 decorators
- Integration with Task 2 LLM judge
- Basic performance metrics collection
- Memory accumulation across conversation turns

**Out of Scope:**
- Parallel test execution
- Custom test case creation
- Real-time result streaming
- Test case modification

#### **Acceptance Criteria**
- [ ] Loads JSON datasets from `test_datasets/` directory
- [ ] Executes conversation turns sequentially
- [ ] Maintains conversation context across turns
- [ ] Task 1 decorators capture metrics automatically
- [ ] Task 2 LLM judge evaluates each response
- [ ] Progress indicator shows test completion

### **Mini-EDD**

#### **Chosen Approach**
Async test orchestrator that processes conversation datasets turn-by-turn, maintaining conversation state and collecting metrics via existing decorators.

#### **Key Components**
- `app/evaluation/minimal_test_runner.py` - Main orchestration logic
- `app/evaluation/conversation_state.py` - Conversation context management
- Integration with existing Task 1-2 components

#### **Implementation Steps**
1. Create dataset loader for Task 4 formats (1 hour)
2. Implement conversation state management (2 hours)
3. Add sequential test execution with @evaluate decorator (2 hours)
4. Integrate LLM judge for response scoring (1 hour)
5. Add progress tracking and logging (1 hour)

#### **Risks & Mitigation**
- Memory accumulation errors → Clear state management
- Test failures blocking suite → Continue on error with logging
- Large dataset performance → Chunked processing option

#### **Testing Plan**
- Test with 5-turn conversation dataset
- Verify memory accumulation works correctly
- Test error recovery (failed turns don't stop suite)
- Validate metrics captured by decorators

---

## **Subtask 4: Log Collection Integration**

**Name:** Performance Metrics Extraction  
**Description:** Parse Render logs to extract detailed performance metrics  
**Estimated Time:** 7 hours  
**Dependencies:** Subtask 3 (for correlation with tests)

### **Mini-FRD**

#### **What**
Parse Render service logs to extract detailed performance metrics about memory searches, AI planning, context execution, and cache hits that aren't available in MCP responses.

#### **Why**
MCP responses only contain the final output. Log analysis reveals critical performance metrics like search latency, context strategy selection, and orchestration timing needed for comprehensive evaluation.

#### **Scope**

**In Scope:**
- Parse existing log format from Render
- Extract performance metrics ([PERF] tags)
- Extract context engineering decisions
- Extract memory search patterns
- Calculate aggregate statistics

**Out of Scope:**
- Real-time log streaming
- Log storage or persistence
- Custom logging implementation
- Render API integration
- SSH log access

#### **Acceptance Criteria**
- [ ] Parses performance metrics from [PERF] log lines
- [ ] Extracts context strategy (deep_understanding, etc.)
- [ ] Counts memory searches and cache hits
- [ ] Calculates total orchestration time
- [ ] Handles missing or malformed logs gracefully

### **Mini-EDD**

#### **Chosen Approach**
Regex-based log parser that processes saved log files from manual extraction. This avoids Render API complexity while providing needed metrics.

#### **Key Components**
- `app/evaluation/log_parser.py` - Core parsing logic
- `app/evaluation/metrics_extractor.py` - Metric extraction patterns
- Regular expressions for log pattern matching

#### **Implementation Steps**
1. Define regex patterns for each metric type (2 hours)
2. Implement log file reader and parser (2 hours)
3. Create metric aggregation logic (1 hour)
4. Add error handling for incomplete logs (1 hour)
5. Test with sample production logs (1 hour)

#### **Risks & Mitigation**
- Log format changes → Versioned regex patterns
- Incomplete logs → Default values and partial parsing
- Large log files → Streaming parser implementation

#### **Testing Plan**
- Test with various log samples from production
- Verify metric extraction accuracy
- Test with incomplete/corrupted logs
- Validate aggregation calculations

---

## **Subtask 5: Report Generation**

**Name:** Evaluation Report Generator  
**Description:** Generate comprehensive markdown and JSON reports from test results  
**Estimated Time:** 7 hours  
**Dependencies:** Subtasks 1-4

### **Mini-FRD**

#### **What**
Generate comprehensive evaluation reports combining MCP responses, LLM judge scores, and performance metrics into readable markdown and JSON formats.

#### **Why**
We need actionable insights from test runs to identify performance regressions, compare against LoCoMo benchmarks, and track improvements over time.

#### **Scope**

**In Scope:**
- Markdown report with summary statistics
- JSON export for programmatic analysis
- LoCoMo reasoning type breakdowns
- Performance trend analysis
- LLM judge score distributions
- Test failure analysis

**Out of Scope:**
- HTML reports or dashboards
- Real-time report updates
- Comparison across multiple runs
- Automated regression detection

#### **Acceptance Criteria**
- [ ] Generates markdown report with all key metrics
- [ ] Exports JSON with structured test results
- [ ] Shows per-reasoning-type performance
- [ ] Includes LLM judge scores and explanations
- [ ] Highlights failed tests with error details
- [ ] Calculates summary statistics (mean, p50, p95)

### **Mini-EDD**

#### **Chosen Approach**
Template-based report generator using Jinja2 for markdown and native JSON serialization, leveraging Task 1's storage patterns.

#### **Key Components**
- `app/evaluation/report_generator.py` - Main report generation
- `app/evaluation/templates/report.md.j2` - Markdown template
- Integration with Task 1 MetricsStorage

#### **Implementation Steps**
1. Design report template structure (1 hour)
2. Implement markdown generation with Jinja2 (2 hours)
3. Add JSON export functionality (1 hour)
4. Create summary statistics calculator (1 hour)
5. Add visualization helpers (tables, charts) (1 hour)
6. Test with real evaluation data (1 hour)

#### **Risks & Mitigation**
- Large reports → Pagination or summary options
- Missing data → Graceful handling with placeholders
- Format compatibility → Standard markdown, valid JSON

#### **Testing Plan**
- Generate reports from test runs
- Verify markdown renders correctly
- Validate JSON structure
- Test with incomplete data
- Check statistics calculations

---

## **Implementation Timeline**

### **Week 1 Schedule**

| Day | Subtask | Hours | Deliverables |
|-----|---------|-------|--------------|
| **Day 1** | Subtask 1: Authentication | 5 | Token management system |
| **Day 2** | Subtask 2: MCP Client | 6 | Working MCP client |
| **Day 3** | Subtask 3: Test Orchestration | 7 | Test runner with Task 1-2 integration |
| **Day 4** | Subtask 4: Log Collection | 7 | Log parser with metrics extraction |
| **Day 5** | Subtask 5: Report Generation | 7 | Complete evaluation reports |

**Total Implementation Time:** 32 hours (~1 week)

---

## **Success Metrics**

### **Technical Success**
- [ ] All 5 subtasks completed and integrated
- [ ] Successfully evaluates 10+ conversation test cases
- [ ] Generates comprehensive reports with metrics
- [ ] Zero modifications to Python SDK or backend

### **Performance Targets**
- [ ] Test execution < 5 seconds per conversation turn
- [ ] Report generation < 30 seconds for 100 test cases
- [ ] LLM judge evaluation accuracy > 85%
- [ ] Log parsing success rate > 95%

### **Quality Metrics**
- [ ] No authentication credentials in code
- [ ] All components have error handling
- [ ] Documentation covers setup and usage
- [ ] Code follows existing Task 1-4 patterns

---

## **Risk Analysis**

### **High Risk Items**
1. **Token Expiry** - Mitigation: Clear error messages, refresh documentation
2. **MCP API Changes** - Mitigation: Version locking, monitoring
3. **Log Format Changes** - Mitigation: Flexible regex patterns

### **Medium Risk Items**
1. **Performance at Scale** - Mitigation: Chunked processing
2. **Network Reliability** - Mitigation: Retry logic, timeout handling
3. **LLM Judge Availability** - Mitigation: Fallback to cached scores

### **Low Risk Items**
1. **Storage Space** - Mitigation: Log rotation, cleanup scripts
2. **Report Size** - Mitigation: Summary options, pagination

---

## **Definition of Done**

The Minimal SDK Test Harness is complete when:

1. **Authentication Works** - Token extraction documented and tested
2. **MCP Client Functional** - Successfully calls jean_memory tool
3. **Tests Execute** - Processes Task 4 datasets end-to-end
4. **Metrics Collected** - Logs parsed, metrics extracted
5. **Reports Generated** - Markdown and JSON reports created
6. **Documentation Complete** - Setup guide and usage instructions
7. **Integration Verified** - Works with Tasks 1-4 infrastructure
8. **No SDK Changes** - Python SDK remains unmodified

---

## **Appendix: Quick Start Code Example**

```python
# Complete minimal test example
import asyncio
from app.evaluation.minimal_harness import MinimalJeanMemoryHarness

async def run_evaluation():
    # Initialize with real user ID
    harness = MinimalJeanMemoryHarness(
        user_id="fa97efb5-410d-4806-b137-8cf13b6cb464"
    )
    
    # Authenticate once
    await harness.authenticate()
    
    # Load test dataset
    dataset = await harness.load_dataset("test_datasets/conversation_5turns.json")
    
    # Run evaluation
    results = await harness.evaluate_dataset(dataset)
    
    # Generate report
    report = await harness.generate_report(results)
    print(f"Report saved to: {report.path}")
    print(f"Overall Score: {report.summary.mean_score:.1f}/10")

# Execute
asyncio.run(run_evaluation())
```

---

**Document Status:** READY FOR IMPLEMENTATION  
**Next Steps:** Begin with Subtask 1 - Authentication Token Management  
**Questions/Clarifications:** None - Ready to proceed