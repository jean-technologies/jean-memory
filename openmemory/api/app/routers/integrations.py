from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict
from app.database import get_db
from app.auth import get_current_supa_user
from gotrue.types import User as SupabaseUser
from app.utils.db import get_or_create_user, get_user_and_app
from app.models import User, Document, App, Memory, MemoryState
from app.integrations.substack_service import SubstackService
import asyncio
from app.services.chunking_service import ChunkingService
from app.integrations.twitter_service import sync_twitter_to_memory
from app.integrations.substack_service import sync_substack_to_memory
import logging
from sqlalchemy import text
from app.background_tasks import create_task, get_task, update_task_progress, run_task_async, mark_task_started, mark_task_completed, mark_task_failed, get_task_health_status
import psutil
from pydantic import BaseModel
import httpx
import os
from app.services.background_sync import background_sync_service
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])

@router.post("/substack/sync")
async def sync_substack(
    request: Dict,
    background_tasks: BackgroundTasks,
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    db: Session = Depends(get_db)
):
    """Start Substack sync in background and return task ID immediately"""
    substack_url = request.get("substack_url")
    max_posts = request.get("max_posts", 20)
    
    if not substack_url:
        raise HTTPException(status_code=400, detail="Substack URL is required")
    
    # Get the local user record
    supabase_user_id_str = str(current_supa_user.id)
    user = get_or_create_user(db, supabase_user_id_str, current_supa_user.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found or could not be created")
    
    # Create a background task
    task_id = create_task("substack_sync", supabase_user_id_str)
    
    # Define the sync function (non-async wrapper)
    def execute_sync():
        """Non-blocking sync execution with asyncio timeout protection"""
        import asyncio
        
        async def sync_task():
            service = SubstackService()
            try:
                # Create a new database session for the background task
                from app.database import SessionLocal
                db_session = SessionLocal()
                try:
                    synced_count, message = await service.sync_substack_posts(
                        db=db_session,
                        supabase_user_id=supabase_user_id_str,
                        substack_url=substack_url,
                        max_posts=max_posts,
                        use_mem0=True,
                        progress_callback=lambda p, m, count: update_task_progress(task_id, p, f"{m} ({count} essays synced)")
                    )
                    return {"synced_count": synced_count, "message": message}
                finally:
                    db_session.close()
            except Exception as e:
                logger.error(f"Sync task error: {e}")
                raise e
        
        # Create new event loop for this task with asyncio timeout protection
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Monitor memory during execution
            initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
            logger.info(f"Starting sync with {initial_memory:.1f}MB memory usage")
            
            # Use asyncio timeout instead of signal (works in background threads)
            result = loop.run_until_complete(
                asyncio.wait_for(sync_task(), timeout=1800)  # 30 minutes timeout
            )
            
            final_memory = psutil.Process().memory_info().rss / 1024 / 1024
            logger.info(f"Sync completed with {final_memory:.1f}MB memory usage (+{final_memory-initial_memory:.1f}MB)")
            
            mark_task_completed(task_id, result)
            logger.info(f"Task {task_id} completed successfully with result: {result}")
            
        except asyncio.TimeoutError:
            mark_task_failed(task_id, "Sync operation timed out after 30 minutes")
            logger.error(f"Task {task_id} timed out")
        except Exception as e:
            mark_task_failed(task_id, str(e))
            logger.error(f"Task {task_id} failed: {e}")
        finally:
            try:
                loop.close()
            except:
                pass
    
    # Add to background tasks (this won't block or cause shutdown)
    background_tasks.add_task(execute_sync)
    
    return {
        "task_id": task_id,
        "status": "started",
        "message": f"Substack sync started for {substack_url}. Use /api/v1/integrations/tasks/{task_id} to check progress."
    }


@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    current_supa_user: SupabaseUser = Depends(get_current_supa_user)
):
    """Get the status of a background task"""
    task = get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Verify the task belongs to the current user
    if task.user_id != str(current_supa_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "task_id": task.task_id,
        "type": task.task_type,
        "status": task.status.value,
        "progress": task.progress,
        "progress_message": task.progress_message,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "result": task.result,
        "error": task.error
    }


@router.get("/documents/count")
async def get_document_count(
    document_type: str,
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    db: Session = Depends(get_db)
):
    """Get count of documents by type for the authenticated user (only documents with active memories)"""
    user = get_or_create_user(db, current_supa_user.id, current_supa_user.email)
    
    # Count documents that have at least one active memory
    count = db.query(Document).filter(
        Document.user_id == user.id,
        Document.document_type == document_type
    ).filter(
        # Only include documents that have active memories
        Document.id.in_(
            db.query(Document.id).join(
                Memory,
                text("memories.metadata->>'document_id' = CAST(documents.id AS TEXT)")
            ).filter(
                Memory.user_id == user.id,
                Memory.state == MemoryState.active
            )
        )
    ).count()
    
    return {"count": count}


@router.post("/documents/chunk")
async def chunk_documents(
    background_tasks: BackgroundTasks,
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    db: Session = Depends(get_db)
):
    """Chunk all documents for the authenticated user in background"""
    user = get_or_create_user(db, current_supa_user.id, current_supa_user.email)
    
    # Create a background task
    task_id = create_task("document_chunking", str(current_supa_user.id))
    
    # Define the chunking function (non-async wrapper)
    def execute_chunking():
        """Non-blocking chunking execution"""
        try:
            from app.database import SessionLocal
            db_session = SessionLocal()
            try:
                chunking_service = ChunkingService()
                processed = chunking_service.chunk_all_documents(db_session, user.id)
                result = {
                    "documents_processed": processed,
                    "message": f"Successfully chunked {processed} documents"
                }
                mark_task_completed(task_id, result)
                logger.info(f"Chunking task {task_id} completed: {processed} documents")
            finally:
                db_session.close()
        except Exception as e:
            mark_task_failed(task_id, str(e))
            logger.error(f"Chunking task {task_id} failed: {e}")
    
    # Add to background tasks
    background_tasks.add_task(execute_chunking)
    
    return {
        "task_id": task_id,
        "status": "started",
        "message": f"Document chunking started. Use /api/v1/integrations/tasks/{task_id} to check progress."
    }


@router.post("/sync/twitter")
async def sync_twitter(
    username: str = Query(..., description="Twitter username without @"),
    max_posts: int = Query(20, description="Maximum number of tweets to sync (max 40)"),
    background_tasks: BackgroundTasks = None,
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    db: Session = Depends(get_db)
):
    """
    Sync recent tweets from a Twitter user to memory in background.
    """
    try:
        # Limit max_posts to prevent resource exhaustion
        max_posts = min(max_posts, 40)
        
        # Get user and Twitter app (create if doesn't exist)
        user, app = get_user_and_app(
            db,
            supabase_user_id=str(current_supa_user.id),
            app_name="twitter",
            email=current_supa_user.email
        )
        
        if not app.is_active:
            raise HTTPException(
                status_code=400,
                detail="Twitter app is paused. Cannot sync tweets."
            )
        
        # Create a background task
        task_id = create_task("twitter_sync", str(current_supa_user.id))
        
        # Define the sync function (non-async wrapper)
        def execute_twitter_sync():
            """Non-blocking Twitter sync execution with asyncio timeout"""
            import asyncio
            
            async def twitter_sync_task():
                # Create a new database session for the background task
                from app.database import SessionLocal
                db_session = SessionLocal()
                try:
                    await sync_twitter_to_memory(
                        username=username,
                        user_id=str(current_supa_user.id),
                        app_id="twitter",
                        db_session=db_session,
                        progress_callback=lambda p, m, c: update_task_progress(task_id, p, f"{m}")
                    )
                finally:
                    db_session.close()
            
            # Create new event loop for this task
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Use asyncio timeout for Twitter sync too (15 minutes)
                result = loop.run_until_complete(
                    asyncio.wait_for(twitter_sync_task(), timeout=900)  # 15 minutes timeout
                )
                
                mark_task_completed(task_id, result)
                logger.info(f"Twitter task {task_id} completed successfully")
                
            except asyncio.TimeoutError:
                mark_task_failed(task_id, "Twitter sync timed out after 15 minutes")
                logger.error(f"Twitter task {task_id} timed out")
            except Exception as e:
                mark_task_failed(task_id, str(e))
                logger.error(f"Twitter task {task_id} failed: {e}")
            finally:
                try:
                    loop.close()
                except:
                    pass
        
        # Add to background tasks
        background_tasks.add_task(execute_twitter_sync)
        
        return {
            "task_id": task_id,
            "status": "started",
            "message": "Sync started! This may take a few minutes. Feel free to close this window and connect other apps."
        }
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error starting Twitter sync for user {current_supa_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start Twitter sync: {str(e)}"
        ) 

@router.post("/sync/substack")
async def sync_substack_simple(
    substack_url: str = Query(..., description="Substack URL (e.g., username.substack.com)"),
    max_posts: int = Query(20, description="Maximum number of posts to sync (max 40)"),
    background_tasks: BackgroundTasks = None,
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    db: Session = Depends(get_db)
):
    """
    Sync recent Substack posts to memory in background.
    Uses existing infrastructure with Jean Memory V2 integration.
    """
    try:
        # Limit max_posts to prevent resource exhaustion
        max_posts = min(max_posts, 40)
        
        # Get user and Substack app (create if doesn't exist)
        user, app = get_user_and_app(
            db,
            supabase_user_id=str(current_supa_user.id),
            app_name="substack",
            email=current_supa_user.email
        )
        
        if not app.is_active:
            raise HTTPException(
                status_code=400,
                detail="Substack app is paused. Cannot sync posts."
            )
        
        # Create a background task
        task_id = create_task("substack_sync", str(current_supa_user.id))
        
        # Define the sync function (non-async wrapper)
        def execute_substack_sync():
            """Non-blocking Substack sync execution with asyncio timeout"""
            import asyncio
            
            async def substack_sync_task():
                # Create a new database session for the background task
                from app.database import SessionLocal
                db_session = SessionLocal()
                try:
                    await sync_substack_to_memory(
                        substack_url=substack_url,
                        user_id=str(current_supa_user.id),
                        app_id="substack",
                        db_session=db_session,
                        max_posts=max_posts,
                        progress_callback=lambda p, m, c: update_task_progress(task_id, p, f"{m}")
                    )
                finally:
                    db_session.close()
            
            # Create new event loop for this task
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Use asyncio timeout for Substack sync (20 minutes)
                result = loop.run_until_complete(
                    asyncio.wait_for(substack_sync_task(), timeout=1200)  # 20 minutes timeout
                )
                
                mark_task_completed(task_id, result)
                logger.info(f"Substack task {task_id} completed successfully")
                
            except asyncio.TimeoutError:
                mark_task_failed(task_id, "Substack sync timed out after 20 minutes")
                logger.error(f"Substack task {task_id} timed out")
            except Exception as e:
                mark_task_failed(task_id, str(e))
                logger.error(f"Substack task {task_id} failed: {e}")
            finally:
                try:
                    loop.close()
                except:
                    pass
        
        # Add to background tasks
        background_tasks.add_task(execute_substack_sync)
        
        return {
            "task_id": task_id,
            "status": "started",
            "message": "Sync started! This may take a few minutes. Feel free to close this window and connect other apps."
        }
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error starting Substack sync for user {current_supa_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start Substack sync: {str(e)}"
        ) 

@router.get("/health")
async def get_integration_health():
    """Get health status of integration services and background tasks"""
    import psutil
    
    # Get task system health
    task_health = get_task_health_status()
    
    # Get current memory usage
    memory_info = psutil.Process().memory_info()
    memory_mb = memory_info.rss / 1024 / 1024
    
    # Get CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    
    # Overall health check
    is_healthy = (
        task_health.get('healthy', False) and
        memory_mb < 1500 and  # Stay under 1.5GB for 2GB container
        cpu_percent < 80  # CPU usage reasonable
    )
    
    return {
        "status": "healthy" if is_healthy else "degraded",
        "memory_usage_mb": round(memory_mb, 1),
        "cpu_percent": round(cpu_percent, 1),
        "task_system": task_health,
        "limits": {
            "memory_limit_mb": 1500,
            "cpu_limit_percent": 80
        },
        "recommendations": {
            "memory": "OK" if memory_mb < 1200 else "High" if memory_mb < 1500 else "Critical",
            "cpu": "OK" if cpu_percent < 60 else "High" if cpu_percent < 80 else "Critical",
            "tasks": "OK" if task_health.get('healthy') else "Issues detected"
        }
    }


@router.post("/health/cleanup")
async def force_cleanup(
    current_supa_user: SupabaseUser = Depends(get_current_supa_user)
):
    """Force cleanup of old tasks and memory (admin endpoint)"""
    import gc
    from app.background_tasks import cleanup_old_tasks
    
    # Force garbage collection
    gc.collect()
    
    # Cleanup old tasks
    cleanup_old_tasks()
    
    # Get updated health status
    health_status = get_task_health_status()
    
    return {
        "message": "Cleanup completed",
        "task_health": health_status,
        "memory_after_cleanup_mb": round(psutil.Process().memory_info().rss / 1024 / 1024, 1)
    } 


# Integration Request Model
class IntegrationRequest(BaseModel):
    appName: str
    useCase: str
    priority: str
    additionalInfo: str = ""
    userEmail: str
    userId: str


@router.post("/request")
async def request_integration(
    request_data: IntegrationRequest,
    background_tasks: BackgroundTasks,
    current_user: SupabaseUser = Depends(get_current_supa_user)
):
    """Submit an integration request via email"""
    try:
        # Send email in background
        background_tasks.add_task(send_integration_request_email, request_data)
        
        logger.info(f"Integration request submitted by user {current_user.id} for {request_data.appName}")
        
        return {
            "message": "Integration request submitted successfully",
            "app_name": request_data.appName
        }
        
    except Exception as e:
        logger.error(f"Failed to submit integration request: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit integration request")


async def send_integration_request_email(request_data: IntegrationRequest):
    """Send integration request email using Resend"""
    try:
        # Check if Resend API key is configured
        resend_api_key = os.getenv("RESEND_API_KEY")
        if not resend_api_key:
            logger.warning("RESEND_API_KEY not configured, email not sent")
            return

        # Format email content
        email_content = f"""
New Integration Request - Jean Memory

App/Service: {request_data.appName}
Priority: {request_data.priority.title()}

Use Case:
{request_data.useCase}

Additional Information:
{request_data.additionalInfo or 'None provided'}

User Details:
- Email: {request_data.userEmail}
- User ID: {request_data.userId}

Submitted via Jean Memory Dashboard
        """.strip()

        # Send via Resend API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {resend_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": "Jean Memory <onboarding@resend.dev>",
                    "to": ["politzki18@gmail.com"],
                    "subject": f"Integration Request: {request_data.appName} ({request_data.priority.title()} Priority)",
                    "text": email_content
                }
            )
            
            if response.status_code == 200:
                logger.info(f"Integration request email sent successfully for {request_data.appName}")
            else:
                logger.error(f"Failed to send email via Resend: {response.status_code} - {response.text}")
                
    except Exception as e:
        logger.error(f"Error sending integration request email: {e}")

@router.post("/apps/{app_name}/refresh")
async def manual_refresh_app(
    app_name: str,
    current_supa_user: SupabaseUser = Depends(get_current_supa_user)
):
    """
    Manually refresh an app's data (replaces real-time polling).
    Triggers background sync and returns immediately.
    """
    try:
        supabase_user_id_str = str(current_supa_user.id)
        
        result = await background_sync_service.manual_refresh_app(
            user_id=supabase_user_id_str,
            app_name=app_name
        )
        
        if result['success']:
            return {
                "message": result['message'],
                "sync_status": result['sync_status'],
                "last_synced_at": result.get('last_synced_at')
            }
        else:
            raise HTTPException(status_code=400, detail=result['error'])
            
    except Exception as e:
        logger.error(f"Manual refresh failed for {app_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Refresh failed: {str(e)}")


@router.get("/apps/{app_name}/sync-status")
async def get_app_sync_status(
    app_name: str,
    current_supa_user: SupabaseUser = Depends(get_current_supa_user)
):
    """
    Get the current sync status for an app.
    Returns last sync time, current status, and any errors.
    """
    try:
        supabase_user_id_str = str(current_supa_user.id)
        
        status = await background_sync_service.get_app_sync_status(
            user_id=supabase_user_id_str,
            app_name=app_name
        )
        
        if not status['found']:
            raise HTTPException(status_code=404, detail=status['error'])
        
        return {
            "sync_status": status['sync_status'],
            "last_synced_at": status['last_synced_at'],
            "sync_error": status['sync_error'],
            "total_memories_created": status['total_memories_created'],
            "total_memories_accessed": status['total_memories_accessed']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get sync status for {app_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.post("/cron/hourly-sync")
async def hourly_sync_cron(
    # TODO: Add proper authentication for CRON jobs
    # cron_token: str = Query(..., description="CRON authentication token")
):
    """
    CRON endpoint: Triggered every hour to sync all integrations.
    This replaces the frontend polling approach.
    """
    try:
        logger.info("🕐 Hourly CRON sync triggered")
        
        # TODO: Verify CRON token for security
        # if cron_token != settings.CRON_SECRET_TOKEN:
        #     raise HTTPException(status_code=401, detail="Invalid CRON token")
        
        results = await background_sync_service.sync_all_integrations()
        
        return {
            "message": "Hourly sync completed",
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Hourly CRON sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"CRON sync failed: {str(e)}")

@router.post("/refresh-all")
async def refresh_all_user_integrations(
    current_supa_user: SupabaseUser = Depends(get_current_supa_user)
):
    """
    Refresh all integrations for the current user.
    Used by dashboard refresh button and session-based auto-refresh.
    """
    try:
        supabase_user_id_str = str(current_supa_user.id)
        
        result = await background_sync_service.refresh_all_user_integrations(
            user_id=supabase_user_id_str
        )
        
        return {
            "message": result['message'],
            "total_apps": result['total_apps'],
            "successful_refreshes": result['successful_refreshes'],
            "failed_refreshes": result['failed_refreshes'],
            "skipped_apps": result['skipped_apps'],
            "results": result['results'],
            "errors": result['errors'],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to refresh all user integrations: {e}")
        raise HTTPException(status_code=500, detail=f"Refresh failed: {str(e)}") 