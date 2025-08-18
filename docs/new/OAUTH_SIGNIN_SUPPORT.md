# Jean Memory OAuth Sign-in Support - GitHub & Google Integration

**Date:** August 7, 2025  
**Status:** Design Phase  
**Purpose:** Enable OAuth sign-in options alongside email authentication for broader user adoption

## Executive Summary

Currently, Jean Memory SDK only supports email/password authentication. This limitation creates friction for users who prefer OAuth sign-in methods they use across other platforms. By adding GitHub and Google OAuth support (already available on jeanmemory.com), we can significantly reduce sign-in friction, increase conversion rates, and provide a more familiar authentication experience for users.

## Current State Analysis

### What We Have
- Email/password authentication working in SDK
- GitHub and Google OAuth working on jeanmemory.com main site
- Supabase Auth infrastructure with OAuth providers configured
- API endpoints for email authentication

### What's Missing
- OAuth flow support in SDK endpoints
- OAuth redirect handling for SDK applications
- Token exchange mechanism for OAuth → SDK tokens
- UI components for OAuth sign-in buttons

## OAuth Flow Architecture

### Standard OAuth Flow (Web)

```
User clicks "Sign in with GitHub" → Redirect to GitHub → User authorizes → 
    ↓                                    ↓                      ↓
SDK OAuth Handler                   GitHub OAuth            GitHub Callback
    ↓                                    ↓                      ↓
Redirect to Jean Memory OAuth  →  Validate & Exchange  →  Return SDK Token
```

### SDK-Specific OAuth Flow

```typescript
// Developer's Application
<JeanAgent apiKey="jean_sk_..." />
         ↓
// Jean Memory OAuth Modal
[Sign in with Email]
[Sign in with GitHub]  → OAuth Popup/Redirect
[Sign in with Google]  → OAuth Popup/Redirect
         ↓
// OAuth Provider Auth
         ↓
// Jean Memory Callback
Exchange OAuth token for SDK session
         ↓
// Return to Developer's App
With authenticated session
```

## Technical Implementation

### OAuth Endpoints for SDK

```yaml
# Initiate OAuth flow
GET /sdk/auth/oauth/authorize
Query Parameters:
  provider: "github" | "google"
  api_key: developer_api_key
  redirect_uri: callback_url
  state: csrf_token
Response:
  redirect_url: OAuth provider authorization URL

# Handle OAuth callback
GET /sdk/auth/oauth/callback
Query Parameters:
  code: authorization_code
  state: csrf_token
Response:
  user_token: SDK session token
  user_id: Jean Memory user ID
  provider: OAuth provider used

# Token exchange endpoint
POST /sdk/auth/oauth/exchange
Body:
  provider_token: OAuth access token
  provider: "github" | "google"
  api_key: developer_api_key
Response:
  user_token: SDK session token
  user_id: Jean Memory user ID
```

### Supabase OAuth Integration

```typescript
// Reuse existing Supabase OAuth configuration
async function handleOAuthSignIn(provider: 'github' | 'google', apiKey: string) {
  const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
  
  // Generate SDK-specific redirect URL
  const redirectUrl = `${API_URL}/sdk/auth/oauth/callback?api_key=${apiKey}`;
  
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider,
    options: {
      redirectTo: redirectUrl,
      scopes: provider === 'github' ? 'read:user user:email' : 'email profile',
      queryParams: {
        access_type: 'offline',
        prompt: 'consent'
      }
    }
  });
  
  if (error) throw error;
  return data.url;  // OAuth authorization URL
}
```

### SDK OAuth Handler

```typescript
// /openmemory/api/app/routers/sdk_oauth.py
from fastapi import APIRouter, HTTPException, Request
from app.auth import supabase_service_client, _get_user_from_api_key
from app.models.sdk_models import OAuthExchangeRequest, AuthResponse

router = APIRouter(prefix="/sdk/auth/oauth", tags=["sdk-oauth"])

@router.get("/authorize")
async def initiate_oauth(
    provider: Literal["github", "google"],
    api_key: str,
    redirect_uri: str,
    state: str,
    db: Session = Depends(get_db)
):
    """Initiate OAuth flow for SDK applications"""
    # Validate developer API key
    developer = await _get_user_from_api_key(api_key, db)
    if not developer:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Store state for CSRF protection
    await cache.set(f"oauth_state:{state}", {
        "api_key": api_key,
        "redirect_uri": redirect_uri,
        "developer_id": developer.id
    }, expire=600)  # 10 minutes
    
    # Generate OAuth URL
    callback_url = f"{API_URL}/sdk/auth/oauth/callback"
    auth_url = supabase_service_client.auth.sign_in_with_oauth({
        "provider": provider,
        "options": {
            "redirect_to": callback_url,
            "state": state
        }
    })
    
    return {"redirect_url": auth_url}

@router.get("/callback")
async def oauth_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """Handle OAuth provider callback"""
    # Validate state
    state_data = await cache.get(f"oauth_state:{state}")
    if not state_data:
        raise HTTPException(status_code=400, detail="Invalid state")
    
    # Exchange code for Supabase session
    session = await supabase_service_client.auth.exchange_code_for_session(code)
    if not session:
        raise HTTPException(status_code=400, detail="Invalid authorization code")
    
    # Create SDK session token
    sdk_token = create_sdk_token(
        user_id=session.user.id,
        api_key=state_data["api_key"],
        provider=session.user.app_metadata.get("provider")
    )
    
    # Redirect back to developer's app
    redirect_uri = state_data["redirect_uri"]
    return RedirectResponse(
        url=f"{redirect_uri}?token={sdk_token}&state={state}",
        status_code=302
    )
```

## Frontend OAuth Components

### React OAuth Component

```typescript
import { useState } from 'react';
import { Button } from '@/components/ui/button';

interface OAuthSignInProps {
  apiKey: string;
  onSuccess: (token: string) => void;
  onError?: (error: Error) => void;
}

export function OAuthSignIn({ apiKey, onSuccess, onError }: OAuthSignInProps) {
  const [loading, setLoading] = useState<string | null>(null);
  
  const handleOAuth = async (provider: 'github' | 'google') => {
    setLoading(provider);
    
    try {
      // Generate state for CSRF protection
      const state = crypto.randomUUID();
      sessionStorage.setItem('oauth_state', state);
      
      // Prepare callback URL
      const redirectUri = `${window.location.origin}/oauth/callback`;
      
      // Get OAuth URL from backend
      const response = await fetch(`${API_URL}/sdk/auth/oauth/authorize?` + 
        new URLSearchParams({
          provider,
          api_key: apiKey,
          redirect_uri: redirectUri,
          state
        })
      );
      
      const { redirect_url } = await response.json();
      
      // Open OAuth popup
      const popup = window.open(
        redirect_url,
        'oauth-popup',
        'width=500,height=600,left=100,top=100'
      );
      
      // Listen for callback
      window.addEventListener('message', function handler(event) {
        if (event.origin !== window.location.origin) return;
        
        if (event.data.type === 'oauth-callback') {
          window.removeEventListener('message', handler);
          popup?.close();
          
          if (event.data.token) {
            onSuccess(event.data.token);
          } else {
            onError?.(new Error(event.data.error || 'OAuth failed'));
          }
          
          setLoading(null);
        }
      });
      
    } catch (error) {
      onError?.(error as Error);
      setLoading(null);
    }
  };
  
  return (
    <div className="space-y-3">
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-background px-2 text-muted-foreground">
            Or continue with
          </span>
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-3">
        <Button
          variant="outline"
          onClick={() => handleOAuth('github')}
          disabled={loading !== null}
          className="w-full"
        >
          {loading === 'github' ? (
            <Spinner className="h-4 w-4" />
          ) : (
            <>
              <GitHubIcon className="mr-2 h-4 w-4" />
              GitHub
            </>
          )}
        </Button>
        
        <Button
          variant="outline"
          onClick={() => handleOAuth('google')}
          disabled={loading !== null}
          className="w-full"
        >
          {loading === 'google' ? (
            <Spinner className="h-4 w-4" />
          ) : (
            <>
              <GoogleIcon className="mr-2 h-4 w-4" />
              Google
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
```

### OAuth Callback Handler

```typescript
// /oauth/callback page in developer's app
export function OAuthCallback() {
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    const state = params.get('state');
    const error = params.get('error');
    
    // Validate state
    const savedState = sessionStorage.getItem('oauth_state');
    if (state !== savedState) {
      window.opener?.postMessage({
        type: 'oauth-callback',
        error: 'Invalid state'
      }, window.location.origin);
      window.close();
      return;
    }
    
    // Send result to opener
    window.opener?.postMessage({
      type: 'oauth-callback',
      token,
      error
    }, window.location.origin);
    
    // Close popup
    window.close();
  }, []);
  
  return <div>Completing sign in...</div>;
}
```

### Updated JeanAgent Component

```typescript
export function JeanAgent({ apiKey, systemPrompt, scope }: JeanAgentProps) {
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [showAuth, setShowAuth] = useState(false);
  
  if (!authToken) {
    return (
      <div className="jean-auth-modal">
        <h2>Sign in to Continue</h2>
        
        {/* Email sign in form */}
        <EmailSignInForm 
          apiKey={apiKey}
          onSuccess={setAuthToken}
        />
        
        {/* OAuth options */}
        <OAuthSignIn
          apiKey={apiKey}
          onSuccess={setAuthToken}
          onError={(error) => console.error('OAuth error:', error)}
        />
      </div>
    );
  }
  
  // Render chat interface with auth token
  return <JeanChat token={authToken} systemPrompt={systemPrompt} />;
}
```

## Python SDK OAuth Support

```python
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

class OAuthHandler:
    """Handle OAuth flow for Python SDK"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.token = None
        
    def authenticate(self, provider: str = 'github') -> str:
        """Open browser for OAuth and capture callback"""
        # Start local server for callback
        server = self._start_callback_server()
        
        # Generate OAuth URL
        state = str(uuid.uuid4())
        callback_url = "http://localhost:8080/callback"
        
        auth_url = f"{API_URL}/sdk/auth/oauth/authorize?" + urllib.parse.urlencode({
            "provider": provider,
            "api_key": self.api_key,
            "redirect_uri": callback_url,
            "state": state
        })
        
        # Open browser
        print(f"Opening browser for {provider} authentication...")
        webbrowser.open(auth_url)
        
        # Wait for callback
        server.handle_request()
        server.server_close()
        
        if not self.token:
            raise Exception("OAuth authentication failed")
            
        return self.token
    
    def _start_callback_server(self):
        """Start local server to receive OAuth callback"""
        parent = self
        
        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                # Parse query parameters
                query = urllib.parse.urlparse(self.path).query
                params = urllib.parse.parse_qs(query)
                
                if 'token' in params:
                    parent.token = params['token'][0]
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b"""
                        <html><body>
                        <h1>Authentication successful!</h1>
                        <p>You can close this window and return to your application.</p>
                        <script>window.close();</script>
                        </body></html>
                    """)
                else:
                    self.send_response(400)
                    self.end_headers()
                    
            def log_message(self, format, *args):
                pass  # Suppress logs
        
        server = HTTPServer(('localhost', 8080), CallbackHandler)
        return server

# Enhanced JeanAgent with OAuth
class JeanAgent:
    def __init__(self, api_key: str, system_prompt: str, scope: str = "all_memories"):
        self.api_key = api_key
        self.system_prompt = system_prompt
        self.scope = scope
        self.token = None
        
    def authenticate(self, method: str = "email", **kwargs):
        """Authenticate using email or OAuth"""
        if method == "email":
            self.token = self._email_auth(kwargs.get("email"), kwargs.get("password"))
        elif method in ["github", "google"]:
            oauth = OAuthHandler(self.api_key)
            self.token = oauth.authenticate(method)
        else:
            raise ValueError(f"Unknown authentication method: {method}")
            
        return self.token
```

## Mobile SDK Considerations

### React Native OAuth

```typescript
import { authorize } from 'react-native-app-auth';

const config = {
  issuer: 'https://api.jeanmemory.com',
  clientId: 'jean-memory-sdk',
  redirectUrl: 'com.jeanmemory.sdk://oauth',
  scopes: ['openid', 'profile', 'email'],
  additionalParameters: {
    api_key: 'jean_sk_...'
  },
  customHeaders: {}
};

// GitHub OAuth config
const githubConfig = {
  ...config,
  serviceConfiguration: {
    authorizationEndpoint: 'https://github.com/login/oauth/authorize',
    tokenEndpoint: 'https://api.jeanmemory.com/sdk/auth/oauth/token'
  }
};

// Google OAuth config  
const googleConfig = {
  ...config,
  serviceConfiguration: {
    authorizationEndpoint: 'https://accounts.google.com/o/oauth2/v2/auth',
    tokenEndpoint: 'https://api.jeanmemory.com/sdk/auth/oauth/token'
  }
};

async function signInWithProvider(provider: 'github' | 'google') {
  const config = provider === 'github' ? githubConfig : googleConfig;
  const result = await authorize(config);
  return result.accessToken;
}
```

## Security Considerations

### CSRF Protection

```typescript
// Generate and validate state parameter
function generateState(): string {
  const array = new Uint8Array(16);
  crypto.getRandomValues(array);
  return btoa(String.fromCharCode.apply(null, array));
}

function validateState(receivedState: string, storedState: string): boolean {
  return receivedState === storedState && receivedState.length > 0;
}
```

### Token Security

```typescript
interface OAuthTokenExchange {
  // Never expose provider tokens to SDK apps
  provider_token: string;  // Internal only
  
  // Issue scoped SDK tokens instead
  sdk_token: string;  // Time-limited, scoped to developer
  
  // Track OAuth provider for audit
  auth_provider: 'email' | 'github' | 'google';
  
  // Link to Jean Memory user
  user_id: string;
}
```

### Redirect URI Validation

```python
def validate_redirect_uri(redirect_uri: str, developer_id: str) -> bool:
    """Ensure redirect URI is registered for developer"""
    allowed_patterns = get_developer_redirect_patterns(developer_id)
    
    parsed = urllib.parse.urlparse(redirect_uri)
    
    # Check against allowed patterns
    for pattern in allowed_patterns:
        if fnmatch.fnmatch(parsed.netloc, pattern):
            return True
            
    # Allow localhost for development
    if parsed.hostname in ['localhost', '127.0.0.1']:
        return True
        
    return False
```

## Implementation Phases

### Phase 1: OAuth Infrastructure
- OAuth authorization endpoints
- Token exchange mechanism
- State management for CSRF
- Basic GitHub integration

### Phase 2: Frontend Components
- React OAuth component
- Callback handling
- Popup/redirect flow
- Error handling

### Phase 3: Provider Integration
- Complete GitHub OAuth
- Add Google OAuth
- Test with real accounts
- Handle edge cases

### Phase 4: Enhanced Features
- Remember auth method preference
- Social account linking
- OAuth scope customization
- Provider-specific features

## Migration Strategy

### Supporting Existing Email Users

```typescript
// Check if user has OAuth linked
async function checkOAuthAvailable(email: string): Promise<{
  github?: boolean;
  google?: boolean;
}> {
  const response = await fetch(`${API_URL}/sdk/auth/oauth/available`, {
    method: 'POST',
    body: JSON.stringify({ email })
  });
  
  return response.json();
}

// Suggest OAuth upgrade
if (authMethod === 'email' && oauthAvailable.github) {
  showNotification('Link your GitHub account for easier sign-in next time!');
}
```

### Account Linking Flow

```typescript
// Allow users to link OAuth to existing email account
async function linkOAuthProvider(
  provider: 'github' | 'google',
  currentToken: string
) {
  const { url } = await initiateLinking(provider, currentToken);
  
  // Complete OAuth flow
  const linkedToken = await completeOAuthFlow(url);
  
  // Update user's auth methods
  await updateAuthMethods(currentToken, provider);
}
```

## Benefits & Impact

### User Benefits
1. **Faster Sign-in**: One-click OAuth vs typing email/password
2. **Familiar Flow**: Use existing GitHub/Google accounts
3. **Better Security**: No password to remember or leak
4. **Account Recovery**: Use provider's recovery options

### Developer Benefits
1. **Higher Conversion**: OAuth reduces sign-up friction
2. **User Trust**: Familiar providers increase confidence
3. **Less Support**: Fewer password reset requests
4. **Rich Profiles**: Get user info from OAuth providers

### Business Impact
1. **Increased Adoption**: Lower barrier to entry
2. **Market Expansion**: Appeal to developer community (GitHub)
3. **Enterprise Ready**: Google Workspace integration
4. **Reduced Churn**: Easier re-authentication

## Success Metrics

1. **OAuth Adoption Rate**: % of new users choosing OAuth
2. **Conversion Improvement**: Sign-up completion rate increase
3. **Time to Auth**: Average seconds to complete sign-in
4. **Provider Distribution**: GitHub vs Google vs Email usage
5. **Account Linking**: % of email users who add OAuth

## Conclusion

Adding OAuth support to Jean Memory SDK removes a significant friction point in the user authentication flow. By leveraging existing Supabase OAuth infrastructure and providing familiar sign-in options, we can improve user experience, increase adoption rates, and position Jean Memory as a modern, developer-friendly platform. The implementation is straightforward given our existing OAuth support on the main site, requiring mainly SDK-specific endpoints and UI components.