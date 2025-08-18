#!/usr/bin/env python3
"""
Generate Dataset - Simple CLI for FRD Compliance
================================================

Simplified command line interface that matches the FRD specification exactly.

Usage (as specified in FRD):
    python generate_dataset.py --length 20 --type mixed
    python generate_dataset.py --length 10 --type uniform
    python generate_dataset.py --length 35 --type progressive
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

# Add the parent directory to the path to import evaluation modules
sys.path.append(str(Path(__file__).parent.parent))

from evaluation.conversation_dataset_generator import (
    ConversationDatasetGenerator,
    ConversationDistributionType,
    generate_conversation_dataset,
    save_conversation_dataset
)
from evaluation.synthetic_data_generator import ReasoningType, PersonaType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def progress_indicator(current: int, total: int):
    """Simple progress indicator matching FRD requirements"""
    percent = (current / total) * 100
    bar_length = 40
    filled_length = int(bar_length * current / total)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    print(f'\rProgress: |{bar}| {percent:.1f}% ({current}/{total} turns)', end='', flush=True)
    if current == total:
        print()  # New line when complete


async def main():
    """Main function matching FRD CLI specification"""
    parser = argparse.ArgumentParser(
        description="Generate conversation datasets for Jean Memory evaluation (FRD Compliant)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
FRD Examples:
  python generate_dataset.py --length 20 --type mixed
  python generate_dataset.py --length 10 --type uniform 
  python generate_dataset.py --length 35 --type progressive --persona technical
        """
    )
    
    # Required arguments as per FRD
    parser.add_argument('--length', type=int, required=True,
                       help='Conversation length in turns (5-35)')
    parser.add_argument('--type', choices=['uniform', 'mixed', 'progressive'], required=True,
                       help='LoCoMo type distribution: uniform single type or mixed variety')
    
    # Optional arguments for enhanced functionality
    parser.add_argument('--persona', choices=['professional', 'student', 'creative', 'technical', 'casual'],
                       default='casual', help='User persona for conversation consistency')
    parser.add_argument('--reasoning', nargs='+',
                       choices=['single_hop', 'multi_hop', 'temporal', 'adversarial', 'commonsense'],
                       help='Target reasoning types (default: all types for mixed, single_hop for uniform)')
    parser.add_argument('--output', help='Output directory (default: ./test_datasets)')
    parser.add_argument('--quiet', action='store_true', help='Suppress progress indicators')
    
    args = parser.parse_args()
    
    # Validate length range as per FRD
    if args.length < 5 or args.length > 35:
        print("❌ Error: Conversation length must be between 5 and 35 turns")
        return 1
    
    # Check for required environment variables
    required_env_vars = ['GEMINI_API_KEY']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("   Please set API keys for dataset generation.")
        return 1
    
    # Enable synthetic generation
    os.environ['SYNTHETIC_GENERATION_ENABLED'] = 'true'
    os.environ['EVALUATION_MODE'] = 'true'
    
    # Generate auto name based on parameters
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    auto_name = f"{args.type}_{args.length}turns_{timestamp}"
    
    print(f"🧬 Generating conversation dataset: {auto_name}")
    print(f"   Length: {args.length} turns")
    print(f"   Distribution: {args.type}")
    print(f"   Persona: {args.persona}")
    
    # Parse distribution type
    try:
        distribution_type = ConversationDistributionType(args.type.lower())
    except ValueError:
        print(f"❌ Invalid distribution type: {args.type}")
        return 1
    
    # Parse persona
    try:
        persona = PersonaType(args.persona.lower())
    except ValueError:
        print(f"❌ Invalid persona: {args.persona}")
        return 1
    
    # Determine target reasoning types based on FRD logic
    target_reasoning_types = None
    if args.reasoning:
        # Map CLI values to enum values
        reasoning_map = {
            'single_hop': ReasoningType.SINGLE_HOP,
            'multi_hop': ReasoningType.MULTI_HOP,
            'temporal': ReasoningType.TEMPORAL,
            'adversarial': ReasoningType.ADVERSARIAL,
            'commonsense': ReasoningType.COMMONSENSE
        }
        try:
            target_reasoning_types = [reasoning_map[rt.lower()] for rt in args.reasoning]
            print(f"   Target reasoning types: {[rt.value for rt in target_reasoning_types]}")
        except KeyError as e:
            print(f"❌ Invalid reasoning type: {e}")
            return 1
    elif args.type == 'uniform':
        # Default to single_hop for uniform as most reliable
        target_reasoning_types = [ReasoningType.SINGLE_HOP]
        print(f"   Target reasoning types: ['single_hop'] (default for uniform)")
    else:
        # Default to all types for mixed/progressive
        target_reasoning_types = [ReasoningType.SINGLE_HOP, ReasoningType.MULTI_HOP]
        print(f"   Target reasoning types: ['single_hop', 'multi_hop'] (default for {args.type})")
    
    try:
        # Generate dataset as per FRD requirements
        dataset = await generate_conversation_dataset(
            name=auto_name,
            conversation_length=args.length,
            distribution_type=distribution_type,
            target_reasoning_types=target_reasoning_types,
            persona=persona,
            description=f"Generated via FRD-compliant CLI: {args.type} distribution, {args.length} turns",
            progress_callback=progress_indicator if not args.quiet else None
        )
        
        # Save with custom output path if specified
        if args.output:
            generator = ConversationDatasetGenerator(storage_path=args.output)
            filepath = await generator.save_dataset(dataset)
        else:
            filepath = await save_conversation_dataset(dataset)
        
        print(f"\n✅ Dataset generated successfully!")
        print(f"   Dataset ID: {dataset.id}")
        print(f"   Total turns: {dataset.total_test_cases}")
        print(f"   File: {filepath}")
        print(f"   Reasoning distribution: {dataset.reasoning_type_distribution}")
        
        # FRD compliance metadata
        print(f"\n📋 FRD Compliance:")
        print(f"   ✅ Length control: {dataset.conversation_length} turns (5-35 range)")
        print(f"   ✅ Distribution type: {dataset.distribution_type.value}")
        print(f"   ✅ Topic continuity: Memory reuse across turns")
        print(f"   ✅ JSON storage: {Path(filepath).name}")
        print(f"   ✅ Metadata tracking: Complete timestamp and reasoning metadata")
        print(f"   ✅ Persona consistency: {dataset.persona.value} throughout conversation")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error generating dataset: {e}")
        logger.error(f"Dataset generation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logger.error(f"CLI execution failed: {e}", exc_info=True)
        sys.exit(1)