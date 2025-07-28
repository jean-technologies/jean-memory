from typing import Dict, Any, List
from .base import BaseClient, BaseClientProfile
from app.config.tool_config import get_tools_for_client

class DefaultClient(BaseClient):
    def get_tools(self) -> list:
        """
        Returns a list of tools for the default client
        by fetching them from the centralized tool configuration.
        """
        return get_tools_for_client(self.get_client_name())

    def get_client_name(self) -> str:
        return "default"

    def get_client_profile(self) -> BaseClientProfile:
        from .claude import ClaudeProfile  # Re-use a standard profile
        return ClaudeProfile() 