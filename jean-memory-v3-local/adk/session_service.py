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
import time

from services.google_memory_service import GoogleADKMemoryService

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

class GoogleADKSessionService(BaseSessionService):
    """Google ADK Session management with state persistence"""
    
    def __init__(self, google_service: GoogleADKMemoryService):
        self.google_service = google_service
        self.sessions: Dict[str, SessionData] = {}
        self.session_analytics: Dict[str, Dict[str, Any]] = {}
        self.max_sessions_per_user = 100
        self.session_memory_limit = 1000  # memories per session
        
    async def create_google_session(self, user_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create Google ADK session with state management"""
        session_id = f"google_adk_session_{uuid.uuid4().hex[:12]}"
        
        session_data = SessionData(session_id, user_id)
        session_data.metadata.update({
            "provider": "google_adk",
            "tier": "tier_1",
            **(metadata or {})
        })
        
        # Store session
        self.sessions[session_id] = session_data
        
        # Initialize analytics
        self.session_analytics[session_id] = {
            "created_at": time.time(),
            "memory_count": 0,
            "search_count": 0,
            "total_duration_ms": 0,
            "avg_memory_size": 0
        }
        
        # Store session context in Google Memory Bank
        if self.google_service.initialized:
            try:
                session_context = f"Session {session_id} created for user {user_id}"
                await self.google_service.add_memory_to_google_adk(
                    content=session_context,
                    user_id=user_id,
                    metadata={
                        "type": "session_context",
                        "session_id": session_id,
                        "action": "session_created"
                    }
                )
            except Exception as e:
                logger.error(f"Failed to store session context in Google ADK: {e}")
        
        logger.info(f"🔗 Created Google ADK session: {session_id}", extra={
            "session_id": session_id,
            "user_id": user_id,
            "provider": "google_adk"
        })
        
        return session_id
    
    async def create_session(self, user_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create session (BaseSessionService interface)"""
        return await self.create_google_session(user_id, metadata)
    
    async def add_session_to_memory(self, session_id: str, content: str, 
                                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add session context to Google Memory Bank"""
        session = self.sessions.get(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            return False
        
        if not self.google_service.initialized:
            logger.warning("Google ADK service not initialized")
            return False
        
        try:
            # Prepare session-specific metadata
            session_metadata = {
                "session_id": session_id,
                "user_id": session.user_id,
                "type": "session_memory",
                "timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }
            
            # Add memory to Google ADK
            result = await self.google_service.add_memory_to_google_adk(
                content=content,
                user_id=session.user_id,
                metadata=session_metadata
            )
            
            if result:
                # Update session context
                await self.add_context(session_id, {
                    "type": "memory_added",
                    "content_preview": content[:100] + "..." if len(content) > 100 else content,
                    "memory_id": result.get("id"),
                    "timestamp": datetime.now().isoformat()
                })
                
                # Update analytics
                analytics = self.session_analytics.get(session_id, {})
                analytics["memory_count"] = analytics.get("memory_count", 0) + 1
                analytics["avg_memory_size"] = (
                    (analytics.get("avg_memory_size", 0) * (analytics["memory_count"] - 1) + len(content)) 
                    / analytics["memory_count"]
                )
                
                logger.info(f"🔗 Added session memory to Google ADK", extra={
                    "session_id": session_id,
                    "user_id": session.user_id,
                    "memory_id": result.get("id"),
                    "content_size": len(content)
                })
                
                return True
            
        except Exception as e:
            logger.error(f"Failed to add session memory to Google ADK: {e}")
        
        return False
    
    async def search_session_memories(self, session_id: str, query: str, 
                                     limit: int = 10) -> List[Dict[str, Any]]:
        """Search memories specific to this session"""
        session = self.sessions.get(session_id)
        if not session:
            return []
        
        if not self.google_service.initialized:
            return []
        
        try:
            # Search with session filter
            results = await self.google_service.search_google_memories(
                query=query,
                user_id=session.user_id,
                limit=limit
            )
            
            # Filter by session ID
            session_results = []
            for memory in results:
                memory_metadata = memory.get("metadata", {})
                if memory_metadata.get("session_id") == session_id:
                    session_results.append(memory)
            
            # Update analytics
            analytics = self.session_analytics.get(session_id, {})
            analytics["search_count"] = analytics.get("search_count", 0) + 1
            
            return session_results
            
        except Exception as e:
            logger.error(f"Failed to search session memories: {e}")
            return []
    
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
            
            # Store state change in Google Memory Bank
            if self.google_service.initialized:
                try:
                    state_content = f"Session state updated: {key} = {value}"
                    await self.google_service.add_memory_to_google_adk(
                        content=state_content,
                        user_id=session.user_id,
                        metadata={
                            "type": "session_state_change",
                            "session_id": session_id,
                            "state_key": key,
                            "action": "state_updated"
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to store state change in Google ADK: {e}")
            
            return True
        return False
    
    async def add_context(self, session_id: str, context: Dict[str, Any]) -> bool:
        """Add context to session"""
        session = self.sessions.get(session_id)
        if session:
            context_with_timestamp = {
                **context,
                "timestamp": datetime.now().isoformat()
            }
            
            session.context.append(context_with_timestamp)
            session.update_access()
            
            # Enforce context length limit
            max_context = 200  # Larger limit for Google ADK sessions
            if len(session.context) > max_context:
                session.context = session.context[-max_context:]
            
            return True
        return False
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete Google ADK session"""
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        # Store session end in Google Memory Bank
        if self.google_service.initialized:
            try:
                end_content = f"Session {session_id} ended"
                await self.google_service.add_memory_to_google_adk(
                    content=end_content,
                    user_id=session.user_id,
                    metadata={
                        "type": "session_context",
                        "session_id": session_id,
                        "action": "session_ended",
                        "duration_minutes": (datetime.now() - session.created_at).total_seconds() / 60
                    }
                )
            except Exception as e:
                logger.error(f"Failed to store session end in Google ADK: {e}")
        
        # Remove session and analytics
        del self.sessions[session_id]
        if session_id in self.session_analytics:
            del self.session_analytics[session_id]
        
        logger.info(f"🗑️ Deleted Google ADK session: {session_id}")
        return True
    
    async def get_session_analytics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session analytics and monitoring data"""
        session = self.sessions.get(session_id)
        analytics = self.session_analytics.get(session_id)
        
        if not session or not analytics:
            return None
        
        current_time = time.time()
        duration_ms = (current_time - analytics["created_at"]) * 1000
        
        return {
            "session_id": session_id,
            "user_id": session.user_id,
            "created_at": datetime.fromtimestamp(analytics["created_at"]).isoformat(),
            "duration_ms": duration_ms,
            "memory_count": analytics.get("memory_count", 0),
            "search_count": analytics.get("search_count", 0),
            "avg_memory_size": analytics.get("avg_memory_size", 0),
            "context_length": len(session.context),
            "state_keys": list(session.state.keys()),
            "metadata": session.metadata
        }
    
    async def get_user_sessions(self, user_id: str, limit: int = 10) -> List[SessionData]:
        """Get user's Google ADK sessions"""
        user_sessions = []
        
        for session in self.sessions.values():
            if session.user_id == user_id:
                user_sessions.append(session)
        
        # Sort by most recent first
        user_sessions.sort(key=lambda s: s.last_accessed, reverse=True)
        return user_sessions[:limit]
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get Google ADK session service statistics"""
        total_memory_count = sum(
            analytics.get("memory_count", 0) 
            for analytics in self.session_analytics.values()
        )
        
        total_search_count = sum(
            analytics.get("search_count", 0) 
            for analytics in self.session_analytics.values()
        )
        
        return {
            "service_type": "google_adk",
            "total_sessions": len(self.sessions),
            "total_memory_count": total_memory_count,
            "total_search_count": total_search_count,
            "google_adk_enabled": self.google_service.initialized,
            "max_sessions_per_user": self.max_sessions_per_user,
            "session_memory_limit": self.session_memory_limit
        }