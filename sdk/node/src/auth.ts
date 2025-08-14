/**
 * Jean Memory Node.js SDK Authentication
 * OAuth 2.1 PKCE authentication for Node.js applications
 */

import { createHash, randomBytes } from 'crypto';
import { createServer, Server } from 'http';
import { URL } from 'url';

interface AuthConfig {
  apiKey: string;
  oauthBase?: string;
  redirectPort?: number;
}

interface PKCEPair {
  verifier: string;
  challenge: string;
}

interface AuthResult {
  user_id: string;
  email: string;
  name?: string;
  access_token: string;
  created_at: string;
}

export class JeanMemoryAuth {
  private apiKey: string;
  private oauthBase: string;
  private redirectPort: number;
  private redirectUri: string;

  constructor(config: AuthConfig) {
    this.apiKey = config.apiKey;
    this.oauthBase = config.oauthBase || 'https://jean-memory-api-virginia.onrender.com';
    this.redirectPort = config.redirectPort || 8080;
    this.redirectUri = `http://localhost:${this.redirectPort}/callback`;
  }

  /**
   * Generate PKCE code verifier and challenge
   */
  private generatePKCEPair(): PKCEPair {
    // Generate cryptographically secure random verifier
    const verifier = randomBytes(32)
      .toString('base64url')
      .slice(0, 43); // Remove padding

    // Create challenge from verifier using SHA256
    const challenge = createHash('sha256')
      .update(verifier)
      .digest('base64url');

    return { verifier, challenge };
  }

  /**
   * Generate secure random state parameter
   */
  private generateState(): string {
    return randomBytes(32).toString('base64url');
  }

  /**
   * Create authorization URL for OAuth flow
   */
  createAuthorizationUrl(): { url: string; state: string; verifier: string } {
    const { verifier, challenge } = this.generatePKCEPair();
    const state = this.generateState();

    const authParams = new URLSearchParams({
      response_type: 'code',
      client_id: this.apiKey,
      redirect_uri: this.redirectUri,
      scope: 'read write',
      state,
      code_challenge: challenge,
      code_challenge_method: 'S256'
    });

    const authUrl = `${this.oauthBase}/oauth/authorize?${authParams.toString()}`;

    return { url: authUrl, state, verifier };
  }

  /**
   * Exchange authorization code for access token
   */
  async exchangeCodeForToken(code: string, verifier: string): Promise<AuthResult> {
    const tokenData = new URLSearchParams({
      grant_type: 'authorization_code',
      code,
      redirect_uri: this.redirectUri,
      code_verifier: verifier,
      client_id: this.apiKey
    });

    const tokenResponse = await fetch(`${this.oauthBase}/oauth/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: tokenData.toString()
    });

    if (!tokenResponse.ok) {
      const errorText = await tokenResponse.text();
      throw new Error(`Token exchange failed: ${errorText}`);
    }

    const tokenInfo = await tokenResponse.json() as any;
    const accessToken = tokenInfo.access_token;

    // Get user information
    const userResponse = await fetch(`${this.oauthBase}/api/v1/user/me`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });

    if (!userResponse.ok) {
      const errorText = await userResponse.text();
      throw new Error(`Failed to get user info: ${errorText}`);
    }

    const userInfo = await userResponse.json() as any;
    
    return {
      user_id: userInfo.user_id,
      email: userInfo.email,
      name: userInfo.name,
      created_at: userInfo.created_at,
      access_token: accessToken
    };
  }

  /**
   * Start local server for OAuth callback
   */
  private createCallbackServer(): Promise<{
    server: Server;
    getAuthCode: () => Promise<{ code: string; state: string }>;
  }> {
    return new Promise((resolve, reject) => {
      let authCode: string | null = null;
      let authState: string | null = null;
      let authError: string | null = null;

      const server = createServer((req, res) => {
        if (!req.url) {
          res.writeHead(400);
          res.end('Bad request');
          return;
        }

        const parsedUrl = new URL(req.url, `http://localhost:${this.redirectPort}`);
        
        if (parsedUrl.pathname === '/callback') {
          const code = parsedUrl.searchParams.get('code');
          const state = parsedUrl.searchParams.get('state');
          const error = parsedUrl.searchParams.get('error');

          if (error) {
            authError = error;
            res.writeHead(400, { 'Content-Type': 'text/html' });
            res.end(`
              <html>
                <head><title>Jean Memory Authentication Error</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                  <h1>Authentication Failed</h1>
                  <p>Error: ${error}</p>
                  <p>Please try again.</p>
                </body>
              </html>
            `);
          } else if (code && state) {
            authCode = code;
            authState = state;
            res.writeHead(200, { 'Content-Type': 'text/html' });
            res.end(`
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
            `);
          } else {
            res.writeHead(400, { 'Content-Type': 'text/html' });
            res.end(`
              <html>
                <head><title>Jean Memory Authentication Error</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                  <h1>Authentication Failed</h1>
                  <p>Missing authorization code or state parameter.</p>
                </body>
              </html>
            `);
          }
        } else {
          res.writeHead(404);
          res.end('Not found');
        }
      });

      server.listen(this.redirectPort, 'localhost', () => {
        const getAuthCode = (): Promise<{ code: string; state: string }> => {
          return new Promise((resolveCode, rejectCode) => {
            const checkForCode = () => {
              if (authError) {
                rejectCode(new Error(`OAuth error: ${authError}`));
              } else if (authCode && authState) {
                resolveCode({ code: authCode, state: authState });
              } else {
                setTimeout(checkForCode, 100);
              }
            };
            checkForCode();
          });
        };

        resolve({ server, getAuthCode });
      });

      server.on('error', (err) => {
        reject(err);
      });
    });
  }

  /**
   * Perform complete OAuth 2.1 PKCE authentication flow
   * This method requires user interaction (opening browser)
   */
  async authenticate(timeout: number = 300000): Promise<AuthResult> {
    // Start callback server
    const { server, getAuthCode } = await this.createCallbackServer();

    try {
      // Generate auth URL
      const { url: authUrl, state: expectedState, verifier } = this.createAuthorizationUrl();

      console.log('Opening browser for authentication...');
      console.log(`If the browser doesn't open automatically, visit: ${authUrl}`);

      // In a real implementation, you might want to open the browser automatically
      // For now, we'll log the URL for manual opening
      
      // Wait for callback with timeout
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => reject(new Error('Authentication timeout')), timeout);
      });

      const { code, state } = await Promise.race([
        getAuthCode(),
        timeoutPromise
      ]);

      // Verify state to prevent CSRF attacks
      if (state !== expectedState) {
        throw new Error('State mismatch - possible CSRF attack');
      }

      // Exchange code for token
      return await this.exchangeCodeForToken(code, verifier);

    } finally {
      // Clean up server
      server.close();
    }
  }

  /**
   * Validate an existing access token
   */
  async validateToken(accessToken: string): Promise<boolean> {
    try {
      const response = await fetch(`${this.oauthBase}/api/v1/user/me`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });
      return response.ok;
    } catch {
      return false;
    }
  }

  /**
   * Get user info from access token
   */
  async getUserInfo(accessToken: string): Promise<AuthResult> {
    const response = await fetch(`${this.oauthBase}/api/v1/user/me`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to get user info: ${errorText}`);
    }

    const userInfo = await response.json() as any;
    
    return {
      user_id: userInfo.user_id,
      email: userInfo.email,
      name: userInfo.name,
      created_at: userInfo.created_at,
      access_token: accessToken
    };
  }
}