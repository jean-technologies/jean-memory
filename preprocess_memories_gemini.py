#!/usr/bin/env python3
"""
Gemini Flash Memory Preprocessing Script
Uses Gemini Flash to extract temporal context from raw memories with structured output.
"""

import json
import os
import time
import argparse
from datetime import datetime
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def initialize_gemini_client():
    """Initialize Gemini client"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    return genai.Client(api_key=api_key)

def preprocess_memory_with_gemini(client, memory_data):
    """Process a single memory with Gemini Flash to extract temporal context"""
    
    # Prepare input text for Gemini
    input_text = f"""
Raw Memory Data:
- Content: {memory_data['content']}
- Created At: {memory_data['created_at']}
- Metadata: {json.dumps(memory_data.get('metadata', {}), indent=2)}

Please analyze this memory and extract:
1. Clean, well-formatted memory text (the actual memory content)
2. Temporal context - when did this memory/event likely occur based on the content and creation date

Consider:
- Temporal keywords in the content ("today", "yesterday", "last week", "July", etc.)
- The creation date as a reference point
- Context clues about when the event actually happened vs when it was recorded
- If no specific temporal context can be inferred, use the creation date
"""

    model = "gemini-2.0-flash"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=input_text),
            ],
        ),
    ]
    
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=genai.types.Schema(
            type=genai.types.Type.OBJECT,
            properties={
                "memory_text": genai.types.Schema(
                    type=genai.types.Type.STRING,
                    description="Clean, well-formatted memory text"
                ),
                "temporal_context": genai.types.Schema(
                    type=genai.types.Type.STRING,
                    description="Inferred temporal context - when the memory/event occurred"
                ),
                "temporal_keywords": genai.types.Schema(
                    type=genai.types.Type.ARRAY,
                    items=genai.types.Schema(type=genai.types.Type.STRING),
                    description="Temporal keywords found in the memory text"
                ),
                "confidence": genai.types.Schema(
                    type=genai.types.Type.STRING,
                    description="Confidence level: high, medium, low"
                ),
                "reasoning": genai.types.Schema(
                    type=genai.types.Type.STRING,
                    description="Brief explanation of temporal inference reasoning"
                )
            },
            required=["memory_text", "temporal_context"]
        ),
        system_instruction=[
            types.Part.from_text(text="""You are an expert at analyzing memories and extracting temporal context. 

Your task is to:
1. Clean and format the memory text (remove any artifacts, make it readable)
2. Infer when the memory/event actually occurred based on:
   - Temporal keywords in the text
   - Creation date as reference
   - Context clues about timing
3. Extract any temporal keywords you find
4. Assess your confidence in the temporal inference
5. Provide brief reasoning for your inference

Be precise and thoughtful in your temporal analysis."""),
        ],
    )

    try:
        # Generate content using streaming
        response_text = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            response_text += chunk.text
        
        # Parse the JSON response
        result = json.loads(response_text)
        return result
        
    except Exception as e:
        print(f"❌ Error processing memory with Gemini: {e}")
        # Fallback to basic processing
        return {
            "memory_text": memory_data['content'],
            "temporal_context": memory_data['created_at'],
            "temporal_keywords": [],
            "confidence": "low",
            "reasoning": "Gemini processing failed, using creation date"
        }

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
    parser = argparse.ArgumentParser(description='Preprocess memories using Gemini Flash')
    parser.add_argument('--input', required=True, help='Input JSON file with raw memories')
    parser.add_argument('--output', default='preprocessed_memories.json', help='Output file for preprocessed memories')
    
    args = parser.parse_args()
    
    print("🧠 Gemini Flash Memory Preprocessing")
    print("=" * 50)
    
    # Load raw memories
    raw_file = args.input
    if not os.path.exists(raw_file):
        print(f"❌ Raw memories file not found: {raw_file}")
        print("💡 Make sure the input file exists")
        return
    
    print(f"📂 Loading raw memories from '{raw_file}'...")
    raw_data = load_raw_memories(raw_file)
    
    if not raw_data:
        print("❌ Failed to load raw memories")
        return
    
    memories = raw_data.get('memories', [])
    print(f"📚 Found {len(memories)} raw memories to process")
    
    # Initialize Gemini client
    try:
        print("🚀 Initializing Gemini Flash client...")
        client = initialize_gemini_client()
        print("✅ Gemini client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Gemini client: {e}")
        return
    
    # Process memories with Gemini
    preprocessed_memories = []
    successful_count = 0
    
    print(f"\n🧠 Processing {len(memories)} memories with Gemini Flash...")
    print("-" * 60)
    
    for i, memory in enumerate(memories, 1):
        print(f"  📝 Processing Memory {i}/{len(memories)}: {memory['content'][:50]}...")
        
        # Add rate limiting to avoid API limits
        if i > 1:
            time.sleep(0.5)  # 500ms delay between requests
        
        try:
            # Process with Gemini
            gemini_result = preprocess_memory_with_gemini(client, memory)
            
            # Create preprocessed memory
            preprocessed_memory = {
                "id": memory['id'],
                "original_content": memory['content'],
                "memory_text": gemini_result['memory_text'],
                "temporal_context": gemini_result['temporal_context'],
                "temporal_keywords": gemini_result.get('temporal_keywords', []),
                "confidence": gemini_result.get('confidence', 'unknown'),
                "reasoning": gemini_result.get('reasoning', ''),
                "created_at": memory['created_at'],
                "updated_at": memory['updated_at'],
                "metadata": memory.get('metadata', {}),
                "gemini_processed": True
            }
            
            preprocessed_memories.append(preprocessed_memory)
            successful_count += 1
            
            print(f"      ✅ Success (confidence: {gemini_result.get('confidence', 'unknown')})")
            if gemini_result.get('temporal_keywords'):
                print(f"         Keywords: {gemini_result['temporal_keywords']}")
            
        except Exception as e:
            print(f"      ❌ Failed: {e}")
            # Add fallback memory
            fallback_memory = {
                "id": memory['id'],
                "original_content": memory['content'],
                "memory_text": memory['content'],
                "temporal_context": memory['created_at'],
                "temporal_keywords": [],
                "confidence": "low",
                "reasoning": "Gemini processing failed",
                "created_at": memory['created_at'],
                "updated_at": memory['updated_at'],
                "metadata": memory.get('metadata', {}),
                "gemini_processed": False
            }
            preprocessed_memories.append(fallback_memory)
    
    print(f"\n✅ Processing completed: {successful_count}/{len(memories)} successful")
    
    # Save preprocessed memories
    output_data = {
        "user_id": raw_data['user_id'],
        "preprocessing_timestamp": datetime.now().isoformat(),
        "total_memories": len(preprocessed_memories),
        "gemini_processed_count": successful_count,
        "gemini_failed_count": len(memories) - successful_count,
        "memories": preprocessed_memories
    }
    
    output_file = args.output
    if save_preprocessed_memories(output_data, output_file):
        print(f"💾 Saved preprocessed memories to '{output_file}'")
        print(f"📊 File size: {os.path.getsize(output_file) / 1024:.1f} KB")
    else:
        print("❌ Failed to save preprocessed memories")
    
    print(f"\n🎉 Preprocessing complete!")
    print(f"   📈 Success rate: {successful_count/len(memories)*100:.1f}%")

if __name__ == "__main__":
    main() 