from functools import lru_cache
from .base import BaseClient
from .claude import ClaudeClient
from .chatgpt import ChatGPTClient
from .default import DefaultClient
from .chorus import ChorusClient

# A mapping of client names to their respective client classes.
# This allows for dynamic loading of clients based on their name.
CLIENT_MAP = {
    "claude": ClaudeClient,
    "chatgpt": ChatGPTClient,
    "default": DefaultClient,
    "chorus": ChorusClient,
}

@lru_cache(maxsize=None)
def get_client(client_name: str) -> BaseClient:
    """
    Returns an instance of the client class for the given client name.
    Uses an LRU cache to ensure that client instances are reused, which
    improves performance by avoiding repeated object creation.

    If a specific client is not found, it safely falls back to the DefaultClient.
    """
    client_class = CLIENT_MAP.get(client_name.lower(), DefaultClient)
    return client_class()

def get_client_profile(client_name: str):
    """
    Fetches the client's profile, which contains specific formatting rules
    and other client-specific configurations.
    """
    client = get_client(client_name)
    return client.get_client_profile()

def get_client_name(client_name: str) -> str:
    """
    A simple helper to get the canonical name of the client.
    """
    client = get_client(client_name)
    return client.get_client_name() 