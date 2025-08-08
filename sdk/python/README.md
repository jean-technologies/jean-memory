# Jean Memory Python SDK

The official Python SDK for Jean Memory - Build personalized AI chatbots with persistent memory.

## Installation

```bash
pip install jeanmemory
```

## Quick Start

```python
from jeanmemory import JeanAgent
import os

# Create agent
agent = JeanAgent(
    api_key=os.getenv("JEAN_API_KEY")
)

# Run the agent
agent.run()
```

## Features

- 🧠 **Persistent Memory**: Conversations remember previous interactions
- 🚀 **Easy Setup**: Get started in 3 lines of code
- 🔒 **Secure**: OAuth 2.1 authentication with JWT tokens
- ⚡ **Fast**: Optimized for production use
- 🐍 **Pythonic**: Follows Python best practices

## API Reference

### JeanAgent

```python
class JeanAgent:
    def __init__(self, api_key: str, demo_mode: bool = False)
    def run(self) -> None
    async def process_message(self, message: str) -> str
```

### Example Usage

```python
import asyncio
from jeanmemory import JeanAgent

async def main():
    agent = JeanAgent(api_key="jean_sk_your_api_key")
    
    # Process a message
    response = await agent.process_message("Remember that I love pizza")
    print(response)
    
    # Later conversation
    response = await agent.process_message("What do I like to eat?")
    print(response)  # Will remember pizza preference

if __name__ == "__main__":
    asyncio.run(main())
```

## Links

- [Documentation](https://docs.jeanmemory.com)
- [GitHub](https://github.com/jean-technologies/jean-memory)
- [Website](https://jeanmemory.com)