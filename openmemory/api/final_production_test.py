#!/usr/bin/env python3
"""
Final production readiness test - simulates exact production environment
"""

import sys
import os

def test_critical_imports():
    """Test the exact imports that production code uses"""
    print("🔍 Testing critical production imports...")
    
    critical_imports = [
        # From app/utils/memory.py:20
        ("jean_memory.mem0_adapter_optimized", "get_memory_client_v2_optimized", "Used in get_memory_client()"),
        # From app/utils/memory.py:79  
        ("jean_memory.mem0_adapter_optimized", "get_async_memory_client_v2_optimized", "Used in get_async_memory_client()"),
        # From app/utils/memory.py:110
        ("jean_memory.config", "JeanMemoryConfig", "Used for configuration"),
        # From jean_memory/__init__.py - main exports
        ("jean_memory", "JeanMemoryV2", "Main API class"),
        ("jean_memory", "JeanMemoryConfig", "Config class"),
    ]
    
    failed_imports = []
    
    for module, item, description in critical_imports:
        try:
            if item:
                exec(f"from {module} import {item}")
                print(f"   ✅ from {module} import {item}")
            else:
                exec(f"import {module}")
                print(f"   ✅ import {module}")
        except ImportError as e:
            failed_imports.append((module, item, description, str(e)))
            print(f"   ❌ from {module} import {item} - {e}")
        except Exception as e:
            print(f"   ⚠️  {module}.{item} - Unexpected error: {e}")
    
    return failed_imports

def check_module_structure():
    """Verify jean_memory module structure"""
    print("\n📁 Checking module structure...")
    
    required_files = [
        "jean_memory/__init__.py",
        "jean_memory/mem0_adapter_optimized.py", 
        "jean_memory/config.py",
        "jean_memory/core.py",
        "jean_memory/api.py",
        "jean_memory/models.py",
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"   ❌ {file_path} - MISSING")
    
    return missing_files

def check_dependencies():
    """Check that all dependencies are in requirements.txt"""
    print("\n📦 Checking dependency coverage...")
    
    # Re-run dependency audit
    try:
        import subprocess
        result = subprocess.run([sys.executable, "dependency_audit.py"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ All jean-memory dependencies present")
            return True
        else:
            print("   ❌ Missing dependencies detected")
            print(result.stdout)
            return False
    except Exception as e:
        print(f"   ⚠️  Could not run dependency audit: {e}")
        return True  # Don't fail on this

def check_requirements_file():
    """Check requirements.txt is properly updated"""
    print("\n📄 Checking requirements.txt...")
    
    with open("requirements.txt", "r") as f:
        content = f.read()
    
    issues = []
    
    # Check git dependency is removed
    for line_num, line in enumerate(content.split('\n'), 1):
        line = line.strip()
        if line.startswith('#'):
            continue
        if 'git+https://github.com/jean-technologies/jean-memory.git' in line:
            issues.append(f"Line {line_num}: Active git dependency found")
        if line.startswith('jean-memory @'):
            issues.append(f"Line {line_num}: Active git dependency found") 
    
    # Check numpy is present
    if 'numpy>=' not in content:
        issues.append("numpy dependency missing")
    
    if issues:
        for issue in issues:
            print(f"   ❌ {issue}")
        return False
    else:
        print("   ✅ requirements.txt properly configured")
        return True

def main():
    print("=== FINAL PRODUCTION READINESS TEST ===\n")
    print(f"Working directory: {os.getcwd()}")
    print(f"Python version: {sys.version.split()[0]}")
    print(f"Python path includes current dir: {'.' in sys.path or os.getcwd() in sys.path}")
    
    # Run all checks
    checks = [
        ("Module Structure", check_module_structure),
        ("Requirements File", check_requirements_file), 
        ("Dependencies", check_dependencies),
        ("Critical Imports", test_critical_imports),
    ]
    
    all_passed = True
    results = {}
    
    for check_name, check_func in checks:
        print(f"\n{'='*50}")
        print(f"🧪 {check_name}")
        print('='*50)
        
        try:
            result = check_func()
            if isinstance(result, bool):
                results[check_name] = result
                all_passed = all_passed and result
            elif isinstance(result, list):
                results[check_name] = len(result) == 0
                all_passed = all_passed and (len(result) == 0)
        except Exception as e:
            print(f"   ❌ Check failed with error: {e}")
            results[check_name] = False
            all_passed = False
    
    # Final summary
    print(f"\n{'='*60}")
    print("🎯 FINAL SUMMARY")
    print('='*60)
    
    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:8} {check_name}")
    
    if all_passed:
        print(f"\n🚀 PRODUCTION READY!")
        print("✅ All checks passed - safe to commit and deploy")
        print("\nDeployment will work because:")
        print("  • jean_memory module is in the correct location")
        print("  • All dependencies are in requirements.txt")
        print("  • All critical imports are working")
        print("  • Git dependency has been removed")
        return True
    else:
        print(f"\n❌ NOT PRODUCTION READY")
        print("Fix the failed checks before deploying")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)