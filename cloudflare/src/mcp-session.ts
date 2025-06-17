// cloudflare/src/mcp-session.ts

interface JSONRPCRequest {
    jsonrpc: "2.0";
    id: number | string | null;
    method: string;
    params?: any;
}

interface JSONRPCResponse {
    jsonrpc: "2.0";
    id: number | string | null;
    result?: any;
    error?: {
        code: number;
        message: string;
        data?: any;
    };
}

export class McpSession implements DurableObject {
	state: DurableObjectState;
	backendUrl!: string;
	clientName!: string;
	userId!: string;
    sseController?: ReadableStreamDefaultController;
    sessionReady: boolean = false;
    keepAliveInterval?: any;

	constructor(state: DurableObjectState) {
		this.state = state;
	}

    private cleanupSession() {
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
		this.backendUrl = request.headers.get('X-Backend-Url')!;
		this.clientName = request.headers.get('X-Client-Name')!;
		this.userId = request.headers.get('X-User-Id')!;

		if (!this.backendUrl || !this.clientName || !this.userId) {
			return new Response('Internal error: Missing backend URL or client identifiers.', { status: 500 });
		}

		const url = new URL(request.url);
		const path = url.pathname;

        if (path === '/sse' && request.method === 'GET') {
            return this.handleSseRequest(request);
        } else if (path === '/messages' && request.method === 'POST') {
            return this.handlePostMessage(request);
        } else if (path === '/sse' && request.method === 'POST') {
            return this.handlePostMessage(request);
        }

        return new Response(`Method ${request.method} not allowed for path ${path}`, { status: 405 });
	}

    async handleSseRequest(request: Request): Promise<Response> {
        // Clean up any existing session
        if (this.sseController) {
            console.log("Cleaning up existing SSE session before creating new one");
            this.cleanupSession();
        }

        const encoder = new TextEncoder();

        // Create SSE stream following official MCP SSE pattern
        const readable = new ReadableStream({
            start: (controller) => {
                console.log("MCP SSE stream started");
                this.sseController = controller;
                this.sessionReady = true;

                // Send endpoint event (official MCP SSE protocol requirement)
                // The endpoint should match our routing pattern: /mcp/{client_name}/messages/{user_id}
                const endpointEvent = `event: endpoint\ndata: /mcp/${this.clientName}/messages/${this.userId}\n\n`;
                controller.enqueue(encoder.encode(endpointEvent));
                console.log("Sent MCP endpoint event");

                // Start sending keep-alive pings every 45 seconds
                this.keepAliveInterval = setInterval(() => {
                    if (this.sseController) {
                        try {
                            const keepAliveComment = ': keep-alive\n\n';
                            this.sseController.enqueue(encoder.encode(keepAliveComment));
                        } catch(e) {
                            console.error("Error sending keep-alive, closing session:", e);
                            this.cleanupSession();
                        }
                    }
                }, 45000); // Reduced frequency to 45 seconds for better performance

                // Handle client disconnection
                request.signal?.addEventListener('abort', () => {
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
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Cache-Control',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            },
        });
    }

    async handlePostMessage(request: Request): Promise<Response> {
        if (!this.sessionReady || !this.sseController) {
            return new Response("MCP session not ready", { status: 408 });
        }

        try {
            const messageText = await request.text();
            const message = JSON.parse(messageText) as JSONRPCRequest;

            // Handle ChatGPT tools/list requests directly in the worker
            if (message.method === "tools/list" && this.clientName === "chatgpt") {
                console.log("Handling ChatGPT tools/list request directly in worker");
                const chatgptToolsResponse: JSONRPCResponse = {
                    jsonrpc: "2.0",
                    id: message.id,
                    result: {
                        tools: [
                            {
                                name: "search",
                                description: "Searches for resources using the provided query string and returns matching results.",
                                inputSchema: {
                                    type: "object",
                                    properties: {
                                        query: { type: "string", description: "Search query." }
                                    },
                                    required: ["query"]
                                }
                            },
                            {
                                name: "fetch",
                                description: "Retrieves detailed content for a specific resource identified by the given ID.",
                                inputSchema: {
                                    type: "object",
                                    properties: {
                                        id: { type: "string", description: "ID of the resource to fetch." }
                                    },
                                    required: ["id"]
                                }
                            }
                        ]
                    }
                };
                
                this.sendSseResponse(chatgptToolsResponse, message.id);
                return new Response(JSON.stringify({ status: "ok" }), { status: 200 });
            }

            // Handle ChatGPT tools/call requests by mapping to backend tools
            if (message.method === "tools/call" && this.clientName === "chatgpt") {
                const toolName = message.params?.name;
                const toolArgs = message.params?.arguments || {};
                
                if (toolName === "search") {
                    console.log("Mapping ChatGPT search to ask_memory");
                    // Map ChatGPT search to ask_memory for better results
                    const mappedMessage = {
                        ...message,
                        params: {
                            name: "ask_memory",
                            arguments: {
                                question: toolArgs.query
                            }
                        }
                    };
                    const mappedMessageText = JSON.stringify(mappedMessage);
                    
                    // Proxy to backend with mapped tool
                    const backendResponse = await this.proxyToBackend(mappedMessageText, message.id);
                    
                    // Convert backend response to ChatGPT format
                    if (backendResponse.result && backendResponse.result.content) {
                        const content = backendResponse.result.content[0]?.text || "";
                        // Parse the content to extract memories and format for ChatGPT
                        const chatgptResponse = {
                            jsonrpc: "2.0",
                            id: message.id,
                            result: {
                                results: this.parseMemoriesForChatGPT(content, toolArgs.query)
                            }
                        };
                        this.sendSseResponse(chatgptResponse, message.id);
                    } else {
                        this.sendSseResponse(backendResponse, message.id);
                    }
                    return new Response(JSON.stringify({ status: "ok" }), { status: 200 });
                }
                
                if (toolName === "fetch") {
                    console.log("Mapping ChatGPT fetch to search_memory");
                    // Map ChatGPT fetch to search_memory with the ID as query
                    const mappedMessage = {
                        ...message,
                        params: {
                            name: "search_memory",
                            arguments: {
                                query: toolArgs.id,
                                limit: 1
                            }
                        }
                    };
                    const mappedMessageText = JSON.stringify(mappedMessage);
                    
                    // Proxy to backend with mapped tool
                    const backendResponse = await this.proxyToBackend(mappedMessageText, message.id);
                    
                    // Convert backend response to ChatGPT fetch format
                    if (backendResponse.result && backendResponse.result.content) {
                        const content = backendResponse.result.content[0]?.text || "";
                        const chatgptResponse = {
                            jsonrpc: "2.0",
                            id: message.id,
                            result: this.parseMemoryForChatGPTFetch(content, toolArgs.id)
                        };
                        this.sendSseResponse(chatgptResponse, message.id);
                    } else {
                        this.sendSseResponse(backendResponse, message.id);
                    }
                    return new Response(JSON.stringify({ status: "ok" }), { status: 200 });
                }
            }

            // Race the backend proxy against a 1-second timer.
            const proxyPromise = this.proxyToBackend(messageText, message.id);
            const timerPromise = new Promise(resolve => setTimeout(() => resolve("timeout"), 1000));
        
            const winner = await Promise.race([proxyPromise, timerPromise]);
        
            if (winner === "timeout") {
                // The backend is taking too long.
                // Let it continue in the background and send an immediate response.
                console.log(`[${this.userId}] Backend task for ID ${message.id} is slow. Running in background.`);
                this.state.waitUntil(
                    proxyPromise.then(backendResponseJson => {
                        this.sendSseResponse(backendResponseJson, message.id);
                    }).catch(e => {
                        this.sendSseError(e, message.id);
                    })
                );
                // Respond to the client that the request is being processed.
                return new Response(JSON.stringify({ status: "processing" }), { status: 200 });
        
            } else {
                // The backend was fast! We have the result.
                console.log(`[${this.userId}] Backend task for ID ${message.id} was fast. Sending response synchronously.`);
                const backendResponseJson = winner as JSONRPCResponse;
                this.sendSseResponse(backendResponseJson, message.id);
                // Respond to the client that the request is complete.
                return new Response(JSON.stringify({ status: "ok" }), { status: 200 });
            }
        } catch (e: any) {
            console.error(`[${this.userId}] Error in handlePostMessage: ${e}`);
            return new Response("Internal Server Error", { status: 500 });
        }
    }

    sendSseResponse(responseJson: any, id: string | number | null) {
        if (this.sseController) {
            const encoder = new TextEncoder();
            const sseMessage = `event: message\ndata: ${JSON.stringify(responseJson)}\n\n`;
            this.sseController.enqueue(encoder.encode(sseMessage));
            console.log(`[${this.userId}] Enqueued SSE response for ID: ${id}`);
        } else {
            console.error(`[${this.userId}] SSE Controller not available for ID: ${id}`);
        }
    }
    
    sendSseError(error: any, id: string | number | null) {
        if (this.sseController) {
            const errorResponse: JSONRPCResponse = {
                jsonrpc: "2.0",
                id: id,
                error: { code: -32603, message: `Backend task failed: ${error.message}` }
            };
            const encoder = new TextEncoder();
            const errorSseMessage = `event: message\ndata: ${JSON.stringify(errorResponse)}\n\n`;
            this.sseController.enqueue(encoder.encode(errorSseMessage));
        }
    }

    async proxyToBackend(message: string, requestId: number | string | null) {
        const url = `${this.backendUrl}/mcp/messages/`;
        console.log(`Proxying to backend: ${url} for request ID: ${requestId}`);
        const startTime = Date.now();

        const controller = new AbortController();
        const timeoutId = setTimeout(() => {
            console.error(`Backend request timed out from worker for ID: ${requestId}`);
            controller.abort()
        }, 90000); // 90s timeout

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-User-Id': this.userId,
                    'X-Client-Name': this.clientName,
                },
                body: message,
                signal: controller.signal,
            });

            const duration = Date.now() - startTime;
            console.log(`Backend responded for ID ${requestId} in ${duration}ms with status ${response.status}`);

            if (!response.ok) {
                const errorText = await response.text();
                console.error(`Backend error for ID ${requestId}: ${response.status} ${errorText}`);
                return { jsonrpc: "2.0", id: requestId, error: { code: response.status, message: "Backend Error", data: errorText }};
            }

            const responseText = await response.text();
            try {
                const jsonResponse = JSON.parse(responseText);
                // Simple ID check without unnecessary logging for performance
                if (jsonResponse.id !== requestId) {
                    jsonResponse.id = requestId;
                }
                return jsonResponse;
            } catch (e: any) {
                console.error(`Failed to parse backend response as JSON for ID ${requestId}. Error:`, e.message);
                return { jsonrpc: "2.0", id: requestId, error: { code: -32002, message: "Backend response is not valid JSON", data: responseText.substring(0, 500) }}; // Truncate large responses
            }

        } catch (error: any) {
            const duration = Date.now() - startTime;
            if (error.name === 'AbortError') {
                console.error(`Error proxying to backend: fetch aborted after ${duration}ms for ID ${requestId}.`);
                return { jsonrpc: "2.0", id: requestId, error: { code: -32000, message: "Proxy Timeout", data: `Request to backend timed out after ${duration}ms` }};
            }
            console.error(`Error proxying to backend after ${duration}ms for ID ${requestId}:`, error);
            return { jsonrpc: "2.0", id: requestId, error: { code: -32000, message: "Proxy Error", data: error.message }};
        } finally {
            clearTimeout(timeoutId);
        }
    }

    // Helper method to parse memories for ChatGPT search format
    parseMemoriesForChatGPT(content: string, query: string): any[] {
        try {
            // Try to parse as JSON first (in case it's structured data)
            const parsed = JSON.parse(content);
            if (Array.isArray(parsed)) {
                return parsed.slice(0, 10).map((item: any, index: number) => ({
                    id: item.id || `mem_${index}`,
                    title: (item.memory || item.content || item.text || "").substring(0, 100) + "...",
                    text: item.memory || item.content || item.text || "",
                    url: null
                }));
            }
        } catch (e) {
            // Content is not JSON, treat as plain text
        }
        
        // Fallback: create a single result from the content
        return [{
            id: "mem_0",
            title: `Memory about: ${query}`,
            text: content,
            url: null
        }];
    }

    // Helper method to parse memory for ChatGPT fetch format
    parseMemoryForChatGPTFetch(content: string, id: string): any {
        try {
            // Try to parse as JSON first
            const parsed = JSON.parse(content);
            if (Array.isArray(parsed) && parsed.length > 0) {
                const item = parsed[0];
                return {
                    id: item.id || id,
                    title: (item.memory || item.content || item.text || "").substring(0, 100) + "...",
                    text: item.memory || item.content || item.text || "",
                    url: null,
                    metadata: item.metadata || {}
                };
            }
        } catch (e) {
            // Content is not JSON, treat as plain text
        }
        
        // Fallback: create result from the content
        return {
            id: id,
            title: `Memory ${id}`,
            text: content,
            url: null,
            metadata: {}
        };
    }
}

interface Env {
	BACKEND_URL: string;
}