from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict
import uuid
import datetime
from app.database import SessionLocal
from app.utils.db import get_user_and_app
from app.models import User, App, Memory, MemoryState
import logging
import asyncio
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test", tags=["test"])

# Test session storage (in production, use Redis)
test_sessions: Dict[str, Dict] = {}

class TestMemoryRequest(BaseModel):
    action: str
    input: str
    sessionId: str

class TestSessionInfo(BaseModel):
    sessionId: str

def cleanup_old_test_sessions():
    """Remove test sessions older than 1 hour"""
    try:
        one_hour_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
        sessions_to_remove = []
        
        for session_id, session_data in test_sessions.items():
            if session_data.get('created_at', datetime.datetime.now(datetime.timezone.utc)) < one_hour_ago:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del test_sessions[session_id]
            logger.info(f"Cleaned up old test session: {session_id}")
            
    except Exception as e:
        logger.error(f"Error cleaning up test sessions: {e}")

def get_or_create_test_user(db, session_id: str):
    """Create a test user for the demo session"""
    try:
        # Generate a unique test user ID
        test_user_id = f"test_user_{session_id}"
        
        # Check if test user already exists in our session storage
        if session_id in test_sessions:
            existing_user_data = test_sessions[session_id].get('user_data')
            if existing_user_data:
                user = db.query(User).filter(User.user_id == test_user_id).first()
                if user:
                    return user
        
        # Create new test user
        user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, test_user_id)
        
        test_user = User(
            id=user_uuid,
            user_id=test_user_id,
            email=f"test_{session_id}@demo.jeanmemory.com",
            name=f"Demo User {session_id[-6:]}",
            is_anonymous=True
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        # Store in session cache
        test_sessions[session_id] = {
            'created_at': datetime.datetime.now(datetime.timezone.utc),
            'user_data': {
                'id': str(test_user.id),
                'user_id': test_user.user_id,
                'email': test_user.email
            }
        }
        
        logger.info(f"Created test user: {test_user_id}")
        return test_user
        
    except Exception as e:
        logger.error(f"Error creating test user: {e}")
        raise HTTPException(status_code=500, detail="Error creating test user")

def get_or_create_test_app(db, user, session_id: str):
    """Create a test app for the demo session"""
    try:
        app_name = f"demo_app_{session_id}"
        
        existing_app = db.query(App).filter(
            App.owner_id == user.id,
            App.name == app_name
        ).first()
        
        if existing_app:
            return existing_app
        
        test_app = App(
            name=app_name,
            owner_id=user.id,
            is_active=True,
            description="Demo app for testing Jean Memory"
        )
        
        db.add(test_app)
        db.commit()
        db.refresh(test_app)
        
        logger.info(f"Created test app: {app_name}")
        return test_app
        
    except Exception as e:
        logger.error(f"Error creating test app: {e}")
        raise HTTPException(status_code=500, detail="Error creating test app")

@router.post("/memory")
async def test_memory_operation(request: TestMemoryRequest, background_tasks: BackgroundTasks):
    """Handle memory operations for test/demo users"""
    try:
        # Validate session ID
        if not request.sessionId.startswith('test_'):
            raise HTTPException(status_code=400, detail="Invalid test session ID")
        
        # Periodic cleanup
        cleanup_old_test_sessions()
        
        # Rate limiting: max 50 operations per session
        session_data = test_sessions.get(request.sessionId, {})
        operation_count = session_data.get('operation_count', 0)
        
        if operation_count >= 50:
            raise HTTPException(
                status_code=429, 
                detail="Demo limit reached. Please start a new session or sign up for unlimited usage."
            )
        
        db = SessionLocal()
        try:
            # Get or create test user and app
            test_user = get_or_create_test_user(db, request.sessionId)
            test_app = get_or_create_test_app(db, test_user, request.sessionId)
            
            # Execute the memory operation
            if request.action == "add_memory":
                result = await handle_add_memory(db, test_user, test_app, request.input)
            elif request.action == "search_memory":
                result = await handle_search_memory(db, test_user, request.input)
            elif request.action == "ask_memory":
                result = await handle_ask_memory(db, test_user, request.input)
            else:
                raise HTTPException(status_code=400, detail="Invalid action")
            
            # Update operation count
            if request.sessionId in test_sessions:
                test_sessions[request.sessionId]['operation_count'] = operation_count + 1
            
            # Schedule cleanup of test data in background
            background_tasks.add_task(schedule_test_cleanup, request.sessionId)
            
            return {
                "success": True,
                "result": result,
                "sessionInfo": {
                    "memoryCount": get_test_memory_count(db, test_user),
                    "sessionId": request.sessionId.split('_')[1]
                }
            }
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in test memory operation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

async def handle_add_memory(db, user, app, content: str):
    """Add a memory for the test user"""
    try:
        # Create memory record in database
        memory = Memory(
            user_id=user.id,
            app_id=app.id,
            content=content,
            state=MemoryState.active,
            metadata_={
                "source": "demo",
                "session_type": "test",
                "demo_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
        )
        
        db.add(memory)
        db.commit()
        db.refresh(memory)
        
        logger.info(f"Added test memory for user {user.user_id}: {content[:50]}...")
        
        return f"✅ Memory stored successfully! I've remembered: \"{content[:80]}{'...' if len(content) > 80 else ''}\"\n\nThis information is now part of your demo memory bank and can be searched or referenced in future queries during this session.\n\n💡 In the full version, this would also be stored in the vector database for semantic search across all your AI applications."
        
    except Exception as e:
        logger.error(f"Error adding test memory: {e}")
        return f"❌ Error storing memory: {str(e)}"

async def handle_search_memory(db, user, query: str):
    """Search memories for the test user"""
    try:
        # Get all memories for this test user
        memories = db.query(Memory).filter(
            Memory.user_id == user.id,
            Memory.state == MemoryState.active
        ).order_by(Memory.created_at.desc()).all()
        
        if not memories:
            return f"🔍 No memories found for \"{query}\". Try adding some memories first using phrases like \"Remember that I...\" or \"Store this information...\""
        
        # Simple keyword matching for demo
        query_words = query.lower().split()
        matching_memories = []
        
        for memory in memories:
            content_lower = memory.content.lower()
            if any(word in content_lower for word in query_words if len(word) > 2):
                matching_memories.append(memory)
        
        if not matching_memories:
            memory_previews = [m.content[:30] + "..." if len(m.content) > 30 else m.content for m in memories[:3]]
            preview_text = ', '.join(f'"{preview}"' for preview in memory_previews)
            return f"🔍 No memories found matching \"{query}\".\n\nYour current memories contain information about: {preview_text}"
        
        # Format results
        results = []
        for i, memory in enumerate(matching_memories[:10], 1):
            timestamp = memory.created_at.strftime("%H:%M:%S") if memory.created_at else "Unknown time"
            results.append(f"{i}. {memory.content} (stored at {timestamp})")
        
        result_text = f"🔍 Found {len(matching_memories)} matching memor{'y' if len(matching_memories) == 1 else 'ies'} for \"{query}\":\n\n" + "\n\n".join(results)
        
        if len(matching_memories) > 10:
            result_text += f"\n\n... and {len(matching_memories) - 10} more results"
        
        result_text += "\n\n💡 The full Jean Memory system uses advanced semantic search with vector embeddings for much more accurate and contextual results."
        
        return result_text
        
    except Exception as e:
        logger.error(f"Error searching test memories: {e}")
        return f"❌ Error searching memories: {str(e)}"

async def handle_ask_memory(db, user, question: str):
    """Answer questions based on stored memories"""
    try:
        # Get all memories for this test user
        memories = db.query(Memory).filter(
            Memory.user_id == user.id,
            Memory.state == MemoryState.active
        ).order_by(Memory.created_at.desc()).all()
        
        if not memories:
            return f"🤔 I don't have any memories stored yet for this demo session. Try adding some information about yourself first!\n\nExamples:\n• \"Remember that I'm a software developer\"\n• \"Store that I love hiking and outdoor activities\"\n• \"I work at a tech startup in San Francisco\""
        
        # Generate a simple conversational response
        memory_count = len(memories)
        response = f"🤔 Based on your {memory_count} stored memor{'y' if memory_count == 1 else 'ies'}, here's what I know:\n\n"
        
        # Add memory summaries
        for memory in memories:
            response += f"• {memory.content}\n"
        
        response += f"\n💡 This is a simplified demo response. The full Jean Memory system uses advanced AI (Claude, GPT, Gemini) to provide sophisticated analysis, insights, and conversations based on your complete memory bank across all your applications and documents."
        
        return response
        
    except Exception as e:
        logger.error(f"Error in ask memory: {e}")
        return f"❌ Error processing question: {str(e)}"

def get_test_memory_count(db, user):
    """Get the count of memories for a test user"""
    try:
        return db.query(Memory).filter(
            Memory.user_id == user.id,
            Memory.state == MemoryState.active
        ).count()
    except Exception:
        return 0

async def schedule_test_cleanup(session_id: str):
    """Schedule cleanup of test data after 1 hour"""
    try:
        # In a real implementation, this would schedule a background task
        # For now, we'll just mark it for later cleanup
        if session_id in test_sessions:
            test_sessions[session_id]['cleanup_scheduled'] = True
        
        logger.info(f"Scheduled cleanup for test session: {session_id}")
    except Exception as e:
        logger.error(f"Error scheduling cleanup: {e}")

@router.get("/session")
async def get_test_session_info(sessionId: str):
    """Get information about a test session"""
    try:
        if not sessionId.startswith('test_'):
            raise HTTPException(status_code=400, detail="Invalid session ID")
        
        session_data = test_sessions.get(sessionId)
        
        if not session_data:
            return {
                "success": True,
                "sessionExists": False,
                "memoryCount": 0,
                "createdAt": None
            }
        
        db = SessionLocal()
        try:
            test_user = get_or_create_test_user(db, sessionId)
            memory_count = get_test_memory_count(db, test_user)
            
            return {
                "success": True,
                "sessionExists": True,
                "memoryCount": memory_count,
                "createdAt": session_data.get('created_at'),
                "operationCount": session_data.get('operation_count', 0)
            }
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error getting session info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/cleanup")
async def cleanup_test_data():
    """Manually trigger cleanup of old test data (admin endpoint)"""
    try:
        db = SessionLocal()
        try:
            # Delete old test users and their data
            one_hour_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
            
            # Find test users older than 1 hour
            old_test_users = db.query(User).filter(
                User.user_id.like('test_user_%'),
                User.created_at < one_hour_ago
            ).all()
            
            deleted_count = 0
            for user in old_test_users:
                # Delete user's memories
                db.query(Memory).filter(Memory.user_id == user.id).delete()
                
                # Delete user's apps
                db.query(App).filter(App.owner_id == user.id).delete()
                
                # Delete user
                db.delete(user)
                deleted_count += 1
            
            db.commit()
            
            # Clean up session storage
            cleanup_old_test_sessions()
            
            logger.info(f"Cleaned up {deleted_count} old test users")
            
            return {
                "success": True,
                "message": f"Cleaned up {deleted_count} old test users and their data"
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in cleanup: {e}")
        raise HTTPException(status_code=500, detail="Cleanup failed") 