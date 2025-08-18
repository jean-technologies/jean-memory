"""
LLM Judge & Scoring System for Jean Memory Evaluation
====================================================

Implements Gemini Flash and OpenAI GPT-5 powered automated evaluation that scores:
- Context relevance (0-10 scale) 
- Completeness evaluation
- Reasoning quality across LoCoMo reasoning types
- Long-range consistency across conversation sessions

Part of Task 2: LLM Judge & Scoring System
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

# LLM Provider imports
import google.generativeai as genai
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class ReasoningType(Enum):
    """LoCoMo reasoning types for evaluation"""
    SINGLE_HOP = "single_hop"  # Direct fact retrieval
    MULTI_HOP = "multi_hop"    # Cross-memory synthesis  
    TEMPORAL = "temporal"      # Time-based context
    COMMONSENSE = "commonsense"  # Background knowledge integration
    ADVERSARIAL = "adversarial"  # Conflicting information handling


class LLMProvider(Enum):
    """Supported LLM providers for judging"""
    GEMINI_FLASH = "gemini-2.5-flash"
    GEMINI_PRO = "gemini-2.5-pro"
    OPENAI_GPT5 = "gpt-5"
    OPENAI_GPT4O = "gpt-4o"


@dataclass
class JudgeScore:
    """Individual judge score with explanation"""
    relevance: float          # 0-10 scale
    completeness: float       # 0-10 scale  
    reasoning_quality: float  # 0-10 scale
    consistency: float        # 0-10 scale (for multi-session)
    overall: float           # Weighted average
    explanation: str         # Judge's reasoning
    reasoning_type: ReasoningType
    timestamp: datetime
    latency_ms: float
    provider: LLMProvider


@dataclass
class EvaluationContext:
    """Context for evaluation including query, retrieved memories, and response"""
    query: str
    retrieved_memories: List[str]
    generated_response: str
    conversation_history: Optional[List[Dict]] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    reasoning_type: Optional[ReasoningType] = None


class LLMJudgeService:
    """
    LLM-as-a-Judge service that evaluates Jean Memory's context relevance,
    completeness, reasoning quality, and consistency using multiple LLM providers.
    """
    
    def __init__(self):
        """Initialize LLM judge with multiple provider support"""
        self.gemini_model = None
        self.gemini_pro_model = None
        self.openai_client = None
        
        # Initialize providers based on available API keys
        self._init_gemini()
        self._init_openai()
        
        # Default provider preference: GPT-5 > Gemini Flash > Gemini Pro > GPT-4o
        self.default_provider = self._determine_default_provider()
        
        # Scoring weights for overall calculation
        self.score_weights = {
            "relevance": 0.35,      # How well retrieved memories match query
            "completeness": 0.25,   # Are all query requirements addressed
            "reasoning": 0.25,      # Quality of multi-hop/temporal reasoning
            "consistency": 0.15     # Cross-session coherence
        }
        
    def _init_gemini(self):
        """Initialize Gemini models if API key available"""
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
                self.gemini_pro_model = genai.GenerativeModel('gemini-2.5-pro')
                
                # Note: For now, we'll use the existing genai with better JSON parsing
                # The new structured output client isn't available in this version
                self.gemini_client = None
                
                logger.info("✅ Gemini models and client initialized")
            else:
                logger.warning("⚠️ GEMINI_API_KEY not found")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini: {e}")
            # Fallback to old client
            self.gemini_client = None
            
    def _init_openai(self):
        """Initialize OpenAI client if API key available"""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = AsyncOpenAI(api_key=api_key)
                logger.info("✅ OpenAI client initialized")
            else:
                logger.warning("⚠️ OPENAI_API_KEY not found")
        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenAI: {e}")
            
    def _determine_default_provider(self) -> LLMProvider:
        """Determine best available provider"""
        if self.openai_client:
            return LLMProvider.OPENAI_GPT5  # GPT-5 is newest and most powerful
        elif self.gemini_model:
            return LLMProvider.GEMINI_FLASH  # Fast and cost-effective
        elif self.gemini_pro_model:
            return LLMProvider.GEMINI_PRO
        elif self.openai_client:
            return LLMProvider.OPENAI_GPT4O
        else:
            raise ValueError("No LLM providers available - check API keys")
    
    async def evaluate_context(
        self, 
        context: EvaluationContext,
        provider: Optional[LLMProvider] = None
    ) -> JudgeScore:
        """
        Main evaluation method that scores context across all dimensions.
        """
        provider = provider or self.default_provider
        start_time = time.perf_counter()
        
        try:
            # Create comprehensive evaluation prompt
            prompt = self._create_evaluation_prompt(context)
            
            # Get LLM evaluation
            raw_response = await self._call_llm(prompt, provider)
            
            # Parse response into structured score
            score = self._parse_judge_response(raw_response, context, provider)
            
            # Add timing
            score.latency_ms = (time.perf_counter() - start_time) * 1000
            
            logger.info(f"🎯 Judge evaluation complete: {score.overall:.1f}/10 ({provider.value})")
            return score
            
        except Exception as e:
            logger.error(f"❌ Judge evaluation failed: {e}")
            # Return fallback score
            return self._create_fallback_score(context, provider, str(e))
    
    def _create_evaluation_prompt(self, context: EvaluationContext) -> str:
        """Create comprehensive evaluation prompt for LLM judge"""
        
        # Determine reasoning type if not specified
        reasoning_type = context.reasoning_type or self._infer_reasoning_type(context.query)
        
        base_prompt = f"""You are an expert evaluator for AI memory systems. Evaluate how well this AI retrieved and used relevant memories to answer a user query.

USER QUERY: "{context.query}"

RETRIEVED MEMORIES:
{self._format_memories(context.retrieved_memories)}

AI RESPONSE:
{context.generated_response}

REASONING TYPE: {reasoning_type.value.replace('_', ' ').title()}

Evaluate the AI's performance across these dimensions:

1. RELEVANCE (0-10): How well do the retrieved memories match the query intent?
   - 10: Perfect semantic match, exactly what's needed
   - 7-9: Highly relevant with minor gaps
   - 4-6: Somewhat relevant but missing key aspects  
   - 1-3: Mostly irrelevant or off-topic
   - 0: Completely irrelevant

2. COMPLETENESS (0-10): Are all query requirements addressed?
   - 10: Fully comprehensive answer covering all aspects
   - 7-9: Mostly complete with minor omissions
   - 4-6: Partial answer missing important elements
   - 1-3: Severely incomplete 
   - 0: No meaningful response to query

3. REASONING QUALITY (0-10): For {reasoning_type.value} queries, how well did the AI reason?"""

        # Add reasoning-specific criteria
        if reasoning_type == ReasoningType.SINGLE_HOP:
            base_prompt += """
   - 10: Direct, accurate fact retrieval with perfect precision
   - 7-9: Correct facts with minor presentation issues
   - 4-6: Generally correct but some inaccuracies
   - 1-3: Major factual errors or misunderstandings
   - 0: Completely incorrect or nonsensical"""
            
        elif reasoning_type == ReasoningType.MULTI_HOP:
            base_prompt += """
   - 10: Flawless synthesis across multiple memory sources
   - 7-9: Good cross-memory connections with minor gaps
   - 4-6: Some connections made but reasoning unclear
   - 1-3: Poor synthesis, missed connections
   - 0: No multi-hop reasoning attempted"""
            
        elif reasoning_type == ReasoningType.TEMPORAL:
            base_prompt += """
   - 10: Perfect temporal understanding and sequencing
   - 7-9: Good time-based context with minor issues
   - 4-6: Some temporal awareness but inconsistencies
   - 1-3: Poor time-based reasoning
   - 0: No temporal context considered"""
            
        elif reasoning_type == ReasoningType.ADVERSARIAL:
            base_prompt += """
   - 10: Expertly handled conflicting information with clear resolution
   - 7-9: Acknowledged conflicts and attempted resolution
   - 4-6: Noted conflicts but unclear resolution
   - 1-3: Ignored or poorly handled conflicts
   - 0: Contradictory or incoherent response"""

        # Add consistency evaluation for multi-session contexts
        consistency_section = ""
        if context.conversation_history:
            consistency_section = f"""

4. CONSISTENCY (0-10): How well does this response align with conversation history?
   - 10: Perfect coherence with prior context and established facts
   - 7-9: Generally consistent with minor inconsistencies
   - 4-6: Some contradictions or context drift
   - 1-3: Major inconsistencies with prior conversation
   - 0: Completely contradictory or incoherent

CONVERSATION HISTORY:
{self._format_conversation_history(context.conversation_history)}"""
        else:
            consistency_section = """

4. CONSISTENCY (0-10): N/A for single-turn evaluation
   - Score: N/A (will be excluded from overall calculation)"""

        # Response format
        response_format = """

RESPOND WITH VALID JSON:
{
  "relevance": <score 0-10>,
  "completeness": <score 0-10>, 
  "reasoning_quality": <score 0-10>,
  "consistency": <score 0-10 or null if N/A>,
  "explanation": "<detailed reasoning for each score>",
  "key_strengths": ["<strength 1>", "<strength 2>"],
  "key_weaknesses": ["<weakness 1>", "<weakness 2>"], 
  "improvement_suggestions": ["<suggestion 1>", "<suggestion 2>"]
}

Be precise, specific, and constructive in your evaluation."""

        return base_prompt + consistency_section + response_format
    
    def _format_memories(self, memories: List[str]) -> str:
        """Format retrieved memories for evaluation prompt"""
        if not memories:
            return "No memories retrieved."
        
        formatted = ""
        for i, memory in enumerate(memories, 1):
            formatted += f"Memory {i}: {memory}\n"
        return formatted.strip()
    
    def _format_conversation_history(self, history: List[Dict]) -> str:
        """Format conversation history for consistency evaluation"""
        if not history:
            return "No conversation history."
        
        formatted = ""
        for i, turn in enumerate(history[-5:], 1):  # Last 5 turns
            role = turn.get('role', 'unknown')
            content = turn.get('content', '')[:200] + "..." if len(turn.get('content', '')) > 200 else turn.get('content', '')
            formatted += f"Turn {i} ({role}): {content}\n"
        return formatted.strip()
    
    def _infer_reasoning_type(self, query: str) -> ReasoningType:
        """Infer reasoning type from query content"""
        query_lower = query.lower()
        
        # Temporal indicators
        temporal_keywords = ['when', 'before', 'after', 'during', 'since', 'until', 'timeline', 'chronological']
        if any(keyword in query_lower for keyword in temporal_keywords):
            return ReasoningType.TEMPORAL
        
        # Multi-hop indicators  
        multi_hop_keywords = ['compare', 'contrast', 'relationship', 'connection', 'how does', 'impact of', 'because']
        if any(keyword in query_lower for keyword in multi_hop_keywords):
            return ReasoningType.MULTI_HOP
        
        # Adversarial indicators
        adversarial_keywords = ['conflicting', 'contradiction', 'disagree', 'different', 'versus', 'but']
        if any(keyword in query_lower for keyword in adversarial_keywords):
            return ReasoningType.ADVERSARIAL
        
        # Default to single-hop for simple fact retrieval
        return ReasoningType.SINGLE_HOP
    
    async def _call_llm(self, prompt: str, provider: LLMProvider) -> str:
        """Call the specified LLM provider with retry logic"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                if provider in [LLMProvider.GEMINI_FLASH, LLMProvider.GEMINI_PRO]:
                    return await self._call_gemini(prompt, provider)
                elif provider in [LLMProvider.OPENAI_GPT5, LLMProvider.OPENAI_GPT4O]:
                    return await self._call_openai(prompt, provider)
                else:
                    raise ValueError(f"Unsupported provider: {provider}")
                    
            except Exception as e:
                logger.warning(f"⚠️ LLM call attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    async def _call_gemini(self, prompt: str, provider: LLMProvider) -> str:
        """Call Gemini API with appropriate model"""
        model = self.gemini_pro_model if provider == LLMProvider.GEMINI_PRO else self.gemini_model
        
        if not model:
            raise ValueError(f"Gemini model not initialized for {provider}")
        
        # Configure safety settings to disable all filters for evaluation
        safety_settings = {
            genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
        }
        
        response = await model.generate_content_async(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.3,  # Slightly higher for more creative content
                max_output_tokens=4096,  # Increased for longer responses
                candidate_count=1,
                top_p=0.95,
                top_k=40,
                response_mime_type="application/json"  # Request JSON format for structured output
            ),
            safety_settings=safety_settings
        )
        
        # Handle safety filter blocking
        if not response.text:
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback and hasattr(response.prompt_feedback, 'block_reason'):
                raise ValueError(f"Content blocked by safety filter: {response.prompt_feedback.block_reason}")
            elif hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason'):
                    raise ValueError(f"Content blocked, finish_reason: {candidate.finish_reason}")
            raise ValueError("Content blocked by safety filter (unknown reason)")
        
        return response.text
    
    async def _call_gemini_structured(self, prompt: str, response_schema: type, provider: LLMProvider = LLMProvider.GEMINI_FLASH) -> Any:
        """Call Gemini API with structured output using response_schema"""
        model = self.gemini_pro_model if provider == LLMProvider.GEMINI_PRO else self.gemini_model
        
        if not model:
            raise ValueError(f"Gemini model not initialized for {provider}")
        
        # Configure safety settings to disable all filters for evaluation
        safety_settings = {
            genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
        }
        
        try:
            # Use structured output with response_schema
            response = await model.generate_content_async(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,  # Lower temperature for consistency
                    max_output_tokens=1024,  # Reduced to prevent verbose responses
                    candidate_count=1,
                    top_p=0.8,  # More focused responses
                    top_k=20,   # Reduced for more deterministic output
                    response_mime_type="application/json",
                    response_schema=response_schema  # This enables structured output
                ),
                safety_settings=safety_settings
            )
            
            # Handle safety filter blocking
            if not response.text:
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback and hasattr(response.prompt_feedback, 'block_reason'):
                    raise ValueError(f"Content blocked by safety filter: {response.prompt_feedback.block_reason}")
                elif hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'finish_reason'):
                        raise ValueError(f"Content blocked, finish_reason: {candidate.finish_reason}")
                raise ValueError("Content blocked by safety filter (unknown reason)")
            
            # Parse the structured JSON response with robust cleaning
            import json
            import re
            import os
            from datetime import datetime
            
            raw_text = response.text.strip()
            
            # DEBUG: Save raw response to file for inspection (only if debug enabled)
            debug_enabled = os.getenv("DEBUG_JSON_RESPONSES", "false").lower() == "true"
            debug_file = None
            
            if debug_enabled:
                debug_dir = "/tmp/gemini_debug"
                os.makedirs(debug_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                debug_file = f"{debug_dir}/raw_response_{timestamp}.json"
                
                try:
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(raw_text)
                    logger.debug(f"Raw Gemini response saved to {debug_file}")
                except Exception as debug_e:
                    logger.warning(f"Could not save debug file: {debug_e}")
            
            # Clean common JSON issues
            try:
                # First attempt: direct parsing
                data = json.loads(raw_text)
                return response_schema(**data)
            except json.JSONDecodeError as e:
                if debug_enabled:
                    logger.debug(f"Initial JSON parse failed: {e}, attempting repair...")
                    logger.debug(f"JSON parse error at position {e.pos} in file {debug_file}")
                
                # Attempt 2: Clean and repair the JSON
                cleaned_text = self._repair_json(raw_text)
                
                if debug_enabled:
                    # Save cleaned version too
                    cleaned_file = f"{debug_dir}/cleaned_response_{timestamp}.json"
                    try:
                        with open(cleaned_file, 'w', encoding='utf-8') as f:
                            f.write(cleaned_text)
                        logger.debug(f"Cleaned response saved to {cleaned_file}")
                    except Exception as debug_e:
                        logger.warning(f"Could not save cleaned debug file: {debug_e}")
                
                try:
                    data = json.loads(cleaned_text)
                    return response_schema(**data)
                except json.JSONDecodeError as e2:
                    if debug_enabled:
                        logger.debug(f"JSON repair failed: {e2}, trying fallback extraction...")
                    
                    # Attempt 3: Extract JSON object manually
                    extracted_json = self._extract_json_object(raw_text)
                    if extracted_json:
                        if debug_enabled:
                            # Save extracted version
                            extracted_file = f"{debug_dir}/extracted_response_{timestamp}.json"
                            try:
                                with open(extracted_file, 'w', encoding='utf-8') as f:
                                    f.write(extracted_json)
                                logger.debug(f"Extracted JSON saved to {extracted_file}")
                            except Exception as debug_e:
                                logger.warning(f"Could not save extracted debug file: {debug_e}")
                        
                        try:
                            data = json.loads(extracted_json)
                            return response_schema(**data)
                        except json.JSONDecodeError as e3:
                            if debug_enabled:
                                logger.debug(f"Even extracted JSON failed: {e3}")
                    
                    # If all attempts fail, raise the original error
                    raise e
            
        except Exception as e:
            logger.error(f"❌ Structured output call failed: {e}")
            
            # Fallback to text-based parsing
            try:
                response_text = await self._call_gemini(prompt, provider)
                import json
                data = json.loads(response_text)
                return response_schema(**data)
            except Exception as fallback_e:
                logger.error(f"❌ Fallback parsing also failed: {fallback_e}")
                
                # Create a minimal fallback object based on the schema type
                if hasattr(response_schema, '__name__'):
                    schema_name = response_schema.__name__
                else:
                    schema_name = str(response_schema)
                
                fallback_data = {
                    "scenario_description": "Fallback scenario",
                    "memories": [
                        {"content": "User has interests", "days_ago": 7, "importance": 0.7}
                    ],
                    "query": "What are my interests?",
                    "expected_response": "Based on your memories, you have interests.",
                    "reasoning_explanation": "Fallback case"
                }
                
                # Add schema-specific required fields
                if "MultiHop" in schema_name:
                    fallback_data["hop_sequence"] = ["Memory provides context", "User has interests"]
                elif "Temporal" in schema_name:
                    fallback_data["temporal_span_days"] = 30
                    fallback_data["temporal_relationships"] = ["Memory relates to interests"]
                elif "Adversarial" in schema_name:
                    fallback_data["conflicting_info_count"] = 1
                    fallback_data["resolution_strategy"] = "Use recent information"
                elif "Commonsense" in schema_name:
                    fallback_data["commonsense_required"] = ["General knowledge"]
                
                return response_schema(**fallback_data)
    
    def _repair_json(self, text: str) -> str:
        """Repair common JSON formatting issues"""
        import re
        
        # Remove any text before the first { and after the last }
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx == -1 or end_idx == -1:
            return text
            
        json_text = text[start_idx:end_idx+1]
        
        # Fix common issues
        # 1. Remove trailing commas before } or ]
        json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
        
        # 2. Fix unterminated strings by adding closing quotes at line ends
        lines = json_text.split('\n')
        fixed_lines = []
        for line in lines:
            # Count quotes in line (excluding escaped quotes)
            quote_count = len(re.findall(r'(?<!\\)"', line))
            # If odd number of quotes, add closing quote at end
            if quote_count % 2 == 1 and not line.strip().endswith('"'):
                line = line.rstrip() + '"'
            fixed_lines.append(line)
        json_text = '\n'.join(fixed_lines)
        
        # 3. Remove control characters that aren't valid in JSON
        json_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_text)
        
        # 4. Fix common escape sequence issues
        json_text = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', json_text)
        
        return json_text
    
    def _extract_json_object(self, text: str) -> str:
        """Extract the main JSON object from text with better bracket matching"""
        import re
        
        # Find the first opening brace
        start = text.find('{')
        if start == -1:
            return None
            
        # Count braces to find matching closing brace
        brace_count = 0
        in_string = False
        escape_next = False
        
        for i, char in enumerate(text[start:], start):
            if escape_next:
                escape_next = False
                continue
                
            if char == '\\':
                escape_next = True
                continue
                
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
                
            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        return text[start:i+1]
        
        return None
    
    async def _call_openai(self, prompt: str, provider: LLMProvider) -> str:
        """Call OpenAI API with appropriate model"""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")
        
        model_name = provider.value  # "gpt-5" or "gpt-4o"
        
        # Use the correct API based on model
        if model_name == "gpt-5":
            # GPT-5 uses the new Responses API, not Chat Completions
            import httpx
            import json
            
            api_key = os.getenv("OPENAI_API_KEY")
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # GPT-5 Responses API payload
            # Modify prompt to ensure JSON output
            json_prompt = f"{prompt}\n\nIMPORTANT: You MUST respond with ONLY valid JSON. No other text before or after the JSON."
            
            payload = {
                "model": "gpt-5",
                "input": json_prompt,
                "reasoning": {"effort": "low"},  # For faster responses in evaluation
                "text": {"verbosity": "medium"}
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/responses",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    raise ValueError(f"GPT-5 API error: {response.status_code} - {response.text}")
                
                result = response.json()
                
                # GPT-5 Responses API has nested structure: output[1].content[0].text
                try:
                    # Navigate the nested response structure
                    output_items = result.get("output", [])
                    
                    # Find the message item (type: "message")
                    message_item = None
                    for item in output_items:
                        if item.get("type") == "message":
                            message_item = item
                            break
                    
                    if not message_item:
                        raise ValueError("No message item found in GPT-5 response")
                    
                    # Get the content from the message
                    content_items = message_item.get("content", [])
                    if not content_items:
                        raise ValueError("No content items found in GPT-5 message")
                    
                    # Get the text from the first content item
                    text_content = content_items[0].get("text", "")
                    
                    if not text_content or not text_content.strip():
                        raise ValueError("Empty text content in GPT-5 response")
                    
                    logger.debug(f"GPT-5 extracted text: {text_content[:200]}...")
                    return text_content.strip()
                    
                except (KeyError, IndexError, TypeError) as e:
                    logger.error(f"Failed to parse GPT-5 response structure: {e}")
                    logger.debug(f"Full GPT-5 response: {result}")
                    raise ValueError(f"Invalid GPT-5 response structure: {e}")
                
        elif model_name == "gpt-4o":
            # GPT-4o uses Chat Completions API
            response = await self.openai_client.chat.completions.create(
                model=model_name,
                messages=[{"role": "system", "content": prompt}],
                temperature=0.1,
                max_completion_tokens=2048,
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        else:
            # Legacy models
            response = await self.openai_client.chat.completions.create(
                model=model_name,
                messages=[{"role": "system", "content": prompt}],
                temperature=0.1,
                max_tokens=2048,
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
    
    def _parse_judge_response(
        self, 
        raw_response: str, 
        context: EvaluationContext, 
        provider: LLMProvider
    ) -> JudgeScore:
        """Parse LLM response into structured JudgeScore"""
        try:
            # Parse JSON response
            response_data = json.loads(raw_response)
            
            # Extract scores
            relevance = float(response_data.get("relevance", 0))
            completeness = float(response_data.get("completeness", 0))
            reasoning_quality = float(response_data.get("reasoning_quality", 0))
            consistency = response_data.get("consistency")
            consistency = float(consistency) if consistency is not None else None
            
            # Calculate overall score (weighted average)
            weights = self.score_weights.copy()
            if consistency is None:
                # Redistribute consistency weight if not applicable
                weights.pop("consistency")
                total_weight = sum(weights.values())
                weights = {k: v/total_weight for k, v in weights.items()}
            
            overall = (
                relevance * weights["relevance"] +
                completeness * weights["completeness"] + 
                reasoning_quality * weights["reasoning"] +
                (consistency * weights.get("consistency", 0) if consistency is not None else 0)
            )
            
            # Build explanation
            explanation = response_data.get("explanation", "No explanation provided")
            strengths = response_data.get("key_strengths", [])
            weaknesses = response_data.get("key_weaknesses", [])
            suggestions = response_data.get("improvement_suggestions", [])
            
            full_explanation = f"{explanation}\n\nStrengths: {', '.join(strengths)}\nWeaknesses: {', '.join(weaknesses)}\nSuggestions: {', '.join(suggestions)}"
            
            return JudgeScore(
                relevance=relevance,
                completeness=completeness,
                reasoning_quality=reasoning_quality,
                consistency=consistency or 0.0,
                overall=overall,
                explanation=full_explanation,
                reasoning_type=context.reasoning_type or self._infer_reasoning_type(context.query),
                timestamp=datetime.utcnow(),
                latency_ms=0.0,  # Will be set by caller
                provider=provider
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"❌ Failed to parse judge response: {e}")
            logger.debug(f"Raw response: {raw_response}")
            raise ValueError(f"Invalid judge response format: {e}")
    
    def _create_fallback_score(
        self, 
        context: EvaluationContext, 
        provider: LLMProvider, 
        error_msg: str
    ) -> JudgeScore:
        """Create fallback score when evaluation fails"""
        return JudgeScore(
            relevance=0.0,
            completeness=0.0,
            reasoning_quality=0.0,
            consistency=0.0,
            overall=0.0,
            explanation=f"Evaluation failed: {error_msg}",
            reasoning_type=context.reasoning_type or ReasoningType.SINGLE_HOP,
            timestamp=datetime.utcnow(),
            latency_ms=0.0,
            provider=provider
        )
    
    async def evaluate_batch(
        self, 
        contexts: List[EvaluationContext],
        provider: Optional[LLMProvider] = None
    ) -> List[JudgeScore]:
        """Evaluate multiple contexts in parallel"""
        tasks = [
            self.evaluate_context(context, provider) 
            for context in contexts
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to fallback scores
        scores = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                scores.append(self._create_fallback_score(
                    contexts[i], 
                    provider or self.default_provider, 
                    str(result)
                ))
            else:
                scores.append(result)
        
        return scores
    
    def calculate_aggregate_metrics(self, scores: List[JudgeScore]) -> Dict[str, Any]:
        """Calculate aggregate metrics from a list of judge scores"""
        if not scores:
            return {}
        
        valid_scores = [s for s in scores if s.overall > 0]  # Exclude failed evaluations
        
        if not valid_scores:
            return {"error": "No valid scores to aggregate"}
        
        def avg(values):
            return sum(values) / len(values)
        
        # Overall statistics
        metrics = {
            "count": len(scores),
            "valid_count": len(valid_scores),
            "success_rate": len(valid_scores) / len(scores),
            
            # Score averages
            "avg_relevance": avg([s.relevance for s in valid_scores]),
            "avg_completeness": avg([s.completeness for s in valid_scores]),
            "avg_reasoning_quality": avg([s.reasoning_quality for s in valid_scores]),
            "avg_consistency": avg([s.consistency for s in valid_scores if s.consistency > 0]),
            "avg_overall": avg([s.overall for s in valid_scores]),
            
            # Performance metrics
            "avg_latency_ms": avg([s.latency_ms for s in valid_scores]),
            "max_latency_ms": max([s.latency_ms for s in valid_scores]),
            
            # Provider breakdown
            "provider_breakdown": {},
            "reasoning_type_breakdown": {}
        }
        
        # Provider-specific metrics
        for provider in LLMProvider:
            provider_scores = [s for s in valid_scores if s.provider == provider]
            if provider_scores:
                metrics["provider_breakdown"][provider.value] = {
                    "count": len(provider_scores),
                    "avg_overall": avg([s.overall for s in provider_scores]),
                    "avg_latency_ms": avg([s.latency_ms for s in provider_scores])
                }
        
        # Reasoning type metrics  
        for reasoning_type in ReasoningType:
            type_scores = [s for s in valid_scores if s.reasoning_type == reasoning_type]
            if type_scores:
                metrics["reasoning_type_breakdown"][reasoning_type.value] = {
                    "count": len(type_scores),
                    "avg_overall": avg([s.overall for s in type_scores]),
                    "avg_relevance": avg([s.relevance for s in type_scores]),
                    "avg_completeness": avg([s.completeness for s in type_scores]),
                    "avg_reasoning_quality": avg([s.reasoning_quality for s in type_scores])
                }
        
        return metrics


# Singleton instance for global access
_judge_service = None

def get_judge_service() -> LLMJudgeService:
    """Get singleton LLM judge service instance"""
    global _judge_service
    if _judge_service is None:
        _judge_service = LLMJudgeService()
    return _judge_service


# Convenience functions for common evaluation patterns
async def evaluate_single_response(
    query: str,
    memories: List[str], 
    response: str,
    reasoning_type: Optional[ReasoningType] = None,
    provider: Optional[LLMProvider] = None
) -> JudgeScore:
    """Evaluate a single query-memory-response triplet"""
    context = EvaluationContext(
        query=query,
        retrieved_memories=memories,
        generated_response=response,
        reasoning_type=reasoning_type
    )
    
    judge = get_judge_service()
    return await judge.evaluate_context(context, provider)


async def evaluate_conversation_consistency(
    query: str,
    memories: List[str],
    response: str,
    conversation_history: List[Dict],
    session_id: str,
    provider: Optional[LLMProvider] = None
) -> JudgeScore:
    """Evaluate response consistency across conversation history"""
    context = EvaluationContext(
        query=query,
        retrieved_memories=memories,
        generated_response=response,
        conversation_history=conversation_history,
        session_id=session_id,
        reasoning_type=ReasoningType.TEMPORAL  # Consistency is temporal reasoning
    )
    
    judge = get_judge_service()
    return await judge.evaluate_context(context, provider)