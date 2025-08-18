# OAuth Developer Handoff: Building the Universal Identity Service

**To:** Lead Developer
**From:** Gemini
**Date:** August 17, 2025
**Re:** Implementation Guide for the New Backend-Driven OAuth 2.1 Flow

---

## 1. Objective

This document outlines the technical steps required to build our new, centralized OAuth service. This will replace the current `oauth-bridge.html` and provide a more robust, secure, and extensible authentication solution for all clients.

We are moving from a client-side, bridge-based Supabase flow to a backend-controlled, standard OAuth 2.1 PKCE flow.

## 2. Foundational Code (Already Implemented)

I have already laid the groundwork in the `feature/universal-identity-poc` branch.

-   **`openmemory/api/app/settings.py`**:
    -   A new `SUPABASE_SERVICE_ROLE_KEY` has been added. This **must** be populated in your `.env` file with the "service_role key" from your Supabase project's API settings. It is a secret.

-   **`openmemory/api/app/auth.py`**:
    -   A new **`supabase_admin_client`** has been created. It uses the service role key to perform administrative actions.
    -   A new function, **`get_or_create_user_from_provider`**, is now available. This is the core of our universal identity system. It takes an email from an OAuth provider (like Google) and either finds the existing user in Supabase or creates a new one, returning the definitive user object.

## 3. Implementation Steps

Your primary task is to build a new FastAPI router that orchestrates the OAuth flow using these foundational pieces.

### Step 1: Create the New OAuth Router

1.  Create a new file: `openmemory/api/app/routers/sdk_oauth.py`.
2.  In this file, create a new `APIRouter`.
3.  This router will house the three main endpoints for our OAuth flow.

### Step 2: Build the `/authorize` Endpoint

This endpoint starts the login process.

-   **Path:** `GET /v1/oauth/authorize`
-   **Parameters:**
    -   `response_type`: Must be `code`.
    -   `client_id`: The client's API key.
    -   `redirect_uri`: The URL to send the user back to after success.
    -   `scope`: e.g., `openid profile email`.
    -   `state`: A random string for CSRF protection.
    -   `code_challenge`: The PKCE code challenge.
    -   `code_challenge_method`: Must be `S256`.
-   **Logic:**
    1.  Validate the `client_id` and `redirect_uri` against a list of allowed clients.
    2.  Store the `redirect_uri`, `state`, and `code_challenge` in a secure, temporary location (e.g., a database table or a Redis cache keyed by the `state` parameter).
    3.  Construct the URL to redirect the user to the OAuth provider (e.g., Google's authorization endpoint).
    4.  Return a `RedirectResponse` to send the user's browser to Google.

### Step 3: Build the `/callback` Endpoint

This endpoint handles the user's return from the provider.

-   **Path:** `GET /v1/oauth/callback`
-   **Logic:**
    1.  Receive the `code` and `state` from Google as query parameters.
    2.  Retrieve the original `redirect_uri` and `code_challenge` from your temporary storage using the `state` value.
    3.  **Exchange the `code` for an access token** by making a secure, server-to-server `POST` request to Google's token endpoint. You will need your Google OAuth client ID and secret for this.
    4.  With the access token, **fetch the user's profile** (especially their verified email) from Google's userinfo endpoint.
    5.  Call the **`get_or_create_user_from_provider`** function with the user's email to get their universal Jean Memory `user_id`.
    6.  **Generate a new authorization code** (a short-lived, random string).
    7.  Store this new code along with the Jean Memory `user_id` and the original `redirect_uri`.
    8.  Return a `RedirectResponse` to send the user to the original `redirect_uri` with the new authorization `code` and the original `state` attached.

### Step 4: Build the `/token` Endpoint

This is the final, secure step where the client application exchanges the code for a real Jean Memory JWT.

-   **Path:** `POST /v1/oauth/token`
-   **Body:**
    -   `grant_type`: Must be `authorization_code`.
    -   `code`: The authorization code from the previous step.
    -   `redirect_uri`: The original redirect URI.
    -   `client_id`: The client's API key.
    -   `code_verifier`: The original PKCE code verifier.
-   **Logic:**
    1.  Retrieve the stored `user_id` and `redirect_uri` using the `code`.
    2.  Verify that the `redirect_uri` and `client_id` in the request match what was originally stored.
    3.  **Validate the PKCE `code_verifier`** by hashing it and comparing it to the `code_challenge` stored in Step 2.
    4.  If everything is valid, **generate a Jean Memory JWT**.
        -   The `sub` (subject) claim **must** be the universal Jean Memory `user_id`.
        -   Include other relevant claims like `email`, `scope`, etc.
    5.  Return the JWT in a JSON response.

## 4. Next Steps

-   **UI Development:** A simple, hosted HTML page will need to be created and served by the `/authorize` endpoint to present the login options.
-   **SDK Update:** The React SDK will need to be updated to point to this new flow.

This architecture is a standard, secure, and robust implementation of OAuth 2.1. It gives us full control over the user experience and sets us up for future growth.
