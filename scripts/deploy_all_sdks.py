#!/usr/bin/env python3
"""
Unified SDK Deployment Script
Ensures consistent versioning and deployment across all 3 SDKs
"""

import os
import sys
import json
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Optional
import datetime

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "openmemory" / "api"))

class Colors:
    """ANSI color codes for terminal output"""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def log(message: str, color: str = Colors.WHITE) -> None:
    """Print colored log message"""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"{Colors.CYAN}[{timestamp}]{Colors.END} {color}{message}{Colors.END}")

def log_success(message: str) -> None:
    log(f"✅ {message}", Colors.GREEN)

def log_warning(message: str) -> None:
    log(f"⚠️  {message}", Colors.YELLOW)

def log_error(message: str) -> None:
    log(f"❌ {message}", Colors.RED)

def log_info(message: str) -> None:
    log(f"ℹ️  {message}", Colors.BLUE)

def log_step(message: str) -> None:
    log(f"🚀 {message}", Colors.PURPLE + Colors.BOLD)

class SDKDeployer:
    """Unified SDK deployment manager"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.sdk_root = project_root / "sdk"
        
        # SDK configurations
        self.sdks = {
            "react": {
                "path": self.sdk_root / "react",
                "package_file": "package.json",
                "build_command": ["npm", "run", "build"],
                "publish_command": ["npm", "publish"],
                "registry": "npm",
                "name": "@jeanmemory/react"
            },
            "node": {
                "path": self.sdk_root / "node", 
                "package_file": "package.json",
                "build_command": ["npm", "run", "build"],
                "publish_command": ["npm", "publish"],
                "registry": "npm",
                "name": "@jeanmemory/node"
            },
            "python": {
                "path": self.sdk_root / "python",
                "package_file": "setup.py",
                "build_command": ["python3", "setup.py", "build"],
                "publish_command": ["python3", "-m", "twine", "upload", "dist/*"],
                "registry": "pypi",
                "name": "jeanmemory"
            }
        }
    
    def get_current_versions(self) -> Dict[str, str]:
        """Get current version of each SDK"""
        versions = {}
        
        for sdk_name, config in self.sdks.items():
            try:
                if sdk_name == "python":
                    # Parse version from setup.py
                    setup_file = config["path"] / "setup.py"
                    with open(setup_file, 'r') as f:
                        content = f.read()
                        match = re.search(r'version="([^"]+)"', content)
                        if match:
                            versions[sdk_name] = match.group(1)
                        else:
                            versions[sdk_name] = "unknown"
                else:
                    # Parse version from package.json
                    package_file = config["path"] / "package.json"
                    with open(package_file, 'r') as f:
                        package_data = json.load(f)
                        versions[sdk_name] = package_data.get("version", "unknown")
            except Exception as e:
                log_error(f"Failed to get version for {sdk_name}: {e}")
                versions[sdk_name] = "error"
        
        return versions
    
    def update_version(self, sdk_name: str, new_version: str) -> bool:
        """Update version in SDK configuration files"""
        config = self.sdks[sdk_name]
        
        try:
            if sdk_name == "python":
                # Update setup.py
                setup_file = config["path"] / "setup.py"
                with open(setup_file, 'r') as f:
                    content = f.read()
                
                # Replace version in setup.py
                updated_content = re.sub(
                    r'version="[^"]+"',
                    f'version="{new_version}"',
                    content
                )
                
                with open(setup_file, 'w') as f:
                    f.write(updated_content)
                
                # Also update __init__.py if it has version
                init_file = config["path"] / "jean_memory" / "__init__.py"
                if init_file.exists():
                    with open(init_file, 'r') as f:
                        init_content = f.read()
                    
                    updated_init = re.sub(
                        r'__version__ = "[^"]+"',
                        f'__version__ = "{new_version}"',
                        init_content
                    )
                    
                    with open(init_file, 'w') as f:
                        f.write(updated_init)
                        
            else:
                # Update package.json
                package_file = config["path"] / "package.json"
                with open(package_file, 'r') as f:
                    package_data = json.load(f)
                
                package_data["version"] = new_version
                
                with open(package_file, 'w') as f:
                    json.dump(package_data, f, indent=2)
            
            log_success(f"Updated {sdk_name} version to {new_version}")
            return True
            
        except Exception as e:
            log_error(f"Failed to update {sdk_name} version: {e}")
            return False
    
    def build_sdk(self, sdk_name: str) -> bool:
        """Build a specific SDK"""
        config = self.sdks[sdk_name]
        
        try:
            log_info(f"Building {sdk_name} SDK...")
            
            # Change to SDK directory
            os.chdir(config["path"])
            
            # Run build command
            result = subprocess.run(
                config["build_command"],
                capture_output=True,
                text=True,
                check=True
            )
            
            log_success(f"Built {sdk_name} SDK successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            log_error(f"Failed to build {sdk_name} SDK: {e.stderr}")
            return False
        except Exception as e:
            log_error(f"Failed to build {sdk_name} SDK: {e}")
            return False
    
    def publish_sdk(self, sdk_name: str, dry_run: bool = False) -> bool:
        """Publish a specific SDK"""
        config = self.sdks[sdk_name]
        
        try:
            if dry_run:
                log_info(f"DRY RUN: Would publish {sdk_name} SDK to {config['registry']}")
                return True
            
            log_info(f"Publishing {sdk_name} SDK to {config['registry']}...")
            
            # Change to SDK directory
            os.chdir(config["path"])
            
            # Special handling for Python
            if sdk_name == "python":
                # Clean previous builds
                subprocess.run(["rm", "-rf", "dist/", "build/", "*.egg-info"], 
                             capture_output=True, check=False)
                
                # Build distribution
                subprocess.run(["python3", "setup.py", "sdist", "bdist_wheel"], 
                             capture_output=True, text=True, check=True)
            
            # Run publish command
            result = subprocess.run(
                config["publish_command"],
                capture_output=True,
                text=True,
                check=True
            )
            
            log_success(f"Published {sdk_name} SDK successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            log_error(f"Failed to publish {sdk_name} SDK: {e.stderr}")
            return False
        except Exception as e:
            log_error(f"Failed to publish {sdk_name} SDK: {e}")
            return False
    
    def increment_version(self, version: str, bump_type: str = "patch") -> str:
        """Increment version number (semantic versioning)"""
        try:
            major, minor, patch = map(int, version.split('.'))
            
            if bump_type == "major":
                major += 1
                minor = 0
                patch = 0
            elif bump_type == "minor":
                minor += 1
                patch = 0
            elif bump_type == "patch":
                patch += 1
            
            return f"{major}.{minor}.{patch}"
            
        except Exception as e:
            log_error(f"Failed to increment version {version}: {e}")
            return version
    
    def deploy_all(self, version: Optional[str] = None, bump_type: str = "patch", 
                   dry_run: bool = False, skip_build: bool = False) -> bool:
        """Deploy all SDKs with unified versioning"""
        
        log_step("🎯 JEAN MEMORY SDK UNIFIED DEPLOYMENT")
        print()
        
        # Get current versions
        current_versions = self.get_current_versions()
        log_info("Current versions:")
        for sdk_name, version in current_versions.items():
            print(f"  📦 {sdk_name}: {version}")
        print()
        
        # Determine new version
        if version is None:
            # Use highest current version and increment
            versions = [v for v in current_versions.values() if v != "unknown" and v != "error"]
            if not versions:
                log_error("No valid versions found")
                return False
            
            highest_version = max(versions, key=lambda v: tuple(map(int, v.split('.'))))
            new_version = self.increment_version(highest_version, bump_type)
        else:
            new_version = version
        
        log_step(f"Target version: {new_version}")
        if dry_run:
            log_warning("DRY RUN MODE - No actual changes will be made")
        print()
        
        # Update all versions
        log_step("📝 Updating versions...")
        for sdk_name in self.sdks:
            if not self.update_version(sdk_name, new_version):
                return False
        print()
        
        # Build all SDKs
        if not skip_build:
            log_step("🔨 Building SDKs...")
            for sdk_name in self.sdks:
                if not self.build_sdk(sdk_name):
                    return False
            print()
        
        # Publish all SDKs
        log_step("📤 Publishing SDKs...")
        for sdk_name in self.sdks:
            if not self.publish_sdk(sdk_name, dry_run):
                return False
        print()
        
        log_success("🎉 All SDKs deployed successfully!")
        log_info(f"All SDKs are now at version {new_version}")
        
        return True

def main():
    """Main deployment script"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Deploy all Jean Memory SDKs with unified versioning")
    parser.add_argument("--version", help="Specific version to deploy (e.g., 1.3.0)")
    parser.add_argument("--bump", choices=["major", "minor", "patch"], default="patch",
                       help="Version bump type (default: patch)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--skip-build", action="store_true", help="Skip build step")
    parser.add_argument("--sdks", nargs="+", choices=["react", "node", "python"], 
                       help="Deploy only specific SDKs")
    
    args = parser.parse_args()
    
    # Initialize deployer
    deployer = SDKDeployer(project_root)
    
    # Filter SDKs if specified
    if args.sdks:
        original_sdks = deployer.sdks.copy()
        deployer.sdks = {name: config for name, config in original_sdks.items() if name in args.sdks}
    
    # Run deployment
    success = deployer.deploy_all(
        version=args.version,
        bump_type=args.bump,
        dry_run=args.dry_run,
        skip_build=args.skip_build
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()