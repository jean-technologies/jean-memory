#!/usr/bin/env python3
"""
Environment Safety Check for Unified Memory System

This script verifies that the unified memory system is properly isolated
from production and safe to use for local development.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
import json

# Add project paths
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class EnvironmentChecker:
    """Checks environment safety for unified memory system."""
    
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = []
        
    def run_all_checks(self) -> bool:
        """Run all environment checks."""
        print("🔍 Unified Memory Environment Safety Check")
        print("=" * 60)
        
        checks = [
            ("Environment Variables", self.check_env_vars),
            ("Docker Services", self.check_docker_services),
            ("Database Isolation", self.check_database_isolation),
            ("API Configuration", self.check_api_config),
            ("File Permissions", self.check_file_permissions),
            ("Git Branch", self.check_git_branch),
        ]
        
        for check_name, check_func in checks:
            print(f"\n📋 {check_name}:")
            try:
                result, message = check_func()
                if result:
                    print(f"   ✅ {message}")
                    self.checks_passed += 1
                else:
                    print(f"   ❌ {message}")
                    self.checks_failed += 1
            except Exception as e:
                print(f"   ❌ Error: {e}")
                self.checks_failed += 1
        
        # Print summary
        self.print_summary()
        
        return self.checks_failed == 0
    
    def check_env_vars(self) -> Tuple[bool, str]:
        """Check critical environment variables."""
        required_vars = {
            "ENVIRONMENT": "development",
            "USE_UNIFIED_MEMORY": "true",
            "IS_LOCAL_UNIFIED_MEMORY": "true"
        }
        
        missing = []
        incorrect = []
        
        for var, expected in required_vars.items():
            value = os.getenv(var, "").lower()
            if not value:
                missing.append(var)
            elif value != expected.lower():
                incorrect.append(f"{var}={value} (expected: {expected})")
        
        if missing:
            return False, f"Missing variables: {', '.join(missing)}"
        if incorrect:
            return False, f"Incorrect values: {', '.join(incorrect)}"
        
        # Check for production indicators
        prod_indicators = [
            ("ENVIRONMENT", "production"),
            ("DATABASE_URL", "render.com"),
            ("SUPABASE_URL", "supabase.co"),
            ("QDRANT_HOST", "cloud.qdrant.io")
        ]
        
        prod_detected = []
        for var, indicator in prod_indicators:
            value = os.getenv(var, "")
            if indicator in value.lower():
                prod_detected.append(f"{var} contains '{indicator}'")
        
        if prod_detected:
            self.warnings.append(f"Production indicators detected: {', '.join(prod_detected)}")
        
        return True, "All required environment variables are correctly set"
    
    def check_docker_services(self) -> Tuple[bool, str]:
        """Check if unified memory Docker services are running."""
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                check=True
            )
            
            running_containers = result.stdout.strip().split('\n')
            required_containers = ["neo4j_unified_memory", "qdrant_unified_memory"]
            
            missing = [c for c in required_containers if c not in running_containers]
            
            if missing:
                return False, f"Missing containers: {', '.join(missing)}. Run ./start-unified-memory.sh"
            
            # Check for production containers
            prod_containers = [c for c in running_containers if 'prod' in c.lower() and 'unified' not in c]
            if prod_containers:
                self.warnings.append(f"Production containers detected: {', '.join(prod_containers)}")
            
            return True, "All unified memory containers are running"
            
        except subprocess.CalledProcessError:
            return False, "Docker is not running or docker command failed"
    
    def check_database_isolation(self) -> Tuple[bool, str]:
        """Check database configuration for isolation."""
        # Check Neo4j configuration
        neo4j_uri = os.getenv("NEO4J_URI", "")
        if "localhost" not in neo4j_uri and "127.0.0.1" not in neo4j_uri:
            return False, f"Neo4j URI '{neo4j_uri}' is not pointing to localhost"
        
        # Check Qdrant configuration
        qdrant_host = os.getenv("QDRANT_HOST", "")
        if qdrant_host and qdrant_host not in ["localhost", "127.0.0.1"]:
            return False, f"Qdrant host '{qdrant_host}' is not localhost"
        
        # Check collection names
        collection_name = os.getenv("UNIFIED_QDRANT_COLLECTION_NAME", "")
        if "prod" in collection_name.lower():
            self.warnings.append(f"Collection name '{collection_name}' contains 'prod'")
        
        return True, "Databases are properly isolated to localhost"
    
    def check_api_config(self) -> Tuple[bool, str]:
        """Check API configuration."""
        settings_file = project_root / "openmemory" / "api" / "app" / "settings.py"
        
        if not settings_file.exists():
            return False, "settings.py not found"
        
        # Check if unified memory import exists
        unified_memory_file = project_root / "openmemory" / "api" / "app" / "utils" / "unified_memory.py"
        if not unified_memory_file.exists():
            return False, "unified_memory.py not found"
        
        # Check for feature flag function
        memory_utils = project_root / "openmemory" / "api" / "app" / "utils" / "memory.py"
        if memory_utils.exists():
            content = memory_utils.read_text()
            if "should_use_unified_memory" not in content:
                return False, "should_use_unified_memory function not found in memory.py"
        
        return True, "API is properly configured for unified memory"
    
    def check_file_permissions(self) -> Tuple[bool, str]:
        """Check file permissions for safety."""
        sensitive_files = [
            "scripts/local-dev/unified-memory/.env.unified-memory",
            "migration_state.json",
            "unified_migration.log"
        ]
        
        issues = []
        for file_path in sensitive_files:
            full_path = project_root / file_path
            if full_path.exists():
                # Check if file is readable by others
                stat = full_path.stat()
                if stat.st_mode & 0o004:
                    issues.append(f"{file_path} is world-readable")
        
        if issues:
            self.warnings.append(f"Permission issues: {', '.join(issues)}")
        
        return True, "File permissions checked"
    
    def check_git_branch(self) -> Tuple[bool, str]:
        """Check current git branch."""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True,
                cwd=project_root
            )
            
            current_branch = result.stdout.strip()
            
            if current_branch in ["main", "master", "production"]:
                return False, f"On production branch '{current_branch}'. Switch to feature branch."
            
            if "unified" not in current_branch.lower() and "memory" not in current_branch.lower():
                self.warnings.append(f"Branch '{current_branch}' doesn't indicate unified memory work")
            
            return True, f"On feature branch: {current_branch}"
            
        except subprocess.CalledProcessError:
            return False, "Failed to check git branch"
    
    def print_summary(self):
        """Print check summary."""
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.checks_passed}")
        print(f"❌ Failed: {self.checks_failed}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   - {warning}")
        
        if self.checks_failed == 0:
            print("\n🎉 Environment is SAFE for unified memory development!")
            print("   - Isolated from production ✓")
            print("   - Local services running ✓")
            print("   - Proper configuration ✓")
        else:
            print("\n❌ Environment is NOT SAFE. Fix the issues above before proceeding.")
            print("\n💡 Quick fixes:")
            print("   1. Set environment variables in .env or .env.unified-memory")
            print("   2. Run ./start-unified-memory.sh to start Docker services")
            print("   3. Switch to a feature branch for development")


def main():
    """Main function."""
    checker = EnvironmentChecker()
    success = checker.run_all_checks()
    
    # Write status to file for other scripts
    status = {
        "safe": success,
        "checks_passed": checker.checks_passed,
        "checks_failed": checker.checks_failed,
        "warnings": checker.warnings
    }
    
    with open("environment_check_status.json", "w") as f:
        json.dump(status, f, indent=2)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 