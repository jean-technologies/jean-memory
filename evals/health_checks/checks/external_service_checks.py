"""
External service connectivity and health checks for Jean Memory
Tests OpenAI, Gemini, Supabase, Stripe, Twilio, and PostHog integrations
"""

import asyncio
import os
import sys
from typing import Dict, Any, Optional
import logging
import httpx
from datetime import datetime

# Add the API directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../openmemory/api'))

from .base import HealthCheck, HealthCheckResult

logger = logging.getLogger(__name__)

class ExternalServiceHealthCheck(HealthCheck):
    """External service connectivity health checks"""
    
    def __init__(self):
        super().__init__("External Services")
    
    async def run_checks(self, level: str = "critical") -> HealthCheckResult:
        """Run external service connectivity checks"""
        result = HealthCheckResult(self.name)
        
        # Core AI services (critical)
        await self._check_openai(result)
        await self._check_gemini(result)
        
        # Authentication service (critical)
        await self._check_supabase(result)
        
        # Optional integrations (only in comprehensive mode)
        if level == "comprehensive":
            await self._check_stripe(result)
            await self._check_twilio(result)
            await self._check_posthog(result)
        
        return result
    
    async def _check_openai(self, result: HealthCheckResult) -> None:
        """Check OpenAI API connectivity and embedding generation"""
        try:
            # Test 1: API key configuration
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                result.add_check("OpenAI - Configuration", False, "OPENAI_API_KEY not configured")
                return
            if not api_key.startswith('sk-'):
                result.add_check("OpenAI - Configuration", False, "Invalid OPENAI_API_KEY format")
                return
            result.add_check("OpenAI - Configuration", True, "API key configured")
            
            # Test 2: Import OpenAI client
            try:
                import openai
                result.add_check("OpenAI - Import", True, "OpenAI client imported successfully")
            except ImportError as e:
                result.add_check("OpenAI - Import", False, f"Import failed: {e}")
                return
            
            # Test 3: Basic API connectivity test
            try:
                client = openai.OpenAI(api_key=api_key)
                
                # Test with a minimal embedding request
                response = await asyncio.to_thread(
                    client.embeddings.create,
                    input="health check test",
                    model="text-embedding-3-small"
                )
                
                if response and response.data and len(response.data) > 0:
                    embedding_dim = len(response.data[0].embedding)
                    result.add_check("OpenAI - Embedding Test", True, 
                                   f"Successfully generated {embedding_dim}D embedding")
                else:
                    result.add_check("OpenAI - Embedding Test", False, "Invalid embedding response")
                    
            except Exception as e:
                result.add_check("OpenAI - Embedding Test", False, f"API call failed: {e}")
                
        except Exception as e:
            result.add_check("OpenAI - General", False, f"Unexpected error: {e}")
    
    async def _check_gemini(self, result: HealthCheckResult) -> None:
        """Check Gemini AI API connectivity"""
        try:
            # Test 1: API key configuration
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                result.add_check("Gemini - Configuration", False, "GEMINI_API_KEY not configured")
                return
            result.add_check("Gemini - Configuration", True, "API key configured")
            
            # Test 2: Import Gemini service
            try:
                from app.utils.gemini import GeminiService
                result.add_check("Gemini - Import", True, "Gemini service imported successfully")
            except ImportError as e:
                result.add_check("Gemini - Import", False, f"Import failed: {e}")
                return
            
            # Test 3: Basic generation test
            try:
                gemini_service = GeminiService()
                
                # Simple test prompt
                response = await gemini_service.generate_async(
                    "Respond with exactly: 'health check success'"
                )
                
                if response and "health check success" in response.lower():
                    result.add_check("Gemini - Generation Test", True, "Successfully generated response")
                else:
                    result.add_check("Gemini - Generation Test", False, 
                                   f"Unexpected response: {response[:100] if response else 'None'}")
                    
            except Exception as e:
                result.add_check("Gemini - Generation Test", False, f"API call failed: {e}")
                
        except Exception as e:
            result.add_check("Gemini - General", False, f"Unexpected error: {e}")
    
    async def _check_supabase(self, result: HealthCheckResult) -> None:
        """Check Supabase authentication service"""
        try:
            # Test 1: Configuration
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
            supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
            
            if not supabase_url:
                result.add_check("Supabase - Configuration", False, "SUPABASE_URL not configured")
                return
            if not supabase_anon_key:
                result.add_check("Supabase - Configuration", False, "SUPABASE_ANON_KEY not configured") 
                return
            if not supabase_service_key:
                result.add_check("Supabase - Configuration", False, "SUPABASE_SERVICE_KEY not configured")
                return
                
            result.add_check("Supabase - Configuration", True, f"Supabase configured: {supabase_url}")
            
            # Test 2: Import Supabase
            try:
                from supabase import create_client
                result.add_check("Supabase - Import", True, "Supabase client imported successfully")
            except ImportError as e:
                result.add_check("Supabase - Import", False, f"Import failed: {e}")
                return
            
            # Test 3: Basic connectivity test
            try:
                client = create_client(supabase_url, supabase_service_key)
                
                # Test auth endpoint with a simple request
                response = client.auth.get_session()
                # If we get here without error, the service is reachable
                result.add_check("Supabase - Connectivity", True, "Successfully connected to Supabase")
                
            except Exception as e:
                # Check if it's a network/auth issue vs service unavailable
                if "network" in str(e).lower() or "connection" in str(e).lower():
                    result.add_check("Supabase - Connectivity", False, f"Network error: {e}")
                else:
                    # Auth errors are expected with empty session, just means service is up
                    result.add_check("Supabase - Connectivity", True, "Supabase service reachable")
                
        except Exception as e:
            result.add_check("Supabase - General", False, f"Unexpected error: {e}")
    
    async def _check_stripe(self, result: HealthCheckResult) -> None:
        """Check Stripe billing service (optional)"""
        try:
            # Test 1: Configuration
            stripe_key = os.getenv('STRIPE_SECRET_KEY')
            if not stripe_key:
                result.add_warning("Stripe - Configuration", "STRIPE_SECRET_KEY not configured (optional)")
                return
            result.add_check("Stripe - Configuration", True, "Stripe key configured")
            
            # Test 2: Import
            try:
                import stripe
                result.add_check("Stripe - Import", True, "Stripe library imported successfully")
            except ImportError as e:
                result.add_check("Stripe - Import", False, f"Import failed: {e}")
                return
            
            # Test 3: Basic API test
            try:
                stripe.api_key = stripe_key
                
                # Simple API test - list payment methods (lightweight)
                response = await asyncio.to_thread(stripe.PaymentMethod.list, limit=1)
                result.add_check("Stripe - API Test", True, "Successfully connected to Stripe API")
                
            except Exception as e:
                result.add_check("Stripe - API Test", False, f"API call failed: {e}")
                
        except Exception as e:
            result.add_check("Stripe - General", False, f"Unexpected error: {e}")
    
    async def _check_twilio(self, result: HealthCheckResult) -> None:
        """Check Twilio SMS service (optional)"""
        try:
            # Test 1: Configuration
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            
            if not account_sid or not auth_token:
                result.add_warning("Twilio - Configuration", "Twilio credentials not configured (optional)")
                return
            result.add_check("Twilio - Configuration", True, "Twilio credentials configured")
            
            # Test 2: Import
            try:
                from twilio.rest import Client
                result.add_check("Twilio - Import", True, "Twilio client imported successfully")
            except ImportError as e:
                result.add_check("Twilio - Import", False, f"Import failed: {e}")
                return
            
            # Test 3: Basic connectivity test
            try:
                client = Client(account_sid, auth_token)
                
                # Test with account info (lightweight, no SMS sent)
                account = await asyncio.to_thread(lambda: client.api.accounts(account_sid).fetch())
                if account:
                    result.add_check("Twilio - Connectivity", True, f"Connected to account: {account.friendly_name}")
                else:
                    result.add_check("Twilio - Connectivity", False, "Failed to fetch account info")
                    
            except Exception as e:
                result.add_check("Twilio - Connectivity", False, f"Connection failed: {e}")
                
        except Exception as e:
            result.add_check("Twilio - General", False, f"Unexpected error: {e}")
    
    async def _check_posthog(self, result: HealthCheckResult) -> None:
        """Check PostHog analytics service (optional)"""
        try:
            # Test 1: Configuration
            posthog_key = os.getenv('POSTHOG_API_KEY')
            posthog_host = os.getenv('POSTHOG_HOST', 'https://app.posthog.com')
            
            if not posthog_key:
                result.add_warning("PostHog - Configuration", "POSTHOG_API_KEY not configured (optional)")
                return
            result.add_check("PostHog - Configuration", True, f"PostHog configured: {posthog_host}")
            
            # Test 2: Import
            try:
                import posthog
                result.add_check("PostHog - Import", True, "PostHog client imported successfully")
            except ImportError as e:
                result.add_check("PostHog - Import", False, f"Import failed: {e}")
                return
            
            # Test 3: Basic connectivity test
            try:
                # Configure PostHog
                posthog.api_key = posthog_key
                posthog.host = posthog_host
                
                # Test connection by checking if we can reach the service
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{posthog_host}/api/users/@me/", 
                                              headers={"Authorization": f"Bearer {posthog_key}"})
                    
                if response.status_code in [200, 401, 403]:  # Service is up
                    result.add_check("PostHog - Connectivity", True, "PostHog service reachable")
                else:
                    result.add_check("PostHog - Connectivity", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                result.add_check("PostHog - Connectivity", False, f"Connection failed: {e}")
                
        except Exception as e:
            result.add_check("PostHog - General", False, f"Unexpected error: {e}")