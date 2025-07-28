from typing import Dict, Any, List
from .base import BaseClientProfile, BaseClient
from app.config.tool_config import get_tools_for_client

class ClaudeClient(BaseClient):
    def get_tools(self) -> list:
        """
        Returns a list of tools specifically curated for the Claude client
        by fetching them from the centralized tool configuration.
        """
        return get_tools_for_client(self.get_client_name())

    def get_client_name(self) -> str:
        return "claude"

    def get_client_profile(self) -> BaseClientProfile:
        return ClaudeProfile()

class ClaudeProfile(BaseClientProfile):
    def get_tools_schema(self, include_annotations: bool = False) -> List[Dict[str, Any]]:
        """
        Returns the JSON schema for tools available to Claude client.
        """
        # Get the tools from the client
        client = ClaudeClient()
        tools = client.get_tools()
        
        # Extract the schema from each tool
        tool_schemas = []
        for tool in tools:
            if hasattr(tool, 'mcp_tool_def'):
                tool_schemas.append(tool.mcp_tool_def)
                
        return tool_schemas
    
    def get_tool_prompt(self, tools: List[Dict[str, Any]]) -> str:
        # Claude-specific prompt formatting can go here if needed
        return super().get_tool_prompt(tools) 