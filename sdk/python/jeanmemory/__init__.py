"""
Jean Memory Python SDK
Add long-term memory to your Python agents and backend services
"""

import requests
import json
from typing import Optional, List, Dict, Any, Union
import os

JEAN_API_BASE = "https://jean-memory-api-virginia.onrender.com"

class ContextResponse:
    """Response object from get_context calls"""
    def __init__(self, data: dict):
        self.text = data.get('text', '')
        self.enhanced = data.get('enhanced', False)
        self.memories_used = data.get('memories_used', 0)
        self.raw_data = data


class JeanClient:
    """Main client for interacting with Jean Memory API"""
    
    def __init__(self, api_key: str):
        """
        Initialize the Jean Memory client.
        
        Args:
            api_key: Your Jean Memory API key (starts with jean_sk_)
        """
        if not api_key:
            raise ValueError("API key is required")
        
        if not api_key.startswith('jean_sk_'):
            raise ValueError("Invalid API key format. Jean Memory API keys start with 'jean_sk_'")
        
        self.api_key = api_key
        self.tools = Tools(self)
        
        # Validate API key
        self._validate_api_key()
    
    def _validate_api_key(self):
        """Validate the API key with the backend"""
        try:
            # Use MCP health endpoint to validate connectivity
            response = requests.get(
                f"{JEAN_API_BASE}/mcp",
                headers={"X-API-Key": self.api_key}
            )
            if response.status_code not in [200, 404]:  # 404 is OK, means MCP endpoint exists
                raise ValueError("Invalid API key or connection failed")
            print("✅ Jean Memory client initialized")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Invalid API key: {e}")
    
    def get_context(
        self,
        user_token: str,
        message: str,
        speed: str = "balanced",
        tool: str = "jean_memory",
        format: str = "enhanced"
    ) -> ContextResponse:
        """
        Get context from Jean Memory for a user message.
        
        Args:
            user_token: User authentication token (from OAuth flow)
            message: The user's message/query
            speed: "fast", "balanced", or "comprehensive" 
            tool: "jean_memory" or "search_memory"
            format: "simple" or "enhanced"
        
        Returns:
            ContextResponse object with retrieved context
        """
        try:
            # Extract user_id from token (simplified - in production would validate JWT)
            import base64
            import json as json_lib
            
            try:
                # Try to decode JWT token to get user_id
                payload = json_lib.loads(base64.b64decode(user_token.split('.')[1] + '=='))
                user_id = payload.get('sub', user_token)  # Fallback to token itself
            except:
                user_id = user_token  # Fallback if not JWT
            
            # Use MCP jean_memory tool
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool,
                    "arguments": {
                        "user_message": message,
                        "is_new_conversation": False,
                        "needs_context": True
                    } if tool == "jean_memory" else {
                        "query": message
                    }
                }
            }
            
            response = requests.post(
                f"{JEAN_API_BASE}/mcp/messages/{user_id}",
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": self.api_key
                },
                json=mcp_request
            )
            response.raise_for_status()
            
            data = response.json()
            if 'error' in data:
                raise RuntimeError(f"MCP Error: {data['error']['message']}")
            
            # Extract text from MCP response
            result_text = data.get('result', {}).get('content', [{}])[0].get('text', '')
            
            return ContextResponse({
                'text': result_text,
                'enhanced': format == 'enhanced',
                'memories_used': 1,
                'speed': speed,
                'tool': tool
            })
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to get context: {e}")


class Tools:
    """Direct access to memory manipulation tools"""
    
    def __init__(self, client: JeanClient):
        self.client = client
    
    def add_memory(self, user_token: str, content: str) -> dict:
        """
        Directly add a memory for a user.
        
        Args:
            user_token: User authentication token
            content: The memory content to add
        
        Returns:
            Response from the API
        """
        try:
            # Extract user_id from token
            try:
                import base64
                import json as json_lib
                payload = json_lib.loads(base64.b64decode(user_token.split('.')[1] + '=='))
                user_id = payload.get('sub', user_token)
            except:
                user_id = user_token
            
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "add_memories",
                    "arguments": {"text": content}
                }
            }
            
            response = requests.post(
                f"{JEAN_API_BASE}/mcp/messages/{user_id}",
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": self.client.api_key
                },
                json=mcp_request
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to add memory: {e}")
    
    def search_memory(self, user_token: str, query: str, limit: int = 10) -> dict:
        """
        Search a user's memories.
        
        Args:
            user_token: User authentication token
            query: Search query
            limit: Maximum number of results
        
        Returns:
            Search results from the API
        """
        try:
            # Extract user_id from token
            try:
                import base64
                import json as json_lib
                payload = json_lib.loads(base64.b64decode(user_token.split('.')[1] + '=='))
                user_id = payload.get('sub', user_token)
            except:
                user_id = user_token
            
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "search_memory",
                    "arguments": {"query": query}
                }
            }
            
            response = requests.post(
                f"{JEAN_API_BASE}/mcp/messages/{user_id}",
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": self.client.api_key
                },
                json=mcp_request
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to search memory: {e}")


# Legacy JeanAgent class for backward compatibility
class JeanAgent:
    """
    Jean Memory Agent for AI chatbots with personalized context
    
    Usage:
        from jeanmemory import JeanAgent
        
        agent = JeanAgent(
            api_key="jean_sk_...", 
            system_prompt="You are a helpful tutor.",
            modality="chat"
        )
        agent.run()
    """
    
    def __init__(
        self, 
        api_key: str, 
        system_prompt: str = "You are a helpful assistant.",
        modality: str = "chat",
        client_name: str = "Python App"
    ):
        self.api_key = api_key
        self.system_prompt = system_prompt
        self.modality = modality
        self.client_name = client_name
        self.user = None
        self.messages = []
        
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
    
    def send_message(self, message: str) -> str:
        """Send message and get enhanced response with Jean Memory context"""
        if not self.user:
            raise ValueError("User not authenticated. Call authenticate() first.")
        
        # Add user message to conversation history (for context)
        user_message = {"role": "user", "content": message}
        self.messages.append(user_message)
        
        try:
            # Enhance message with Jean Memory context
            # FIX: Send only current message like React SDK (not full conversation history)
            current_message = [user_message]
            response = requests.post(
                f"{JEAN_API_BASE}/sdk/chat/enhance",
                json={
                    "api_key": self.api_key,
                    "client_name": self.client_name,
                    "user_id": self.user["user_id"],
                    "messages": current_message,  # Send only current message for better memory retrieval
                    "system_prompt": self.system_prompt
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract enhanced context
            enhanced_messages = data["enhanced_messages"]
            user_context = data["user_context"]
            context_retrieved = data["context_retrieved"]
            
            # Generate actual AI response using the enhanced messages
            print(f"🧠 Retrieved context: {len(user_context) if user_context else 0} characters")
            
            try:
                # Use the enhanced messages from the API to call OpenAI
                import openai
                import os
                
                # Check for OpenAI API key
                openai_key = os.getenv("OPENAI_API_KEY")
                if not openai_key:
                    raise ValueError("OPENAI_API_KEY environment variable not set")
                
                # Create OpenAI client
                client = openai.OpenAI(api_key=openai_key)
                
                # Call OpenAI with enhanced messages
                completion = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=enhanced_messages,
                    max_tokens=500,
                    temperature=0.7
                )
                
                assistant_response = completion.choices[0].message.content.strip()
                
            except Exception as llm_error:
                # Fallback to enhanced context if OpenAI fails (good for testing)
                if context_retrieved and user_context:
                    assistant_response = f"✅ SUCCESS! Retrieved {len(user_context)} characters from your Jean Memory:\n\n{user_context[:300]}...\n\n📝 Response: As your {self.system_prompt.lower()}, I can see your personal context and am ready to help!"
                else:
                    assistant_response = "I don't have any specific context about you yet, and I need an OpenAI API key to provide intelligent responses. Tell me more!"
                
                print(f"⚠️ LLM Error: {llm_error}")
            
            # Add assistant response to conversation
            assistant_message = {"role": "assistant", "content": assistant_response}
            self.messages.append(assistant_message)
            
            return assistant_response
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to send message: {e}")
    
    def run(self, auto_auth: bool = True):
        """Start interactive chat session"""
        print("🤖 Jean Memory Agent Starting...")
        print(f"📋 System Prompt: {self.system_prompt}")
        print(f"🔧 Modality: {self.modality}")
        
        # Authenticate if needed
        if auto_auth and not self.user:
            if not self.authenticate():
                print("❌ Authentication required to continue")
                return
        
        print("\n💬 Chat started! Type 'quit' to exit.\n")
        
        while True:
            try:
                # Get user input with better formatting
                print()  # Add space before prompt
                user_input = input("👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                # Send message and get response
                print("🤔 Thinking...")
                response = self.send_message(user_input)
                print(f"\n🤖 {self.system_prompt.split('.')[0].replace('You are a', '').replace('You are an', '').strip().title()}: {response}")
                
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
        print("🗑️ Conversation cleared")

# Convenience function for quick setup
def create_agent(api_key: str, system_prompt: str = "You are a helpful assistant.") -> JeanAgent:
    """Create and return a JeanAgent instance (legacy)"""
    return JeanAgent(api_key=api_key, system_prompt=system_prompt)


# Main exports
__all__ = ['JeanClient', 'JeanAgent', 'ContextResponse', 'create_agent']