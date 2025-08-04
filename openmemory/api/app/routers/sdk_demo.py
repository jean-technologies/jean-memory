"""
Jean Memory SDK Demo Router
Enables developers to build multi-tenant AI chatbots with "Sign in with Jean" functionality
"""
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks, status
from pydantic import BaseModel, EmailStr
from supabase import Client as SupabaseClient
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
import logging

from app.auth import get_service_client
from app.database import get_db
from app.models import User, ApiKey
from app.tools.orchestration import jean_memory
from app.context import user_id_var, client_name_var, background_tasks_var

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sdk", tags=["SDK Demo"])

# Pydantic models defined in router file following existing patterns
class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class DeveloperRequest(BaseModel):
    api_key: str
    client_name: str

class UserLoginResponse(BaseModel):
    user_id: str
    email: str
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: int

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    api_key: str
    client_name: str
    user_id: str
    messages: List[ChatMessage]
    system_prompt: Optional[str] = None

class ChatResponse(BaseModel):
    enhanced_messages: List[Dict[str, Any]]
    context_retrieved: bool
    user_context: Optional[str] = None

class SynthesizeRequest(BaseModel):
    api_key: str
    messages: List[Dict[str, str]]
    user_id: Optional[str] = None

class SynthesizeResponse(BaseModel):
    response: str

async def _validate_api_key_and_get_user(api_key: str, db: Session) -> User:
    """Validate API key and return associated user"""
    logger.info(f"🔍 SDK VALIDATE: Validating API key format (starts with jean_sk_: {api_key.startswith('jean_sk_')})")
    
    if not api_key.startswith("jean_sk_"):
        logger.error(f"❌ SDK VALIDATE: Invalid API key format - does not start with jean_sk_")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format"
        )
    
    from app.auth import hash_api_key
    logger.info(f"🔐 SDK VALIDATE: Hashing API key for database lookup")
    hashed_key = hash_api_key(api_key)
    
    logger.info(f"🔍 SDK VALIDATE: Querying database for API key")
    db_api_key = db.query(ApiKey).filter(
        ApiKey.key_hash == hashed_key,
        ApiKey.is_active == True
    ).first()
    
    if not db_api_key:
        logger.error(f"❌ SDK VALIDATE: API key not found in database or inactive")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key"
        )
    
    logger.info(f"✅ SDK VALIDATE: API key validated successfully for user {db_api_key.user.user_id}")
    return db_api_key.user

@router.post("/auth/login", response_model=UserLoginResponse)
async def sdk_auth_login(
    request: Request,
    credentials: UserLoginRequest,
    supabase_client: SupabaseClient = Depends(get_service_client),
    db: Session = Depends(get_db)
):
    """
    Authenticate a user for SDK-enabled applications.
    Returns tokens that can be used for SDK operations.
    """
    logger.info(f"🚀 SDK AUTH: Starting authentication for email: {credentials.email}")
    try:
        # Authenticate with Supabase using service client
        logger.info(f"🔐 SDK AUTH: Attempting Supabase authentication for {credentials.email}")
        auth_response = supabase_client.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        logger.info(f"✅ SDK AUTH: Supabase authentication response received for {credentials.email}")
        
        # Validate response structure
        if not auth_response or not auth_response.user or not auth_response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )
        
        supa_user = auth_response.user
        session = auth_response.session
        
        # Ensure user exists in our database
        logger.info(f"🔍 SDK AUTH: Checking if user {supa_user.id} exists in database")
        db_user = db.query(User).filter(User.user_id == str(supa_user.id)).first()
        if not db_user:
            logger.info(f"➕ SDK AUTH: Creating new user record for {supa_user.email}")
            db_user = User(
                user_id=str(supa_user.id),
                email=supa_user.email or credentials.email
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            logger.info(f"✅ SDK AUTH: New user created successfully")
        else:
            logger.info(f"✅ SDK AUTH: Existing user found in database")
        
        logger.info(f"🎉 SDK AUTH: Authentication successful for user {supa_user.email} (ID: {supa_user.id})")
        
        return UserLoginResponse(
            user_id=str(supa_user.id),
            email=supa_user.email,
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            expires_in=session.expires_in
        )
        
    except HTTPException as he:
        logger.error(f"❌ SDK AUTH: HTTP Exception - {he.detail} (status: {he.status_code})")
        raise
    except Exception as e:
        logger.error(f"💥 SDK AUTH: Unexpected error during authentication: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

@router.post("/validate-developer", response_model=Dict[str, str])
async def validate_developer_credentials(
    developer_request: DeveloperRequest,
    db: Session = Depends(get_db)
):
    """
    Validate developer API key and client name.
    Returns developer information if valid.
    """
    logger.info(f"🔑 SDK DEV: Validating developer API key for client: {developer_request.client_name}")
    try:
        user = await _validate_api_key_and_get_user(developer_request.api_key, db)
        logger.info(f"✅ SDK DEV: API key validated successfully for developer {user.user_id}")
        
        return {
            "status": "valid",
            "developer_id": str(user.user_id),
            "client_name": developer_request.client_name,
            "message": f"Developer authenticated for client: {developer_request.client_name}"
        }
        
    except HTTPException as he:
        logger.error(f"❌ SDK DEV: HTTP Exception - {he.detail} (status: {he.status_code})")
        raise
    except Exception as e:
        logger.error(f"💥 SDK DEV: Unexpected error during validation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Developer validation failed"
        )

@router.post("/chat/enhance", response_model=ChatResponse)
async def enhance_chat_with_context(
    request: Request,
    background_tasks: BackgroundTasks,
    chat_request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Enhance chat messages with user's Jean Memory context.
    This is the core SDK functionality for AI chatbot integration.
    """
    logger.info(f"💬 SDK CHAT: Starting chat enhancement for user {chat_request.user_id} via client {chat_request.client_name}")
    logger.info(f"💬 SDK CHAT: Processing {len(chat_request.messages)} message(s)")
    try:
        # Validate developer API key
        logger.info(f"🔐 SDK CHAT: Validating developer API key")
        developer_user = await _validate_api_key_and_get_user(chat_request.api_key, db)
        logger.info(f"✅ SDK CHAT: Developer API key validated for user {developer_user.user_id}")
        
        # Set context variables for MCP tools
        logger.info(f"🔧 SDK CHAT: Setting context variables for MCP tools")
        user_id_var.set(chat_request.user_id)
        client_name_var.set(chat_request.client_name)
        background_tasks_var.set(background_tasks)
        logger.info(f"✅ SDK CHAT: Context variables set successfully")
        
        # Get user's most recent message for context retrieval
        user_messages = [msg for msg in chat_request.messages if msg.role == "user"]
        if not user_messages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No user messages found to enhance"
            )
        
        latest_user_message = user_messages[-1].content
        
        # Retrieve relevant context using jean_memory tool  
        logger.info(f"🧠 SDK CHAT: Retrieving context for message: '{latest_user_message[:100]}...'")
        try:
            # Determine if this is a new conversation (first user message)
            is_new_conversation = len([msg for msg in chat_request.messages if msg.role == "user"]) == 1
            logger.info(f"🔧 SDK CHAT: Calling jean_memory with is_new_conversation={is_new_conversation}")
            
            # Call jean_memory with proper parameters - FIXED VERSION
            memory_result = await jean_memory(
                user_message=latest_user_message,
                is_new_conversation=is_new_conversation,
                needs_context=True
            )
            context_retrieved = True
            user_context = memory_result if memory_result else "No relevant context found"
            logger.info(f"✅ SDK CHAT: Context retrieved successfully (length: {len(user_context) if user_context else 0} chars)")
        except Exception as e:
            logger.warning(f"⚠️ SDK CHAT: Context retrieval failed: {str(e)}", exc_info=True)
            context_retrieved = False
            user_context = None
        
        # Enhance messages with system prompt and context
        enhanced_messages = []
        
        # Add system prompt if provided, enhanced with context
        if chat_request.system_prompt:
            system_content = chat_request.system_prompt
            if user_context:
                system_content += f"\n\nUser's relevant context from Jean Memory:\n{user_context}"
            
            enhanced_messages.append({
                "role": "system",
                "content": system_content
            })
        elif user_context:
            # Add context as system message if no custom system prompt
            enhanced_messages.append({
                "role": "system", 
                "content": f"User's relevant context from Jean Memory:\n{user_context}"
            })
        
        # Add all original messages
        for msg in chat_request.messages:
            enhanced_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        logger.info(f"🎉 SDK CHAT: Chat enhancement completed for user {chat_request.user_id} via client {chat_request.client_name}")
        logger.info(f"📊 SDK CHAT: Response contains {len(enhanced_messages)} enhanced message(s), context_retrieved={context_retrieved}")
        
        return ChatResponse(
            enhanced_messages=enhanced_messages,
            context_retrieved=context_retrieved,
            user_context=user_context
        )
        
    except HTTPException as he:
        logger.error(f"❌ SDK CHAT: HTTP Exception - {he.detail} (status: {he.status_code})")
        raise
    except Exception as e:
        logger.error(f"💥 SDK CHAT: Unexpected error during chat enhancement: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chat enhancement failed"
        )

@router.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize_natural_response(
    synthesize_request: SynthesizeRequest,
    db: Session = Depends(get_db)
):
    """
    Synthesize natural conversational responses using OpenAI
    Takes context from jean_memory and generates human-like responses
    """
    logger.info(f"🤖 SDK SYNTHESIZE: Starting synthesis for user {synthesize_request.user_id}")
    try:
        # Validate developer API key
        developer_user = await _validate_api_key_and_get_user(synthesize_request.api_key, db)
        logger.info(f"✅ SDK SYNTHESIZE: Developer API key validated for user {developer_user.user_id}")
        
        # Call OpenAI for natural response synthesis
        import openai
        import os
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OpenAI API key not configured"
            )
        
        client = openai.OpenAI(api_key=openai_key)
        
        logger.info(f"🤖 SDK SYNTHESIZE: Calling OpenAI with {len(synthesize_request.messages)} messages")
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": msg["role"], "content": msg["content"]} for msg in synthesize_request.messages],
            max_tokens=500,
            temperature=0.7
        )
        
        response_text = completion.choices[0].message.content.strip()
        logger.info(f"✅ SDK SYNTHESIZE: Generated {len(response_text)} character response")
        
        return SynthesizeResponse(response=response_text)
        
    except HTTPException as he:
        logger.error(f"❌ SDK SYNTHESIZE: HTTP Exception - {he.detail} (status: {he.status_code})")
        raise
    except Exception as e:
        logger.error(f"💥 SDK SYNTHESIZE: Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Response synthesis failed"
        )

@router.get("/health")
async def sdk_health_check():
    """Health check endpoint for SDK functionality"""
    logger.info("🏥 SDK HEALTH: Health check endpoint called")
    return {
        "status": "healthy",
        "service": "Jean Memory SDK",
        "endpoints": [
            "POST /sdk/auth/login",
            "POST /sdk/validate-developer", 
            "POST /sdk/chat/enhance",
            "POST /sdk/synthesize",
            "GET /sdk/health"
        ]
    }