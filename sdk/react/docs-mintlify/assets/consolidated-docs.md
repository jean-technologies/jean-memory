# Jean Memory - Complete Documentation for AI Coding Tools

**Generated on:** 2025-08-07 17:44:52

## What is Jean Memory?

Jean Memory is the universal memory layer for AI applications. It provides persistent, cross-application memory that allows AI agents to remember user preferences, conversation context, and personal information across different applications and sessions.

### Key Capabilities:
- **Universal Memory**: Works across any application or platform
- **5-Line Integration**: Add persistent memory to any React app in under 5 minutes
- **Cross-Application Persistence**: Users' AI agents remember them across different apps
- **Context Engineering**: Intelligent context building for personalized AI experiences
- **Multiple Integration Methods**: REST API, React SDK, Python SDK, Node.js SDK, and MCP

### Quick Integration Examples:

#### React (5 lines):
```tsx
import { useState } from 'react';
import { useJean, SignInWithJean, JeanChat } from 'jeanmemory-react';

function MyApp() {
  const [user, setUser] = useState(null);
  const { agent } = useJean({ user });
  
  if (!agent) return <SignInWithJean apiKey="your-api-key" onSuccess={setUser} />;
  return <JeanChat agent={agent} />;
}
```

#### Python:
```python
from jeanmemory import JeanAgent
agent = JeanAgent(api_key="your-api-key")
agent.run()
```

#### Node.js:
```javascript
import { JeanAgent } from '@jeanmemory/node';
const agent = new JeanAgent({ apiKey: "your-api-key" });
await agent.run();
```

### NPM Packages:
- React: `npm install jeanmemory-react` 
- Node.js: `npm install @jeanmemory/node`
- Python: `pip install jeanmemory`

---

# Complete Documentation


## Additional Context for AI Development

### Common Integration Patterns:
- **Chat Applications**: Use JeanChat component for instant AI chat with memory
- **Personal Assistants**: Build context with user preferences and history  
- **Customer Support**: Maintain customer context across support sessions
- **Learning Platforms**: Track progress and adapt to learning style
- **Team Collaboration**: Share context across team members

### API Base URL:
- Production: `https://jean-memory-api-virginia.onrender.com`

### Authentication:
- All SDKs handle OAuth 2.1 PKCE flow automatically
- Get API keys at: https://jeanmemory.com

### Key Features to Highlight in Applications:
- Cross-application memory persistence
- Personalized AI experiences
- Context-aware responses
- User preference learning
- Conversation continuity

This documentation contains everything needed to integrate Jean Memory into any application. Focus on the SDK that matches your technology stack and follow the quickstart examples.
