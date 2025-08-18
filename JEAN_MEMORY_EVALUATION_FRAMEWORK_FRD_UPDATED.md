# **Jean Memory Performance Evaluation & Testing Framework - Updated FRD**

## **1. What**

Build a streamlined evaluation system for the Jean Memory context engineering algorithm that measures memory retrieval accuracy, reasoning capabilities, and conversation consistency using LoCoMo benchmarks while maintaining zero impact on production performance through non-invasive instrumentation.

## **2. Why**

Jean Memory's sophisticated context engineering system currently operates without systematic evaluation, making it impossible to measure improvements, detect regressions, or validate performance claims against research benchmarks. With LoCoMo research showing RAG systems perform best for long-term memory (exactly what Jean Memory is), we need evaluation to demonstrate competitive advantage and guide optimization efforts. This unblocks our ability to confidently iterate on the algorithm and prove Jean Memory's superiority over existing solutions.

## **3. Scope**

### **In Scope:**

- LoCoMo framework integration (5 reasoning types: single-hop, multi-hop, temporal, commonsense, adversarial)
- Extended conversation testing (5-35 message sequences)
- Evaluation of all three decision paths (New Conversation, Generic Knowledge, Contextual Conversation)
- Memory retrieval accuracy measurement at key pipeline points
- Long-range conversation consistency evaluation
- Synthetic test data generation using LLMs
- Python SDK-based evaluation environment for realistic testing
- Minimal-invasive decorator pattern for production monitoring
- Markdown-based reporting with performance analysis
- CLI-based test orchestration for easy execution

### **Out of Scope:**

- React SDK testing (focus on Python SDK only)
- Web-based dashboards or UI components
- Database storage (using JSON file storage)
- Gold standard human annotations
- Modifying core jean_memory tool logic (only add evaluation layers)
- Real-time evaluation during production (evaluation mode toggle only)
- User-facing evaluation features
- Integration with external evaluation platforms
- Evaluation of non-memory features (OAuth, UI, etc.)
- Performance optimization implementation (only measurement)
- Complex visualization or analytics dashboards

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

### **Conversation Dataset Management** (Task 4 - New)

- [ ] JSON file-based storage in `./test_datasets/` folder
- [ ] Generate conversations of configurable length (5-35 messages)
- [ ] Control LoCoMo type distribution (uniform or mixed)
- [ ] CLI interface for dataset generation
- [ ] Metadata tracking for each dataset

### **Python SDK Testing Harness** (Task 5 - New)

- [ ] Python SDK integration for conversation simulation
- [ ] Load and execute test datasets sequentially
- [ ] Non-invasive metric capture via Task 1 decorators
- [ ] No modifications to production code required
- [ ] Async execution with realistic timing

### **Performance Reporting** (Task 6 - New)

- [ ] Markdown report generation with LoCoMo breakdown
- [ ] LLM Judge scores for each conversation turn
- [ ] Response time analysis (average, P50, P95)
- [ ] Export to `./evaluation_reports/` folder
- [ ] Basic trend analysis across test runs

### **CLI Test Orchestration** (Task 7 - New)

- [ ] Single command evaluation execution
- [ ] Configurable via command-line arguments
- [ ] Progress indicators during execution
- [ ] Automatic report generation
- [ ] CI/CD compatible with proper exit codes

### **LoCoMo Performance Targets**

- [ ] Single-hop reasoning: >90% accuracy
- [ ] Multi-hop reasoning: >80% accuracy
- [ ] Temporal reasoning: >75% accuracy
- [ ] Adversarial handling: >70% accuracy
- [ ] Commonsense integration: >75% accuracy
- [ ] Long-range consistency: >85% across conversations

### **System Performance Requirements**

- [ ] Evaluation mode disabled by default in production
- [ ] Zero measurable latency impact when disabled
- [ ] Response latency P50 <1000ms, P95 <3000ms when enabled
- [ ] Support for 100+ test cases across all reasoning types
- [ ] Test execution completes within reasonable timeframes

## **5. Implementation Status**

### **Completed Tasks (1-3)**

1. **Core Evaluation Infrastructure** ✅
   - Non-invasive decorator pattern implemented
   - Zero production impact verified
   - Async metric collection operational

2. **LLM Judge & Scoring System** ✅
   - Multi-provider consensus judging implemented
   - All LoCoMo reasoning types supported
   - Quality scoring with detailed explanations

3. **Synthetic Test Data Generator** ✅
   - Complete LoCoMo coverage
   - Quality validation integrated
   - Dataset management foundation ready

### **Remaining Tasks (4-7)**

4. **Conversation Dataset Generator**
   - Simple JSON-based dataset creation
   - Configurable conversation generation

5. **Python SDK Test Harness**
   - Minimal SDK-based testing
   - Leverages existing infrastructure

6. **Basic Performance Report Generator**
   - Markdown reports with key metrics
   - LoCoMo performance breakdown

7. **CLI Test Runner**
   - Single command orchestration
   - CI/CD ready implementation

## **6. Technical Architecture**

```
Task 1 (Infrastructure) → Task 2 (LLM Judge) → Task 3 (Generator)
            ↓                      ↓                    ↓
    Metric Collection      Quality Scoring      Test Creation
            ↓                      ↓                    ↓
Task 5 (SDK Harness) → Task 6 (Reports) ← Task 4 (Datasets)
            ↓                      ↓                    ↓
                    Task 7 (CLI Orchestration)
```

## **7. Success Metrics**

- **Coverage**: All 5 LoCoMo reasoning types evaluated
- **Scale**: 100+ test cases across conversation lengths
- **Performance**: Meeting latency targets (P50 <1s, P95 <3s)
- **Quality**: LLM Judge scores >7/10 average
- **Automation**: Single CLI command for complete evaluation
- **Safety**: Zero production impact when disabled

## **8. Deliverables**

### **Code Components**
- Evaluation infrastructure with decorators (Complete)
- LLM Judge service with consensus (Complete)
- Synthetic data generator (Complete)
- Conversation dataset generator
- Python SDK test harness
- Markdown report generator
- CLI orchestration script

### **Documentation**
- Implementation guides for each component
- API documentation for evaluation interfaces
- Performance benchmark reports
- LoCoMo comparison analysis

### **Test Artifacts**
- Generated conversation datasets
- Evaluation reports with metrics
- Performance trend analysis
- CI/CD integration scripts

## **9. Timeline**

- **Weeks 1-2**: ✅ Tasks 1-3 (Complete)
- **Week 3**: Task 4 (Conversation Dataset Generator)
- **Week 4**: Task 5 (Python SDK Test Harness)
- **Week 5**: Task 6 (Report Generator)
- **Week 6**: Task 7 (CLI Orchestration) & Integration Testing

## **10. Risk Mitigation**

- **Performance Impact**: Evaluation disabled by default, async processing
- **Complexity Creep**: Focus on minimal viable implementation
- **Integration Issues**: Non-invasive design, no production code changes
- **Timeout Concerns**: Configurable timeouts, batch processing
- **Quality Validation**: Multi-dimensional scoring with consensus