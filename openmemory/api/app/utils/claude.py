"""
Claude Haiku service for fast strategy decisions.
Uses Claude Haiku 3.5 for ultra-fast, cost-effective simple reasoning tasks.
"""
import os
import anthropic
import logging
import time
from typing import Union, Dict

logger = logging.getLogger(__name__)


class ClaudeService:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        
    async def generate_response(self, prompt: str, model: str = "claude-3-5-haiku-20241022") -> str:
        """
        Generate response using Claude.
        
        Args:
            prompt: The prompt to send
            model: Model to use (default: claude-3-5-haiku for speed)
        """
        start_time = time.time()
        logger.info(f"🤖 [CLAUDE] Starting API call - Model: {model}")
        logger.debug(f"🤖 [CLAUDE] Prompt length: {len(prompt)} chars")
        
        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=1000,  # Keep low for strategy decisions
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            elapsed = time.time() - start_time
            logger.info(f"⏱️ [CLAUDE] API call completed: {elapsed:.2f}s")
            
            return response.content[0].text
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ [CLAUDE] API call failed after {elapsed:.2f}s: {e}")
            raise
    
    async def fast_strategy_decision(self, prompt: str) -> str:
        """Fast strategy decision using Haiku for sub-second response"""
        return await self.generate_response(prompt, model="claude-3-5-haiku-20241022")