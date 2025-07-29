# Jean Memory Multi-Mode Evaluation Framework

## Overview

The Multi-Mode Evaluation Framework allows you to test Jean Memory using two different client modes:

1. **Local Mode**: Direct function calls (current development approach)
2. **Production Mode**: HTTP API calls (simulates how Claude would actually use Jean Memory)

This addresses your requirement to test both local functions and production API interactions.

## Usage

### Local Mode (Direct Function Calls)
```bash
# Basic local evaluation
python multi_mode_evaluation_runner.py --mode local

# Local with result saving (default)
python multi_mode_evaluation_runner.py --mode local --save-results
```

### Production Mode (HTTP API Calls)
```bash
# Production mode with your server
python multi_mode_evaluation_runner.py --mode production --base-url https://your-jean-memory-api.com

# Production mode with API key
python multi_mode_evaluation_runner.py --mode production --base-url https://api.jean-memory.com --api-key your-api-key

# Example for Claude production testing
python multi_mode_evaluation_runner.py --mode production --base-url https://api.anthropic.com/jean-memory --api-key sk-...
```

## Key Differences

### Local Mode
- ✅ **Fast**: Direct function calls, no network overhead
- ✅ **Development**: Perfect for debugging and development
- ✅ **Full Access**: Can test internal functions directly
- ❌ **Not Realistic**: Doesn't simulate real client behavior

### Production Mode  
- ✅ **Realistic**: Simulates how Claude actually calls Jean Memory
- ✅ **End-to-End**: Tests full HTTP API stack
- ✅ **Network Effects**: Includes real network latency and failures
- ❌ **Slower**: Network overhead and API processing time
- ❌ **Dependencies**: Requires running server and network access

## Results Comparison

The framework shows which mode was used for each test:

```
📈 DETAILED RESULTS:
✅ Memory Triage   | 95.0% accuracy (local mode)
✅ Context Quality | 75.0/100 average (production mode)  
✅ Performance     | Completed (local mode)
✅ Integration     | 100.0% operational (production mode)
```

## Configuration Examples

### For Local Development
```python
# In your test scripts
runner = MultiModeEvaluationRunner("local")
```

### For Claude Production Testing
```python
# Simulates how Claude would call Jean Memory
runner = MultiModeEvaluationRunner(
    "production", 
    base_url="https://api.jean-memory.com",
    api_key="your-claude-api-key"
)
```

### For API Testing
```python
# Test your Jean Memory API endpoints
runner = MultiModeEvaluationRunner(
    "production",
    base_url="https://your-api.com",
    api_key="test-key"
)
```

## API Client Architecture

The framework uses different clients:

### LocalJeanMemoryClient
- Calls `jean_memory()` function directly
- Sets up FastAPI context variables
- No network calls

### ProductionAPIClient  
- Makes HTTP POST to `/api/v1/jean_memory`
- Includes proper headers and authentication
- Handles network errors and timeouts

## Expected API Endpoint

For production mode, your server should have:

```
POST /api/v1/jean_memory
Content-Type: application/json
Authorization: Bearer <api-key>

{
  "user_message": "Help me with my project",
  "is_new_conversation": false,
  "needs_context": true,
  "user_id": "user-123",
  "client_name": "claude"
}

Response:
{
  "context": "Relevant user context...",
  "status": "success"
}
```

## Health Check Endpoint

```
GET /health

Response:
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "database": "ok",
    "memory_system": "ok"
  }
}
```

## Performance Expectations

### Local Mode
- Memory triage: < 1s per test
- Context retrieval: < 3s per test
- Integration checks: < 1s per test

### Production Mode  
- Memory triage: < 5s per test (includes network)
- Context retrieval: < 8s per test (includes network)
- Integration checks: < 3s per test

## Next Steps

1. **Test Local Mode**: Verify your current implementation works
2. **Set Up API Endpoints**: Create the HTTP API endpoints  
3. **Test Production Mode**: Validate API behavior
4. **Claude Integration**: Use production mode to simulate Claude's usage
5. **Continuous Testing**: Run both modes in CI/CD

## Toggle Implementation

The toggle is implemented via command-line arguments and can easily be extended:

```python
# Easy to add more modes
parser.add_argument("--mode", choices=["local", "production", "claude", "api"], default="local")

# Easy to add client-specific settings
if args.mode == "claude":
    client_kwargs.update(claude_specific_settings())
```

This gives you the flexibility to test both your local development setup and production API behavior, ensuring Jean Memory works correctly for both internal development and external clients like Claude.