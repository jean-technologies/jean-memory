# **Mini-FRD (What & Why) - UPDATED WITH CONSENSUS JUDGING**

### **1. What**

Implement an LLM-as-a-Judge system using multiple LLM providers with consensus scoring that automatically evaluates context relevance, completeness, reasoning quality, and consistency without human intervention.

### **2. Why**

Manual evaluation doesn't scale and human annotation is expensive and time-consuming. Single-LLM judging can suffer from model-specific biases and inconsistencies. Multi-LLM consensus judging provides more reliable, automated evaluation by leveraging multiple AI perspectives, reducing individual model bias, and improving scoring consistency. This enables continuous evaluation with higher confidence in results for rapid iteration and regression detection. This is essential for measuring the subjective quality aspects that traditional metrics can't capture.

### **3. Scope**

**In Scope:**

- Gemini Flash integration for automated scoring
- **Multi-LLM consensus judging system with configurable providers**
- **Support for OpenAI models (GPT-4o, GPT-5) as additional judges**
- **Ensemble scoring by averaging multiple judge outputs**
- **Configurable judge combinations (single, 2-judge, 3-judge consensus)**
- Relevance scoring (0-10 scale) for context-query alignment
- Completeness evaluation against query requirements
- Reasoning quality assessment for multi-hop queries
- Long-range consistency scoring across conversation sessions
- Judge reliability validation against human annotations
- **Consensus reliability measurement vs single-judge baseline**
- Prompt engineering for reliable scoring
- **Outlier detection and handling in consensus scoring**

**Out of Scope:**

- Human annotation interface (manual process initially)
- Real-time scoring during production (evaluation mode only)
- Custom judge training or fine-tuning
- **Integration with non-OpenAI/non-Gemini models**

### **4. Acceptance Criteria**

### **Core Judge Implementation**

- [ ]  Gemini Flash integration with proper error handling and retries
- [ ]  **OpenAI integration (GPT-4o, GPT-5) with proper error handling**
- [ ]  Relevance scoring returns 0-10 values with explanatory reasoning
- [ ]  Completeness evaluation identifies missing required information
- [ ]  Reasoning quality assessment for multi-hop and temporal queries
- [ ]  Consistency scoring across extended conversation sessions

### **Consensus Judging System**

- [ ]  **Support for multiple LLM judges running in parallel**
- [ ]  **Configurable judge combinations: single-judge, 2-judge, 3-judge consensus**
- [ ]  **Consensus scoring by averaging individual judge scores across all dimensions**
- [ ]  **Outlier detection: identify and handle judges with significantly different scores**
- [ ]  **Reliability improvement: consensus scores show lower variance than single-judge**
- [ ]  **Graceful degradation: fallback to fewer judges if some fail**
- [ ]  **Performance optimization: parallel judge execution within timeout limits**

### **Judge Reliability & Validation**

- [ ]  Judge scores correlate >0.8 with human annotations on gold standard dataset
- [ ]  **Consensus scores show improved correlation vs single-judge baseline**
- [ ]  Consistent scoring across multiple runs (variance <0.5 points)
- [ ]  **Consensus scoring reduces variance by >20% compared to single-judge**
- [ ]  Judge explanations provide actionable feedback for improvements
- [ ]  **Consensus explanations synthesize insights from multiple judges**
- [ ]  Proper handling of edge cases and ambiguous queries

### **Evaluation Categories**

- [ ]  Single-hop recall evaluation (direct fact retrieval)
- [ ]  Multi-hop reasoning assessment (cross-memory synthesis)
- [ ]  Temporal reasoning evaluation (time-based context)
- [ ]  Adversarial robustness testing (conflicting information)
- [ ]  Commonsense reasoning integration assessment
- [ ]  **All evaluation categories support both single-judge and consensus modes**

### **Performance & Integration**

- [ ]  Judge evaluation completes within 2-5 seconds per query (single-judge)
- [ ]  **Consensus evaluation completes within 5-10 seconds per query (multi-judge)**
- [ ]  Async processing doesn't block main evaluation flow
- [ ]  **Parallel judge execution for optimal consensus performance**
- [ ]  Graceful fallback when judge service unavailable
- [ ]  **Intelligent fallback: 3-judge → 2-judge → single-judge based on availability**
- [ ]  Integration with evaluation infrastructure for metric storage
- [ ]  **Consensus metadata storage: individual scores + final consensus score**

### **Configuration & Deployment**

- [ ]  **Environment-based consensus configuration (CONSENSUS_MODE=single|dual|triple)**
- [ ]  **Provider priority configuration (primary, secondary, tertiary judges)**
- [ ]  **Cost optimization: configurable consensus for different evaluation contexts**
- [ ]  **Production safety: consensus mode disabled by default, single-judge fallback**