# Jean Memory MCP Integration Setup Guide

## Overview

This document provides a comprehensive guide to the Jean Memory MCP (Model Context Protocol) integration architecture, covering Claude Desktop Extensions (DXT), Chorus, and Cursor IDE integrations.

## Architecture Summary

### Transport Methods
- **Primary**: HTTP transport (recommended for performance)
- **Legacy**: SSE (Server-Sent Events) for backward compatibility
- **Performance**: HTTP is 50-75% faster than SSE transport

### Client Integrations
1. **Claude Desktop**: Via DXT (Desktop Extensions) files
2. **Chorus**: Direct HTTP integration with fallback SSE
3. **Cursor IDE**: HTTP-only transport (no SSE)

## Claude Desktop Extensions (DXT)

### What are DXT Files?
Desktop Extensions (.dxt) are zip files containing:
- `manifest.json` (required configuration)
- `server/index.js` (MCP server entry point)
- `package.json` (dependencies)
- `assets/icon.png` (extension icon)

### Current DXT Files
Located in: `openmemory/api/app/static/`
- `jean-memory-claude.dxt` - HTTP transport version (recommended)
- `jean-memory-legacy.dxt` - SSE transport version (legacy)

### DXT Configuration
```json
{
  "server": {
    "mcp_config": {
      "args": [
        "${__dirname}/server/index.js",
        "https://jean-memory-api-virginia.onrender.com/mcp/v2/claude/${user_config.user_id}"
      ]
    }
  }
}
```

### DXT Distribution Process
1. **Build**: Use `zip -r filename.dxt assets/ manifest.json package.json server/`
2. **Test**: Verify on both Windows and macOS
3. **Deploy**: Users double-click .dxt file to install
4. **Update**: Replace DXT files and redistribute

## Transport Architecture

### HTTP V2 Transport (Recommended)
**Endpoint**: `/mcp/v2/{client_name}/{user_id}`
**Features**:
- Direct backend connection (no Cloudflare proxy)
- 50-75% faster performance
- Better debugging and logging
- Simplified infrastructure

### Legacy SSE Transport
**Endpoint**: `/mcp/{client_name}/sse/{user_id}`
**Usage**: Maintained for backward compatibility with older clients

## Client-Specific Configurations

### Chorus Integration
**File**: `app/routing/chorus.py`
**Transport**: HTTP-first with SSE fallback
**Endpoints**:
- Primary: `/mcp/chorus/messages/{user_id}` (HTTP)
- Fallback: `/mcp/chorus/sse/{user_id}` (SSE)

**Key Features**:
- SSE endpoint redirects to HTTP for performance
- Direct JSON-RPC responses via HTTP
- No Worker dependency

### Cursor IDE Integration
**Configuration**: Built into main MCP router
**Transport**: HTTP-only (no SSE)
**Special Handling**: 
```python
# Lines 260-262 in app/routing/mcp.py
if client_name == "cursor":
    return response  # Direct JSON-RPC response
```

## Server Configuration

### Current Production URLs
- **Virginia**: `https://jean-memory-api-virginia.onrender.com`
- **Legacy**: `https://jean-memory-api.onrender.com` (deprecated)

### Service Detection
```python
SERVICE_NAME = os.getenv('RENDER_SERVICE_NAME', 'unknown-service')
RENDER_REGION = os.getenv('RENDER_REGION', 'unknown-region')
```

## Authentication & Context

### Authentication Methods
1. **API Key**: Header-based authentication for agents
2. **User ID**: Direct user identification via headers
3. **Client Name**: Identifies the requesting client type

### Context Variables
```python
user_id_var.set(user_id_from_header)
client_name_var.set(client_name_from_header)
background_tasks_var.set(background_tasks)
```

## MCP Protocol Implementation

### Supported Methods
- `initialize` - Protocol handshake
- `tools/list` - Available tools enumeration
- `tools/call` - Tool execution
- `notifications/initialized` - Client ready notification
- `notifications/cancelled` - Operation cancellation
- `resources/list` - Resource enumeration (empty)
- `prompts/list` - Prompt enumeration (empty)

### Protocol Versions
- **2024-11-05**: Standard MCP protocol
- **2025-03-26**: Enhanced protocol with annotations

## Tool Registration

### Centralized Architecture
```python
# app/mcp_instance.py - Singleton MCP instance
from app.mcp_instance import mcp

# Tool registration via decorators
@mcp.tool
def example_tool():
    pass
```

### Client Profiles
Each client has a profile that handles:
- Tool schema generation
- Request routing
- Response formatting
- Client-specific features

## Debugging & Monitoring

### Logging Configuration
```python
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Key Log Points
- Connection establishment
- Method execution
- Tool calls
- Error handling
- Performance metrics

## Deployment Checklist

### DXT File Updates
1. ✅ Update manifest.json URLs to Virginia service
2. ✅ Rebuild DXT packages
3. ✅ Test on target platforms
4. ✅ Distribute updated files

### Service Migration
1. ✅ Verify Virginia service is operational
2. ✅ Update all client configurations
3. ✅ Monitor performance improvements
4. ✅ Deprecate legacy service

### Transport Verification
1. ✅ Chorus: HTTP-first confirmed
2. ✅ Cursor: HTTP-only confirmed
3. ✅ Claude Desktop: HTTP via V2 endpoints
4. ✅ Legacy SSE: Maintained for compatibility

## Performance Optimizations

### HTTP vs SSE Benefits
- **Latency**: 50-75% reduction
- **Reliability**: Direct connection eliminates proxy issues
- **Debugging**: Better error visibility
- **Infrastructure**: Simplified deployment

### Client-Specific Optimizations
- **Cursor**: Direct JSON-RPC responses (no SSE queue)
- **Chorus**: HTTP endpoint with SSE fallback
- **Claude Desktop**: V2 HTTP transport via DXT

## Security Considerations

### Authentication Layers
1. API key validation for agent clients
2. User ID verification
3. Client name validation
4. CORS headers for web clients

### Data Protection
- Sensitive configuration stored in OS keychain (DXT)
- Request/response logging excludes sensitive data
- Background task isolation per user context

## Troubleshooting

### Common Issues
1. **Connection Failures**: Check service URL in DXT manifest
2. **Tool Not Found**: Verify tool registration and client profile
3. **Authentication Errors**: Validate headers and API keys
4. **Performance Issues**: Prefer HTTP over SSE transport

### Debug Commands
```bash
# Check service status
curl https://jean-memory-api-virginia.onrender.com/health

# Test MCP endpoint
curl -X POST https://jean-memory-api-virginia.onrender.com/mcp/v2/claude/USER_ID \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}'
```

## Future Enhancements

### Planned Improvements
1. **Auto-update mechanism** for DXT files
2. **Enhanced client detection** and feature negotiation
3. **Performance monitoring** and metrics collection
4. **Expanded protocol support** for emerging MCP features

### Migration Path
- Continue HTTP-first approach
- Phase out SSE dependency
- Standardize on V2 endpoints
- Implement streaming where beneficial

---

**Last Updated**: July 28, 2025
**Service**: jean-memory-api-virginia.onrender.com
**Transport**: HTTP V2 (Primary), SSE (Legacy)