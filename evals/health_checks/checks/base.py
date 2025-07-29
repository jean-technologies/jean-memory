"""
Base classes for Jean Memory health checks
"""

import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class HealthStatus(Enum):
    """Health check status levels"""
    PASS = "PASS"
    WARN = "WARN" 
    FAIL = "FAIL"

@dataclass
class HealthCheckItem:
    """Individual health check result"""
    name: str
    status: HealthStatus
    message: str
    execution_time: float
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None

class HealthCheckResult:
    """Container for health check results"""
    
    def __init__(self, category: str):
        self.category = category
        self.checks: List[HealthCheckItem] = []
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        
    def add_check(self, name: str, passed: bool, message: str, details: Optional[Dict[str, Any]] = None):
        """Add a health check result"""
        status = HealthStatus.PASS if passed else HealthStatus.FAIL
        execution_time = time.time() - self.start_time
        
        check = HealthCheckItem(
            name=name,
            status=status, 
            message=message,
            execution_time=execution_time,
            timestamp=datetime.now(),
            details=details
        )
        self.checks.append(check)
        
    def add_warning(self, name: str, message: str, details: Optional[Dict[str, Any]] = None):
        """Add a warning (non-critical issue)"""
        execution_time = time.time() - self.start_time
        
        check = HealthCheckItem(
            name=name,
            status=HealthStatus.WARN,
            message=message, 
            execution_time=execution_time,
            timestamp=datetime.now(),
            details=details
        )
        self.checks.append(check)
        
    def finish(self):
        """Mark the health check as complete"""
        self.end_time = time.time()
        
    @property
    def total_time(self) -> float:
        """Total execution time"""
        end = self.end_time or time.time()
        return end - self.start_time
        
    @property
    def passed_count(self) -> int:
        """Number of passed checks"""
        return len([c for c in self.checks if c.status == HealthStatus.PASS])
        
    @property
    def failed_count(self) -> int:
        """Number of failed checks"""
        return len([c for c in self.checks if c.status == HealthStatus.FAIL])
        
    @property
    def warning_count(self) -> int:
        """Number of warning checks"""  
        return len([c for c in self.checks if c.status == HealthStatus.WARN])
        
    @property
    def total_count(self) -> int:
        """Total number of checks"""
        return len(self.checks)
        
    @property
    def overall_status(self) -> HealthStatus:
        """Overall status of the health check category"""
        if self.failed_count > 0:
            return HealthStatus.FAIL
        elif self.warning_count > 0:
            return HealthStatus.WARN
        else:
            return HealthStatus.PASS
            
    def get_summary(self) -> str:
        """Get a summary of the health check results"""
        return f"{self.category}: {self.passed_count} passed, {self.failed_count} failed, {self.warning_count} warnings ({self.total_time:.2f}s)"

class HealthCheck:
    """Base class for health checks"""
    
    def __init__(self, name: str):
        self.name = name
        
    async def run_checks(self, level: str = "critical") -> HealthCheckResult:
        """Run the health checks - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement run_checks")
        
    def is_critical(self) -> bool:
        """Whether this health check is critical for deployment"""
        return True

class HealthCheckRunner:
    """Runs multiple health checks and aggregates results"""
    
    def __init__(self):
        self.health_checks: List[HealthCheck] = []
        
    def add_check(self, health_check: HealthCheck):
        """Add a health check to the runner"""
        self.health_checks.append(health_check)
        
    async def run_all_checks(self, level: str = "critical") -> List[HealthCheckResult]:
        """Run all registered health checks"""
        results = []
        
        for health_check in self.health_checks:
            if level == "critical" and not health_check.is_critical():
                continue
                
            try:
                result = await health_check.run_checks(level)
                result.finish()
                results.append(result)
            except Exception as e:
                # Create a failed result for checks that crash
                result = HealthCheckResult(health_check.name)
                result.add_check("Execution", False, f"Health check crashed: {e}")
                result.finish()
                results.append(result)
                
        return results
        
    def print_results(self, results: List[HealthCheckResult], verbose: bool = False):
        """Print formatted health check results"""
        total_passed = sum(r.passed_count for r in results)
        total_failed = sum(r.failed_count for r in results)
        total_warnings = sum(r.warning_count for r in results)
        total_time = sum(r.total_time for r in results)
        
        print("\n" + "="*80)
        print("🏥 JEAN MEMORY HEALTH CHECK RESULTS")
        print("="*80)
        
        # Summary
        print(f"\n📊 SUMMARY:")
        print(f"   ✅ Passed: {total_passed}")
        print(f"   ❌ Failed: {total_failed}")
        print(f"   ⚠️  Warnings: {total_warnings}")
        print(f"   ⏱️  Total Time: {total_time:.2f}s")
        
        # Overall status
        if total_failed > 0:
            print(f"\n🚨 OVERALL STATUS: CRITICAL ISSUES FOUND")
            exit_code = 2
        elif total_warnings > 0:
            print(f"\n⚠️  OVERALL STATUS: WARNINGS FOUND")
            exit_code = 1
        else:
            print(f"\n🎉 OVERALL STATUS: ALL SYSTEMS HEALTHY")
            exit_code = 0
            
        # Category results
        print(f"\n📋 CATEGORY RESULTS:")
        for result in results:
            status_icon = {
                HealthStatus.PASS: "✅",
                HealthStatus.WARN: "⚠️",
                HealthStatus.FAIL: "❌"
            }[result.overall_status]
            
            print(f"   {status_icon} {result.get_summary()}")
            
        # Detailed results (if verbose or there are failures)
        if verbose or total_failed > 0 or total_warnings > 0:
            print(f"\n📝 DETAILED RESULTS:")
            for result in results:
                if not verbose and result.overall_status == HealthStatus.PASS:
                    continue
                    
                print(f"\n   📁 {result.category}:")
                for check in result.checks:
                    status_icon = {
                        HealthStatus.PASS: "✅",
                        HealthStatus.WARN: "⚠️", 
                        HealthStatus.FAIL: "❌"
                    }[check.status]
                    
                    print(f"      {status_icon} {check.name}: {check.message}")
                    
        return exit_code