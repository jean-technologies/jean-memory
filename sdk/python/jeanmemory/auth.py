"""
Jean Memory Python SDK Authentication
Handles OAuth 2.1 PKCE flow for Python applications
"""

import secrets
import base64
import hashlib
import webbrowser
import urllib.parse
from typing import Optional, Dict
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time

class OAuthHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback"""
    
    def do_GET(self):
        """Handle OAuth callback GET request"""
        parsed_path = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed_path.query)
        
        # Store the authorization code
        if 'code' in params:
            self.server.auth_code = params['code'][0]
            self.server.auth_state = params.get('state', [None])[0]
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("""
            <html>
            <head><title>Jean Memory Authentication</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1>Authentication Successful!</h1>
                <p>You can now close this window and return to your application.</p>
                <script>
                    setTimeout(() => window.close(), 3000);
                </script>
            </body>
            </html>
            """.encode('utf-8'))
        else:
            # Handle error
            error = params.get('error', ['unknown'])[0]
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f"""
            <html>
            <head><title>Jean Memory Authentication Error</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1>Authentication Failed</h1>
                <p>Error: {error}</p>
                <p>Please try again.</p>
            </body>
            </html>
            """.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Suppress log messages"""
        pass

class JeanMemoryAuth:
    """
    OAuth 2.1 PKCE authentication for Jean Memory
    
    Example:
        auth = JeanMemoryAuth(api_key="jean_sk_...")
        user_info = auth.authenticate()
        print(f"Authenticated as {user_info['email']}")
    """
    
    def __init__(self, api_key: str, oauth_base: Optional[str] = None, redirect_port: int = 8080):
        """
        Initialize authentication
        
        Args:
            api_key: Jean Memory API key
            oauth_base: OAuth server base URL (optional)
            redirect_port: Local port for OAuth callback (default: 8080)
        """
        self.api_key = api_key
        self.oauth_base = oauth_base or "https://jean-memory-api-virginia.onrender.com"
        self.redirect_port = redirect_port
        self.redirect_uri = f"http://localhost:{redirect_port}/callback"
    
    def _generate_pkce_pair(self) -> tuple[str, str]:
        """
        Generate PKCE code verifier and challenge
        
        Returns:
            Tuple of (verifier, challenge)
        """
        # Generate cryptographically random verifier
        verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        
        # Create challenge from verifier
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        return verifier, challenge
    
    def _generate_state(self) -> str:
        """Generate secure random state parameter"""
        return secrets.token_urlsafe(32)
    
    def authenticate(self, timeout: int = 300) -> Dict:
        """
        Perform OAuth 2.1 PKCE authentication flow
        
        Args:
            timeout: Authentication timeout in seconds (default: 300)
            
        Returns:
            Dictionary containing user information and access token
            
        Raises:
            Exception: If authentication fails
        """
        # Generate PKCE parameters
        verifier, challenge = self._generate_pkce_pair()
        state = self._generate_state()
        
        # Build authorization URL
        auth_params = {
            'response_type': 'code',
            'client_id': self.api_key,
            'redirect_uri': self.redirect_uri,
            'scope': 'read write',
            'state': state,
            'code_challenge': challenge,
            'code_challenge_method': 'S256'
        }
        
        auth_url = f"{self.oauth_base}/oauth/authorize?" + urllib.parse.urlencode(auth_params)
        
        # Start local server for callback
        server = HTTPServer(('localhost', self.redirect_port), OAuthHandler)
        server.auth_code = None
        server.auth_state = None
        server.timeout = 1
        
        # Start server in background
        server_thread = threading.Thread(target=self._run_server, args=(server, timeout))
        server_thread.daemon = True
        server_thread.start()
        
        print(f"Opening browser for authentication...")
        print(f"If the browser doesn't open automatically, visit: {auth_url}")
        
        # Open browser
        webbrowser.open(auth_url)
        
        # Wait for callback
        start_time = time.time()
        while server.auth_code is None and (time.time() - start_time) < timeout:
            time.sleep(0.5)
        
        if server.auth_code is None:
            raise Exception("Authentication timeout - no authorization code received")
        
        if server.auth_state != state:
            raise Exception("State mismatch - possible CSRF attack")
        
        # Exchange code for token
        return self._exchange_code_for_token(server.auth_code, verifier)
    
    def _run_server(self, server: HTTPServer, timeout: int):
        """Run the OAuth callback server"""
        start_time = time.time()
        while server.auth_code is None and (time.time() - start_time) < timeout:
            server.handle_request()
    
    def _exchange_code_for_token(self, code: str, verifier: str) -> Dict:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from OAuth callback
            verifier: PKCE code verifier
            
        Returns:
            User information with access token
        """
        import requests
        
        # Token exchange request
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
            'code_verifier': verifier,
            'client_id': self.api_key
        }
        
        token_response = requests.post(
            f"{self.oauth_base}/oauth/token",
            data=token_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        if not token_response.ok:
            raise Exception(f"Token exchange failed: {token_response.text}")
        
        token_info = token_response.json()
        access_token = token_info['access_token']
        
        # Get user information
        user_response = requests.get(
            f"{self.oauth_base}/api/v1/user/me",
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if not user_response.ok:
            raise Exception(f"Failed to get user info: {user_response.text}")
        
        user_info = user_response.json()
        user_info['access_token'] = access_token
        
        return user_info