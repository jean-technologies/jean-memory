import logging
import os
import secrets
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from jose import jwt
from sqlalchemy.orm import Session
from supabase import Client as SupabaseClient

from app.auth import get_or_create_user_from_provider, get_supabase_admin_client
from app.database import get_db
from app.settings import config

router = APIRouter()

# In-memory store for active OAuth flows. In production, use Redis or a database.
oauth_flows = {}
logger = logging.getLogger(__name__)

@router.get("/v1/sdk/oauth/authorize")
async def authorize(
    response_type: str,
    client_id: str,
    redirect_uri: str,
    state: str,
    code_challenge: str,
    code_challenge_method: str = "S256",
):
    if response_type != "code" or code_challenge_method != "S256":
        raise HTTPException(status_code=400, detail="Invalid request parameters.")

    oauth_flows[state] = {
        "code_challenge": code_challenge,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
    }

    # Use environment variables for Google credentials, falling back to placeholders
    google_client_id = os.getenv("GOOGLE_CLIENT_ID", "YOUR_GOOGLE_CLIENT_ID")
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8765")
    
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"response_type=code&"
        f"client_id={google_client_id}&"
        f"redirect_uri={api_base_url}/v1/sdk/oauth/callback&"
        f"scope=openid%20profile%20email&"
        f"state={state}&"
        f"access_type=offline"
    )
    return RedirectResponse(url=google_auth_url)

@router.get("/v1/sdk/oauth/callback")
async def callback(
    code: str,
    state: str,
    db: Session = Depends(get_db),
    supabase_admin: SupabaseClient = Depends(get_supabase_admin_client),
):
    flow = oauth_flows.get(state)
    if not flow:
        raise HTTPException(status_code=400, detail="Invalid state parameter.")

    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": os.getenv("GOOGLE_CLIENT_ID", "YOUR_GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", "YOUR_GOOGLE_CLIENT_SECRET"),
        "redirect_uri": f"{os.getenv('API_BASE_URL', 'http://localhost:8765')}/v1/sdk/oauth/callback",
        "grant_type": "authorization_code",
    }
    
    async with httpx.AsyncClient() as client:
        token_response = await client.post(token_url, data=token_data)
        token_json = token_response.json()

    if "error" in token_json:
        raise HTTPException(status_code=400, detail=token_json.get("error_description", "Unknown error from Google."))

    userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {"Authorization": f"Bearer {token_json['access_token']}"}
    async with httpx.AsyncClient() as client:
        userinfo_response = await client.get(userinfo_url, headers=headers)
        userinfo = userinfo_response.json()

    user = await get_or_create_user_from_provider(
        provider_email=userinfo["email"],
        provider_user_id=userinfo["id"],
        provider_name="google",
        db=db,
        supabase_admin=supabase_admin,
    )

    auth_code = secrets.token_urlsafe(32)
    oauth_flows[state]["auth_code"] = auth_code
    oauth_flows[state]["user_id"] = str(user.id)

    redirect_url = f"{flow['redirect_uri']}?code={auth_code}&state={state}"
    return RedirectResponse(url=redirect_url)

@router.post("/v1/sdk/oauth/token")
async def token(request: Request):
    form = await request.form()
    code = form.get("code")
    redirect_uri = form.get("redirect_uri")
    client_id = form.get("client_id")
    code_verifier = form.get("code_verifier")
    
    # Find the state associated with the authorization code
    state = None
    for s, data in oauth_flows.items():
        if data.get("auth_code") == code:
            state = s
            break
            
    if not state:
        raise HTTPException(status_code=400, detail="Invalid or expired authorization code.")
        
    flow = oauth_flows[state]
    # Basic validation
    if flow["redirect_uri"] != redirect_uri or flow["client_id"] != client_id:
        raise HTTPException(status_code=400, detail="Mismatched redirect_uri or client_id.")

    # In a real PKCE flow, you would verify the code_verifier against the code_challenge
    
    user_id = flow["user_id"]
    jwt_secret = os.getenv("JWT_SECRET", "a_very_secret_key")
    
    jwt_payload = {
        "sub": user_id,
        "iss": os.getenv("API_BASE_URL", "http://localhost:8765"),
        "aud": "jean-memory-sdk",
        "client_id": client_id,
    }
    
    encoded_jwt = jwt.encode(jwt_payload, jwt_secret, algorithm="HS256")
    
    del oauth_flows[state]

    return JSONResponse(content={"access_token": encoded_jwt, "token_type": "bearer"})
