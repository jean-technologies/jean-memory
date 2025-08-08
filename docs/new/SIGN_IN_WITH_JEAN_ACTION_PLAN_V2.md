# "Sign in with Jean Memory" Action Plan (V2)

## 1. Vision & Goal

**Our North Star:** To be the first and best universal memory layer for AI, enabling any application to offer personalized experiences through a simple "Sign in with Jean Memory" button.

**The "5-Minute/5-Line" Integration:** A developer should be able to add meaningful, persistent, cross-application memory to their product in under 5 minutes, with just a few lines of code.

## 2. The Plan: A Clean, Step-by-Step Approach

### Phase 1: Build the Foundation (New Feature Branch)

This phase is about re-building the core components of the "Sign in with Jean" feature in a new, clean feature branch.

#### 1.1. Create a New Feature Branch
*   **Action:** Create a new feature branch called `feature/sdk-oauth-v2`.
*   **Owner:** Gemini

#### 1.2. Create the `useJean` Hook
*   **Action:** Create a new `sdk/react/useJean.tsx` file.
*   **Details:** This hook will be the single, unified way to interact with the Jean Memory API. It will be MCP-first and will not handle authentication directly, but will be initialized with a user object.
*   **Owner:** Gemini

#### 1.3. Create the `SignInWithJean` Component
*   **Action:** Create a new `sdk/react/components/SignInWithJean.tsx` file.
*   **Details:** This will be a beautiful, production-ready React component that handles the entire OAuth 2.1 flow. It will be highly customizable to fit any application's branding.
*   **Owner:** Gemini

#### 1.4. Create the `JeanChat` Component
*   **Action:** Create a new `sdk/react/components/JeanChat.tsx` file.
*   **Details:** This will be a simple, production-ready chat component for interacting with the Jean Memory agent.
*   **Owner:** Gemini

#### 1.5. Update the React SDK Entry Point
*   **Action:** Update `sdk/react/index.ts`.
*   **Details:** This file will be updated to export the new `useJean` hook and the `SignInWithJean` and `JeanChat` components.
*   **Owner:** Gemini

### Phase 2: Test Against the Deployed Dev Server

This phase is about testing our new SDK against your deployed dev server.

#### 2.1. Create a New Test Application
*   **Action:** Create a new, separate test repository and build a simple Next.js application.
*   **Details:** This will allow us to test the developer experience from end to end.
*   **Owner:** Gemini

#### 2.2. Configure the Test Application
*   **Action:** Configure the test application to use the new `jeanmemory-react` SDK and to point to your deployed dev server.
*   **Details:** We will use the dev server URL and a valid API key from the dev environment.
*   **Owner:** Gemini

#### 2.3. Test the Full Flow
*   **Action:** Test the full, end-to-end authentication and chat flow.
*   **Details:** This will involve clicking the "Sign in with Jean" button, authenticating with the dev server, and then sending a message through the `JeanChat` component.
*   **Owner:** Gemini

### Phase 3: Refine and Deploy

This phase is about refining the SDK and deploying it to production.

#### 3.1. Refine the SDK
*   **Action:** Based on the results of our testing, we will refine the SDK to ensure that it is as simple and easy to use as possible.
*   **Owner:** Gemini

#### 3.2. Update the Documentation
*   **Action:** We will update the documentation to reflect the new, streamlined authentication flow.
*   **Owner:** Gemini

#### 3.3. Merge to `dev` and Deploy
*   **Action:** We will merge the `feature/sdk-oauth-v2` branch into `dev` and deploy to the development server.
*   **Owner:** Gemini

This is a clean, simple, and achievable plan. It will allow us to build the "Sign in with Jean" feature in a controlled and predictable way, and it will ensure that we have a solid foundation for future development.

I am ready to begin.
