# Synthetic Data Generator - Mini-FRD

## **Part 1 — Mini-FRD (What & Why)**

### 1. **What**
Build an LLM-powered synthetic data generation system that creates diverse conversation scenarios, memory sequences, and test cases across all LoCoMo reasoning types for comprehensive evaluation coverage.

### 2. **Why**
Manual test case creation is time-consuming and lacks coverage of edge cases. Synthetic generation ensures comprehensive testing across all reasoning types, difficulty levels, and scenarios while enabling rapid expansion of test datasets. This is crucial for thorough evaluation without relying solely on limited real-world data.

### 3. **Scope**

**In Scope:**
- LLM-powered conversation scenario generation
- Memory injection sequence creation for multi-hop testing
- Adversarial scenario generation (conflicting information)
- Temporal event sequence generation
- Persona-based conversation generation
- LoCoMo reasoning type coverage (single-hop, multi-hop, temporal, commonsense, adversarial)
- Difficulty level variation (simple to complex)
- Quality validation of generated test cases

**Out of Scope:**
- Real user data collection or processing
- Manual test case authoring tools (separate task)
- Integration with external data sources
- Test case execution (handled by evaluation infrastructure)

### 4. **Acceptance Criteria**

#### Core Generation Capabilities
- [ ] Generate diverse conversation scenarios with consistent personas
- [ ] Create memory injection sequences that require 3-5 hop reasoning
- [ ] Generate adversarial scenarios with conflicting information
- [ ] Create temporal event sequences with proper causal relationships
- [ ] Generate test cases across all 5 LoCoMo reasoning types

#### Quality & Coverage
- [ ] Generated scenarios cover all three Jean Memory decision paths
- [ ] Balanced distribution across difficulty levels (easy, medium, hard)
- [ ] Quality validation ensures coherent and logical test cases
- [ ] Generated conversations maintain character consistency
- [ ] Scenarios include realistic edge cases and corner conditions

#### Output Format & Integration
- [ ] Standardized JSON output format compatible with test dataset management
- [ ] Metadata inclusion (difficulty, reasoning type, expected outcomes)
- [ ] Batch generation capability (10-100 test cases per run)
- [ ] Integration with dataset management suite for storage

#### Validation & Reliability
- [ ] Generated test cases pass basic coherence validation
- [ ] Manual review process for quality assurance on samples
- [ ] Reproducible generation with seed parameters
- [ ] Error handling for generation failures or invalid outputs