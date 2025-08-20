# Jean Memory Speed Modes - Developer Guide

Welcome to Jean Memory! This guide explains how to use the different speed modes available in the `jean_memory` tool for optimal performance based on your use case.

## Overview

Jean Memory offers 4 distinct speed modes, each optimized for different scenarios:

- **🚀 Fast**: Direct memory search (0.5-1s)
- **⚖️ Balanced**: AI synthesis with Gemini 2.5 Flash (3-5s) 
- **🧠 Autonomous**: Intelligent orchestration (variable latency)
- **📚 Comprehensive**: Deep document analysis (20-30s)

## Speed Mode Details

### 🚀 Fast Mode
```javascript
await jeanMemory({
  user_message: "What are my morning routine preferences?",
  is_new_conversation: false,
  needs_context: true,
  speed: "fast"
});
```

**Best for:**
- Quick lookups
- Simple factual retrieval
- Real-time chat responses
- Mobile applications with latency constraints

**Performance:** 0.5-1 second response time
**Returns:** Raw memory search results (maximum 10 results)

### ⚖️ Balanced Mode ⭐ RECOMMENDED
```javascript
await jeanMemory({
  user_message: "How do I usually handle work stress?",
  is_new_conversation: false,
  needs_context: true,
  speed: "balanced"
});
```

**Best for:**
- Conversational AI responses
- Natural language synthesis
- Most chatbot interactions
- Default recommendation for most use cases

**Performance:** 3-5 seconds with Gemini 2.5 Flash
**Returns:** AI-synthesized conversational response based on memories
**Technology:** Powered by Gemini 2.5 Flash for optimal adaptive thinking

### 🧠 Autonomous Mode
```javascript
await jeanMemory({
  user_message: "Help me plan my week based on my goals",
  is_new_conversation: false,
  needs_context: true,
  speed: "autonomous"
});
```

**Best for:**
- Complex analysis requiring intelligent decision-making
- Context-aware responses
- Multi-step reasoning
- Adaptive behavior based on conversation state

**Performance:** Variable latency (can exceed comprehensive mode for complex analysis)
**Returns:** Intelligently orchestrated response with adaptive context analysis

### 📚 Comprehensive Mode
```javascript
await jeanMemory({
  user_message: "What did the article about productivity say about morning routines?",
  is_new_conversation: false,
  needs_context: true,
  speed: "comprehensive"
});
```

**Best for:**
- Deep document searches
- Detailed content analysis
- Research queries
- When you need exhaustive information

**Performance:** 20-30 seconds
**Returns:** Extensive memory analysis with document chunk search
**Alternative:** Can use `speed: "deep"` (same functionality)

## Usage Examples

### React SDK
```typescript
import { useJeanMemory } from '@jeanmemory/react';

function MyComponent() {
  const { getContext } = useJeanMemory();
  
  // Quick lookup
  const quickResult = await getContext(
    "What's my favorite coffee?", 
    { mode: 'fast' }
  );
  
  // Conversational response (recommended)
  const chatResponse = await getContext(
    "How should I approach this work conflict?",
    { mode: 'balanced' }
  );
  
  // Deep analysis
  const detailedAnalysis = await getContext(
    "Analyze my career progression patterns",
    { mode: 'comprehensive' }
  );
}
```

### Node.js SDK
```javascript
const { JeanMemoryClient } = require('@jeanmemory/node');

const client = new JeanMemoryClient({ apiKey: 'your_api_key' });

// Fast mode for quick responses
const quickMemories = await client.getContext({
  query: "Meeting preferences",
  speed: "fast"
});

// Balanced mode for natural conversations
const conversation = await client.getContext({
  query: "How do I handle difficult conversations?",
  speed: "balanced"
});
```

### Python SDK
```python
from jeanmemory import JeanMemoryClient

client = JeanMemoryClient(api_key="your_api_key")

# Comprehensive analysis
result = client.get_context(
    query="Analyze my learning patterns from all documents",
    speed="comprehensive"
)

# Autonomous intelligent response
smart_response = client.get_context(
    query="Help me prepare for my upcoming presentation",
    speed="autonomous"
)
```

## Performance Comparison

| Mode | Response Time | Use Case | Technology |
|------|---------------|----------|------------|
| Fast | 0.5-1s | Quick lookups | Direct search |
| Balanced | 3-5s | Conversations | Gemini 2.5 Flash synthesis |
| Autonomous | Variable | Complex analysis | Intelligent orchestration |
| Comprehensive | 20-30s | Deep research | Document + memory search |

## Best Practices

### 🎯 Mode Selection Guidelines

1. **Default Choice**: Use `balanced` mode for most conversational interactions
2. **Performance Critical**: Use `fast` mode when sub-second response is required
3. **Complex Queries**: Use `autonomous` mode for multi-step reasoning
4. **Research Tasks**: Use `comprehensive` mode for thorough document analysis

### 💡 Optimization Tips

- **Fast Mode**: Perfect for autocomplete, quick facts, simple queries
- **Balanced Mode**: Ideal for chatbots, personal assistants, natural conversations
- **Autonomous Mode**: Best for planning, analysis, context-dependent responses
- **Comprehensive Mode**: Use sparingly due to latency, great for detailed research

### ⚠️ Important Notes

- **New Conversations**: Set `is_new_conversation: true` for the first message
- **Context Control**: Use `needs_context: false` for generic knowledge questions
- **Error Handling**: Always implement proper error handling for all modes
- **Rate Limits**: Be mindful of API rate limits, especially with comprehensive mode

## Example Response Formats

### Fast Mode Response
```json
{
  "status": "success",
  "memories": [
    {
      "id": "mem_123",
      "content": "User prefers morning meetings at 9 AM",
      "score": 0.92,
      "created_at": "2024-01-15T09:00:00Z"
    }
  ],
  "total_found": 5
}
```

### Balanced Mode Response
```json
{
  "status": "success",
  "question": "How do I handle work stress?",
  "answer": "Based on your memories, you typically handle work stress by taking short walks, practicing deep breathing, and scheduling regular breaks. You've mentioned that listening to calm music during breaks is particularly effective for you.",
  "memories_found": 8,
  "total_duration": 3.2
}
```

## Getting Started

1. **Install SDK**: Choose React, Node.js, or Python SDK
2. **Get API Key**: Sign up at [jeanmemory.com](https://jeanmemory.com)
3. **Start with Balanced**: Begin with balanced mode for most use cases
4. **Optimize**: Switch to other modes based on specific performance needs

## Support

- 📚 **Documentation**: [jeanmemory.com/docs](https://jeanmemory.com/docs)
- 🐛 **Issues**: [GitHub Issues](https://github.com/jean-technologies/jean-memory/issues)
- 💬 **Community**: [Discord](https://discord.gg/jeanmemory)
- 📧 **Email**: support@jeanmemory.com

---

**Happy coding with Jean Memory! 🎉**

*Last updated: August 2024 - SDK v2.0.6*