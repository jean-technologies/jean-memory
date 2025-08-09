"""
Notion Integration Service for OpenMemory
Handles OAuth authentication and data synchronization with Notion
"""
import httpx
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.models import User
from app.settings import config

logger = logging.getLogger(__name__)

NOTION_API_BASE_URL = "https://api.notion.com/v1"
NOTION_OAUTH_URL = "https://api.notion.com/v1/oauth"


class NotionService:
    """Service for Notion OAuth and API operations"""
    
    def __init__(self):
        self.client_id = config.NOTION_CLIENT_ID
        self.client_secret = config.NOTION_CLIENT_SECRET
        self.redirect_uri = config.NOTION_REDIRECT_URI
        
        if not self.client_id or not self.client_secret:
            logger.warning("Notion OAuth credentials not configured")
    
    def get_oauth_url(self, user_id: str, state: Optional[str] = None) -> str:
        """Generate Notion OAuth authorization URL"""
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "owner": "user",
            "redirect_uri": self.redirect_uri,
        }
        
        if state:
            params["state"] = state
            
        return f"{NOTION_OAUTH_URL}/authorize?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{NOTION_OAUTH_URL}/token",
                auth=(self.client_id, self.client_secret),
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                json={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get Notion user information"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{NOTION_API_BASE_URL}/users/me",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Notion-Version": "2022-06-28"
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def search_pages(self, access_token: str, query: str = "", page_size: int = 100) -> Dict[str, Any]:
        """Search for pages in the user's Notion workspace"""
        async with httpx.AsyncClient() as client:
            payload = {
                "filter": {
                    "property": "object",
                    "value": "page"
                },
                "page_size": page_size
            }
            
            if query:
                payload["query"] = query
            
            response = await client.post(
                f"{NOTION_API_BASE_URL}/search",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Notion-Version": "2022-06-28",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def get_page_content(self, access_token: str, page_id: str) -> Dict[str, Any]:
        """Get content of a specific page"""
        async with httpx.AsyncClient() as client:
            # Get page properties
            page_response = await client.get(
                f"{NOTION_API_BASE_URL}/pages/{page_id}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Notion-Version": "2022-06-28"
                }
            )
            page_response.raise_for_status()
            page_data = page_response.json()
            
            # Get page blocks (content)
            blocks_response = await client.get(
                f"{NOTION_API_BASE_URL}/blocks/{page_id}/children",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Notion-Version": "2022-06-28"
                }
            )
            blocks_response.raise_for_status()
            blocks_data = blocks_response.json()
            
            return {
                "page": page_data,
                "blocks": blocks_data
            }
    
    def extract_text_from_blocks(self, blocks: List[Dict[str, Any]]) -> str:
        """Extract plain text content from Notion blocks"""
        text_content = []
        
        for block in blocks.get("results", []):
            block_type = block.get("type")
            
            if block_type in ["paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item"]:
                rich_text = block.get(block_type, {}).get("rich_text", [])
                for text_obj in rich_text:
                    if text_obj.get("type") == "text":
                        text_content.append(text_obj.get("text", {}).get("content", ""))
            
            elif block_type == "quote":
                rich_text = block.get("quote", {}).get("rich_text", [])
                for text_obj in rich_text:
                    if text_obj.get("type") == "text":
                        text_content.append(f">{text_obj.get('text', {}).get('content', '')}")
            
            elif block_type == "code":
                rich_text = block.get("code", {}).get("rich_text", [])
                for text_obj in rich_text:
                    if text_obj.get("type") == "text":
                        text_content.append(f"```\n{text_obj.get('text', {}).get('content', '')}\n```")
        
        return "\n\n".join(text_content)
    
    def store_access_token(self, db: Session, user: User, token_data: Dict[str, Any]) -> None:
        """Store Notion access token in user metadata"""
        if not user.metadata_:
            user.metadata_ = {}
        
        user.metadata_["notion_access_token"] = token_data.get("access_token")
        user.metadata_["notion_token_type"] = token_data.get("token_type", "bearer")
        user.metadata_["notion_bot_id"] = token_data.get("bot_id")
        user.metadata_["notion_workspace_name"] = token_data.get("workspace_name")
        user.metadata_["notion_workspace_icon"] = token_data.get("workspace_icon")
        user.metadata_["notion_owner"] = token_data.get("owner")
        
        # Mark the metadata field as modified so SQLAlchemy saves it
        flag_modified(user, "metadata_")
        
        db.commit()
        logger.info(f"Stored Notion access token for user {user.user_id}")
    
    def get_access_token(self, user: User) -> Optional[str]:
        """Get stored Notion access token from user metadata"""
        if not user.metadata_:
            return None
        return user.metadata_.get("notion_access_token")
    
    def has_notion_integration(self, user: User) -> bool:
        """Check if user has connected Notion"""
        return bool(self.get_access_token(user))