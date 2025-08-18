#!/usr/bin/env python3
"""
Jean Memory Performance Evaluation & Testing Framework
Main CLI script for running complete evaluation pipeline

Usage:
    ./run_evaluation.py --setup                           # One-time token setup
    ./run_evaluation.py --user-id {user_id} --length 20   # Full evaluation
    ./run_evaluation.py --quick-test                      # Quick validation
"""

import asyncio
import argparse
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any
import json

# Add project paths
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "openmemory" / "api"))

try:
    from app.evaluation import (
        # Task 1: Core Infrastructure
        evaluate,
        # Task 2: LLM Judge
        evaluate_single_response,
        # Task 3: Synthetic Data Generator  
        generate_balanced_dataset,
        create_test_dataset,
        # Task 4: Conversation Dataset Generator
        generate_conversation_dataset,
        ConversationDistributionType,
        # Task 5: Authentication
        SecureTokenManager,
        is_authenticated,
        get_auth_headers,
        # Task 6: MCP Client
        call_jean_memory,
        test_mcp_connection,
        # Task 7: Conversation Test Runner
        run_conversation_test,
        # Task 8: Performance Metrics
        parse_log_file,
        parse_log_text,
        # Task 9: Report Generator
        generate_evaluation_report,
        # Supporting types
        ReasoningType,
        PersonaType,
        DifficultyLevel
    )
    EVALUATION_AVAILABLE = True
except ImportError as e:
    print(f"❌ Error importing evaluation framework: {e}")
    print("Make sure you're running from the jean-memory directory with:")
    print("  cd /path/to/jean-memory")
    print("  python run_evaluation.py --setup")
    EVALUATION_AVAILABLE = False

class JeanMemoryEvaluationRunner:
    """Main evaluation runner that orchestrates all 9 tasks"""
    
    def __init__(self):
        self.user_id: Optional[str] = None
        self.datasets_dir = Path("./test_datasets")
        self.reports_dir = Path("./evaluation_reports")
        self.results: Dict[str, Any] = {}
        
    async def setup_authentication(self) -> bool:
        """Task 5: Set up authentication tokens"""
        print("🔐 Task 5: Setting up authentication...")
        
        if not EVALUATION_AVAILABLE:
            print("❌ Evaluation framework not available")
            return False
            
        token_manager = SecureTokenManager()
        
        if token_manager.token_exists():
            print("✅ Token file already exists")
            # Validate existing token
            try:
                if await token_manager.validate_token():
                    print("✅ Existing token is valid")
                    return True
                else:
                    print("❌ Existing token is invalid, please re-run setup")
                    return False
            except Exception as e:
                print(f"⚠️ Token validation failed: {e}")
                print("Please follow the manual setup process:")
        else:
            print("📋 No token found. Please follow the setup guide:")
            
        print("\n" + "="*60)
        print("MANUAL TOKEN SETUP REQUIRED")
        print("="*60)
        print("1. Open your browser and go to: https://jeanmemory.com")
        print("2. Open Developer Tools (F12)")
        print("3. Go to Network tab")
        print("4. Make any request on the site")
        print("5. Find a request with 'Authorization: Bearer ...' header")
        print("6. Copy the token (everything after 'Bearer ')")
        print("7. Run: python -m app.evaluation.auth_helper --setup")
        print("8. Enter the token when prompted")
        print("="*60)
        
        return False
        
    async def run_quick_test(self) -> Dict[str, Any]:
        """Quick validation test of all components"""
        print("🚀 Running Quick Test...")
        print("="*50)
        
        results = {
            "test_type": "quick",
            "timestamp": time.time(),
            "components": {},
            "success": True
        }
        
        # Test Task 5: Authentication
        print("🔐 Testing authentication...")
        try:
            if is_authenticated():
                results["components"]["authentication"] = {"status": "✅ Working", "details": "Token exists and loaded"}
            else:
                results["components"]["authentication"] = {"status": "❌ Failed", "details": "No valid token"}
                results["success"] = False
        except Exception as e:
            results["components"]["authentication"] = {"status": "❌ Error", "details": str(e)}
            results["success"] = False
            
        # Test Task 6: MCP Client  
        print("🌐 Testing MCP connection...")
        try:
            if self.user_id:
                mcp_working = await test_mcp_connection(self.user_id)
                if mcp_working:
                    results["components"]["mcp_client"] = {"status": "✅ Working", "details": "MCP endpoint accessible"}
                else:
                    results["components"]["mcp_client"] = {"status": "❌ Failed", "details": "MCP connection failed"}
                    results["success"] = False
            else:
                results["components"]["mcp_client"] = {"status": "⚠️ Skipped", "details": "No user_id provided"}
        except Exception as e:
            results["components"]["mcp_client"] = {"status": "❌ Error", "details": str(e)}
            results["success"] = False
            
        # Test Task 4: Dataset Generation
        print("📊 Testing dataset generation...")
        try:
            self.datasets_dir.mkdir(exist_ok=True)
            existing_datasets = list(self.datasets_dir.glob("*.json"))
            if existing_datasets:
                results["components"]["datasets"] = {
                    "status": "✅ Working", 
                    "details": f"Found {len(existing_datasets)} existing datasets"
                }
            else:
                results["components"]["datasets"] = {
                    "status": "⚠️ Empty", 
                    "details": "No datasets found, generate with --length option"
                }
        except Exception as e:
            results["components"]["datasets"] = {"status": "❌ Error", "details": str(e)}
            results["success"] = False
            
        # Test Task 2: LLM Judge
        print("🤖 Testing LLM Judge...")
        try:
            score = await evaluate_single_response(
                query="What is my name?",
                memories=[{"content": "User's name is John"}],
                response="Your name is John.",
                reasoning_type=ReasoningType.SINGLE_HOP
            )
            results["components"]["llm_judge"] = {
                "status": "✅ Working", 
                "details": f"Judge score: {score.overall:.1f}/10"
            }
        except Exception as e:
            results["components"]["llm_judge"] = {"status": "❌ Error", "details": str(e)}
            results["success"] = False
            
        # Test Task 9: Report Generation
        print("📋 Testing report generation...")
        try:
            # Create minimal test data
            test_conversation_results = [{
                "dataset_name": "quick_test",
                "turns": [{"success": True, "response_time_ms": 1000, "reasoning_type": "single_hop"}],
                "success_rate": 1.0
            }]
            
            report_result = generate_evaluation_report(
                conversation_results=test_conversation_results,
                output_dir=str(self.reports_dir)
            )
            
            results["components"]["report_generation"] = {
                "status": "✅ Working",
                "details": f"Report generated: {len(report_result['markdown'])} chars"
            }
        except Exception as e:
            results["components"]["report_generation"] = {"status": "❌ Error", "details": str(e)}
            results["success"] = False
            
        # Print results
        print("\n" + "="*50)
        print("🎯 QUICK TEST RESULTS")
        print("="*50)
        
        for component, result in results["components"].items():
            print(f"{result['status']} {component:20} | {result['details']}")
            
        overall_status = "✅ PASS" if results["success"] else "❌ FAIL"
        print(f"\n{overall_status} Quick Test Overall Status")
        
        return results
        
    async def run_full_evaluation(self, user_id: str, length: int = 10, conversation_type: str = "mixed") -> Dict[str, Any]:
        """Run complete evaluation pipeline"""
        print(f"🚀 Running Full Evaluation...")
        print(f"   User ID: {user_id}")
        print(f"   Length: {length} turns")
        print(f"   Type: {conversation_type}")
        print("="*60)
        
        start_time = time.time()
        self.user_id = user_id
        
        results = {
            "evaluation_type": "full",
            "parameters": {"user_id": user_id, "length": length, "type": conversation_type},
            "timestamp": start_time,
            "stages": {},
            "success": True
        }
        
        try:
            # Stage 1: Verify Authentication
            print("\n🔐 Stage 1: Verifying Authentication...")
            if not is_authenticated():
                raise Exception("Authentication required. Run --setup first.")
            print("✅ Authentication verified")
            
            # Stage 2: Generate/Load Test Datasets  
            print("\n📊 Stage 2: Preparing Test Datasets...")
            self.datasets_dir.mkdir(exist_ok=True)
            
            # Check for existing datasets
            existing_datasets = list(self.datasets_dir.glob("conversation_*.json"))
            
            if not existing_datasets or length > 10:
                print(f"Generating new {length}-turn conversation dataset...")
                
                # Map conversation type to distribution
                if conversation_type == "progressive":
                    distribution = ConversationDistributionType.PROGRESSIVE
                elif conversation_type == "mixed":
                    distribution = ConversationDistributionType.MIXED  
                else:
                    distribution = ConversationDistributionType.PROGRESSIVE
                    
                # Generate new dataset
                dataset = await generate_conversation_dataset(
                    name=f"evaluation_{conversation_type}_{length}turns",
                    conversation_length=length,
                    distribution_type=distribution,
                    persona=PersonaType.CASUAL
                )
                
                # Save to file
                dataset_file = self.datasets_dir / f"conversation_{conversation_type}_{length}turns_{int(time.time())}.json"
                with open(dataset_file, 'w') as f:
                    json.dump(dataset.to_dict(), f, indent=2, default=str)
                
                print(f"✅ Generated dataset: {dataset_file.name}")
                results["stages"]["dataset_generation"] = {"status": "✅ Generated", "file": str(dataset_file)}
            else:
                print(f"✅ Using existing datasets: {len(existing_datasets)} found")
                results["stages"]["dataset_generation"] = {"status": "✅ Existing", "count": len(existing_datasets)}
            
            # Stage 3: Run Conversation Tests (Task 7)
            print("\n🗣️ Stage 3: Running Conversation Tests...")
            conversation_results = await run_conversation_test(
                datasets_directory=str(self.datasets_dir),
                user_id=user_id,
                enable_judge=True,  # Enable Task 2 LLM Judge
                max_datasets=3,  # Limit for performance
                progress_callback=lambda c, t, d: print(f"   Progress: {c}/{t} - {d}")
            )
            
            success_rate = conversation_results["suite_execution_summary"]["suite_success_rate"]
            avg_judge_score = conversation_results["suite_execution_summary"].get("avg_judge_score", 0)
            
            print(f"✅ Conversation tests completed:")
            print(f"   Success Rate: {success_rate:.1%}")
            print(f"   Average Judge Score: {avg_judge_score:.1f}/10")
            
            results["stages"]["conversation_tests"] = {
                "status": "✅ Completed",
                "success_rate": success_rate,
                "avg_judge_score": avg_judge_score,
                "detailed_results": conversation_results
            }
            
            # Stage 4: Performance Metrics (Task 8) 
            print("\n⚡ Stage 4: Extracting Performance Metrics...")
            try:
                # Try to parse any available logs
                log_files = list(Path(".").glob("*.log"))
                if log_files:
                    performance_metrics, log_stats = parse_log_file(log_files[0])
                    print(f"✅ Parsed {log_stats.total_lines_processed} log lines")
                    results["stages"]["performance_metrics"] = {
                        "status": "✅ Parsed", 
                        "log_file": str(log_files[0]),
                        "metrics": performance_metrics.to_dict()
                    }
                else:
                    print("⚠️ No log files found, using conversation metrics only")
                    performance_metrics = None
                    results["stages"]["performance_metrics"] = {"status": "⚠️ No logs", "metrics": None}
            except Exception as e:
                print(f"⚠️ Performance metrics extraction failed: {e}")
                performance_metrics = None
                results["stages"]["performance_metrics"] = {"status": "❌ Failed", "error": str(e)}
            
            # Stage 5: Generate Reports (Task 9)
            print("\n📋 Stage 5: Generating Evaluation Reports...")
            self.reports_dir.mkdir(exist_ok=True)
            
            report_data = generate_evaluation_report(
                conversation_results=conversation_results["dataset_results"],
                performance_metrics=performance_metrics,
                output_dir=str(self.reports_dir)
            )
            
            print(f"✅ Reports generated:")
            for report_type, path in report_data["file_paths"].items():
                print(f"   {report_type}: {path}")
                
            results["stages"]["report_generation"] = {
                "status": "✅ Generated",
                "files": report_data["file_paths"]
            }
            
            # Stage 6: Validate Performance Targets (FRD Section 8)
            print("\n🎯 Stage 6: Validating Performance Targets...")
            
            # Extract reasoning type performance from results
            reasoning_performance = {}
            total_score = 0
            total_count = 0
            
            for dataset_result in conversation_results["dataset_results"]:
                for turn_result in dataset_result.get("turn_results", []):
                    reasoning_type = turn_result.get("reasoning_type", "unknown")
                    judge_score = turn_result.get("judge_score", {}).get("overall", 0)
                    
                    if reasoning_type not in reasoning_performance:
                        reasoning_performance[reasoning_type] = []
                    reasoning_performance[reasoning_type].append(judge_score)
                    
                    total_score += judge_score
                    total_count += 1
            
            # Calculate averages and check targets
            targets_met = {}
            frd_targets = {
                "single_hop": 9.0,  # >90% accuracy (9.0/10)
                "multi_hop": 8.0,   # >80% accuracy (8.0/10)  
                "temporal": 7.5,    # >75% accuracy (7.5/10)
            }
            
            overall_avg = total_score / total_count if total_count > 0 else 0
            
            print(f"Performance vs FRD Targets:")
            for reasoning_type, scores in reasoning_performance.items():
                if scores:
                    avg_score = sum(scores) / len(scores)
                    target = frd_targets.get(reasoning_type, 7.0)
                    meets_target = avg_score >= target
                    targets_met[reasoning_type] = meets_target
                    
                    status = "✅" if meets_target else "❌"
                    print(f"   {status} {reasoning_type}: {avg_score:.1f}/10 (target: {target:.1f}/10)")
            
            overall_target_met = overall_avg >= 7.0
            overall_status = "✅" if overall_target_met else "❌"
            print(f"   {overall_status} Overall: {overall_avg:.1f}/10 (target: 7.0/10)")
            
            results["stages"]["performance_validation"] = {
                "status": "✅ Validated",
                "reasoning_performance": reasoning_performance,
                "targets_met": targets_met,
                "overall_avg": overall_avg,
                "overall_target_met": overall_target_met
            }
            
        except Exception as e:
            print(f"❌ Evaluation failed: {e}")
            results["success"] = False
            results["error"] = str(e)
            import traceback
            traceback.print_exc()
            
        # Final Results
        execution_time = time.time() - start_time
        results["execution_time"] = execution_time
        
        print(f"\n" + "="*60)
        print("🎯 FULL EVALUATION RESULTS")
        print("="*60)
        
        for stage_name, stage_result in results["stages"].items():
            print(f"{stage_result['status']} {stage_name}")
            
        overall_status = "✅ SUCCESS" if results["success"] else "❌ FAILED"
        print(f"\n{overall_status} Full Evaluation Completed in {execution_time:.1f}s")
        
        if results["success"]:
            print("\n📊 Key Metrics:")
            conv_stage = results["stages"].get("conversation_tests", {})
            print(f"   Success Rate: {conv_stage.get('success_rate', 0):.1%}")
            print(f"   Judge Score: {conv_stage.get('avg_judge_score', 0):.1f}/10")
            
            if "performance_validation" in results["stages"]:
                perf_stage = results["stages"]["performance_validation"]
                print(f"   Overall Performance: {perf_stage.get('overall_avg', 0):.1f}/10")
                print(f"   FRD Target Met: {perf_stage.get('overall_target_met', False)}")
        
        return results

async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Jean Memory Performance Evaluation & Testing Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --setup                           # One-time authentication setup
  %(prog)s --user-id abc123 --length 20      # Full 20-turn evaluation  
  %(prog)s --quick-test                      # Quick component validation
  %(prog)s --user-id abc123 --type mixed     # Mixed reasoning evaluation
        """
    )
    
    parser.add_argument("--setup", action="store_true", 
                       help="Set up authentication tokens")
    parser.add_argument("--quick-test", action="store_true",
                       help="Run quick component validation")
    parser.add_argument("--user-id", type=str,
                       help="User ID for authenticated testing")
    parser.add_argument("--length", type=int, default=10,
                       help="Conversation length in turns (default: 10)")
    parser.add_argument("--type", choices=["progressive", "mixed"], default="mixed",
                       help="Conversation type (default: mixed)")
    
    args = parser.parse_args()
    
    if not EVALUATION_AVAILABLE:
        print("❌ Evaluation framework not available")
        print("Make sure you're in the jean-memory directory and try:")
        print("  cd /path/to/jean-memory")
        print("  python run_evaluation.py --setup")
        return 1
    
    runner = JeanMemoryEvaluationRunner()
    
    try:
        if args.setup:
            success = await runner.setup_authentication()
            return 0 if success else 1
            
        elif args.quick_test:
            results = await runner.run_quick_test()
            return 0 if results["success"] else 1
            
        elif args.user_id:
            results = await runner.run_full_evaluation(args.user_id, args.length, args.type)
            return 0 if results["success"] else 1
            
        else:
            parser.print_help()
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Evaluation interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)