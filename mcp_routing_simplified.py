# Simplified MCP routing module without multi-agent complexity
# This can replace the parse_virtual_user_id and register_agent_connection functions

def parse_virtual_user_id(user_id: str) -> Dict[str, Any]:
    """
    Simplified user ID parsing - always treats as single agent.
    Maintains backward compatibility but removes multi-agent complexity.
    """
    # Always return single-agent mode
    return {"is_multi_agent": False, "real_user_id": user_id}

async def register_agent_connection(session_id: str, agent_id: str, real_user_id: str, connection_url: str) -> bool:
    """
    No-op function for backward compatibility.
    Multi-agent registration is no longer needed.
    """
    # Log for debugging but don't actually register anything
    logger.debug(f"Skipping multi-agent registration for user {real_user_id}")
    return True