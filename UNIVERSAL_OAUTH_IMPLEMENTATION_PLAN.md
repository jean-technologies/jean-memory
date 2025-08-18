# Universal OAuth Implementation Plan

**Objective:** To create a single, robust, backend-driven authentication service that provides a universal identity for all Jean Memory users, regardless of the entry point (Web App, SDK, Claude MCP, etc.).

---

## 1. Core Principles

-   **Single Source of Truth:** The Supabase `auth.users` table is the definitive record for all user identities.
-   **Backend-Controlled:** All authentication logic, user creation, and token generation will be handled by our secure backend API. This eliminates the complexities and security risks of the client-side bridge.
-   **Consistent User Experience:** The authentication UI will be hosted by our service, presenting a consistent "Sign in with Jean" experience across all integrated applications.
-   **Extensible:** The architecture will be designed to easily accommodate future integrations, such as "Connect your Notion" steps in the onboarding flow.

---

## 2. Authentication Flow Architecture

This flow replaces the bridge and centralizes logic on our backend.

1.  **Initiation (The "Client"):**
    -   A third-party app (using the React SDK, Claude, etc.) needs to authenticate a user.
    -   It redirects the user to our new, centralized endpoint: `https://api.jeanmemory.com/v1/oauth/authorize`.
    -   **Crucially, it includes a `redirect_uri` parameter**, telling us where to send the user back after the flow is complete.

2.  **Authentication UI (Our Service):**
    -   The `/v1/oauth/authorize` endpoint displays a hosted login page.
    -   This page will look identical to your main website's login, offering "Continue with Google," "Continue with GitHub," etc.
    -   This visual consistency assures the user they are signing into Jean Memory.

3.  **Provider Authentication (e.g., Google):**
    -   When the user clicks "Continue with Google," our backend initiates the standard OAuth 2.1 PKCE flow with Google.
    -   The user authenticates with Google and grants permission.

4.  **Callback and Identity Management (Our Backend):**
    -   Google redirects the user back to our backend at a `/v1/oauth/callback` endpoint.
    -   Our backend receives the user's profile from Google, including their **verified email address**.
    -   It then uses the **Supabase Admin Client** (which we've already set up) to perform the critical identity logic:
        -   It queries Supabase: "Does a user with this email exist?"
        -   **If YES,** it retrieves the existing Supabase `user_id`.
        -   **If NO,** it creates a new user in Supabase and gets the new `user_id`.

5.  **Token Generation (Our Backend):**
    -   With the definitive Supabase `user_id` in hand, our backend generates a secure Jean Memory JWT.
    -   This JWT contains the `user_id` in the `sub` claim, ensuring a universal identity.

6.  **Future Integrations (Optional Step):**
    -   *This is where your vision for Notion, etc., fits in.*
    -   Before the final redirect, we can show an intermediate page: "Connect your sources," allowing the user to link other accounts.

7.  **Final Redirect (Back to the Client):**
    -   Our backend retrieves the `redirect_uri` that was provided in Step 1.
    -   It redirects the user back to that URI, appending the newly generated Jean Memory JWT as a query parameter (e.g., `https://customer.app/callback?token=...`).
    -   The client application now has a secure token and a fully authenticated user with a consistent Jean Memory identity.

---

## 3. Implementation Phases

This project will be broken down into manageable phases.

### Phase 1: Foundational Backend (In Progress)

-   [x] **Introduce `SUPABASE_SERVICE_ROLE_KEY`:** Add the necessary secret to our backend configuration.
-   [x] **Create Supabase Admin Client:** Establish a secure, admin-level connection to Supabase.
-   [x] **Implement User Provisioning Logic:** Build the `get_or_create_user_from_provider` function to handle universal identity.
-   [ ] **Build Core OAuth Endpoints:** Create the new router and skeleton endpoints (`/authorize`, `/callback`, `/token`).

### Phase 2: Provider Integration (Google)

-   [ ] **Implement Google OAuth Flow:** Wire up the backend to handle the full redirect and code exchange with Google.
-   [ ] **Connect Identity Logic:** Integrate the `get_or_create_user_from_provider` function into the `/callback` endpoint.
-   [ ] **Implement JWT Generation:** Create and sign a valid Jean Memory JWT.

### Phase 3: Frontend UI

-   [ ] **Create Hosted Login Page:** Build the HTML/CSS for the page served by the `/authorize` endpoint. It should mirror the existing web app's login page.
-   [ ] **(Optional) Create Integration Step Page:** Build the UI for post-auth steps like connecting Notion.

### Phase 4: SDK and Client Migration

-   [ ] **Update React SDK:** Modify the `SignInWithJean` component to redirect to the new `/v1/oauth/authorize` endpoint instead of Supabase.
-   [ ] **Update Claude MCP:** Reconfigure the Claude OAuth flow to use the new endpoints.
-   [ ] **Deprecate the Bridge:** Once all clients are migrated, the `oauth-bridge.html` can be removed.

---

## 4. Fallback Strategy

-   **Branching:** The `feature/universal-identity-poc` branch contains all work on this new system. The `main` branch (or previous working branch) still has the hardened bridge implementation.
-   **Reverting:** If this new implementation proves too difficult or time-consuming, we can safely switch back to the bridge branch and deploy it, knowing it's been improved.
-   **Commit `dcd0c9ef4ac3`:** If both the bridge and the new implementation fail, we have the option to revert to the code at this commit and rebuild the original, simpler PKCE flow from there, as it was known to be working.
