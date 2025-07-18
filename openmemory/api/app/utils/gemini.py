"""
Gemini service for long-context document queries.
Uses Gemini 2.0 Flash for efficient processing of large documents.
"""
import os
import google.generativeai as genai
from typing import List, Dict, Union
from app.models import Document
import logging
import asyncio
import time

logger = logging.getLogger(__name__)


class GeminiService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        # Use Gemini 2.5 Flash - Google's latest hybrid reasoning model
        # Combines speed and cost-efficiency with adjustable thinking budgets
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Also initialize 2.5 Pro for complex reasoning tasks
        self.model_pro = genai.GenerativeModel('gemini-2.5-pro')
    
    async def generate_response(self, prompt: str, response_format: str = "text") -> Union[str, Dict]:
        start_time = time.time()
        logger.info(f"🤖 [GEMINI] Starting API call - Format: {response_format}")
        logger.debug(f"🤖 [GEMINI] Prompt length: {len(prompt)} chars")
        
        try:
            response = await self.model.generate_content_async(prompt)
            logger.info(f"⏱️ [GEMINI] API call completed: {time.time() - start_time:.2f}s")
            
            if response.candidates and response.candidates[0].finish_reason == 2: # 2 is 'SAFETY'
                logger.warning(f"⚠️ [GEMINI] Safety filter triggered for prompt: '{prompt[:100]}...'")
                
            return response.text
            
        except Exception as e:
            logger.error(f"❌ [GEMINI] API call failed after {time.time() - start_time:.2f}s: {e}")
            raise

    async def query_documents(self, documents: List[Document], query: str) -> str:
        """Query documents using Gemini's long context capabilities"""
        
        if not documents:
            return "No documents found to query."
        
        # Format documents into context
        context = "Here are the user's documents:\n\n"
        for i, doc in enumerate(documents, 1):
            context += f"--- Document {i}: {doc.title} ---\n"
            context += f"Type: {doc.document_type}\n"
            context += f"Source: {doc.source_url}\n"
            if doc.metadata_.get('published_date'):
                context += f"Published: {doc.metadata_['published_date']}\n"
            context += f"\nContent:\n{doc.content}\n\n"
            context += "--- End of Document ---\n\n"
        
        # Create the prompt
        prompt = f"""You are an intelligent assistant helping a user understand their saved documents.

{context}

User Query: {query}

Please analyze the documents above and provide a comprehensive answer to the user's query. 
Focus on extracting relevant information from the documents and synthesizing insights.
If the query asks about specific topics, make sure to reference which documents contain that information.
Be specific and cite document titles when referencing information."""

        try:
            # Use async generation
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=2048,
                )
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error querying Gemini: {e}")
            return f"Error querying documents with Gemini: {str(e)}"
    
    async def deep_query(self, documents: List[str], query: str) -> str:
        """Query documents using Gemini's long context capabilities"""
        try:
            full_text = "\n".join(documents)
            prompt = f"Based on the following documents, answer the question: {query}\n\n{full_text}"
            
            response = await self.model.generate_content_async(prompt)
            
            return response.text
        except Exception as e:
            logger.error(f"Error querying Gemini: {e}")
            return f"Error querying documents with Gemini: {str(e)}"
    
    async def _fallback_query(self, memories: List[Dict], documents: List[Document], query: str) -> str:
        """Fallback for when context is too large"""
        context = "=== RELEVANT CONTENT (Summarized) ===\n\n"
        
        # Add fewer memories
        context += "--- KEY MEMORIES ---\n"
        for i, mem in enumerate(memories, 1):
            memory_text = mem.get('memory', mem.get('content', ''))
            context += f"{i}. {memory_text[:200]}...\n"
        
        # Add document summaries only
        if documents:
            context += "\n--- DOCUMENT SUMMARIES ---\n"
            for i, doc in enumerate(documents, 1):
                context += f"{i}. {doc.title}: {doc.content[:500]}...\n"
        
        prompt = f"""{context}

User Query: {query}

Provide a helpful response based on the available content. Note that full document content was truncated due to length constraints."""
        
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=2048,
                )
            )
            return response.text
        except Exception as e:
            return f"Error in fallback query: {str(e)}"
    
    async def extract_insights(self, document_content: str, document_title: str) -> List[str]:
        """Extract key insights from a document"""
        
        prompt = f"""Extract 3-5 key insights from this document. Each insight should be:
- A complete, standalone statement
- Specific and actionable
- No more than 2 sentences

Document Title: {document_title}

Document Content:
{document_content[:8000]}  # Limit to first 8000 chars for insight extraction

Return only the insights, one per line, without numbering or bullet points."""

        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.5,
                    max_output_tokens=500,
                )
            )
            
            # Split response into individual insights
            insights = [line.strip() for line in response.text.split('\n') if line.strip()]
            return insights[:5]  # Limit to 5 insights
            
        except Exception as e:
            logger.error(f"Error extracting insights: {e}")
            return [] 

    async def generate_narrative(self, memories: List[str]) -> str:
        """Generate a user narrative from a list of memories."""
        try:
            if not memories:
                return "No memories provided to generate a narrative."

            full_text = "\n".join(memories)
            prompt = (
                "You are an expert biographer. Based on the following memories, write a brief, "
                "insightful, and coherent narrative about this person's life, focusing on key themes, "
                "growth, and recurring ideas. The narrative should be in the third person.\n\n"
                "Memories:\n"
                f"{full_text}"
            )
            
            # Use Pro model for narrative generation - higher quality for background processing
            response = await self.model_pro.generate_content_async(prompt)
            
            return response.text
        except Exception as e:
            logger.error(f"Error generating narrative with Gemini: {e}")
            raise Exception(f"Failed to generate narrative with Gemini: {str(e)}")
    
    async def generate_narrative_pro(self, memories_text: str, user_full_name: str = "") -> str:
        """
        Generate a high-quality user narrative using Gemini 2.5 Pro.
        Specifically designed for background batch processing where quality > speed.
        """
        try:
            prompt = f"""You are providing context for a conversation with this user. Analyze their memories and documents to create a rich, synthesized understanding that captures their fundamental essence.

USER'S MEMORIES AND CONTEXT:
{memories_text}

Create a comprehensive 'life narrative' structured to provide deep insight into who this person truly is. Write 3-4 substantial paragraphs covering:

**Core Identity & Philosophy**: Who they fundamentally are at their deepest level - their core values, philosophical framework, intellectual approach, and the driving forces that shape their worldview. What makes them uniquely themselves?

**Current Work & Trajectory**: What they're actively building, creating, or pursuing right now. How do their current projects and goals connect to their broader life mission? What patterns emerge in their professional and personal development?

**Communication & Interaction Style**: How they prefer to engage, think, and communicate. What energizes them in conversations? How do they process information and make decisions? What should others understand about working with or talking to them?

**Life Patterns & Evolution**: Recurring themes, growth trajectories, and key insights that define their journey. How do their experiences connect to reveal deeper truths about their character and direction?

Write with sophisticated psychological insight, connecting surface activities to deeper motivations and values. This narrative will prime AI conversations, so include nuanced understanding of their thinking patterns, decision-making style, and what truly matters to them."""
            
            # Use Pro model for maximum quality in background processing
            response = await self.model_pro.generate_content_async(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,  # Balanced creativity
                    max_output_tokens=4096,  # Allow longer, more comprehensive narratives
                )
            )
            
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error generating narrative with Gemini Pro: {e}")
            raise Exception(f"Failed to generate narrative with Gemini Pro: {str(e)}") 