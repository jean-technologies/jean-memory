"""
Jean Memory Python SDK - MCP Direct Integration
Uses the jean_memory MCP tool directly (same as Claude Desktop/Cursor integration)
"""

import requests
import json
from typing import Optional, List, Dict, Any
import getpass

JEAN_API_BASE = "https://jean-memory-api-virginia.onrender.com"

class JeanAgentMCP:
    """
    Jean Memory Agent with direct MCP tool integration
    Uses the same jean_memory tool that Claude Desktop/Cursor clients use
    
    Usage:
        from jeanmemory_mcp import JeanAgentMCP
        
        agent = JeanAgentMCP(
            api_key="jean_sk_...", 
            system_prompt="You are a helpful tutor."
        )
        agent.run()
    """
    
    def __init__(
        self, 
        api_key: str, 
        system_prompt: str = "You are a helpful assistant.",
        client_name: str = "Python MCP App"
    ):
        self.api_key = api_key
        self.system_prompt = system_prompt
        self.client_name = client_name
        self.user = None
        self.messages = []
        self.is_first_message = True
        
        # Validate API key on initialization
        self._validate_api_key()
    
    def _validate_api_key(self):
        """Validate the developer API key"""
        try:
            response = requests.post(
                f"{JEAN_API_BASE}/sdk/validate-developer",
                json={
                    "api_key": self.api_key,
                    "client_name": self.client_name
                }
            )
            response.raise_for_status()
            data = response.json()
            print(f"✅ API key validated for developer: {data['developer_id']}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Invalid API key: {e}")
    
    def authenticate(self, email: Optional[str] = None, password: Optional[str] = None):
        """Authenticate user with Jean Memory"""
        if not email:
            email = input("Enter your Jean Memory email: ")
        if not password:
            password = getpass.getpass("Enter your password: ")
        
        try:
            response = requests.post(
                f"{JEAN_API_BASE}/sdk/auth/login",
                json={
                    "email": email,
                    "password": password
                }
            )
            response.raise_for_status()
            self.user = response.json()
            print(f"✅ Authenticated as: {self.user['email']}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    def _call_jean_memory_tool(self, user_message: str) -> str:
        """Call the jean_memory MCP tool directly (same as Claude Desktop/Cursor)"""
        if not self.user:
            raise ValueError("User not authenticated. Call authenticate() first.")
        
        # Construct MCP JSON-RPC request for jean_memory tool
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "jean_memory",
                "arguments": {
                    "user_message": user_message,
                    "is_new_conversation": self.is_first_message,
                    "needs_context": True
                }
            }
        }
        
        try:
            # Use the MCP endpoint that Claude Desktop/Cursor use
            response = requests.post(
                f"{JEAN_API_BASE}/mcp/{self.client_name}/messages/{self.user['user_id']}",
                headers={
                    "Content-Type": "application/json",
                    "x-user-id": self.user["user_id"],
                    "x-client-name": self.client_name
                },
                json=mcp_request
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract the jean_memory tool response
            if data.get("error"):
                raise RuntimeError(f"MCP Error: {data['error']['message']}")
            
            result = data.get("result", {})
            content = result.get("content", [])
            if content and len(content) > 0:
                memory_response = content[0].get("text", "No response from jean_memory")
            else:
                memory_response = "No response from jean_memory"
            
            # After first message, subsequent messages are continuing conversation
            if self.is_first_message:
                self.is_first_message = False
            
            return memory_response
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to call jean_memory tool: {e}")
    
    def _synthesize_natural_response(self, user_message: str, context: str, has_rich_context: bool = False) -> str:
        """Synthesize natural conversational response using backend OpenAI"""
        if not self.user:
            raise ValueError("User not authenticated. Call authenticate() first.")
        
        # Create messages for LLM synthesis
        system_content = f"{self.system_prompt}"
        if context:
            system_content += f"\n\nPersonal context about the user:\n{context}"
        
        system_content += "\n\nIMPORTANT: Respond naturally as the persona described in the system prompt. Do NOT mention that you retrieved context or accessed memories. Act as if you naturally know this information about the user. Be conversational and helpful."
        
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_message}
        ]
        
        try:
            # Call backend synthesis endpoint
            response = requests.post(
                f"{JEAN_API_BASE}/sdk/synthesize",
                json={
                    "api_key": self.api_key,
                    "messages": messages,
                    "user_id": self.user["user_id"]
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return data.get("response", "I'm here to help!")
            
        except requests.exceptions.RequestException as e:
            print(f"⚠️ LLM synthesis failed: {e}")
            # Fallback to basic response
            if has_rich_context:
                return f"As your {self.system_prompt.lower()}, I can see from our interactions that I can help you with many things. What would you like to work on?"
            else:
                return f"As your {self.system_prompt.lower()}, I'm ready to help! What can I assist you with?"

    def _call_store_document_tool(self, title: str, content: str, document_type: str = "markdown") -> str:
        """Call the store_document MCP tool directly"""
        if not self.user:
            raise ValueError("User not authenticated. Call authenticate() first.")
        
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "store_document",
                "arguments": {
                    "title": title,
                    "content": content,
                    "document_type": document_type
                }
            }
        }
        
        try:
            response = requests.post(
                f"{JEAN_API_BASE}/mcp/{self.client_name}/messages/{self.user['user_id']}",
                headers={
                    "Content-Type": "application/json",
                    "x-user-id": self.user["user_id"],
                    "x-client-name": self.client_name
                },
                json=mcp_request
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("error"):
                raise RuntimeError(f"MCP Error: {data['error']['message']}")
            
            result = data.get("result", {})
            content = result.get("content", [])
            if content and len(content) > 0:
                return content[0].get("text", "Document stored successfully")
            else:
                return "Document stored successfully"
                
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to call store_document tool: {e}")
    
    def send_message(self, message: str) -> str:
        """Send message using jean_memory MCP tool (like Claude Desktop/Cursor)"""
        # Add user message to conversation history
        user_message = {"role": "user", "content": message}
        self.messages.append(user_message)
        
        # Call jean_memory tool to get context and save memory
        print("🧠 Using jean_memory MCP tool...")
        memory_response = self._call_jean_memory_tool(message)
        
        # Synthesize natural conversational response using context
        print("🤖 Synthesizing natural response...")
        if memory_response.startswith("---\n[Your Life Context]"):
            # New conversation with full narrative context
            context = memory_response.replace("---\n[Your Life Context]\n", "").replace("\n---", "")
            assistant_response = self._synthesize_natural_response(message, context, has_rich_context=True)
        elif "Context is not required" in memory_response:
            # No context needed - respond as persona without personal context
            assistant_response = self._synthesize_natural_response(message, "", has_rich_context=False)
        elif "new conversation" in memory_response.lower():
            # First conversation without cached context
            assistant_response = self._synthesize_natural_response(message, "", has_rich_context=False)
        else:
            # Standard context response - use retrieved memories naturally
            assistant_response = self._synthesize_natural_response(message, memory_response, has_rich_context=False)
        
        # Add assistant response to conversation
        assistant_message = {"role": "assistant", "content": assistant_response}
        self.messages.append(assistant_message)
        
        return assistant_response
    
    def store_document(self, title: str, content: str, document_type: str = "markdown") -> str:
        """Store a document using the store_document MCP tool"""
        return self._call_store_document_tool(title, content, document_type)
    
    def run(self, auto_auth: bool = True):
        """Start interactive chat session"""
        print("🤖 Jean Memory MCP Agent Starting...")
        print(f"📋 System Prompt: {self.system_prompt}")
        print(f"🔧 Using MCP Tools: jean_memory, store_document")
        
        # Authenticate if needed
        if auto_auth and not self.user:
            if not self.authenticate():
                print("❌ Authentication required to continue")
                return
        
        print("\n💬 Chat started! Type 'quit' to exit.\n")
        print("💡 Commands:")
        print("   - Just type your message to chat")
        print("   - Type 'store <title>' to store the conversation as a document")
        print("   - Type 'quit' to exit")
        
        while True:
            try:
                # Get user input
                user_input = input("\n👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                # Handle store document command
                if user_input.startswith('store '):
                    title = user_input[6:].strip() or f"Conversation {len(self.messages)//2 + 1}"
                    conversation_content = "\n\n".join([
                        f"**{msg['role'].title()}:** {msg['content']}" 
                        for msg in self.messages
                    ])
                    
                    print("📄 Storing conversation as document...")
                    result = self.store_document(title, conversation_content, "markdown")
                    print(f"✅ {result}")
                    continue
                
                # Send message and get response
                print("🤔 Thinking...")
                response = self.send_message(user_input)
                print(f"🤖 Assistant: {response}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the full conversation history"""
        return self.messages.copy()
    
    def clear_conversation(self):
        """Clear the conversation history"""
        self.messages = []
        self.is_first_message = True
        print("🗑️ Conversation cleared")

# Convenience function for quick setup
def create_mcp_agent(api_key: str, system_prompt: str = "You are a helpful assistant.") -> JeanAgentMCP:
    """Create and return a JeanAgentMCP instance"""
    return JeanAgentMCP(api_key=api_key, system_prompt=system_prompt)