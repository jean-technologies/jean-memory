// Enhanced Cloudflare Worker with Session Support
// This maintains ALL existing functionality while adding session support

export class McpSession {
  state: any;
  backendUrl: string | null = null;
  clientName: string | null = null;
  userId: string | null = null;
  sessionPath: string | null = null; // NEW: for session support
  sseController: ReadableStreamDefaultController | undefined;
  sessionReady = false;
  keepAliveInterval: number | undefined;

  constructor(state: any) {
    this.state = state;
  }

  cleanupSession() {
    if (this.sseController) {
      try {
        if (this.sseController.desiredSize !== null) {
          this.sseController.close();
        }
      } catch (e) {
        console.log("Stream already closed during cleanup");
      }
      this.sseController = undefined;
    }
    if (this.keepAliveInterval) {
      clearInterval(this.keepAliveInterval);
      this.keepAliveInterval = undefined;
    }
    this.sessionReady = false;
  }

  async fetch(request: Request): Promise<Response> {
    this.backendUrl = request.headers.get("X-Backend-Url");
    this.clientName = request.headers.get("X-Client-Name");
    this.userId = request.headers.get("X-User-Id");
    this.sessionPath = request.headers.get("X-Session-Path"); // NEW: session path

    if (!this.backendUrl || !this.clientName || !this.userId) {
      return new Response("Internal error: Missing backend URL or client identifiers.", { status: 500 });
    }

    const url = new URL(request.url);
    const path = url.pathname;

    if (path === "/sse" && request.method === "GET") {
      return this.handleSseRequest(request);
    } else if (path === "/messages" && request.method === "POST") {
      return this.handlePostMessage(request);
    } else if (path === "/sse" && request.method === "POST") {
      return this.handlePostMessage(request);
    }

    return new Response(`Method ${request.method} not allowed for path ${path}`, { status: 405 });
  }

  async handleSseRequest(request: Request): Promise<Response> {
    if (this.sseController) {
      console.log("Cleaning up existing SSE session before creating new one");
      this.cleanupSession();
    }

    const encoder = new TextEncoder();
    const readable = new ReadableStream({
      start: (controller) => {
        console.log("MCP SSE stream started");
        this.sseController = controller;
        this.sessionReady = true;

        // UPDATED: Use session path if available, otherwise fall back to standard format
        const endpointPath = this.sessionPath || `/mcp/${this.clientName}/messages/${this.userId}`;
        const endpointEvent = `event: endpoint\ndata: ${endpointPath}\n\n`;
        
        controller.enqueue(encoder.encode(endpointEvent));
        console.log("Sent MCP endpoint event with path:", endpointPath);

        this.keepAliveInterval = setInterval(() => {
          if (this.sseController) {
            try {
              const keepAliveComment = ": keep-alive\n\n";
              this.sseController.enqueue(encoder.encode(keepAliveComment));
            } catch (e) {
              console.error("Error sending keep-alive, closing session:", e);
              this.cleanupSession();
            }
          }
        }, 45000) as any;

        request.signal?.addEventListener("abort", () => {
          console.log("SSE stream aborted by client");
          this.cleanupSession();
        });
      },
      cancel: () => {
        console.log("SSE stream cancelled");
        this.cleanupSession();
      }
    });

    return new Response(readable, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Cache-Control",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS"
      }
    });
  }

  async handlePostMessage(request: Request): Promise<Response> {
    if (!this.sessionReady || !this.sseController) {
      return new Response("MCP session not ready", { status: 408 });
    }

    try {
      const messageText = await request.text();
      const message = JSON.parse(messageText);
      const proxyPromise = this.proxyToBackend(messageText, message.id);
      const timerPromise = new Promise((resolve) => setTimeout(() => resolve("timeout"), 1000));
      const winner = await Promise.race([proxyPromise, timerPromise]);

      if (winner === "timeout") {
        console.log(`[${this.userId}] Backend task for ID ${message.id} is slow. Running in background.`);
        this.state.waitUntil(
          proxyPromise.then((backendResponseJson) => {
            this.sendSseResponse(backendResponseJson, message.id);
          }).catch((e) => {
            this.sendSseError(e, message.id);
          })
        );
        return new Response(JSON.stringify({ status: "processing" }), { status: 200 });
      } else {
        console.log(`[${this.userId}] Backend task for ID ${message.id} was fast. Sending response synchronously.`);
        const backendResponseJson = winner as any;
        this.sendSseResponse(backendResponseJson, message.id);
        return new Response(JSON.stringify({ status: "ok" }), { status: 200 });
      }
    } catch (e: any) {
      console.error(`[${this.userId}] Error in handlePostMessage: ${e}`);
      return new Response("Internal Server Error", { status: 500 });
    }
  }

  sendSseResponse(responseJson: any, id: string) {
    if (this.sseController) {
      if (this.clientName === "chatgpt" && (responseJson?.result?.protocolVersion || responseJson?.result?.serverInfo)) {
        console.log(`[${this.userId}] Filtering out initialization message from SSE for ChatGPT client, ID: ${id}`);
        return;
      }
      const encoder = new TextEncoder();
      const sseMessage = `event: message\ndata: ${JSON.stringify(responseJson)}\n\n`;
      this.sseController.enqueue(encoder.encode(sseMessage));
      console.log(`[${this.userId}] Enqueued SSE response for ID: ${id}`);
    } else {
      console.error(`[${this.userId}] SSE Controller not available for ID: ${id}`);
    }
  }

  sendSseError(error: any, id: string) {
    if (this.sseController) {
      const errorResponse = {
        jsonrpc: "2.0",
        id,
        error: { code: -32603, message: `Backend task failed: ${error.message}` }
      };
      const encoder = new TextEncoder();
      const errorSseMessage = `event: message\ndata: ${JSON.stringify(errorResponse)}\n\n`;
      this.sseController.enqueue(encoder.encode(errorSseMessage));
    }
  }

  async proxyToBackend(message: string, requestId: string): Promise<any> {
    // UPDATED: Use session path if available, otherwise use standard path
    const backendPath = this.sessionPath || `/mcp/messages/`;
    const url = `${this.backendUrl}${backendPath}`;
    
    console.log(`Proxying to backend: ${url} for request ID: ${requestId}`);
    const startTime = Date.now();
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      console.error(`Backend request timed out from worker for ID: ${requestId}`);
      controller.abort();
    }, 90000);

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json",
          "X-User-Id": this.userId!,
          "X-Client-Name": this.clientName!
        },
        body: message,
        signal: controller.signal
      });

      const duration = Date.now() - startTime;
      console.log(`Backend responded for ID ${requestId} in ${duration}ms with status ${response.status}`);

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`Backend error for ID ${requestId}: ${response.status} ${errorText}`);
        return { jsonrpc: "2.0", id: requestId, error: { code: response.status, message: "Backend Error", data: errorText } };
      }

      const responseText = await response.text();
      try {
        const jsonResponse = JSON.parse(responseText);
        if (jsonResponse.id !== requestId) {
          jsonResponse.id = requestId;
        }
        return jsonResponse;
      } catch (e: any) {
        console.error(`Failed to parse backend response as JSON for ID ${requestId}. Error:`, e.message);
        return { jsonrpc: "2.0", id: requestId, error: { code: -32002, message: "Backend response is not valid JSON", data: responseText.substring(0, 500) } };
      }
    } catch (error: any) {
      const duration = Date.now() - startTime;
      if (error.name === "AbortError") {
        console.error(`Error proxying to backend: fetch aborted after ${duration}ms for ID ${requestId}.`);
        return { jsonrpc: "2.0", id: requestId, error: { code: -32000, message: "Proxy Timeout", data: `Request to backend timed out after ${duration}ms` } };
      }
      console.error(`Error proxying to backend after ${duration}ms for ID ${requestId}:`, error);
      return { jsonrpc: "2.0", id: requestId, error: { code: -32000, message: "Proxy Error", data: error.message } };
    } finally {
      clearTimeout(timeoutId);
    }
  }
}

// Main worker entry point with enhanced URL parsing
export default {
  async fetch(request: Request, env: any, ctx: any): Promise<Response> {
    const url = new URL(request.url);
    const pathParts = url.pathname.split("/").filter(Boolean);
    let user_id: string;
    let client_name = "claude";
    let endpoint: string;
    let sessionPath: string | null = null; // NEW: for session support

    // ENHANCED URL parsing with backward compatibility
    if (pathParts.length === 4 && pathParts[0] === "mcp" && pathParts[1] === "chorus") {
      // EXISTING: /mcp/chorus/sse/{user_id} or /mcp/chorus/messages/{user_id}
      client_name = "chorus";
      endpoint = pathParts[2];
      user_id = pathParts[3];
      if (endpoint !== "sse" && endpoint !== "messages") {
        return new Response("Invalid Chorus endpoint. Expected /mcp/chorus/sse/{user_id} or /mcp/chorus/messages/{user_id}", { status: 400 });
      }
    } else if (pathParts.length === 4 && pathParts[0] === "mcp" && pathParts[1] === "chatgpt") {
      // EXISTING: /mcp/chatgpt/sse/{user_id} or /mcp/chatgpt/messages/{user_id}
      client_name = "chatgpt";
      endpoint = pathParts[2];
      user_id = pathParts[3];
      if (endpoint !== "sse" && endpoint !== "messages") {
        return new Response("Invalid ChatGPT endpoint. Expected /mcp/chatgpt/sse/{user_id} or /mcp/chatgpt/messages/{user_id}", { status: 400 });
      }
    } else if (pathParts.length === 7 && pathParts[0] === "mcp" && pathParts[2] === "sse" && pathParts[4] === "session") {
      // NEW: Session SSE endpoint - /mcp/{client_name}/sse/{user_id}/session/{session_name}/{agent_id}
      client_name = decodeURIComponent(pathParts[1]);
      endpoint = "sse";
      user_id = pathParts[3];
      const sessionName = pathParts[5];
      const agentId = pathParts[6];
      sessionPath = `/mcp/${client_name}/messages/${user_id}/session/${sessionName}/${agentId}`;
    } else if (pathParts.length === 7 && pathParts[0] === "mcp" && pathParts[2] === "messages" && pathParts[4] === "session") {
      // NEW: Session messages endpoint - /mcp/{client_name}/messages/{user_id}/session/{session_name}/{agent_id}
      client_name = decodeURIComponent(pathParts[1]);
      endpoint = "messages";
      user_id = pathParts[3];
      const sessionName = pathParts[5];
      const agentId = pathParts[6];
      sessionPath = `/mcp/${client_name}/messages/${user_id}/session/${sessionName}/${agentId}`;
    } else if (pathParts.length === 3 && pathParts[0] === "mcp") {
      // EXISTING: /mcp/{user_id}/sse or /mcp/{user_id}/messages
      user_id = pathParts[1];
      endpoint = pathParts[2];
      if (endpoint !== "sse" && endpoint !== "messages") {
        return new Response("Invalid endpoint. Expected /mcp/{user_id}/sse or /mcp/{user_id}/messages", { status: 400 });
      }
    } else if (pathParts.length === 4 && pathParts[0] === "mcp") {
      // EXISTING: /mcp/{client_name}/sse/{user_id} or /mcp/{client_name}/messages/{user_id}
      client_name = decodeURIComponent(pathParts[1]);
      endpoint = pathParts[2];
      user_id = pathParts[3];
      if (endpoint !== "sse" && endpoint !== "messages") {
        return new Response("Invalid endpoint. Expected sse or messages", { status: 400 });
      }
    } else {
      return new Response(
        "Invalid MCP URL format. Expected formats:\n" +
        "- /mcp/chorus/sse/{user_id}\n" +
        "- /mcp/chatgpt/sse/{user_id}\n" +
        "- /mcp/{user_id}/sse\n" +
        "- /mcp/{client_name}/sse/{user_id}\n" +
        "- /mcp/{client_name}/sse/{user_id}/session/{session_name}/{agent_id} (NEW)\n" +
        "- Similar patterns for /messages endpoints", 
        { status: 400 }
      );
    }

    // Create unique session ID (including session path for isolation if present)
    const doId = `${user_id}::${client_name}${sessionPath ? `::${sessionPath}` : ''}`;
    const id = env.MCP_SESSION.idFromName(doId);
    const stub = env.MCP_SESSION.get(id);

    // Prepare request for Durable Object
    let newPath: string;
    if (endpoint === "sse") {
      newPath = "/sse";
    } else {
      newPath = "/messages";
    }

    const newUrl = new URL(request.url);
    newUrl.pathname = newPath;
    const requestWithBackendUrl = new Request(newUrl.toString(), request);
    
    // Set required headers
    requestWithBackendUrl.headers.set("X-Backend-Url", env.BACKEND_URL);
    requestWithBackendUrl.headers.set("X-Client-Name", client_name);
    requestWithBackendUrl.headers.set("X-User-Id", user_id);
    
    // NEW: Pass session path if available
    if (sessionPath) {
      requestWithBackendUrl.headers.set("X-Session-Path", sessionPath);
    }

    return stub.fetch(requestWithBackendUrl);
  }
};