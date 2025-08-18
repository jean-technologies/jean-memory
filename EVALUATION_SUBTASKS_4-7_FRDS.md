# Jean Memory Evaluation Framework - Subtasks 4-7 Mini-FRD/EDDs

## **Subtask 4: Conversation Dataset Generator**

**Description**: Build a dataset generator that creates conversation-based test datasets with configurable LoCoMo reasoning type distribution and conversation length control using the existing Task 3 synthetic data generator.

---

### **Mini-FRD/EDD**

### **What**
Create a conversation dataset generator that sequences synthetic test cases from Task 3 into realistic multi-turn conversations, with configurable length and reasoning type distribution.

### **Why**
We need structured conversation datasets that simulate real user interactions to evaluate Jean Memory's performance across extended sessions. Single test cases don't capture the complexity of maintaining context across multiple conversation turns.

### **Scope**

**In Scope:**
- JSON file-based storage in `./test_datasets/` folder
- Generate conversations of configurable length (5-35 messages)
- Control for uniform vs mixed LoCoMo type distribution
- Conversation continuity with related topics
- Leverage existing Task 3 synthetic generator
- Metadata tracking (creation date, reasoning types, length)
- Simple CLI interface for dataset generation

**Out of Scope:**
- Database storage
- Web UI for dataset management
- Version control beyond file naming
- Gold standard annotations
- Real user conversation data

### **Acceptance Criteria**
- [ ] Generate conversation datasets with specified length (5-35 messages)
- [ ] Control LoCoMo type distribution: uniform single type or mixed variety
- [ ] Maintain topic continuity across conversation turns
- [ ] Store datasets as JSON files with timestamp-based naming
- [ ] CLI command: `python generate_dataset.py --length 20 --type mixed`
- [ ] Each dataset includes comprehensive metadata
- [ ] Support for persona consistency across conversation

### **Chosen Approach**
Wrap Task 3's synthetic generator to create sequences of related test cases that form coherent conversations. Each turn builds on previous context while testing specific reasoning types.

### **Key Components**
- `app/evaluation/conversation_dataset_generator.py` - Main generator logic
- `app/evaluation/dataset_cli.py` - CLI interface
- JSON storage in `./test_datasets/`
- Integration with Task 3 SyntheticDataGeneratorService

### **Implementation Steps**
1. Create ConversationDatasetGenerator class wrapping Task 3
2. Implement conversation continuity logic (topic chaining)
3. Add CLI argument parser with validation
4. Implement JSON serialization with metadata
5. Add progress indicators for long generation
6. Create dataset validation utilities

### **Risks & Mitigation**
- Generation timeout for long conversations → Progress indicators, batch processing
- Topic drift across turns → Context window for continuity
- Memory buildup → Clear generator state between datasets

### **Testing Plan**
- Generate small (5), medium (20), and large (35) conversations
- Verify reasoning type distribution accuracy
- Validate JSON structure and metadata completeness
- Test conversation continuity and coherence

---

## **Subtask 5: Python SDK Test Harness**

**Description**: Create a Python SDK test harness that wraps the JeanMemoryClient to run conversation datasets, analyze SDK behavior, handle OAuth authentication, and collect evaluation metrics through existing infrastructure.

---

### **Mini-FRD/EDD**

### **What**
Build a test harness that wraps the Python SDK to execute conversation datasets while analyzing SDK internals, handling OAuth authentication, and leveraging existing metric collection infrastructure.

### **Why**
We need to validate Jean Memory's performance using real SDK interactions exactly as users experience them, while also documenting SDK behavior for maintenance and debugging purposes.

### **Scope**

**In Scope:**
- Python SDK wrapper (no SDK modifications)
- OAuth 2.1 PKCE authentication integration
- SDK behavior analysis and documentation
- Load and execute test datasets from Task 4
- Conversation simulation with proper context flow
- Error handling and edge case testing
- Verification of jean_memory tool invocation
- Integration with Task 1 metrics and Task 2 LLM Judge

**Out of Scope:**
- React SDK testing
- Automatic test user creation
- Authentication bypass mechanisms
- Modifications to Python SDK or jean_memory tool
- Real-time UI for test execution

### **Acceptance Criteria**
- [ ] Harness wraps JeanMemoryClient without modifications
- [ ] OAuth authentication flow with browser-based login
- [ ] Support for pre-authenticated tokens (CI/CD)
- [ ] Document SDK request/response flow during implementation
- [ ] Verify jean_memory tool is called via MCP
- [ ] Test error scenarios (network failures, auth errors)
- [ ] Task 1 decorators capture metrics automatically
- [ ] Task 2 LLM Judge evaluates each response
- [ ] Generate SDK behavior documentation

### **Chosen Approach**
Create a wrapper class around JeanMemoryClient that handles authentication, executes conversations, and documents SDK behavior while the existing decorators capture metrics.

### **Key Components**
- `app/evaluation/sdk_test_harness.py` - Main harness class
- `app/evaluation/sdk_analyzer.py` - SDK behavior documentation
- OAuth authentication via JeanMemoryAuth
- Integration with existing JeanMemoryClient

### **Implementation Steps**
1. Create SDKTestHarness class wrapping JeanMemoryClient
2. Implement OAuth authentication flow with clear user guidance
3. Add SDK request/response logging and analysis
4. Implement conversation execution logic
5. Verify jean_memory tool invocation via MCP
6. Test error handling scenarios
7. Document SDK behavior patterns
8. Integrate with Task 2 LLM Judge for scoring

### **Risks & Mitigation**
- OAuth complexity → Clear documentation, step-by-step guidance
- SDK changes → Wrapper isolation, behavior documentation
- Network latency → Configurable timeouts, retry logic
- Authentication expiry → Token refresh handling

### **Testing Plan**
- Authenticate with real user account
- Execute conversations of varying lengths
- Test network failure scenarios
- Verify metric capture without code changes
- Document all SDK behaviors observed

---

## **Subtask 6: Performance Report Generator**

**Description**: Build a comprehensive markdown report generator that analyzes conversation test results, aggregates LLM Judge scores, calculates LoCoMo performance metrics, and provides detailed timing analysis.

---

### **Mini-FRD/EDD**

### **What**
Create a report generator that produces detailed markdown reports analyzing Jean Memory's performance across all LoCoMo reasoning types, with timing metrics, quality scores, and pass/fail determinations.

### **Why**
We need clear, actionable reports to understand Jean Memory's strengths and weaknesses, track performance over time, and make data-driven decisions about algorithm improvements.

### **Scope**

**In Scope:**
- Comprehensive markdown report generation
- LoCoMo reasoning type performance breakdown
- LLM Judge score aggregation and analysis
- Response time analysis (average, P50, P95, P99)
- Pass/fail determination against thresholds
- Conversation-level and turn-level analysis
- Export to `./evaluation_reports/` folder
- Summary statistics and trends
- Error and timeout tracking

**Out of Scope:**
- Web dashboards or HTML reports
- Real-time streaming analytics
- Complex data visualizations
- Automated regression detection
- Historical trend analysis across reports

### **Acceptance Criteria**
- [ ] Generate comprehensive markdown report post-execution
- [ ] Include overall performance summary with pass/fail status
- [ ] Break down performance by each LoCoMo reasoning type
- [ ] Calculate and display timing percentiles (P50, P95, P99)
- [ ] Show LLM Judge scores with detailed explanations
- [ ] Include conversation-level and turn-level details
- [ ] Export with timestamp and dataset ID in filename
- [ ] Highlight failures and areas needing improvement
- [ ] Generate executive summary section

### **Chosen Approach**
Aggregate metrics from Task 1 decorators and Task 2 LLM Judge scores, calculate statistics, and generate structured markdown report with clear sections and actionable insights.

### **Key Components**
- `app/evaluation/report_generator.py` - Main report generation logic
- `app/evaluation/report_templates.py` - Markdown templates
- Statistical analysis utilities (numpy for percentiles)
- Integration with Task 1 metrics and Task 2 scores

### **Implementation Steps**
1. Create ReportGenerator class with configurable thresholds
2. Design markdown template with clear sections
3. Implement metric aggregation from test results
4. Calculate statistical measures (percentiles, averages)
5. Implement pass/fail logic against thresholds
6. Create detailed and summary view options
7. Add error and timeout reporting
8. Implement file export with proper naming

### **Risks & Mitigation**
- Large result sets → Streaming processing, memory management
- Missing data points → Graceful handling with warnings
- Markdown formatting issues → Template validation
- Performance calculation errors → Unit tests for statistics

### **Testing Plan**
- Generate reports for small, medium, large conversations
- Verify statistical calculations accuracy
- Test with partial data (missing scores, timeouts)
- Validate markdown formatting and readability
- Test threshold-based pass/fail logic

---

## **Subtask 7: CLI Test Runner**

**Description**: Create a Python CLI that orchestrates the complete evaluation pipeline with OAuth authentication, dataset generation, test execution, and report generation.

---

### **Mini-FRD/EDD**

### **What**
Build a Python CLI tool that orchestrates the entire evaluation workflow, handling OAuth authentication, dataset generation, SDK test execution, and report generation with a single command.

### **Why**
We need a unified entry point that makes it simple to run evaluations manually or in CI/CD pipelines, with clear progress indication and proper error handling throughout the multi-step process.

### **Scope**

**In Scope:**
- Single Python CLI command for complete evaluation
- OAuth authentication flow with user guidance
- Support for pre-authenticated tokens (CI/CD)
- Dataset generation orchestration (Task 4)
- SDK test harness execution (Task 5)
- Report generation (Task 6)
- Configuration via command-line arguments
- Progress indicators and logging
- Error handling with graceful recovery
- Exit codes for CI/CD integration

**Out of Scope:**
- GUI interface or web UI
- Remote/distributed execution
- Parallel test execution
- Cloud deployment
- Automatic authentication bypass

### **Acceptance Criteria**
- [ ] Single command: `python run_evaluation.py --api-key KEY --length 20`
- [ ] OAuth authentication with clear instructions
- [ ] Support --user-token for pre-authenticated runs
- [ ] Configurable parameters: length, type, reasoning
- [ ] Progress bars for long-running operations
- [ ] Comprehensive logging to file and console
- [ ] Generate final markdown report automatically
- [ ] Exit code 0 for pass, 1 for fail (CI/CD)
- [ ] --dry-run option for validation without execution
- [ ] Handle interrupts gracefully (Ctrl+C)

### **Chosen Approach**
Python CLI using argparse for argument handling, orchestrating all evaluation components with proper error handling and user feedback throughout the process.

### **Key Components**
- `run_evaluation.py` - Main CLI entry point
- `app/evaluation/cli_orchestrator.py` - Orchestration logic
- Integration with Tasks 4-6 components
- Logging configuration
- Progress indication (tqdm or rich)

### **Implementation Steps**
1. Create CLI with argparse for argument parsing
2. Implement authentication flow with token caching
3. Add dataset generation orchestration
4. Integrate SDK test harness execution
5. Add report generation step
6. Implement progress indicators and logging
7. Add error handling and recovery logic
8. Implement dry-run mode for testing
9. Add interrupt handling (graceful shutdown)
10. Create CI/CD documentation

### **Risks & Mitigation**
- OAuth timeout → Clear instructions, token caching
- Long execution times → Progress indicators, resumable state
- CI/CD complexity → Pre-authenticated token support
- Partial failures → Save intermediate results, detailed logs

### **Testing Plan**
- Test complete pipeline with various configurations
- Verify OAuth flow with real authentication
- Test pre-authenticated token mode
- Validate error handling (invalid args, auth failures)
- Test interrupt handling (Ctrl+C)
- Verify CI/CD compatibility with exit codes
- Test dry-run mode functionality

---

## **Summary of Complete Task List**

1. **Task 1**: ✅ Core Evaluation Infrastructure (Complete)
   - Non-invasive decorator pattern with zero production impact
   - Async metric collection and storage

2. **Task 2**: ✅ LLM Judge & Scoring System (Complete)
   - Multi-provider consensus judging
   - LoCoMo reasoning type evaluation

3. **Task 3**: ✅ Synthetic Test Data Generator (Complete)
   - LLM-powered test case generation
   - Quality validation and dataset management

4. **Task 4**: Conversation Dataset Generator (New - Simplified)
   - JSON-based conversation datasets
   - Configurable LoCoMo type distribution

5. **Task 5**: Python SDK Test Harness (New - Python only)
   - SDK-based conversation simulation
   - Automatic metric capture via Task 1

6. **Task 6**: Basic Performance Report Generator (New - Markdown only)
   - LoCoMo performance breakdown
   - Timing analysis and LLM Judge scores

7. **Task 7**: CLI Test Runner (New - Simple orchestration)
   - Single command evaluation pipeline
   - CI/CD ready with error handling