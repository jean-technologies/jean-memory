# SDK Evaluation Harness - Mini-FRD

## **Part 1 — Mini-FRD (What & Why)**

### 1. **What**
Build an evaluation harness using Jean Memory's React and Python SDKs that simulates real user interactions and tests extended conversation sessions (10-35 interactions) for end-to-end evaluation.

### 2. **Why**
Unit testing individual components doesn't validate end-to-end user experience. SDK-based testing provides the most realistic evaluation by using the actual user interface, ensuring that optimizations improve real-world performance rather than just isolated metrics.

### 3. **Scope**

**In Scope:**
- React SDK integration for conversation session testing
- Python SDK integration for programmatic evaluation
- Extended conversation session simulation (10-35 interactions)
- End-to-end flow testing through actual user interfaces
- Memory injection and retrieval testing via SDKs
- Real-world latency and performance measurement
- Integration with test dataset management for test case execution

**Out of Scope:**
- SDK modifications or new SDK features
- Browser automation or UI testing
- Load testing or stress testing
- Performance optimization (only measurement)

### 4. **Acceptance Criteria**

#### React SDK Integration
- [ ] Evaluation harness runs extended conversation sessions using React SDK
- [ ] Simulates real user interactions through `useJean` hook
- [ ] Captures context, latency, and response quality metrics
- [ ] Supports conversation sessions of 10-35 interactions
- [ ] Memory injection capabilities for controlled testing scenarios

#### Python SDK Integration
- [ ] Programmatic evaluation using Python SDK for automated testing
- [ ] Batch test case execution with results collection
- [ ] Integration with synthetic data generator for automated test runs
- [ ] API-level testing for backend evaluation without UI overhead

#### Extended Conversation Testing
- [ ] Long-range conversation consistency evaluation across sessions
- [ ] Narrative coherence tracking over 10+ interactions
- [ ] Context degradation measurement over extended sessions
- [ ] Session state management and isolation between test runs

#### End-to-End Validation
- [ ] Full user flow testing from query to context retrieval
- [ ] Real-world latency measurement including network overhead
- [ ] Authentication and session management testing
- [ ] Error handling and recovery validation in realistic scenarios

#### Integration & Automation
- [ ] Integration with test dataset management for test case sourcing
- [ ] Automated test execution with configurable parameters
- [ ] Results export to evaluation infrastructure for analysis
- [ ] Support for parallel test execution to reduce runtime

#### Performance Measurement
- [ ] Accurate latency measurement for end-to-end requests
- [ ] Memory usage tracking during extended sessions
- [ ] Network overhead measurement and reporting
- [ ] Comparison baseline establishment for regression detection