# Jean Memory SDK: Architectural Overview

This document outlines the architecture of the Jean Memory SDK, focusing on the end-to-end user authentication and service connection flow.

## Core Philosophy

The SDK is designed around a "Connection" model. Jean Memory serves as the primary identity provider. Users first authenticate with their Jean Memory account and then can "connect" other third-party services (like Notion, Substack, etc.) to their account as "memory sources."

This approach provides a secure and scalable foundation, leveraging the existing robust authentication system while allowing for easy expansion to new services.

## The Two Stages of User Interaction

The user journey is broken down into two distinct stages:

1.  **Primary Authentication**: Establishing the user's core identity with Jean Memory.
2.  **Connecting a Memory Source**: Linking an external service to the user's authenticated Jean Memory account.

---

### Stage 1: Primary Authentication with `SignInWithJean`

This stage is handled entirely by the existing `<SignInWithJean />` React component.

**Key Characteristics:**

*   **Trigger**: A developer integrates the `<SignInWithJean />` button into their application.
*   **Mechanism**: It uses a standard OAuth 2.1 flow with PKCE (Proof Key for Code Exchange) for maximum security.
*   **User Experience**: The user is redirected to the Jean Memory website to log in and grant consent to the third-party application.
*   **Outcome**: On success, the component's `onSuccess` callback is fired, returning an `agent` object. This object contains the user's session information, including a JWT access token, and is the key to all subsequent interactions with the Jean Memory API.

**Flow:**
1.  User clicks the `SignInWithJean` button in a third-party app.
2.  The SDK redirects the user to the Jean Memory authorization endpoint (`/oauth/authorize`).
3.  User signs in and grants consent on the Jean Memory website.
4.  Jean Memory redirects the user back to the third-party app with an authorization code.
5.  The SDK exchanges this code for an access token via the `/oauth/token` endpoint.
6.  The `onSuccess` callback provides the `agent` object to the developer's application.

---

### Stage 2: Connecting Memory Sources with `agent.connect()`

Once a user is authenticated (i.e., the app has an `agent` object), they can connect external memory sources.

**Key Characteristics:**

*   **Trigger**: The developer calls the `agent.connect('serviceName')` method. For example, `agent.connect('notion')`.
*   **Mechanism**: This function opens a secure popup window to initiate a service-specific OAuth flow. The user's Jean Memory JWT is passed in the `Authorization` header to link the external account to the correct user.
*   **User Experience**: The user authenticates with the external service (e.g., Notion) in the popup and grants access. The popup closes automatically on completion.
*   **Outcome**: The `connect()` method returns a promise that resolves upon successful connection or rejects if the user cancels or an error occurs.

**Flow:**
1.  The developer's app calls `agent.connect('notion')`.
2.  The SDK opens a popup window pointing to the Jean Memory API's integration endpoint (e.g., `/api/v1/integrations/notion/auth`).
3.  The API endpoint validates the user's Jean Memory JWT and then redirects the user within the popup to Notion's authorization page.
4.  The user signs into Notion and grants permission.
5.  Notion redirects the user back to the Jean Memory API's callback endpoint (`/api/v1/integrations/notion/callback`).
6.  The Jean Memory backend exchanges the received authorization code for a Notion access token.
7.  The Notion token is securely encrypted and stored in the database, associated with the Jean Memory user.
8.  The backend serves a simple HTML page to the popup with a JavaScript snippet that calls `window.opener.postMessage(...)` and then `window.close()`.
9.  The SDK, listening for this message, resolves the `connect()` promise.
10. The developer's app can now update its UI to show that Notion is connected.

## Scalability

This architecture is highly scalable. To add a new memory source (e.g., "Slack"):

1.  **Backend**: Add new `/api/v1/integrations/slack/auth` and `/api/v1/integrations/slack/callback` endpoints.
2.  **Frontend**: No SDK changes are needed. The developer can simply call `agent.connect('slack')`.

This keeps the SDK lean and ensures that the logic for handling each external service is neatly encapsulated on the backend where it belongs.
