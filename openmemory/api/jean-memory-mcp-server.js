#!/usr/bin/env node

/**
 * Jean Memory MCP Server - Stdio Transport
 * 
 * A clean, minimal MCP server implementation that follows Claude Code documentation patterns.
 * Uses stdio transport for maximum compatibility and simplicity.
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { CallToolRequestSchema, ListToolsRequestSchema } = require('@modelcontextprotocol/sdk/types.js');
const fetch = require('node-fetch');

class JeanMemoryMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'jean-memory-mcp-server',
        version: '1.0.0'
      },
      {
        capabilities: {
          tools: {}
        }
      }
    );

    this.apiBaseUrl = process.env.JEAN_MEMORY_API_URL || 'https://jean-memory-api-dev.onrender.com';
    this.userId = process.env.USER_ID || process.argv[process.argv.indexOf('--user-id') + 1];
    this.apiKey = process.env.JEAN_MEMORY_API_KEY;

    if (!this.userId) {
      console.error('ERROR: USER_ID required. Use --user-id flag or USER_ID environment variable.');
      process.exit(1);
    }

    this.setupToolHandlers();
  }

  setupToolHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'jean_memory',
            description: '🌟 PRIMARY TOOL for all conversational interactions. Intelligently engineers context for the user\'s message, saves new information, and provides relevant background. For the very first message in a conversation, set \'is_new_conversation\' to true. Set needs_context=false for generic knowledge questions that don\'t require personal context about the specific user (e.g., \'what is the relationship between introversion and conformity\', \'explain quantum physics\'). Set needs_context=true only for questions that would benefit from the user\'s personal context, memories, or previous conversations.',
            inputSchema: {
              type: 'object',
              properties: {
                user_message: {
                  type: 'string',
                  description: 'The user\'s complete message or question'
                },
                is_new_conversation: {
                  type: 'boolean',
                  description: 'Set to true only for the very first message in a new chat session, otherwise false.'
                },
                needs_context: {
                  type: 'boolean',
                  description: 'Whether personal context retrieval is needed for this query. Set to false for generic knowledge questions (science, definitions, general concepts). Set to true for questions that would benefit from the user\'s personal memories, experiences, or previous conversations.',
                  default: true
                }
              },
              required: ['user_message', 'is_new_conversation']
            }
          },
          {
            name: 'store_document',
            description: '⚡ FAST document upload. Store large documents (markdown, code, essays) in background. Returns immediately with job ID for status tracking. Perfect for entire files that would slow down chat.',
            inputSchema: {
              type: 'object',
              properties: {
                title: {
                  type: 'string',
                  description: 'A descriptive title for the document'
                },
                content: {
                  type: 'string',
                  description: 'The full text content of the document (markdown, code, etc.)'
                },
                document_type: {
                  type: 'string',
                  description: 'Type of document (e.g., \'markdown\', \'code\', \'notes\', \'documentation\')',
                  default: 'markdown'
                },
                source_url: {
                  type: 'string',
                  description: 'Optional URL where the document came from'
                }
              },
              required: ['title', 'content']
            }
          }
        ]
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'jean_memory':
            return await this.handleJeanMemory(args);
          case 'store_document':
            return await this.handleStoreDocument(args);
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [{
            type: 'text',
            text: `Error: ${error.message}`
          }],
          isError: true
        };
      }
    });
  }

  async handleJeanMemory(args) {
    const { user_message, is_new_conversation, needs_context = true } = args;

    // Use the standard MCP endpoint that matches existing routing
    const response = await fetch(`${this.apiBaseUrl}/mcp/claude%20code/messages/${this.userId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-user-id': this.userId,
        'x-client-name': 'claude code'
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: Date.now(),
        method: 'tools/call',
        params: {
          name: 'jean_memory',
          arguments: {
            user_message,
            is_new_conversation,
            needs_context
          }
        }
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();
    
    if (result.error) {
      throw new Error(result.error.message || 'Unknown API error');
    }

    return {
      content: [{
        type: 'text',
        text: result.result?.content?.[0]?.text || 'No response from Jean Memory'
      }]
    };
  }

  async handleStoreDocument(args) {
    const { title, content, document_type = 'markdown', source_url } = args;

    // Use the standard MCP endpoint that matches existing routing
    const response = await fetch(`${this.apiBaseUrl}/mcp/claude%20code/messages/${this.userId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-user-id': this.userId,
        'x-client-name': 'claude code'
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: Date.now(),
        method: 'tools/call',
        params: {
          name: 'store_document',
          arguments: {
            title,
            content,
            document_type,
            source_url
          }
        }
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();
    
    if (result.error) {
      throw new Error(result.error.message || 'Unknown API error');
    }

    return {
      content: [{
        type: 'text',
        text: result.result?.content?.[0]?.text || 'Document stored successfully'
      }]
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    
    // Log startup info to stderr (so it doesn't interfere with MCP protocol on stdout)
    console.error(`Jean Memory MCP Server started`);
    console.error(`User ID: ${this.userId}`);
    console.error(`API URL: ${this.apiBaseUrl}`);
  }
}

// Handle process signals gracefully
process.on('SIGINT', () => {
  console.error('Received SIGINT, shutting down gracefully...');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.error('Received SIGTERM, shutting down gracefully...');
  process.exit(0);
});

// Start the server
if (require.main === module) {
  const server = new JeanMemoryMCPServer();
  server.run().catch((error) => {
    console.error('Server error:', error);
    process.exit(1);
  });
}

module.exports = JeanMemoryMCPServer;