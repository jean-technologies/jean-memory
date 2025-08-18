# **Jean Memory Performance Evaluation Framework - Final FRD**

**Version:** 3.0  
**Date:** August 16, 2025  
**Status:** Tasks 1-4 Complete, Tasks 5-9 Ready for Implementation

---

## **1. What**

Build a minimal evaluation system that measures Jean Memory's context engineering performance against LoCoMo benchmarks using **direct MCP endpoint testing** of the stable jean_memory tool, bypassing the evolving Python SDK.

## **2. Why**

We need automated evaluation to detect regressions, validate improvements, and prove competitive advantage. Manual testing via Claude Desktop doesn't scale. Direct MCP testing provides a stable, SDK-independent evaluation path.

## **3. Scope**

### **In Scope**
- Direct MCP endpoint calls to jean_memory tool
- OAuth token reuse from Claude Desktop
- LoCoMo reasoning evaluation (5 types)
- Render log parsing for metrics
- Conversation testing (5-35 turns)
- JSON datasets and markdown reports

### **Out of Scope**
- Python/React SDK modifications
- Full OAuth implementation
- Mock users or test accounts
- Web dashboards
- Real-time production monitoring

## **4. Acceptance Criteria by Task**

### **✅ Task 1: Core Evaluation Infrastructure (Complete)**
- [x] Environment toggle with zero production impact
- [x] Decorator pattern (<10 lines changes)
- [x] Async metric capture without blocking
- [x] Memory overhead <50MB

### **✅ Task 2: LLM Judge & Scoring System (Complete)**
- [x] Multi-provider support (Gemini, GPT-5)
- [x] 0-10 scoring with explanations
- [x] All LoCoMo reasoning types
- [x] 5-10 second evaluation time

### **✅ Task 3: Synthetic Test Data Generator (Complete)**
- [x] LLM-powered test generation
- [x] Quality validation pipeline
- [x] Persona-based conversations
- [x] Difficulty levels (easy/medium/hard)

### **✅ Task 4: Conversation Dataset Generator (Complete)**
- [x] JSON storage in `./test_datasets/`
- [x] 5-35 turn conversations
- [x] LoCoMo distribution control
- [x] CLI interface for generation

### **⏳ Task 5: Secure Token Capture and Storage**
- [ ] Browser token extraction helper
- [ ] Encrypted local storage (`.jean_memory_token`)
- [ ] Token validation endpoint
- [ ] Setup documentation with screenshots

### **⏳ Task 6: Direct MCP Endpoint Client**
- [ ] HTTP client for `/mcp/v2/claude/{user_id}`
- [ ] Exact Claude Desktop request format
- [ ] 3-retry logic with backoff
- [ ] Request/response logging

### **⏳ Task 7: Conversation Test Runner**
- [ ] Load Task 4 datasets
- [ ] Sequential turn execution
- [ ] Conversation state management
- [ ] Progress tracking

### **⏳ Task 8: Performance Metrics Extraction**
- [ ] Parse [PERF] tags from logs
- [ ] Extract context strategies
- [ ] Calculate orchestration times
- [ ] Aggregate statistics

### **⏳ Task 9: Evaluation Report Generator**
- [ ] Markdown reports with LoCoMo breakdown
- [ ] JSON export for analysis
- [ ] Performance metrics (P50, P95)
- [ ] Pass/fail thresholds

## **5. Technical Architecture**

```
Test Dataset (Task 4) → MCP Client (Task 6) → jean_memory tool
                              ↓
                     Token Auth (Task 5)
                              ↓
                     Test Runner (Task 7)
                              ↓
                     Log Parser (Task 8)
                              ↓
                     LLM Judge (Task 2)
                              ↓
                     Report Gen (Task 9)
```

## **6. Implementation Plan**

| Day | Tasks | Hours | Deliverable |
|-----|-------|-------|-------------|
| 1 | Task 5 | 5 | Token management system |
| 2 | Task 6 | 6 | MCP client implementation |
| 3 | Task 7 | 7 | Test runner orchestration |
| 4 | Task 8 | 7 | Log parsing metrics |
| 5 | Task 9 | 7 | Report generation |

**Total:** 32 hours (1 week)

## **7. Usage**

```bash
# One-time setup
./run_evaluation.py --setup  # Extract token from browser

# Run evaluation
./run_evaluation.py --user-id {user_id} --length 20 --type mixed

# Quick test
./run_evaluation.py --quick-test
```

## **8. Success Metrics**

### **Performance Targets**
- Single-hop: >90% accuracy (9.0/10)
- Multi-hop: >80% accuracy (8.0/10)
- Temporal: >75% accuracy (7.5/10)
- Overall: >7.0/10 average

### **System Requirements**
- Test execution: <5s per turn
- Full evaluation: <5 minutes
- Zero SDK modifications
- Production code unchanged

## **9. Key Design Decisions**

| Decision | Rationale | Benefit |
|----------|-----------|---------|
| Direct MCP testing | SDK instability | Stable interface |
| Token reuse | Avoid OAuth complexity | Real authentication |
| Log parsing | Rich metrics needed | Full visibility |
| Minimal approach | Speed to market | 1 week vs 3+ weeks |

## **10. Risks & Mitigation**

| Risk | Impact | Mitigation |
|------|--------|------------|
| Token expiry | Medium | Clear refresh guide |
| MCP changes | Low | Version locking |
| Log format changes | Low | Flexible regex |

## **11. Output Example**

```markdown
# Evaluation Report
Date: 2025-08-16
Conversation: 20 turns

## Performance
- Average Score: 8.2/10 ✅
- P50 Latency: 450ms
- Cache Hit Rate: 85%

## LoCoMo Breakdown
| Type | Score | Pass |
|------|-------|------|
| Single-hop | 9.1/10 | ✅ |
| Multi-hop | 7.8/10 | ⚠️ |
| Temporal | 8.5/10 | ✅ |
```

## **12. Definition of Done**

- [ ] Token extraction working
- [ ] MCP calls successful
- [ ] Datasets execute end-to-end
- [ ] Logs parsed correctly
- [ ] Reports generated
- [ ] Documentation complete
- [ ] No SDK changes made

---

**Status:** Ready for Implementation  
**Next Step:** Task 5 - Token Management  
**Effort:** 32 hours  
**Risk:** Minimal