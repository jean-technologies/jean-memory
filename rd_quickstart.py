#!/usr/bin/env python3
"""
R&D Quick Start Script

One-command setup and execution of the R&D pipeline with real customer data.
Perfect for rapid experimentation and development.

Usage:
    python rd_quickstart.py                    # Interactive mode
    python rd_quickstart.py --auto             # Auto-run with defaults  
    python rd_quickstart.py --user-id USER_ID  # Run for specific user
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from rd_setup import RDSetup
from rd_development_pipeline import RDPipeline

class RDQuickStart:
    """Quick start for R&D development"""
    
    def __init__(self):
        self.setup = RDSetup()
        self.pipeline = None
        
    async def ensure_environment_ready(self) -> bool:
        """Ensure R&D environment is ready"""
        print("🚀 R&D Quick Start")
        print("=" * 50)
        
        # Check environment
        results = self.setup.run_full_check()
        
        env_ok = all(results['env_vars'].values())
        docker_ok = all(results['docker_services'].values())
        deps_ok = all(results['python_deps'].values())
        
        # Auto-fix what we can
        if not docker_ok:
            print("\n🔧 Starting Docker services...")
            self.setup.start_services()
        
        if not deps_ok:
            missing_deps = [k for k, v in results['python_deps'].items() if not v]
            print(f"\n📦 Installing missing dependencies...")
            self.setup.install_missing_dependencies(missing_deps)
        
        if not env_ok:
            print("\n⚠️ Environment variables need to be set manually.")
            print("   Run: python rd_setup.py --create-env")
            print("   Then edit .env with your credentials")
            return False
        
        # Re-check after fixes
        final_check = self.setup.run_full_check()
        return all([
            all(final_check['env_vars'].values()),
            all(final_check['docker_services'].values()),
            all(final_check['python_deps'].values())
        ])
    
    async def run_sample_pipeline(self, user_id: str = None, sample_size: int = 30) -> dict:
        """Run a sample R&D pipeline"""
        print(f"\n🔬 Running Sample R&D Pipeline")
        print("-" * 40)
        
        # Initialize pipeline
        self.pipeline = RDPipeline()
        
        # Get user if not provided
        if not user_id:
            users = self.pipeline.list_available_users(limit=10)
            if not users:
                print("❌ No users found in database")
                return {}
            
            # Use user with most memories
            user_id = max(users, key=lambda x: x.get('memory_count', 0))['user_id']
            print(f"   📋 Auto-selected user: {user_id}")
        
        try:
            # Step 1: Download memories
            print(f"\n1️⃣ Downloading {sample_size} memories for user {user_id}...")
            memories = self.pipeline.download_user_memories(user_id, sample_size)
            
            if not memories:
                print("❌ No memories found")
                return {}
            
            print(f"   ✅ Downloaded {len(memories)} memories")
            
            # Step 2: Ingest into unified memory system
            print(f"\n2️⃣ Ingesting memories into unified system...")
            ingestion_results = await self.pipeline.ingest_memories(memories, user_id)
            print(f"   ✅ Ingested {ingestion_results['mem0_ingested']} into mem0")
            print(f"   ✅ Created {ingestion_results['graphiti_episodes']} temporal episodes")
            
            # Step 3: Test retrieval
            print(f"\n3️⃣ Testing GraphRAG retrieval...")
            test_queries = [
                "What exercises do I do?",
                "Where do I like to work out?",
                "What are my fitness goals?",
                "What projects am I working on?",
                "Who do I work with?",
                "What are my daily routines?"
            ]
            
            retrieval_results = await self.pipeline.test_retrieval(user_id, test_queries)
            successful_queries = len([q for q, r in retrieval_results.items() if "error" not in r])
            print(f"   ✅ Successful queries: {successful_queries}/{len(test_queries)}")
            
            # Step 4: Analyze results
            print(f"\n4️⃣ Analyzing results...")
            analysis = self.pipeline.analyze_results(user_id)
            
            # Print sample results
            print(f"\n📊 Sample Results:")
            for query, result in list(retrieval_results.items())[:2]:
                if "error" not in result:
                    response = result.get('response', '')[:200]
                    sources = len(result.get('sources', []))
                    print(f"   Q: {query}")
                    print(f"   A: {response}{'...' if len(response) == 200 else ''}")
                    print(f"   Sources: {sources}")
                    print()
            
            # Summary
            success_rate = analysis.get('retrieval_analysis', {}).get('success_rate', 0)
            print(f"🎯 Pipeline Summary:")
            print(f"   • Memories processed: {len(memories)}")
            print(f"   • Mem0 ingestion: {ingestion_results['mem0_ingested']}")
            print(f"   • Graphiti episodes: {ingestion_results['graphiti_episodes']}")
            print(f"   • Retrieval success rate: {success_rate:.1%}")
            print(f"   • Recommendations: {len(analysis.get('recommendations', []))}")
            
            return {
                'user_id': user_id,
                'memories_count': len(memories),
                'ingestion_results': ingestion_results,
                'retrieval_results': retrieval_results,
                'analysis': analysis,
                'success_rate': success_rate
            }
            
        except Exception as e:
            print(f"❌ Pipeline failed: {e}")
            return {}
    
    async def interactive_mode(self):
        """Interactive R&D mode"""
        print("\n🔬 R&D Interactive Mode")
        print("=" * 50)
        
        while True:
            print("\nQuick Actions:")
            print("1. Run sample pipeline (auto-select user)")
            print("2. Run pipeline for specific user")
            print("3. Browse available users")
            print("4. Open full R&D pipeline")
            print("5. Check environment status")
            print("0. Exit")
            
            choice = input("\nSelect option: ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                await self.run_sample_pipeline()
            elif choice == "2":
                user_id = input("Enter user ID: ").strip()
                sample_size = input("Sample size (default 30): ").strip()
                sample_size = int(sample_size) if sample_size else 30
                await self.run_sample_pipeline(user_id, sample_size)
            elif choice == "3":
                if not self.pipeline:
                    self.pipeline = RDPipeline()
                users = self.pipeline.list_available_users(20)
                print(f"\n📋 Available Users:")
                for i, user in enumerate(users[:10], 1):
                    print(f"   {i}. {user.get('user_id', 'N/A')} - {user.get('memory_count', 0)} memories")
            elif choice == "4":
                print("\n🔄 Launching full R&D pipeline...")
                print("   Run: python rd_development_pipeline.py --interactive")
                break
            elif choice == "5":
                self.setup.run_full_check()
    
    def print_next_steps(self):
        """Print next steps for R&D development"""
        print(f"\n🎯 Next Steps for R&D:")
        print(f"   1. Refine memory ingestion:")
        print(f"      python rd_development_pipeline.py --user-id USER_ID --sample-size 100")
        print(f"   2. Test different queries:")
        print(f"      python rd_development_pipeline.py --interactive")
        print(f"   3. Analyze results:")
        print(f"      Check rd_data/ folder for detailed analysis")
        print(f"   4. Iterate on GraphRAG pipeline:")
        print(f"      Edit graphrag_pipeline.py and test changes")
        print(f"   5. Deploy to production:")
        print(f"      Update MCP tools and website endpoints")

async def main():
    parser = argparse.ArgumentParser(description="R&D Quick Start")
    parser.add_argument("--auto", action="store_true", help="Auto-run with defaults")
    parser.add_argument("--user-id", help="Specific user ID to test")
    parser.add_argument("--sample-size", type=int, default=30, help="Number of memories to sample")
    
    args = parser.parse_args()
    
    quickstart = RDQuickStart()
    
    # Ensure environment is ready
    ready = await quickstart.ensure_environment_ready()
    
    if not ready:
        print("\n❌ Environment not ready. Please fix issues above.")
        return
    
    if args.auto:
        # Auto-run with defaults
        await quickstart.run_sample_pipeline(args.user_id, args.sample_size)
        quickstart.print_next_steps()
    elif args.user_id:
        # Run for specific user
        await quickstart.run_sample_pipeline(args.user_id, args.sample_size)
        quickstart.print_next_steps()
    else:
        # Interactive mode
        await quickstart.interactive_mode()

if __name__ == "__main__":
    asyncio.run(main()) 