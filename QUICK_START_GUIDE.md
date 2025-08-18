# Jean Memory Evaluation Framework - Quick Start Guide

## **Overview**
Complete evaluation system for Jean Memory's context engineering performance with automated testing, LLM judging, and comprehensive reporting.

## **Prerequisites**
- Python 3.8+
- API keys for LLM providers
- Access to Jean Memory production system

## **Setup (One-Time)**

### 1. Set API Keys
```bash
export GEMINI_API_KEY="your_gemini_key"
export OPENAI_API_KEY="your_openai_key"
```

### 2. Configure Authentication
```bash
./run_evaluation.py --setup
```
Follow the prompts to extract and store your Jean Memory token from browser.

## **Usage**

### Quick Validation
```bash
./run_evaluation.py --quick-test
```
Validates all components are working correctly.

### Full Evaluation
```bash
# Basic 10-turn evaluation
./run_evaluation.py --user-id YOUR_USER_ID

# Extended 20-turn evaluation  
./run_evaluation.py --user-id YOUR_USER_ID --length 20

# Mixed reasoning types
./run_evaluation.py --user-id YOUR_USER_ID --length 15 --type mixed
```

## **What It Does**

1. **Generates** conversation datasets with progressive reasoning complexity
2. **Executes** real conversations against Jean Memory via MCP endpoint
3. **Evaluates** responses using multi-provider LLM judges
4. **Extracts** performance metrics from logs
5. **Generates** comprehensive reports with actionable insights

## **Output**

### Reports Location
- **Markdown**: `./evaluation_reports/evaluation_report_TIMESTAMP.md`
- **JSON**: `./evaluation_reports/evaluation_report_TIMESTAMP.json`

### Key Metrics
- **Success Rate**: Percentage of successful conversation turns
- **LLM Judge Scores**: 0-10 quality ratings per reasoning type
- **Performance**: Response times, cache hits, orchestration timing
- **LoCoMo Breakdown**: Single-hop, multi-hop, temporal, adversarial analysis

## **Performance Targets**
- Single-hop: >90% accuracy (9.0/10)
- Multi-hop: >80% accuracy (8.0/10)  
- Temporal: >75% accuracy (7.5/10)
- Overall: >7.0/10 average

## **Troubleshooting**

| Issue | Solution |
|-------|----------|
| "No valid token" | Run `./run_evaluation.py --setup` |
| "No LLM providers" | Set `GEMINI_API_KEY` and `OPENAI_API_KEY` |
| "MCP connection failed" | Verify user_id and token validity |
| "No datasets found" | Run with `--length` to generate datasets |

## **Help**
```bash
./run_evaluation.py --help
```

## **Production Safety**
- Zero impact on existing systems
- Evaluation disabled by default
- No SDK modifications required
- Secure encrypted token storage