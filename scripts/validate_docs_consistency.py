#!/usr/bin/env python3
"""
Script to validate consistency between individual MDX files and the consolidation script.
This prevents hardcoded content in the consolidation script from overriding actual documentation.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

def extract_code_examples_from_mdx(file_path: Path) -> List[str]:
    """Extract all code examples from an MDX file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all code blocks
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', content, re.DOTALL)
        return [block.strip() for block in code_blocks]
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

def extract_hardcoded_examples_from_script(script_path: Path) -> List[str]:
    """Extract hardcoded code examples from the consolidation script."""
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the section where hardcoded examples are defined
        examples = []
        lines = content.split('\n')
        in_code_block = False
        current_block = []
        
        for line in lines:
            if 'consolidated_content.append("```' in line:
                in_code_block = True
                current_block = []
            elif in_code_block and 'consolidated_content.append("```")' in line:
                in_code_block = False
                if current_block:
                    examples.append('\n'.join(current_block))
            elif in_code_block and 'consolidated_content.append(' in line:
                # Extract the content between quotes
                match = re.search(r'consolidated_content\.append\("(.*)"\)', line)
                if match:
                    current_block.append(match.group(1))
        
        return examples
    except Exception as e:
        print(f"Error reading {script_path}: {e}")
        return []

def find_class_usage_inconsistencies(docs_dir: Path, script_path: Path) -> List[str]:
    """Find inconsistencies in class names between docs and script."""
    issues = []
    
    # Check all Python SDK related files
    python_files = list(docs_dir.glob("**/python.mdx")) + list(docs_dir.glob("**/sdk/python.mdx"))
    
    for mdx_file in python_files:
        with open(mdx_file, 'r', encoding='utf-8') as f:
            mdx_content = f.read()
        
        # Check if MDX uses JeanMemoryClient
        if 'JeanMemoryClient' in mdx_content:
            print(f"✅ {mdx_file.name} correctly uses JeanMemoryClient")
        elif 'JeanClient' in mdx_content:
            issues.append(f"❌ {mdx_file.name} uses deprecated JeanClient")
    
    # Check consolidation script
    with open(script_path, 'r', encoding='utf-8') as f:
        script_content = f.read()
    
    # Look for hardcoded examples in the script
    hardcoded_jean_client = script_content.count('JeanClient(')
    hardcoded_jean_memory_client = script_content.count('JeanMemoryClient(')
    
    if hardcoded_jean_client > 0 and hardcoded_jean_memory_client == 0:
        issues.append(f"❌ Consolidation script uses deprecated JeanClient in hardcoded examples")
    elif hardcoded_jean_memory_client > 0:
        print(f"✅ Consolidation script correctly uses JeanMemoryClient")
    
    return issues

def check_version_consistency(docs_dir: Path) -> List[str]:
    """Check that all version references are consistent across documentation."""
    issues = []
    version_patterns = [
        r'v(\d+\.\d+\.\d+)',
        r'version["\s]*:?["\s]*(\d+\.\d+\.\d+)',
        r'@jeanmemory/react@(\d+\.\d+\.\d+)',
        r'jeanmemory==(\d+\.\d+\.\d+)'
    ]
    
    all_versions = set()
    file_versions = {}
    
    for mdx_file in docs_dir.glob("**/*.mdx"):
        with open(mdx_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        versions_in_file = set()
        for pattern in version_patterns:
            matches = re.findall(pattern, content)
            versions_in_file.update(matches)
        
        if versions_in_file:
            file_versions[mdx_file.name] = versions_in_file
            all_versions.update(versions_in_file)
    
    if len(all_versions) > 1:
        issues.append(f"❌ Inconsistent versions found: {all_versions}")
        for file_name, versions in file_versions.items():
            if len(versions) > 1 or not versions.issubset({'2.0.0'}):
                issues.append(f"   - {file_name}: {versions}")
    else:
        print(f"✅ All versions consistent: {all_versions}")
    
    return issues

def main():
    script_dir = Path(__file__).parent
    docs_dir = script_dir.parent / "openmemory" / "ui" / "docs-mintlify"
    consolidation_script = script_dir / "create_consolidated_docs.py"
    
    print("🔍 Validating documentation consistency...")
    print()
    
    all_issues = []
    
    # Check class name consistency
    print("Checking class name consistency...")
    class_issues = find_class_usage_inconsistencies(docs_dir, consolidation_script)
    all_issues.extend(class_issues)
    
    print()
    
    # Check version consistency
    print("Checking version consistency...")
    version_issues = check_version_consistency(docs_dir)
    all_issues.extend(version_issues)
    
    print()
    
    # Summary
    if all_issues:
        print("❌ Documentation consistency issues found:")
        for issue in all_issues:
            print(f"   {issue}")
        print()
        print("🔧 Run the following to fix:")
        print("   1. Update any deprecated class names in MDX files")
        print("   2. Fix hardcoded examples in create_consolidated_docs.py")
        print("   3. Ensure all version references are v2.0.0")
        print("   4. Re-run: python3 scripts/create_consolidated_docs.py")
        return 1
    else:
        print("✅ All documentation is consistent!")
        print("💡 Safe to run: python3 scripts/create_consolidated_docs.py")
        return 0

if __name__ == "__main__":
    exit(main())