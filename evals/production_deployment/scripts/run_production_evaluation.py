#!/usr/bin/env python3
"""
Production Jean Memory Evaluation Runner
Isolated evaluation runner for production deployment
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/evaluation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ProductionEvaluationRunner:
    """Production-ready evaluation runner with isolation and monitoring"""
    
    def __init__(self, config_path="production_config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)
        
    def _load_config(self):
        """Load production configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            return self._default_config()
    
    def _default_config(self):
        """Default configuration if file not found"""
        return {
            "evaluation_settings": {
                "memory_triage": {"enabled": True, "target_accuracy": 85.0},
                "context_quality": {"enabled": True, "target_pass_rate": 60.0},
                "performance_benchmarks": {"enabled": True},
                "system_integration": {"enabled": True}
            },
            "execution_settings": {
                "save_results": True,
                "generate_reports": True
            }
        }
    
    async def run_production_evaluations(self):
        """Run evaluations in production mode"""
        start_time = time.time()
        logger.info("🚀 Starting Jean Memory Production Evaluation")
        
        try:
            # Import the working evaluation runner
            sys.path.insert(0, str(Path(__file__).parent))
            from evaluation_runner import WorkingEvaluationRunner
            
            # Run evaluations with production settings
            runner = WorkingEvaluationRunner()
            results = await runner.run_all_evaluations()
            
            # Process and save results
            await self._process_results(results)
            
            # Generate alerts if needed
            await self._check_alerts(results)
            
            execution_time = time.time() - start_time
            logger.info(f"✅ Production evaluation completed in {execution_time:.2f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Production evaluation failed: {e}")
            raise
    
    async def _process_results(self, results):
        """Process and save evaluation results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed JSON results
        json_file = self.results_dir / f"eval_results_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"📁 Results saved to: {json_file}")
        
        # Generate summary report
        summary_file = self.results_dir / f"eval_summary_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write(self._generate_summary_report(results))
        logger.info(f"📄 Summary saved to: {summary_file}")
    
    def _generate_summary_report(self, results):
        """Generate human-readable summary report"""
        summary = results.get('summary', {})
        overall_metrics = results.get('overall_metrics', {})
        
        report = f"""
JEAN MEMORY EVALUATION FRAMEWORK - PRODUCTION RESULTS
{'='*60}
Timestamp: {datetime.now().isoformat()}
Overall Status: {summary.get('overall_status', 'UNKNOWN')}
System Health Score: {summary.get('system_health_score', 0):.1f}/100
Execution Time: {summary.get('total_execution_time', 0):.2f}s

CATEGORY RESULTS:
{'-'*30}
Memory Triage: {results.get('memory_triage', {}).get('accuracy', 0):.1f}% accuracy
Context Quality: {results.get('context_quality', {}).get('pass_rate', 0):.1f}% pass rate
Performance: {results.get('performance_basic', {}).get('successful', 0)}/{results.get('performance_basic', {}).get('total_tested', 0)} successful
Integration: {results.get('system_integration', {}).get('integration_score', 0):.1f}% operational

KEY FINDINGS:
{'-'*30}
"""
        
        for finding in summary.get('key_findings', []):
            report += f"• {finding}\n"
        
        if summary.get('recommendations'):
            report += f"\nRECOMMENDATIONS:\n{'-'*30}\n"
            for rec in summary.get('recommendations', []):
                report += f"• {rec}\n"
        
        return report
    
    async def _check_alerts(self, results):
        """Check if results trigger any alerts"""
        health_score = results.get('summary', {}).get('system_health_score', 0)
        thresholds = self.config.get('reporting', {}).get('alert_thresholds', {})
        
        if health_score < thresholds.get('system_health_critical', 50):
            logger.critical(f"🚨 CRITICAL: System health score {health_score:.1f}% below critical threshold")
        elif health_score < thresholds.get('system_health_warning', 75):
            logger.warning(f"⚠️ WARNING: System health score {health_score:.1f}% below warning threshold")
        else:
            logger.info(f"✅ System health score {health_score:.1f}% is healthy")

async def main():
    """Main entry point for production evaluation"""
    runner = ProductionEvaluationRunner()
    try:
        results = await runner.run_production_evaluations()
        
        # Return appropriate exit code
        health_score = results.get('summary', {}).get('system_health_score', 0)
        if health_score >= 75:
            print("\n🎉 Production evaluation PASSED!")
            return 0
        else:
            print("\n⚠️ Production evaluation completed with issues")
            return 1
            
    except Exception as e:
        logger.error(f"Production evaluation failed: {e}")
        return 2

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
