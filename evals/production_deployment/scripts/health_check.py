#!/usr/bin/env python3
"""
Health check script for Jean Memory Evaluation Framework
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

async def health_check():
    """Perform basic health check of evaluation framework"""
    print("🏥 Jean Memory Evaluation Framework Health Check")
    print("=" * 50)
    
    checks = {
        "config_file": False,
        "evaluation_runner": False,
        "golden_dataset": False,
        "metrics_framework": False
    }
    
    # Check configuration file
    if Path("production_config.json").exists():
        checks["config_file"] = True
        print("✅ Configuration file: OK")
    else:
        print("❌ Configuration file: MISSING")
    
    # Check evaluation runner
    if Path("evaluation_runner.py").exists():
        checks["evaluation_runner"] = True
        print("✅ Evaluation runner: OK")
    else:
        print("❌ Evaluation runner: MISSING")
    
    # Check golden dataset
    if Path("golden_memories.json").exists():
        checks["golden_dataset"] = True
        print("✅ Golden dataset: OK")
    else:
        print("❌ Golden dataset: MISSING")
    
    # Check metrics framework
    if Path("metrics.py").exists():
        checks["metrics_framework"] = True
        print("✅ Metrics framework: OK")
    else:
        print("❌ Metrics framework: MISSING")
    
    # Overall health
    healthy_checks = sum(checks.values())
    total_checks = len(checks)
    health_percentage = healthy_checks / total_checks * 100
    
    print(f"\n📊 Overall Health: {health_percentage:.1f}% ({healthy_checks}/{total_checks})")
    
    if health_percentage >= 100:
        print("🎉 System is fully operational!")
        return 0
    elif health_percentage >= 75:
        print("⚠️ System is mostly operational with minor issues")
        return 1
    else:
        print("❌ System has critical issues")
        return 2

if __name__ == "__main__":
    exit_code = asyncio.run(health_check())
    sys.exit(exit_code)
