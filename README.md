<h1 align="center">Jean Memory</h1>

<p align="center">
  <strong>A secure, private, and intelligent memory layer for AI.</strong>
</p>

<p align="center">
  <a href="https://jeanmemory.com">Website</a>
  ·
  <a href="https://jeanmemory.com/dashboard-new">Dashboard</a>
  ·
  <a href="https://docs.jeanmemory.com">API Docs</a>
  ·
  <a href="https://github.com/jean-technologies/jean-memory/issues">Report an Issue</a>
</p>

## What is Jean Memory?

Jean Memory provides a persistent and intelligent memory layer that enables AI applications to understand users with deep, personal context. It moves beyond simple information retrieval to sophisticated context engineering, ensuring that an AI has precisely the right information at the time of inference to provide personalized, accurate, and helpful responses.

- **Intelligent Orchestration**: Jean uses an AI-powered orchestration layer to dynamically analyze user intent, save new information, and retrieve the most relevant context. It's more than a vector database; it's a reasoning engine for memory.
- **Secure and Private**: Your context is stored securely, under your control.
- **Universal Compatibility**: Works across MCP-compatible AI tools like Claude and Cursor.
- **Flexible Hosting**: Use our managed cloud service for a zero-setup experience or self-host the entire stack for complete control.

## Architecture: Intelligent Orchestration & Tooling

Jean Memory operates on a two-layer architecture: an intelligent orchestration layer and a core API of granular tools.

1.  **Orchestration Layer (`jean_memory` tool)**: This is the primary entry point for all interactions. When called, this tool analyzes the user's message and conversation history to determine the optimal context strategy. It then calls the necessary core tools to gather information, synthesizes the results, and provides a perfectly engineered context package to the AI. It also handles background memory saving.

2.  **Core API (Granular Tools)**: These are the underlying building blocks that the orchestrator uses. They are also exposed via a REST API for developers who need direct, granular control for building custom agents or applications. The core tools include:
    - `add_memories`: Saves new information.
    - `search_memory`: Performs semantic search.
    - `list_memories`: Retrieves recent memories.
    - `ask_memory`: Answers questions based on stored context.
    - `deep_memory_query`: Conducts comprehensive, analytical searches across all data.

<p align="center">
  <img src="/openmemory/ui/public/og-image.png" width="600px" alt="Jean Memory Knowledge Graph">
</p>

## Quick Start: Hosted Service

Get started in seconds with our managed service:

1.  **Sign Up**: Create an account at [jeanmemory.com](https://jeanmemory.com) and navigate to your dashboard.
2.  **Get Install Command**: Choose a client application (e.g., Claude, Cursor) to generate your unique installation command.
3.  **Connect Client**: Run the provided command in your terminal.
4.  **Restart and Use**: Restart your AI application. Jean Memory will now be available as a tool.

## Local Development Setup

Run the entire Jean Memory stack on your local machine for development and self-hosting.

**Prerequisites:**
- Node.js 18+ and npm
- Python 3.12+
- Docker and Docker Compose
- Git

**1. Clone the repository:**
```bash
git clone https://github.com/jean-technologies/jean-memory.git
cd jean-memory
```

**2. Navigate to the `openmemory` directory:**
```bash
cd openmemory
```

**3. Run one-time setup:**
This script will gather required API keys and generate the necessary environment files.
```bash
make setup
```

**4. Add your API keys when prompted:**
- `OPENAI_API_KEY` (required) - Get from the [OpenAI Platform](https://platform.openai.com/api-keys)
- `GEMINI_API_KEY` (optional) - Get from [Google AI Studio](https://makersuite.google.com/app/apikey)

**5. Build the environment:**
This command builds the Docker containers and configures the environment based on your keys.
```bash
make build
```

**6. Start the development services:**

*Option A: Run all services concurrently:*
```bash
make dev
```

*Option B: Run services individually in separate terminals:*
```bash
# Terminal 1: Start the backend API and databases
make dev-api

# Terminal 2: Start the frontend UI
make dev-ui
```

**7. Access the application:**
- **UI Dashboard**: `http://localhost:3000`
- **API Documentation**: `http://localhost:8765/docs`
- **Supabase Studio**: `http://localhost:54323`

## API Usage

Jean Memory exposes a granular API for memory operations, which is orchestrated by the primary `jean_memory` tool. These underlying tools can also be called directly for specific use cases or when building custom agents. The API includes endpoints for:

- Adding new memories (`add_memories`)
- Searching memories (`search_memory`)
- Listing recent memories (`list_memories`)
- Performing conversational Q&A (`ask_memory`)
- Executing deep, analytical queries (`deep_memory_query`)

For detailed information, please refer to our full **[API Documentation](https://docs.jeanmemory.com)**.

## Contributing

We welcome contributions from the community. Please read our [contributing guide](docs/contributing/CONTRIBUTING.md) to get started with the development process and pull request submission.

## License

This project incorporates code from [mem0ai/mem0](https://github.com/mem0ai/mem0), which is distributed under the Apache 2.0 License. All additions and modifications made by Jean Technologies are proprietary.

## Support

- **Documentation**: [docs.jeanmemory.com](https://docs.jeanmemory.com)
- **Bug Reports**: [GitHub Issues](https://github.com/jean-technologies/jean-memory/issues)
- **General Inquiries**: [jonathan@jeantechnologies.com](mailto:jonathan@jeantechnologies.com)
