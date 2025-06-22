#!/usr/bin/env python3
"""
Gemini Flash Batch Memory Preprocessing Script
Processes multiple memories in batches to optimize API usage and reduce costs.
"""

import json
import os
import time
import argparse
import math
from datetime import datetime
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class BatchMemoryProcessor:
    """Handles batch processing of memories with cost optimization"""
    
    def __init__(self, batch_size=10, max_tokens_per_batch=8000):
        """
        Initialize batch processor
        
        Args:
            batch_size: Number of memories to process per batch (default: 10)
            max_tokens_per_batch: Maximum tokens per batch to stay within context limits
        """
        self.batch_size = batch_size
        self.max_tokens_per_batch = max_tokens_per_batch
        self.client = None
        self.total_api_calls = 0
        self.total_tokens_used = 0
        
    def initialize_gemini_client(self):
        """Initialize Gemini client"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        self.client = genai.Client(api_key=api_key)
        return self.client

    def estimate_tokens(self, text):
        """Rough token estimation (1 token ≈ 4 characters)"""
        return len(text) // 4

    def create_batch_prompt(self, memories_batch):
        """Create a batch prompt for multiple memories"""
        
        batch_prompt = """
I will provide you with a batch of memories to process. For each memory, extract:
1. Clean, well-formatted memory text
2. Temporal context - when the memory/event likely occurred
3. Temporal keywords found in the text
4. Confidence level (high/medium/low)
5. Brief reasoning for temporal inference

Please process ALL memories in this batch and return a JSON array with one object per memory.

MEMORIES TO PROCESS:
"""
        
        for i, memory in enumerate(memories_batch):
            batch_prompt += f"""
--- MEMORY {i+1} ---
ID: {memory['id']}
Content: {memory['content']}
Created At: {memory['created_at']}
Metadata: {json.dumps(memory.get('metadata', {}), indent=2)}
"""
        
        batch_prompt += """

IMPORTANT INSTRUCTIONS:
- Return ONLY a valid JSON array
- Each array element should correspond to one memory in the same order
- Use this exact schema for each memory object:
{
  "memory_id": "string (the ID from input)",
  "memory_text": "string (cleaned memory content)",
  "temporal_context": "string (when the event occurred)",
  "temporal_keywords": ["array", "of", "keywords"],
  "confidence": "high|medium|low",
  "reasoning": "string (brief explanation)"
}

Consider temporal keywords like: today, yesterday, last week, this morning, July, 2023, etc.
If no temporal context can be inferred, use the creation date and mark confidence as "low".
"""
        
        return batch_prompt

    def process_batch_with_gemini(self, memories_batch):
        """Process a batch of memories with Gemini Flash"""
        
        batch_prompt = self.create_batch_prompt(memories_batch)
        
        # Estimate tokens to ensure we're within limits
        estimated_tokens = self.estimate_tokens(batch_prompt)
        if estimated_tokens > self.max_tokens_per_batch:
            print(f"⚠️  Batch too large ({estimated_tokens} tokens), splitting...")
            # Split batch in half and process recursively
            mid = len(memories_batch) // 2
            batch1 = memories_batch[:mid]
            batch2 = memories_batch[mid:]
            
            results1 = self.process_batch_with_gemini(batch1) if batch1 else []
            results2 = self.process_batch_with_gemini(batch2) if batch2 else []
            
            return results1 + results2

        model = "gemini-2.0-flash"
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=batch_prompt)],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            system_instruction=[
                types.Part.from_text(text="""You are an expert at analyzing memories and extracting temporal context in batches. 

Process each memory carefully and return a valid JSON array with exactly one object per input memory, in the same order.

Focus on:
1. Cleaning and formatting memory text
2. Inferring when events actually occurred vs when they were recorded
3. Finding temporal keywords and patterns
4. Assessing confidence in your temporal inference
5. Providing clear reasoning

Be efficient but thorough in your batch analysis."""),
            ],
        )

        try:
            # Generate content using streaming
            response_text = ""
            for chunk in self.client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            ):
                response_text += chunk.text
            
            # Track API usage
            self.total_api_calls += 1
            self.total_tokens_used += estimated_tokens
            
            # Parse the JSON response
            results = json.loads(response_text)
            
            # Validate that we got the right number of results
            if len(results) != len(memories_batch):
                print(f"⚠️  Expected {len(memories_batch)} results, got {len(results)}")
                # Pad with fallback results if needed
                while len(results) < len(memories_batch):
                    missing_memory = memories_batch[len(results)]
                    results.append({
                        "memory_id": missing_memory['id'],
                        "memory_text": missing_memory['content'],
                        "temporal_context": missing_memory['created_at'],
                        "temporal_keywords": [],
                        "confidence": "low",
                        "reasoning": "Missing from batch response"
                    })
            
            return results
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"Raw response: {response_text[:200]}...")
            # Return fallback results
            return self._create_fallback_results(memories_batch, "JSON parsing failed")
            
        except Exception as e:
            print(f"❌ Error processing batch with Gemini: {e}")
            return self._create_fallback_results(memories_batch, f"API error: {str(e)}")

    def _create_fallback_results(self, memories_batch, error_reason):
        """Create fallback results when Gemini processing fails"""
        fallback_results = []
        for memory in memories_batch:
            fallback_results.append({
                "memory_id": memory['id'],
                "memory_text": memory['content'],
                "temporal_context": memory['created_at'],
                "temporal_keywords": [],
                "confidence": "low",
                "reasoning": error_reason
            })
        return fallback_results

    def optimize_batch_size(self, memories_sample):
        """Dynamically optimize batch size based on memory content length"""
        if not memories_sample:
            return self.batch_size
        
        # Calculate average memory size
        avg_memory_size = sum(len(m['content']) for m in memories_sample[:10]) / min(10, len(memories_sample))
        
        # Estimate optimal batch size to stay under token limit
        estimated_tokens_per_memory = self.estimate_tokens(str(avg_memory_size)) + 100  # Add overhead
        optimal_batch_size = max(1, self.max_tokens_per_batch // (estimated_tokens_per_memory * 2))  # Conservative
        
        # Cap at reasonable limits
        optimal_batch_size = min(optimal_batch_size, 20)  # Max 20 memories per batch
        optimal_batch_size = max(optimal_batch_size, 3)   # Min 3 memories per batch
        
        print(f"📊 Optimized batch size: {optimal_batch_size} (avg memory size: {avg_memory_size:.0f} chars)")
        return optimal_batch_size

    def process_all_memories(self, memories):
        """Process all memories in optimized batches"""
        if not memories:
            return []
        
        # Optimize batch size based on content
        optimized_batch_size = self.optimize_batch_size(memories)
        
        total_batches = math.ceil(len(memories) / optimized_batch_size)
        all_results = []
        successful_count = 0
        
        print(f"🚀 Processing {len(memories)} memories in {total_batches} batches (size: {optimized_batch_size})")
        print("-" * 80)
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * optimized_batch_size
            end_idx = min(start_idx + optimized_batch_size, len(memories))
            batch = memories[start_idx:end_idx]
            
            print(f"📦 Batch {batch_idx + 1}/{total_batches}: Processing memories {start_idx + 1}-{end_idx}...")
            
            # Add rate limiting between batches
            if batch_idx > 0:
                time.sleep(1.0)  # 1 second delay between batches
            
            try:
                batch_results = self.process_batch_with_gemini(batch)
                
                # Convert batch results to full memory objects
                for i, result in enumerate(batch_results):
                    original_memory = batch[i]
                    
                    preprocessed_memory = {
                        "id": original_memory['id'],
                        "original_content": original_memory['content'],
                        "memory_text": result['memory_text'],
                        "temporal_context": result['temporal_context'],
                        "temporal_keywords": result.get('temporal_keywords', []),
                        "confidence": result.get('confidence', 'unknown'),
                        "reasoning": result.get('reasoning', ''),
                        "created_at": original_memory['created_at'],
                        "updated_at": original_memory['updated_at'],
                        "metadata": original_memory.get('metadata', {}),
                        "gemini_processed": True,
                        "batch_processed": True,
                        "batch_number": batch_idx + 1
                    }
                    
                    all_results.append(preprocessed_memory)
                    
                    if result.get('confidence') != 'low':
                        successful_count += 1
                
                print(f"      ✅ Batch completed: {len(batch_results)} memories processed")
                
                # Show some sample results
                high_confidence_results = [r for r in batch_results if r.get('confidence') == 'high']
                if high_confidence_results:
                    sample = high_confidence_results[0]
                    print(f"         Sample: {sample.get('temporal_keywords', [])} -> {sample.get('confidence')}")
                
            except Exception as e:
                print(f"      ❌ Batch failed: {e}")
                # Add fallback results for this batch
                fallback_results = self._create_fallback_results(batch, f"Batch processing failed: {str(e)}")
                for i, result in enumerate(fallback_results):
                    original_memory = batch[i]
                    fallback_memory = {
                        "id": original_memory['id'],
                        "original_content": original_memory['content'],
                        "memory_text": result['memory_text'],
                        "temporal_context": result['temporal_context'],
                        "temporal_keywords": result.get('temporal_keywords', []),
                        "confidence": result.get('confidence', 'low'),
                        "reasoning": result.get('reasoning', ''),
                        "created_at": original_memory['created_at'],
                        "updated_at": original_memory['updated_at'],
                        "metadata": original_memory.get('metadata', {}),
                        "gemini_processed": False,
                        "batch_processed": True,
                        "batch_number": batch_idx + 1
                    }
                    all_results.append(fallback_memory)
        
        print(f"\n✅ Batch processing completed!")
        print(f"   📊 Total API calls: {self.total_api_calls} (vs {len(memories)} individual calls)")
        print(f"   💰 Cost reduction: ~{((len(memories) - self.total_api_calls) / len(memories)) * 100:.1f}%")
        print(f"   📈 High-confidence results: {successful_count}/{len(memories)} ({successful_count/len(memories)*100:.1f}%)")
        
        return all_results

def load_raw_memories(file_path):
    """Load raw memories from JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"❌ Error loading raw memories: {e}")
        return None

def save_preprocessed_memories(memories, output_file):
    """Save preprocessed memories to JSON file"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(memories, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ Error saving preprocessed memories: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Batch preprocess memories using Gemini Flash')
    parser.add_argument('--input', required=True, help='Input JSON file with raw memories')
    parser.add_argument('--output', default='preprocessed_memories_batch.json', help='Output file for preprocessed memories')
    parser.add_argument('--batch-size', type=int, default=10, help='Number of memories per batch (default: 10)')
    parser.add_argument('--max-tokens', type=int, default=8000, help='Maximum tokens per batch (default: 8000)')
    parser.add_argument('--dry-run', action='store_true', help='Show batch plan without processing')
    
    args = parser.parse_args()
    
    print("🧠 Gemini Flash Batch Memory Preprocessing")
    print("=" * 60)
    
    # Load raw memories
    if not os.path.exists(args.input):
        print(f"❌ Input file not found: {args.input}")
        return
    
    print(f"📂 Loading memories from '{args.input}'...")
    raw_data = load_raw_memories(args.input)
    
    if not raw_data:
        print("❌ Failed to load raw memories")
        return
    
    memories = raw_data.get('memories', [])
    print(f"📚 Found {len(memories)} memories to process")
    
    # Initialize batch processor
    processor = BatchMemoryProcessor(
        batch_size=args.batch_size,
        max_tokens_per_batch=args.max_tokens
    )
    
    # Optimize batch size
    optimized_batch_size = processor.optimize_batch_size(memories)
    total_batches = math.ceil(len(memories) / optimized_batch_size)
    
    print(f"📊 Batch Processing Plan:")
    print(f"   - Original batch size: {args.batch_size}")
    print(f"   - Optimized batch size: {optimized_batch_size}")
    print(f"   - Total batches: {total_batches}")
    print(f"   - Estimated API calls: {total_batches} (vs {len(memories)} individual)")
    print(f"   - Estimated cost reduction: ~{((len(memories) - total_batches) / len(memories)) * 100:.1f}%")
    
    if args.dry_run:
        print("\n🔍 Dry run completed - no processing performed")
        return
    
    # Initialize Gemini client
    try:
        print("\n🚀 Initializing Gemini Flash client...")
        processor.initialize_gemini_client()
        print("✅ Gemini client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Gemini client: {e}")
        return
    
    # Process all memories in batches
    preprocessed_memories = processor.process_all_memories(memories)
    
    if not preprocessed_memories:
        print("❌ No memories were processed successfully")
        return
    
    # Calculate statistics
    gemini_processed = sum(1 for m in preprocessed_memories if m.get('gemini_processed', False))
    high_confidence = sum(1 for m in preprocessed_memories if m.get('confidence') == 'high')
    medium_confidence = sum(1 for m in preprocessed_memories if m.get('confidence') == 'medium')
    
    # Save results
    output_data = {
        "user_id": raw_data['user_id'],
        "preprocessing_timestamp": datetime.now().isoformat(),
        "processing_method": "batch",
        "batch_size_used": optimized_batch_size,
        "total_memories": len(preprocessed_memories),
        "total_api_calls": processor.total_api_calls,
        "estimated_tokens_used": processor.total_tokens_used,
        "gemini_processed_count": gemini_processed,
        "high_confidence_count": high_confidence,
        "medium_confidence_count": medium_confidence,
        "cost_reduction_percentage": ((len(memories) - processor.total_api_calls) / len(memories)) * 100,
        "memories": preprocessed_memories
    }
    
    if save_preprocessed_memories(output_data, args.output):
        print(f"\n💾 Saved preprocessed memories to '{args.output}'")
        print(f"📊 File size: {os.path.getsize(args.output) / 1024:.1f} KB")
    else:
        print("❌ Failed to save preprocessed memories")
        return
    
    print(f"\n🎉 Batch preprocessing complete!")
    print(f"   📊 Processed: {len(preprocessed_memories)} memories")
    print(f"   🤖 Gemini processed: {gemini_processed} ({gemini_processed/len(preprocessed_memories)*100:.1f}%)")
    print(f"   🎯 High confidence: {high_confidence} ({high_confidence/len(preprocessed_memories)*100:.1f}%)")
    print(f"   📞 API calls: {processor.total_api_calls} (saved {len(memories) - processor.total_api_calls} calls)")
    print(f"   💰 Cost reduction: ~{output_data['cost_reduction_percentage']:.1f}%")

if __name__ == "__main__":
    main() 