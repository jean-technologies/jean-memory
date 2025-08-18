#!/usr/bin/env python3
"""
Conversation Dataset Generator CLI
=================================

Command-line interface for generating conversation datasets using Task 3 synthetic generator.

Usage:
    python dataset_cli.py --length 20 --type mixed --persona casual --name "Test Dataset"
    python dataset_cli.py --length 10 --type uniform --reasoning SINGLE_HOP --output ./datasets
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def progress_indicator(current: int, total: int):
    """Simple progress indicator"""
    percent = (current / total) * 100
    bar_length = 40
    filled_length = int(bar_length * current / total)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    print(f'\rProgress: |{bar}| {percent:.1f}% ({current}/{total} turns)', end='', flush=True)
    if current == total:
        print()  # New line when complete


async def generate_dataset_command(args):
    """Generate a new conversation dataset"""
    print(f"🧬 Generating conversation dataset: {args.name}")
    print(f"   Length: {args.length} turns")
    print(f"   Distribution: {args.type}")
    print(f"   Persona: {args.persona}")
    
    # Parse reasoning types if specified
    target_reasoning_types = None
    if args.reasoning:
        try:
            # Map CLI values to enum values
            reasoning_map = {
                'single_hop': ReasoningType.SINGLE_HOP,
                'multi_hop': ReasoningType.MULTI_HOP,
                'temporal': ReasoningType.TEMPORAL,
                'adversarial': ReasoningType.ADVERSARIAL,
                'commonsense': ReasoningType.COMMONSENSE
            }
            target_reasoning_types = [reasoning_map[rt.lower()] for rt in args.reasoning]
            print(f"   Target reasoning types: {[rt.value for rt in target_reasoning_types]}")
        except KeyError as e:
            print(f"❌ Invalid reasoning type: {e}")
            return 1
    
    try:
        # Parse distribution type
        distribution_type = ConversationDistributionType(args.type.lower())
        
        # Parse persona
        persona = PersonaType(args.persona.lower())
        
        # Generate dataset
        dataset = await generate_conversation_dataset(
            name=args.name,
            conversation_length=args.length,
            distribution_type=distribution_type,
            target_reasoning_types=target_reasoning_types,
            persona=persona,
            description=args.description,
            progress_callback=progress_indicator if not args.quiet else None
        )
        
        # Set custom output path if specified
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
        
        return 0
        
    except Exception as e:
        print(f"❌ Error generating dataset: {e}")
        logger.error(f"Dataset generation failed: {e}", exc_info=True)
        return 1


async def validate_dataset_command(args):
    """Validate an existing dataset"""
    print(f"🔍 Validating dataset: {args.file}")
    
    try:
        generator = ConversationDatasetGenerator(require_generator=False)
        dataset = await generator.load_dataset(args.file)
        
        print(f"   Dataset: {dataset.name}")
        print(f"   ID: {dataset.id}")
        print(f"   Length: {dataset.conversation_length} turns")
        
        validation_results = await generator.validate_dataset(dataset)
        
        if validation_results["valid"]:
            print("✅ Dataset validation passed!")
        else:
            print("❌ Dataset validation failed!")
            for issue in validation_results["issues"]:
                print(f"   Issue: {issue}")
        
        print(f"\n📊 Statistics:")
        stats = validation_results["statistics"]
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        return 0 if validation_results["valid"] else 1
        
    except Exception as e:
        print(f"❌ Error validating dataset: {e}")
        logger.error(f"Dataset validation failed: {e}", exc_info=True)
        return 1


def list_datasets_command(args):
    """List available datasets"""
    output_path = Path(args.output) if args.output else Path("./test_datasets")
    
    if not output_path.exists():
        print(f"📁 No datasets found in {output_path}")
        return 0
    
    json_files = list(output_path.glob("conversation_*.json"))
    
    if not json_files:
        print(f"📁 No conversation datasets found in {output_path}")
        return 0
    
    print(f"📁 Found {len(json_files)} conversation datasets in {output_path}:")
    
    for filepath in sorted(json_files):
        file_size = filepath.stat().st_size / 1024  # KB
        modified_time = filepath.stat().st_mtime
        print(f"   {filepath.name} ({file_size:.1f} KB)")
    
    return 0


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Generate conversation datasets for Jean Memory evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate mixed 20-turn conversation
  python dataset_cli.py generate --length 20 --type mixed --name "Mixed Test"
  
  # Generate uniform single-hop conversation
  python dataset_cli.py generate --length 10 --type uniform --reasoning single_hop
  
  # Generate progressive conversation with technical persona
  python dataset_cli.py generate --length 15 --type progressive --persona technical
  
  # Validate existing dataset
  python dataset_cli.py validate --file ./test_datasets/conversation_test_20250816_143022.json
  
  # List available datasets
  python dataset_cli.py list --output ./custom_datasets
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate new conversation dataset')
    generate_parser.add_argument('--name', required=True, help='Dataset name')
    generate_parser.add_argument('--length', type=int, required=True, 
                                help='Conversation length (5-35 turns)')
    generate_parser.add_argument('--type', choices=['mixed', 'uniform', 'progressive'], 
                                default='mixed', help='Distribution type')
    generate_parser.add_argument('--reasoning', nargs='+', 
                                choices=['single_hop', 'multi_hop', 'temporal', 'adversarial', 'commonsense'],
                                help='Target reasoning types (default: all types)')
    generate_parser.add_argument('--persona', choices=['professional', 'student', 'creative', 'technical', 'casual'],
                                default='casual', help='User persona')
    generate_parser.add_argument('--description', help='Dataset description')
    generate_parser.add_argument('--output', help='Output directory (default: ./test_datasets)')
    generate_parser.add_argument('--quiet', action='store_true', help='Suppress progress output')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate existing dataset')
    validate_parser.add_argument('--file', required=True, help='Dataset file path')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List available datasets')
    list_parser.add_argument('--output', help='Directory to search (default: ./test_datasets)')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Check for required environment variables
    if args.command == 'generate':
        required_env_vars = ['GEMINI_API_KEY', 'OPENAI_API_KEY']
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            print("   Please set API keys for dataset generation.")
            return 1
        
        # Enable synthetic generation
        os.environ['SYNTHETIC_GENERATION_ENABLED'] = 'true'
        os.environ['EVALUATION_MODE'] = 'true'
        
        # Validate length
        if args.length < 5 or args.length > 35:
            print("❌ Conversation length must be between 5 and 35 turns")
            return 1
    
    # Execute command
    try:
        if args.command == 'generate':
            return asyncio.run(generate_dataset_command(args))
        elif args.command == 'validate':
            return asyncio.run(validate_dataset_command(args))
        elif args.command == 'list':
            return list_datasets_command(args)
        else:
            parser.print_help()
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logger.error(f"CLI execution failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())