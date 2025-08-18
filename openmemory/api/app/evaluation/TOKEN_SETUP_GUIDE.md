# Jean Memory Token Setup Guide

## Overview

This guide helps you extract and securely store authentication tokens from your Jean Memory session for use in automated testing.

## Prerequisites

- Active Jean Memory account at https://jeanmemory.com
- Python environment with required dependencies
- Access to browser developer tools

## Quick Setup

### Step 1: Install Dependencies

```bash
cd openmemory/api
pip install cryptography aiohttp
```

### Step 2: Extract Token

1. **Open Jean Memory**: Go to https://jeanmemory.com and sign in
2. **Open Developer Tools**: Press F12 (or Cmd+Option+I on Mac)
3. **Navigate to Network Tab**: Look for the Network panel
4. **Trigger API Request**: Refresh the page or click on "Memories" in the navigation
5. **Find API Request**: Look for requests to `jean-memory-api-virginia.onrender.com`
6. **Copy Token**: 
   - Click on any API request
   - Find `Authorization: Bearer <long-token-string>` in Request Headers
   - Copy everything after "Bearer " (the long token string)

### Step 3: Store Token Securely

```bash
cd openmemory/api
python -m app.evaluation.auth_helper --setup
```

Follow the prompts:
- Paste your token when requested
- Create a secure password (minimum 8 characters)
- Confirm the password

### Step 4: Validate Token

```bash
python -m app.evaluation.auth_helper --validate
```

## Security Features

### 🔐 Encryption
- Tokens are encrypted using PBKDF2 with SHA256
- 100,000 iterations for key derivation
- Random salt for each encryption

### 🛡️ Local Storage
- Tokens stored in `.jean_memory_token` file
- File permissions set to 600 (owner read/write only)
- Automatically added to .gitignore

### 🔍 Validation
- Token validation against live API endpoints
- Clear error messages for expired tokens
- Network timeout protection

## Usage in Tests

### Basic Usage

```python
from app.evaluation.config import get_auth_headers, is_authenticated

# Check if authentication is available
if is_authenticated():
    headers = get_auth_headers()
    # Use headers in your API requests
else:
    print("No authentication available. Run token setup first.")
```

### Advanced Usage

```python
import aiohttp
from app.evaluation.config import auth_config

async def test_with_auth():
    if not await auth_config.validate_auth():
        print("Authentication failed!")
        return
    
    headers = auth_config.get_auth_headers()
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://jean-memory-api-virginia.onrender.com/memories",
            headers=headers
        ) as response:
            data = await response.json()
            print(f"Retrieved {len(data)} memories")
```

## Troubleshooting

### Token Not Working

1. **Check Token Format**: Ensure you copied the full token (usually very long)
2. **Verify Browser Session**: Make sure you're signed in to jeanmemory.com
3. **Extract Fresh Token**: Browser may have refreshed the token

### Password Issues

1. **Forgotten Password**: Delete `.jean_memory_token` file and re-run setup
2. **Password Too Short**: Must be at least 8 characters

### Network Issues

1. **API Endpoint**: Verify `jean-memory-api-virginia.onrender.com` is accessible
2. **Firewall**: Check if requests are being blocked

## Commands Reference

```bash
# Interactive token setup
python -m app.evaluation.auth_helper --setup

# Validate stored token
python -m app.evaluation.auth_helper --validate

# Check if token file exists
python -m app.evaluation.auth_helper --check

# Show help
python -m app.evaluation.auth_helper
```

## Security Best Practices

### ✅ Do
- Use a strong, unique password for token encryption
- Regularly validate tokens before important test runs
- Extract fresh tokens if tests start failing with auth errors

### ❌ Don't
- Share your token file or password with others
- Commit token files to version control (already gitignored)
- Use tokens extracted from shared/demo accounts

## Token Lifecycle

1. **Extraction**: Manual process using browser dev tools
2. **Storage**: Encrypted local storage with password protection
3. **Usage**: Automatic loading and validation in tests
4. **Expiration**: Jean Memory may expire tokens, requiring fresh extraction
5. **Refresh**: Manual re-extraction when tokens expire

## Integration with Evaluation Framework

The token system integrates seamlessly with the Jean Memory Evaluation Framework:

- **Task 5**: Secure token capture and storage ✅
- **Task 6**: Direct MCP endpoint client (uses stored tokens)
- **Task 7**: Conversation test runner (authenticated API calls)
- **Task 8**: Performance metrics extraction (authenticated access)

## File Structure

```
app/evaluation/
├── auth_helper.py          # Main token management
├── config.py              # Authentication configuration
└── TOKEN_SETUP_GUIDE.md   # This guide

.jean_memory_token          # Encrypted token storage (gitignored)
```

## Support

If you encounter issues:

1. Verify your Jean Memory account is active
2. Check network connectivity to the API
3. Ensure browser session is authenticated
4. Try extracting a fresh token
5. Validate dependencies are installed correctly

---

**Security Notice**: This token grants access to your Jean Memory account. Keep it secure and never share it with unauthorized users.