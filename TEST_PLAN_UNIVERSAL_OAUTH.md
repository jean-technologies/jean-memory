# Test Plan: Universal SDK OAuth Flow

**Objective:** To perform an end-to-end test of the new backend-driven OAuth 2.1 flow in a local development environment.

**Success Criteria:** A new or existing user can successfully authenticate via a simulated third-party application, resulting in a valid Jean Memory JWT that is tied to a consistent Supabase user ID.

---

## 1. Prerequisites: Environment Setup

Before you begin, you must configure your local environment with the necessary secrets.

**Action:** Open your `.env` file for the `openmemory/api` service and add/verify the following variables:

```bash
# Your Supabase Project URL
SUPABASE_URL="https://your-project.supabase.co"

# Your Supabase Service Role Key (this is a secret!)
# Found in your Supabase Project -> Settings -> API -> Project API keys
SUPABASE_SERVICE_ROLE_KEY="your-supabase-service-role-key"

# Your Google OAuth Client ID
# Found in your Google Cloud Console -> APIs & Services -> Credentials
GOOGLE_CLIENT_ID="your-google-client-id.apps.googleusercontent.com"

# Your Google OAuth Client Secret
GOOGLE_CLIENT_SECRET="your-google-client-secret"

# The base URL for your local API server
API_BASE_URL="http://localhost:8765" # Or whatever port you use

# A secret for signing JWTs
JWT_SECRET="a-strong-secret-key-for-testing"
```

**Important:** You must also configure your Google OAuth application to accept redirects from your local server. In your Google Cloud Console, add `http://localhost:8765/v1/sdk/oauth/callback` to the list of "Authorized redirect URIs".

---

## 2. Test Execution: Step-by-Step

This test simulates the entire flow, from a third-party app to Google, through our backend, and back to the third-party app. We will use a web browser to manually perform the redirects.

### Step 1: Start the API Server

1.  Navigate to the project root in your terminal.
2.  Ensure you are on the correct branch: `git checkout feature/universal-identity-poc`
3.  Start the API server using the Makefile command: `make dev-api`
4.  The server should now be running on `http://localhost:8765`.

### Step 2: Manually Construct the "Authorize" URL

This URL is what the React SDK would build to start the login process.

1.  **Generate PKCE Values:** For this test, you can use an online generator or a simple script. Let's use these pre-generated values for simplicity:
    *   `code_verifier`: `a-very-secret-and-random-string-for-pkce`
    *   `code_challenge`: `m26s-B_2-Y2g-Tt-01-D2-83-7_4-1-6-Q-2-K-9-J-6` (This is the S256 hash of the verifier)

2.  **Construct the URL:** Open a text editor and build the following URL. This simulates a developer's app running on `http://localhost:3000`.

    ```
    http://localhost:8765/v1/sdk/oauth/authorize?response_type=code&client_id=test_client_123&redirect_uri=http://localhost:3000/callback&state=random_state_xyz&code_challenge=m26s-B_2-Y2g-Tt-01-D2-83-7_4-1-6-Q-2-K-9-J-6&code_challenge_method=S256
    ```

### Step 3: Initiate the Flow

1.  **Paste and Go:** Copy the complete URL from the previous step and paste it into your web browser's address bar. Press Enter.
2.  **Expected Result:** Your browser should be immediately redirected to a Google "Sign In" page. If not, check your API server logs for errors.

### Step 4: Authenticate with Google

1.  **Sign In:** Complete the Google login flow.
2.  **Expected Result:** After you successfully log in, Google will redirect your browser back to our API at `http://localhost:8765/v1/sdk/oauth/callback`. This happens very quickly.

### Step 5: Verify the Redirect Back to the "Client"

1.  **Check the Address Bar:** After the brief stop at our callback, your browser should be redirected again. The URL in your address bar should now be:
    ```
    http://localhost:3000/callback?code=SOME_LONG_RANDOM_CODE&state=random_state_xyz
    ```
    This simulates the user being returned to the developer's application with a temporary authorization code.

### Step 6: Manually Exchange the Code for a JWT

This is the final step, where the SDK would exchange the temporary code for a real Jean Memory token. We will simulate this using a `curl` command.

1.  **Open a new terminal.**
2.  **Copy the `code`** from the browser address bar in the previous step.
3.  **Construct the `curl` command:**

    ```bash
    curl -X POST http://localhost:8765/v1/sdk/oauth/token \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=authorization_code" \
    -d "code=PASTE_THE_CODE_FROM_YOUR_BROWSER_HERE" \
    -d "redirect_uri=http://localhost:3000/callback" \
    -d "client_id=test_client_123" \
    -d "code_verifier=a-very-secret-and-random-string-for-pkce"
    ```

4.  **Execute the command.**

---

## 3. Verification

### Step 1: Check the `curl` Output

-   **Expected Result:** You should receive a JSON response containing an `access_token`.
    ```json
    {"access_token":"eyJhbGciOi...","token_type":"bearer"}
    ```

### Step 2: Decode the JWT

1.  Copy the long `access_token` string.
2.  Go to a JWT decoder website like [jwt.io](https://jwt.io).
3.  Paste the token into the "Encoded" field.
4.  **Expected Result:** The "Payload" section should show the decoded token. Verify that the `sub` (subject) claim contains a UUID. This is the user's permanent, universal Supabase ID.

### Step 3: Verify the User in Supabase

1.  Go to your Supabase project dashboard.
2.  Navigate to "Authentication" -> "Users".
3.  **Expected Result:** You should see a new user listed with the email you used to log in via Google. The `User UID` column should match the `sub` claim from your JWT perfectly.

---

If all these steps pass, the entire flow is working correctly. You have successfully proven that the new system can authenticate a user and provision them with a consistent, universal identity in your Supabase backend.
