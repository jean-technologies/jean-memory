"""
ADK SessionService for Jean Memory V3
Provides session management with seamless STM → LTM hand-off
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from abc import ABC, abstractmethod
import uuid
import json

logger = logging.getLogger(__name__)

class SessionData:
    """Session data container"""
    
    def __init__(self, session_id: str, user_id: str):
        self.session_id = session_id
        self.user_id = user_id
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.state: Dict[str, Any] = {}
        self.context: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
    
    def update_access(self):
        """Update last accessed timestamp"""
        self.last_accessed = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "state": self.state,
            "context": self.context,
            "metadata": self.metadata
        }

class BaseSessionService(ABC):
    """Abstract base for session services"""
    
    @abstractmethod
    async def create_session(self, user_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create new session"""
        pass
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session data"""
        pass
    
    @abstractmethod
    async def update_session_state(self, session_id: str, key: str, value: Any) -> bool:
        """Update session state"""
        pass
    
    @abstractmethod
    async def add_context(self, session_id: str, context: Dict[str, Any]) -> bool:
        """Add context to session"""
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        pass

class InMemorySessionService(BaseSessionService):
    """In-memory session service for STM (local/device sessions)"""
    
    def __init__(self):
        self.sessions: Dict[str, SessionData] = {}
        self.user_sessions: Dict[str, List[str]] = {}
        self.max_sessions_per_user = 50
        self.max_context_length = 100
    
    async def create_session(self, user_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create new in-memory session"""
        session_id = f"stm_session_{uuid.uuid4().hex[:12]}"
        
        session_data = SessionData(session_id, user_id)
        if metadata:
            session_data.metadata.update(metadata)
        
        # Store session
        self.sessions[session_id] = session_data
        
        # Update user index
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        
        self.user_sessions[user_id].append(session_id)
        
        # Enforce session limit per user
        await self._enforce_session_limits(user_id)
        
        logger.info(f"📝 Created STM session: {session_id}")
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session data"""
        session = self.sessions.get(session_id)
        if session:
            session.update_access()
        return session
    
    async def update_session_state(self, session_id: str, key: str, value: Any) -> bool:
        """Update session state"""
        session = self.sessions.get(session_id)
        if session:
            session.state[key] = value
            session.update_access()
            return True
        return False
    
    async def add_context(self, session_id: str, context: Dict[str, Any]) -> bool:
        """Add context to session"""
        session = self.sessions.get(session_id)
        if session:
            # Add timestamp
            context_with_timestamp = {
                **context,
                "timestamp": datetime.now().isoformat()
            }
            
            session.context.append(context_with_timestamp)
            session.update_access()
            
            # Enforce context length limit
            if len(session.context) > self.max_context_length:
                session.context = session.context[-self.max_context_length:]
            
            return True
        return False
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        session = self.sessions.get(session_id)
        if session:
            # Remove from user index
            user_id = session.user_id
            if user_id in self.user_sessions:
                if session_id in self.user_sessions[user_id]:
                    self.user_sessions[user_id].remove(session_id)
            
            # Remove session
            del self.sessions[session_id]
            logger.info(f"🗑️  Deleted STM session: {session_id}")
            return True
        return False
    
    async def get_user_sessions(self, user_id: str, limit: int = 10) -> List[SessionData]:
        """Get user's sessions"""
        session_ids = self.user_sessions.get(user_id, [])
        sessions = []
        
        for session_id in session_ids[-limit:]:  # Most recent first
            session = self.sessions.get(session_id)
            if session:
                sessions.append(session)
        
        return sessions
    
    async def cleanup_expired_sessions(self, max_age_hours: int = 24):
        """Cleanup expired sessions"""
        now = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            age_hours = (now - session.last_accessed).total_seconds() / 3600
            if age_hours > max_age_hours:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self.delete_session(session_id)
        
        if expired_sessions:
            logger.info(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")
    
    async def _enforce_session_limits(self, user_id: str):
        """Enforce session limits per user"""
        user_session_ids = self.user_sessions.get(user_id, [])
        
        if len(user_session_ids) > self.max_sessions_per_user:
            # Remove oldest sessions
            sessions_to_remove = user_session_ids[:-self.max_sessions_per_user]
            for session_id in sessions_to_remove:
                await self.delete_session(session_id)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get session service statistics"""
        return {
            "total_sessions": len(self.sessions),
            "total_users": len(self.user_sessions),
            "service_type": "in_memory",
            "max_sessions_per_user": self.max_sessions_per_user,
            "max_context_length": self.max_context_length
        }

class CloudSessionService(BaseSessionService):
    """Cloud session service for LTM (persistent sessions)"""
    
    def __init__(self, ltm_service):
        self.ltm = ltm_service
        self.local_cache: Dict[str, SessionData] = {}
        self.cache_ttl_minutes = 30
    
    async def create_session(self, user_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create cloud-persistent session"""
        session_id = f"ltm_session_{uuid.uuid4().hex[:12]}"
        
        session_data = SessionData(session_id, user_id)
        if metadata:
            session_data.metadata.update(metadata)
        
        # Store in LTM
        if self.ltm.is_ready():
            try:
                await self._persist_session(session_data)
            except Exception as e:
                logger.error(f"❌ Failed to persist session to LTM: {e}")
        
        # Cache locally
        self.local_cache[session_id] = session_data
        
        logger.info(f"☁️  Created LTM session: {session_id}")
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session with LTM fallback"""
        # Check cache first
        session = self.local_cache.get(session_id)
        if session:
            session.update_access()
            return session
        
        # Fallback to LTM
        if self.ltm.is_ready():
            try:
                session = await self._load_session_from_ltm(session_id)
                if session:
                    session.update_access()
                    self.local_cache[session_id] = session
                    return session
            except Exception as e:
                logger.error(f"❌ Failed to load session from LTM: {e}")
        
        return None
    
    async def update_session_state(self, session_id: str, key: str, value: Any) -> bool:
        """Update session state with LTM persistence"""
        session = await self.get_session(session_id)
        if session:
            session.state[key] = value
            session.update_access()
            
            # Persist to LTM
            if self.ltm.is_ready():
                try:
                    await self._persist_session(session)
                except Exception as e:
                    logger.error(f"❌ Failed to persist session state: {e}")
            
            return True
        return False
    
    async def add_context(self, session_id: str, context: Dict[str, Any]) -> bool:
        """Add context with LTM persistence"""
        session = await self.get_session(session_id)
        if session:
            context_with_timestamp = {
                **context,
                "timestamp": datetime.now().isoformat()
            }
            
            session.context.append(context_with_timestamp)
            session.update_access()
            
            # Persist to LTM
            if self.ltm.is_ready():
                try:
                    await self._persist_session(session)
                except Exception as e:
                    logger.error(f"❌ Failed to persist session context: {e}")
            
            return True
        return False
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session from cache and LTM"""
        # Remove from cache
        if session_id in self.local_cache:
            del self.local_cache[session_id]
        
        # Remove from LTM
        if self.ltm.is_ready():
            try:
                await self._delete_session_from_ltm(session_id)
            except Exception as e:
                logger.error(f"❌ Failed to delete session from LTM: {e}")
        
        logger.info(f"🗑️  Deleted LTM session: {session_id}")
        return True
    
    async def _persist_session(self, session: SessionData):
        """Persist session to LTM"""
        # Implementation would depend on LTM storage format
        # For now, store as special memory with session metadata
        session_content = f"Session data for {session.session_id}"
        
        await self.ltm.upload_memory(
            content=session_content,
            user_id=session.user_id,
            metadata={
                "type": "session_data",
                "session_id": session.session_id,
                "session_data": session.to_dict()
            }
        )
    
    async def _load_session_from_ltm(self, session_id: str) -> Optional[SessionData]:
        """Load session from LTM"""
        # Implementation would search LTM for session metadata
        # This is a placeholder implementation
        return None
    
    async def _delete_session_from_ltm(self, session_id: str):
        """Delete session from LTM"""
        # Implementation would delete session from LTM storage
        pass
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cloud session service statistics"""
        return {
            "cached_sessions": len(self.local_cache),
            "service_type": "cloud",
            "ltm_connected": self.ltm.is_ready(),
            "cache_ttl_minutes": self.cache_ttl_minutes
        }