import os
import re
from datetime import datetime

def create_consolidated_docs():
    """
    Combines all API documentation files into a single, comprehensive file optimized for AI coding tools.
    """
    
    # Header content for AI context
    ai_context_header = f"""# Jean Memory - Complete Documentation for AI Coding Tools

**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

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
import {{ useState }} from 'react';
import {{ useJean, SignInWithJean, JeanChat }} from 'jeanmemory-react';

function MyApp() {{
  const [user, setUser] = useState(null);
  const {{ agent }} = useJean({{ user }});
  
  if (!agent) return <SignInWithJean apiKey="your-api-key" onSuccess={{setUser}} />;
  return <JeanChat agent={{agent}} />;
}}
```

#### Python:
```python
from jeanmemory import JeanAgent
agent = JeanAgent(api_key="your-api-key")
agent.run()
```

#### Node.js:
```javascript
import {{ JeanAgent }} from '@jeanmemory/node';
const agent = new JeanAgent({{ apiKey: "your-api-key" }});
await agent.run();
```

### NPM Packages:
- React: `npm install jeanmemory-react` 
- Node.js: `npm install @jeanmemory/node`
- Python: `pip install jeanmemory`

---

# Complete Documentation

"""

    doc_files = [
        ("docs-mintlify/overview.mdx", "Platform Overview"),
        ("docs-mintlify/quickstart.mdx", "Quickstart Guide"), 
        ("docs-mintlify/architecture.mdx", "System Architecture"),
        ("docs-mintlify/sdk/react.mdx", "React SDK"),
        ("docs-mintlify/sdk/nodejs.mdx", "Node.js SDK"), 
        ("docs-mintlify/sdk/python.mdx", "Python SDK"),
        ("docs-mintlify/mcp/introduction.mdx", "MCP Introduction"),
        ("docs-mintlify/mcp/authentication.mdx", "Authentication Guide"),
        ("docs-mintlify/mcp/context-engineering.mdx", "Context Engineering"),
        ("docs-mintlify/mcp/setup.mdx", "MCP Setup"),
        ("docs-mintlify/tools.mdx", "Available Tools"),
        ("docs-mintlify/example-use-cases.mdx", "Example Use Cases"),
    ]

    output_dir = "docs-mintlify/assets"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_filename = os.path.join(output_dir, "consolidated-docs.md")
    
    with open(output_filename, "w", encoding='utf-8') as outfile:
        # Write AI context header
        outfile.write(ai_context_header)
        
        for doc_file, section_title in doc_files:
            if os.path.exists(doc_file):
                with open(doc_file, "r", encoding='utf-8') as infile:
                    content = infile.read()
                    # Remove YAML frontmatter
                    content = re.sub(r'^---[\s\S]*?---', '', content).strip()
                    outfile.write(f"## {section_title} ({os.path.basename(doc_file)})\n\n")
                    outfile.write(content)
                    outfile.write("\n\n---\n\n")
            else:
                print(f"Warning: {doc_file} not found.")
        
        # Add footer with additional context
        footer = """
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
"""
        outfile.write(footer)

if __name__ == "__main__":
    create_consolidated_docs()
    print("Consolidated documentation created successfully.")