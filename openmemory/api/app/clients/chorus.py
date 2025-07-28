from .claude import ClaudeProfile
from app.clients.base import BaseClient, BaseClientProfile
from app.config.tool_config import get_tools_for_client


class ChorusProfile(ClaudeProfile):
    """
    Client profile for Chorus.
    For now, it has the exact same behavior as the Claude profile.
    This provides a dedicated point for future customization.
    """
    pass


class ChorusClient(BaseClient):
    def get_tools(self) -> list:
        """
        Returns a list of tools specifically curated for the Chorus client
        by fetching them from the centralized tool configuration.
        """
        return get_tools_for_client(self.get_client_name())

    def get_client_name(self) -> str:
        return "chorus" 