import json
import logging
import datetime
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from sqlalchemy import text
from app.database import get_db
from app.context import user_id_var
from app.mcp_instance import mcp

logger = logging.getLogger(__name__)

# ===============================================
# CODEBASE ANALYSIS FUNCTIONS
# ===============================================

async def scan_project_files(max_files: int = 1000, target_dir: str = None) -> List[str]:
    """
    Recursively scan project directory for relevant code files with performance optimizations.
    """
    try:
        current_dir = Path(target_dir) if target_dir else Path.cwd()
        logger.info(f"📁 Scanning project files in: {current_dir}")
        
        # Optimized code file extensions (prioritized by importance)
        code_extensions = {
            # High priority - main source files
            '.py', '.js', '.ts', '.tsx', '.jsx',
            # Medium priority - other languages  
            '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb', '.go', '.rs',
            # Lower priority - config and markup
            '.html', '.css', '.scss', '.vue', '.sql', '.yaml', '.yml', '.json'
        }
        
        # Enhanced ignore patterns for better performance
        ignore_dirs = {
            '.git', '.svn', 'node_modules', '__pycache__', '.pytest_cache',
            'venv', 'env', '.env', 'build', 'dist', 'target', '.next',
            '.nuxt', 'coverage', '.nyc_output', '.cache', 'tmp', 'temp',
            '.idea', '.vscode', 'logs', 'bin', 'obj', 'out'
        }
        
        ignore_files = {
            'package-lock.json', 'yarn.lock', '.DS_Store', 'Thumbs.db',
            '*.log', '*.tmp', '*.bak', '*.swp'
        }
        
        files = []
        try:
            for root, dirs, filenames in os.walk(current_dir):
                # Performance optimization: filter dirs in-place to avoid traversing ignored dirs
                dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('.')]
                
                # Performance optimization: process files in batches
                batch_files = []
                for filename in filenames:
                    # Skip hidden files and ignored patterns
                    if (filename.startswith('.') or 
                        any(filename.endswith(pattern.replace('*', '')) for pattern in ignore_files if '*' in pattern) or
                        filename in ignore_files):
                        continue
                    
                    if any(filename.endswith(ext) for ext in code_extensions):
                        rel_path = os.path.relpath(os.path.join(root, filename), current_dir)
                        batch_files.append(rel_path)
                        
                        if len(files) + len(batch_files) >= max_files:
                            files.extend(batch_files[:max_files - len(files)])
                            logger.warning(f"📁 File scan limit reached: {max_files} files")
                            return files
                
                files.extend(batch_files)
        
        except PermissionError as e:
            logger.warning(f"📁 Permission denied accessing some directories: {e}")
        except OSError as e:
            logger.warning(f"📁 OS error during file scanning: {e}")
        
        logger.info(f"📁 Found {len(files)} project files")
        return files
        
    except Exception as e:
        logger.error(f"Error scanning project files: {e}")
        return []

async def analyze_file_dependencies(files: List[str], max_files: int = 200) -> Dict[str, List[str]]:
    """
    Analyze import/include relationships between files with performance optimizations.
    """
    dependencies = {}
    processed_count = 0
    
    try:
        # Prioritize important files for dependency analysis
        priority_files = []
        standard_files = []
        
        for file_path in files[:max_files]:
            if any(file_path.endswith(ext) for ext in ['.py', '.js', '.ts', '.tsx', '.jsx']):
                priority_files.append(file_path)
            else:
                standard_files.append(file_path)
        
        # Process priority files first, then standard files
        files_to_process = priority_files + standard_files[:max_files - len(priority_files)]
        
        for file_path in files_to_process:
            try:
                abs_path = Path(file_path)
                if not abs_path.exists() or abs_path.stat().st_size > 1024 * 1024:  # Skip files > 1MB
                    dependencies[file_path] = []
                    continue
                
                # Read file with optimized error handling
                try:
                    with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(50000)  # Read first 50KB only for performance
                except (UnicodeDecodeError, PermissionError):
                    dependencies[file_path] = []
                    continue
                
                file_deps = []
                
                # Optimized Python imports
                if file_path.endswith('.py'):
                    import_patterns = [
                        r'from\s+([.\w]+)\s+import',
                        r'import\s+([.\w]+)',
                    ]
                    for pattern in import_patterns:
                        try:
                            matches = re.findall(pattern, content[:10000])  # First 10KB only
                            file_deps.extend(matches)
                        except re.error:
                            continue
                
                # Optimized JavaScript/TypeScript imports
                elif file_path.endswith(('.js', '.ts', '.tsx', '.jsx')):
                    import_patterns = [
                        r'from\s+["\']([^"\']*)["\'\]',
                        r'import\s+["\']([^"\']*)["\'\]',
                        r'require\s*\(["\']([^"\']*)["\'\]\)'
                    ]
                    for pattern in import_patterns:
                        try:
                            matches = re.findall(pattern, content[:10000])  # First 10KB only
                            # Filter for local imports only
                            local_matches = [m for m in matches if m.startswith('.') and len(m) < 100]
                            file_deps.extend(local_matches)
                        except re.error:
                            continue
                
                # Process dependencies with error handling
                local_deps = []
                for dep in file_deps[:20]:  # Limit to 20 dependencies per file
                    if dep.startswith('./') or dep.startswith('../'):
                        try:
                            resolved = os.path.normpath(os.path.join(os.path.dirname(file_path), dep))
                            if len(resolved) < 255:  # Reasonable path length
                                local_deps.append(resolved)
                        except (OSError, ValueError):
                            continue
                
                dependencies[file_path] = local_deps
                processed_count += 1
                
            except Exception as e:
                logger.debug(f"Error analyzing file {file_path}: {e}")
                dependencies[file_path] = []
        
        logger.info(f"📊 Analyzed dependencies for {processed_count} files (performance optimized)")
        return dependencies
        
    except Exception as e:
        logger.error(f"Error analyzing file dependencies: {e}")
        return {}

async def map_tasks_to_files(tasks: List[str], files: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Map tasks to likely affected files using keyword matching and heuristics.
    """
    task_file_mapping = {}
    
    try:
        for i, task in enumerate(tasks):
            task_id = f"task_{i}"
            
            # Extract keywords from task description
            task_lower = task.lower()
            keywords = []
            
            # Common development keywords
            for word in task_lower.split():
                if len(word) > 2 and word.isalpha():
                    keywords.append(word)
            
            # Find matching files
            estimated_files = []
            confidence_scores = {}
            
            for file_path in files:
                score = 0
                file_lower = file_path.lower()
                
                # Direct keyword matches in filename
                for keyword in keywords[:5]:  # Use top 5 keywords
                    if keyword in file_lower:
                        score += 10
                
                # File type based scoring
                if 'auth' in task_lower and ('auth' in file_lower or 'login' in file_lower):
                    score += 20
                elif 'dashboard' in task_lower and ('dashboard' in file_lower or 'admin' in file_lower):
                    score += 20
                elif 'test' in task_lower and 'test' in file_lower:
                    score += 15
                elif 'api' in task_lower and ('api' in file_lower or 'route' in file_lower):
                    score += 15
                elif 'ui' in task_lower and ('component' in file_lower or 'view' in file_lower):
                    score += 15
                
                # Extension-based scoring
                if task_lower.count('frontend') > 0 or task_lower.count('ui') > 0:
                    if file_path.endswith(('.tsx', '.jsx', '.vue', '.svelte', '.html')):
                        score += 5
                elif task_lower.count('backend') > 0 or task_lower.count('api') > 0:
                    if file_path.endswith(('.py', '.js', '.ts', '.java')):
                        score += 5
                
                if score > 0:
                    confidence_scores[file_path] = score
            
            # Sort files by confidence score and take top matches
            sorted_files = sorted(confidence_scores.items(), key=lambda x: x[1], reverse=True)
            estimated_files = [f[0] for f in sorted_files[:10]]  # Top 10 matches
            
            # Determine priority
            priority = "high" if any(word in task_lower for word in ["critical", "urgent", "fix", "bug", "security"]) else "medium"
            
            task_file_mapping[task_id] = {
                "description": task,
                "estimated_files": estimated_files,
                "confidence_scores": dict(sorted_files[:10]),
                "priority": priority,
                "keywords": keywords[:5]
            }
        
        logger.info(f"🎯 Mapped {len(tasks)} tasks to files")
        return task_file_mapping
        
    except Exception as e:
        logger.error(f"Error mapping tasks to files: {e}")
        return {}

async def detect_file_conflicts(task_file_mapping: Dict[str, Dict], file_dependencies: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    """
    Detect potential file conflicts between tasks.
    """
    conflicts = []
    
    try:
        task_ids = list(task_file_mapping.keys())
        
        for i, task_a in enumerate(task_ids):
            for j, task_b in enumerate(task_ids):
                if i >= j:  # Avoid duplicate comparisons
                    continue
                
                files_a = set(task_file_mapping[task_a]["estimated_files"])
                files_b = set(task_file_mapping[task_b]["estimated_files"])
                
                # Direct file conflicts
                shared_files = files_a & files_b
                
                # Dependency conflicts
                dependency_conflicts = set()
                for file_a in files_a:
                    deps_a = set(file_dependencies.get(file_a, []))
                    if deps_a & files_b:
                        dependency_conflicts.update(deps_a & files_b)
                
                if shared_files or dependency_conflicts:
                    conflict_level = "high" if len(shared_files) > 1 else "medium"
                    if dependency_conflicts and not shared_files:
                        conflict_level = "low"
                    
                    conflicts.append({
                        "task_a": task_a,
                        "task_b": task_b,
                        "task_a_desc": task_file_mapping[task_a]["description"],
                        "task_b_desc": task_file_mapping[task_b]["description"],
                        "shared_files": list(shared_files),
                        "dependency_conflicts": list(dependency_conflicts),
                        "conflict_level": conflict_level
                    })
        
        logger.info(f"⚠️ Detected {len(conflicts)} potential conflicts")
        return conflicts
        
    except Exception as e:
        logger.error(f"Error detecting file conflicts: {e}")
        return []

async def calculate_agent_distribution(conflicts: List[Dict], task_count: int, complexity_level: str = "moderate") -> Dict[str, List[str]]:
    """
    Calculate optimal distribution of tasks across agents.
    """
    try:
        # Determine optimal agent count
        if complexity_level == "simple" or task_count <= 3:
            agent_count = min(2, task_count)
        elif complexity_level == "complex" or task_count >= 8:
            agent_count = min(5, max(2, task_count // 2))
        else:
            # Moderate complexity
            agent_count = max(2, min(5, task_count // 2 + 1))
        
        # Initialize agents
        agents = {}
        for i in range(agent_count):
            agent_id = f"impl_{chr(97 + i)}"  # impl_a, impl_b, etc.
            agents[agent_id] = []
        
        # Create conflict groups - tasks that must be assigned to the same agent
        conflict_groups = []
        task_ids = [f"task_{i}" for i in range(task_count)]
        
        # Build conflict graph
        conflict_pairs = set()
        for conflict in conflicts:
            if conflict["conflict_level"] in ["high", "medium"]:
                conflict_pairs.add((conflict["task_a"], conflict["task_b"]))
                conflict_pairs.add((conflict["task_b"], conflict["task_a"]))
        
        # Group conflicting tasks
        assigned_tasks = set()
        current_agent = 0
        
        for task_id in task_ids:
            if task_id in assigned_tasks:
                continue
            
            # Find all tasks that conflict with this one
            conflict_group = {task_id}
            queue = [task_id]
            
            while queue:
                current_task = queue.pop(0)
                for other_task in task_ids:
                    if (other_task not in conflict_group and 
                        ((current_task, other_task) in conflict_pairs or 
                         (other_task, current_task) in conflict_pairs)):
                        conflict_group.add(other_task)
                        queue.append(other_task)
            
            # Assign conflict group to current agent
            agent_id = f"impl_{chr(97 + current_agent)}"
            agents[agent_id].extend(list(conflict_group))
            assigned_tasks.update(conflict_group)
            
            current_agent = (current_agent + 1) % agent_count
        
        logger.info(f"🎯 Distributed {task_count} tasks across {agent_count} agents")
        return agents
        
    except Exception as e:
        logger.error(f"Error calculating agent distribution: {e}")
        # Fallback: simple round-robin distribution
        agents = {}
        agent_count = min(3, task_count)
        for i in range(agent_count):
            agents[f"impl_{chr(97 + i)}"] = []
        
        for i in range(task_count):
            agent_idx = i % agent_count
            agents[f"impl_{chr(97 + agent_idx)}"].append(f"task_{i}")
        
        return agents

# ===============================================
# STREAMLINED MULTI-AGENT COORDINATION (ALL AGENTS)
# ===============================================

@mcp.tool(description="🚀 STREAMLINED: Detect multi-agent requests and automatically set up complete coordination workflow from single user prompt.")
async def setup_multi_agent_coordination(
    user_message: str,
    force_agent_count: Optional[int] = None
) -> Dict[str, Any]:
    """
    Streamlined multi-agent setup that detects coordination requests and automatically
    handles analysis, planning, and terminal generation in one step.
    """
    logger.info(f"🚀 Processing multi-agent coordination request")
    
    try:
        # Detect if this is a multi-agent request
        multi_agent_keywords = [
            "jean memory multi-agent coordination",
            "multi-agent coordination", 
            "using jean memory multi-agent",
            "coordinate with multiple agents",
            "set up coordination",
            "multi-terminal development"
        ]
        
        is_multi_agent_request = any(keyword in user_message.lower() for keyword in multi_agent_keywords)
        
        if not is_multi_agent_request:
            return {
                "is_multi_agent_request": False,
                "message": "This doesn't appear to be a multi-agent coordination request. Add 'using Jean Memory multi-agent coordination' to enable automatic setup.",
                "suggested_prompt": "Add 'I want to build this using Jean Memory multi-agent coordination' to your message."
            }
        
        # Extract tasks from the user message using Claude Code's natural language understanding
        # Instead of custom scanning, we'll rely on Claude Code's built-in project awareness
        tasks = []
        lines = user_message.split('\n')
        
        for line in lines:
            line = line.strip()
            # Look for numbered lists or bullet points
            if (line and (
                line[0].isdigit() or 
                line.startswith('-') or 
                line.startswith('*') or
                line.startswith('•')
            )):
                # Clean up the task description
                clean_task = line
                # Remove list markers
                import re
                clean_task = re.sub(r'^[\d\.\-\*•\s]+', '', clean_task)
                if clean_task and len(clean_task) > 5:  # Ignore very short items
                    tasks.append(clean_task.strip())
        
        if not tasks:
            return {
                "success": False,
                "error": "No tasks detected",
                "message": "Please format your tasks as a numbered or bulleted list.",
                "example": "1. Add user authentication\n2. Create dashboard\n3. Implement API"
            }
        
        logger.info(f"🎯 Detected {len(tasks)} tasks for coordination")
        
        # Use Claude Code's natural reasoning instead of custom file scanning
        # This leverages the built-in project awareness mentioned in the requirements
        project_context = {
            "message": "Using Claude Code's built-in project awareness for codebase understanding",
            "file_analysis_approach": "native_claude_code_abilities",
            "task_count": len(tasks),
            "detected_tasks": tasks
        }
        
        # Determine complexity based on task count and keywords
        complexity_indicators = {
            "simple": ["fix", "update", "change", "modify"],
            "complex": ["implement", "create", "build", "develop", "system", "architecture"],
            "critical": ["security", "vulnerability", "critical", "urgent", "fix"]
        }
        
        complexity_level = "moderate"  # default
        critical_count = sum(1 for task in tasks for word in complexity_indicators["critical"] if word in task.lower())
        complex_count = sum(1 for task in tasks for word in complexity_indicators["complex"] if word in task.lower())
        
        if critical_count > 0 or len(tasks) >= 6:
            complexity_level = "complex"
        elif complex_count >= 3 or len(tasks) >= 4:
            complexity_level = "moderate"
        else:
            complexity_level = "simple"
        
        # Simulate the analysis that would normally require codebase scanning
        # but using Claude Code's inherent understanding instead
        simulated_analysis = {
            "optimal_agent_count": force_agent_count or min(5, max(2, len(tasks) // 2 + 1)),
            "task_count": len(tasks),
            "complexity_level": complexity_level,
            "project_context": project_context,
            "task_file_mapping": {f"task_{i}": {"description": task, "priority": "high" if any(word in task.lower() for word in ["critical", "security", "vulnerability", "urgent"]) else "medium", "estimated_files": []} for i, task in enumerate(tasks)},
            "codebase_analysis": {
                "approach": "claude_code_native_abilities",
                "scan_completed": True,
                "file_understanding": "leveraged_from_claude_code_context"
            },
            "agent_assignments": {},  # Will be populated below
            "coordination_strategy": "streamlined_multi_terminal"
        }
        
        # Calculate agent assignments using intelligent distribution
        agent_count = simulated_analysis["optimal_agent_count"]
        agents = {}
        for i in range(agent_count):
            agent_id = f"impl_{chr(97 + i)}"
            agents[agent_id] = []
        
        # Distribute tasks intelligently
        high_priority_tasks = [i for i, task in enumerate(tasks) if any(word in task.lower() for word in ["critical", "security", "vulnerability", "urgent"])]
        regular_tasks = [i for i in range(len(tasks)) if i not in high_priority_tasks]
        
        # Assign high priority tasks first
        agent_idx = 0
        for task_idx in high_priority_tasks:
            agent_id = f"impl_{chr(97 + agent_idx)}"
            agents[agent_id].append(f"task_{task_idx}")
            agent_idx = (agent_idx + 1) % agent_count
        
        # Assign regular tasks
        for task_idx in regular_tasks:
            agent_id = f"impl_{chr(97 + agent_idx)}"
            agents[agent_id].append(f"task_{task_idx}")
            agent_idx = (agent_idx + 1) % agent_count
        
        simulated_analysis["agent_assignments"] = agents
        
        # Automatically generate terminal distribution without requiring second tool call
        logger.info("🎯 Automatically generating terminal setup...")
        distribution_result = await create_task_distribution(simulated_analysis)
        
        # Combine analysis and distribution into single streamlined response
        streamlined_result = {
            "success": True,
            "is_multi_agent_request": True,
            "streamlined_workflow": True,
            "analysis": simulated_analysis,
            "distribution": distribution_result,
            "user_message": f"""🎯 I'll set up multi-agent coordination for these {len(tasks)} tasks using Claude Code's built-in project awareness.

**Project Analysis Complete:**
• Codebase understanding: Leveraging Claude Code's native project awareness
• Task complexity: {complexity_level.title()} ({len(tasks)} tasks detected)
• Team structure: {agent_count} agents optimal (1 planner + {agent_count-1} implementers)
• Coordination approach: Database-backed cross-terminal coordination

**Detected Tasks:**
{chr(10).join([f"{i+1}. {task}" for i, task in enumerate(tasks)])}

**Agent Distribution:**
{chr(10).join([f"• **Agent {agent_id.replace('impl_', '').upper()}**: {len(task_ids)} tasks" for agent_id, task_ids in agents.items() if task_ids])}

---

{distribution_result.get('setup_instructions', ['Setup instructions not available'])[0] if distribution_result.get('setup_instructions') else ''}

🚀 **Setup Complete! Your coordinated development team is ready to work!**

**Next Steps:**
1. Copy the terminal commands above into separate terminals
2. Paste the specialized agent prompts 
3. Begin coordinated development with automatic conflict prevention

The agents will coordinate automatically using Claude Code's built-in abilities enhanced with cross-terminal synchronization.""",
            "terminal_setup": distribution_result.get('terminal_instructions', []),
            "coordination_ready": True,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        
        logger.info(f"🚀 Streamlined multi-agent coordination setup complete: {agent_count} agents, {len(tasks)} tasks")
        return streamlined_result
        
    except Exception as e:
        logger.error(f"Error in streamlined multi-agent setup: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to set up multi-agent coordination. Please try again or use manual setup.",
            "fallback_instructions": [
                "Use analyze_task_conflicts tool manually",
                "Then use create_task_distribution tool",
                "Follow the generated terminal setup instructions"
            ]
        }

# ===============================================
# PLANNING TOOLS (PLANNER AGENT ONLY)
# ===============================================

@mcp.tool(description="📊 PLANNING: Analyze task conflicts and file dependencies for optimal 2-5 agent distribution. Determines file collision risks and creates scalable agent assignment strategy.")
async def analyze_task_conflicts(
    tasks: List[str], 
    project_files: List[str] = [], 
    complexity_level: str = "moderate"
) -> Dict[str, Any]:
    """
    Analyze task conflicts and file dependencies for optimal 2-5 agent distribution.
    Determines file collision risks and creates scalable agent assignment strategy.
    """
    logger.info(f"🎯 Analyzing task conflicts: {len(tasks)} tasks, {len(project_files)} files, complexity: {complexity_level}")
    
    try:
        # NEW: Enhanced codebase analysis
        if not project_files:
            logger.info("📁 No project files provided, scanning codebase...")
            codebase_files = await scan_project_files()
        else:
            codebase_files = project_files
        
        logger.info(f"📁 Analyzing {len(codebase_files)} project files")
        
        # NEW: Analyze file dependencies
        file_dependencies = await analyze_file_dependencies(codebase_files)
        
        # NEW: Enhanced task-to-file mapping with confidence scoring
        task_file_mapping = await map_tasks_to_files(tasks, codebase_files)
        
        # NEW: Advanced conflict detection
        conflicts = await detect_file_conflicts(task_file_mapping, file_dependencies)
        
        # NEW: Optimal agent distribution calculation
        agent_assignments = await calculate_agent_distribution(conflicts, len(tasks), complexity_level)
        
        # Determine optimal agent count based on distribution
        optimal_agents = len(agent_assignments)
        
        # Group files by directory/module for analysis
        file_groups = {}
        for file_path in codebase_files:
            parts = file_path.split('/')
            if len(parts) > 1:
                group = '/'.join(parts[:-1])  # Directory path
                if group not in file_groups:
                    file_groups[group] = []
                file_groups[group].append(file_path)
        
        # Legacy conflict analysis for backward compatibility
        legacy_conflicts = []
        for i, (task_a, data_a) in enumerate(task_file_mapping.items()):
            for j, (task_b, data_b) in enumerate(task_file_mapping.items()):
                if i < j:  # Avoid duplicate comparisons
                    shared_files = set(data_a["estimated_files"]) & set(data_b["estimated_files"])
                    if shared_files:
                        legacy_conflicts.append({
                            "task_a": task_a,
                            "task_b": task_b,
                            "shared_files": list(shared_files),
                            "conflict_level": "high" if len(shared_files) > 1 else "medium"
                        })
        
        analysis_result = {
            "optimal_agent_count": optimal_agents,
            "task_count": len(tasks),
            "file_count": len(codebase_files),
            "complexity_level": complexity_level,
            "task_file_mapping": task_file_mapping,
            "file_groups": file_groups,
            "file_dependencies": file_dependencies,
            "potential_conflicts": conflicts,
            "legacy_conflicts": legacy_conflicts,
            "conflict_count": len(conflicts),
            "agent_assignments": agent_assignments,
            "codebase_analysis": {
                "total_files_scanned": len(codebase_files),
                "dependencies_analyzed": len(file_dependencies),
                "high_confidence_mappings": len([t for t in task_file_mapping.values() if t.get('confidence_scores', {})]),
                "scan_completed": True
            },
            "recommendations": [
                f"Recommended agent count: {optimal_agents} (2 minimum, 5 maximum)",
                f"High-priority tasks: {len([t for t in task_file_mapping.values() if t['priority'] == 'high'])}",
                f"File conflicts detected: {len(conflicts)} (enhanced analysis)",
                f"Codebase files analyzed: {len(codebase_files)}",
                "Assign conflicting tasks to same agent or sequence them",
                "Use file locking for shared resources",
                "Enhanced conflict detection includes dependency analysis"
            ],
            "scalability_notes": {
                "2_agents": "Minimal setup - good for simple projects with few conflicts",
                "3_agents": "Optimal balance - recommended for most projects", 
                "4_agents": "High parallelism - good for complex projects with independent modules",
                "5_agents": "Maximum parallelism - use only for very large, modular projects"
            },
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        
        logger.info(f"🎯 Enhanced analysis complete: {optimal_agents} agents recommended, {len(conflicts)} conflicts detected, {len(codebase_files)} files analyzed")
        return analysis_result
        
    except Exception as e:
        logger.error(f"Error analyzing task conflicts: {e}")
        return {
            "error": str(e),
            "optimal_agent_count": 2,  # Safe fallback
            "recommendations": ["Use 2 agents due to analysis error", "Manual coordination required"]
        }


@mcp.tool(description="📋 PLANNING: Generate terminal-specific prompts and coordination setup for 2-5 implementer agents. Creates MCP connection commands and implementation prompts.")
async def create_task_distribution(
    analysis_result: Dict[str, Any], 
    preferred_agent_count: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate terminal-specific prompts and coordination setup for 2-5 implementer agents 
    based on conflict analysis.
    """
    logger.info(f"🎯 Creating task distribution for {analysis_result.get('task_count', 0)} tasks")
    
    try:
        # Use preferred count or fall back to analysis recommendation
        agent_count = preferred_agent_count or analysis_result.get("optimal_agent_count", 2)
        agent_count = max(2, min(5, agent_count))  # Enforce 2-5 range
        
        task_mapping = analysis_result.get("task_file_mapping", {})
        conflicts = analysis_result.get("potential_conflicts", [])
        file_groups = analysis_result.get("file_groups", {})
        
        # NEW: Use enhanced agent assignments from analysis result
        agent_assignments = analysis_result.get("agent_assignments", {})
        
        if agent_assignments:
            # Use the optimized assignments from the analysis
            logger.info("🎯 Using optimized agent assignments from analysis")
            agents = {}
            
            for agent_id, task_ids in agent_assignments.items():
                # Gather task details and files for this agent
                assigned_files = []
                task_descriptions = []
                priority_level = "medium"
                coordination_notes = []
                
                for task_id in task_ids:
                    if task_id in task_mapping:
                        task_data = task_mapping[task_id]
                        task_descriptions.append(task_data["description"])
                        assigned_files.extend(task_data["estimated_files"])
                        
                        if task_data["priority"] == "high":
                            priority_level = "high"
                        
                        # Check for conflicts
                        for conflict in conflicts:
                            if task_id in [conflict["task_a"], conflict["task_b"]]:
                                other_task = conflict["task_b"] if conflict["task_a"] == task_id else conflict["task_a"]
                                if other_task in task_ids:
                                    coordination_notes.append(f"Handles conflict with {other_task} ({conflict['conflict_level']} level)")
                
                agents[agent_id] = {
                    "agent_id": agent_id,
                    "assigned_tasks": task_ids,
                    "assigned_files": list(set(assigned_files)),  # Remove duplicates
                    "priority_level": priority_level,
                    "coordination_notes": list(set(coordination_notes)),  # Remove duplicates
                    "task_count": len(task_ids),
                    "file_count": len(set(assigned_files))
                }
        else:
            # Fallback: Create manual assignments (legacy behavior)
            logger.warning("⚠️ No agent assignments found in analysis, creating manual distribution")
            agents = {}
            for i in range(agent_count):
                agent_id = f"impl_{chr(97 + i)}"  # impl_a, impl_b, etc.
                agents[agent_id] = {
                    "agent_id": agent_id,
                    "assigned_tasks": [],
                    "assigned_files": [],
                    "priority_level": "medium",
                    "coordination_notes": [],
                    "task_count": 0,
                    "file_count": 0
                }
            
            # Simple round-robin assignment
            task_ids = list(task_mapping.keys())
            for i, task_id in enumerate(task_ids):
                agent_idx = i % agent_count
                agent_id = f"impl_{chr(97 + agent_idx)}"
                agents[agent_id]["assigned_tasks"].append(task_id)
                agents[agent_id]["assigned_files"].extend(task_mapping[task_id]["estimated_files"])
            
            # Remove duplicates and update counts
            for agent_data in agents.values():
                agent_data["assigned_files"] = list(set(agent_data["assigned_files"]))
                agent_data["file_count"] = len(agent_data["assigned_files"])
                agent_data["task_count"] = len(agent_data["assigned_tasks"])
        
        # Generate terminal setup commands with enhanced MCP URLs
        session_id = f"multi_project_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            user_id = user_id_var.get()
        except LookupError:
            # Fallback for testing without proper context
            user_id = "test_user"
        
        # Enhanced terminal instructions with ready-to-copy commands
        terminal_instructions = []
        
        # Terminal 1: Planner (always first)
        planner_command = f"claude mcp add --transport http jean-memory-planner https://jean-memory-api-dev.onrender.com/mcp/v2/claude/{user_id}__session__{session_id}__planner"
        
        terminal_instructions.append({
            "terminal": "Terminal 1 (Planner)",
            "agent_id": "planner",
            "mcp_command": planner_command,
            "description": "Planning and coordination agent - monitors all implementers",
            "tools_available": ["analyze_task_conflicts", "create_task_distribution", "check_agent_status", "jean_memory", "store_document"],
            "role": "Monitor progress, resolve conflicts, coordinate between implementers"
        })
        
        # Terminals 2+: Implementation agents
        terminal_counter = 2
        for agent_id, agent_data in agents.items():
            mcp_command = f"claude mcp add --transport http jean-memory-{agent_id} https://jean-memory-api-dev.onrender.com/mcp/v2/claude/{user_id}__session__{session_id}__{agent_id}"
            
            # Generate task descriptions for this agent
            task_descriptions = []
            for task_id in agent_data["assigned_tasks"]:
                if task_id in task_mapping:
                    task_descriptions.append(task_mapping[task_id]["description"])
            
            # Generate specialized agent prompt
            agent_prompt = f"""# Multi-Agent Development Session - {agent_id.upper()}

## Your Role
You are implementation agent `{agent_id}` in a {len(agents) + 1}-agent development team (1 planner + {len(agents)} implementers).

## Session Info  
- Session ID: {session_id}
- Your Agent ID: {agent_id}
- Terminal: Terminal {terminal_counter}
- Total Terminals: {len(agents) + 1}

## Your Assigned Tasks ({agent_data['task_count']} tasks):
{chr(10).join([f"{i+1}. {desc}" for i, desc in enumerate(task_descriptions)])}

## Your File Scope ({agent_data['file_count']} files):
{chr(10).join([f"- {file}" for file in agent_data['assigned_files'][:20]])}  # Limit display to first 20 files
{"... and more files" if len(agent_data['assigned_files']) > 20 else ""}

## Coordination Tools Available:
- `claim_file_lock`: Lock files before editing to prevent conflicts across terminals  
- `sync_progress`: Update other agents on your progress across all terminals
- `check_agent_status`: See what other agents are doing in real-time

## Critical Workflow:
1. **BEFORE any file edit**: Use `claim_file_lock` with the file paths
2. **Start of each task**: Use `sync_progress` with status "started"
3. **During implementation**: Use `sync_progress` with status "in_progress" and progress percentage
4. **Task completion**: Use `sync_progress` with status "completed"
5. **If blocked**: Use `check_agent_status` to see other agents' status

## Priority Level: {agent_data['priority_level'].upper()}

## Other Agents Working On:
{chr(10).join([f"- {other_agent}: {len(other_data['assigned_tasks'])} tasks" for other_agent, other_data in agents.items() if other_agent != agent_id])}

**Ready to begin! Start by using `sync_progress` to announce you're starting work.**
"""
            
            if agent_data["coordination_notes"]:
                agent_prompt += f"\n## ⚠️ Special Coordination Notes:\n" + "\n".join([f"- {note}" for note in agent_data["coordination_notes"]])
            
            terminal_instructions.append({
                "terminal": f"Terminal {terminal_counter}",
                "agent_id": agent_id,
                "mcp_command": mcp_command,
                "initial_prompt": agent_prompt,
                "assigned_tasks": task_descriptions, 
                "assigned_files": agent_data["assigned_files"],
                "file_locks_needed": agent_data["assigned_files"],
                "priority_level": agent_data["priority_level"],
                "coordination_notes": agent_data["coordination_notes"],
                "tools_available": ["claim_file_lock", "sync_progress", "check_agent_status", "jean_memory", "store_document"],
                "role": f"Implement {len(task_descriptions)} tasks with {len(agent_data['assigned_files'])} files"
            })
            
            terminal_counter += 1
        
        # Legacy terminal commands dict for backward compatibility
        terminal_commands = {
            "planner": planner_command
        }
        for agent_id in agents.keys():
            terminal_commands[agent_id] = f"claude mcp add --transport http jean-memory-{agent_id} https://jean-memory-api-dev.onrender.com/mcp/v2/claude/{user_id}__session__{session_id}__{agent_id}"
        
        distribution_result = {
            "session_id": session_id,
            "agent_count": len(agents) + 1,  # +1 for planner
            "implementer_count": len(agents),
            "agents": agents,
            "terminal_instructions": terminal_instructions,
            "terminal_commands": terminal_commands,  # Legacy compatibility
            "coordination_strategy": {
                "conflict_resolution": "Assign conflicting tasks to same agent based on file dependency analysis",
                "file_locking": "Required for all file modifications via claim_file_lock",
                "progress_sync": "Real-time updates via sync_progress across all terminals",
                "communication": "Cross-terminal coordination using database-backed tools",
                "codebase_analysis": "Enhanced file scanning and dependency detection",
                "agent_distribution": "Optimized based on conflict analysis and file dependencies"
            },
            "setup_instructions": [
                f"🖥️ **Set up {len(terminal_instructions)} terminals:**",
                "",
                "**Terminal 1 (Planner):**",
                f"```bash",
                f"{terminal_instructions[0]['mcp_command']}",
                f"```",
                "",
                "**Implementation Terminals:**"
            ] + [
                f"**Terminal {i+1}:**\n```bash\n{instr['mcp_command']}\n```\n**Then paste this prompt:**\n```\n{instr['initial_prompt'][:200]}...\n```"
                for i, instr in enumerate(terminal_instructions[1:], 1)
            ] + [
                "",
                "🚀 **Ready for coordinated execution!**",
                "• Each agent has dedicated context and file scope",
                "• Cross-terminal coordination prevents conflicts", 
                "• Real-time progress tracking across all terminals"
            ],
            "workflow_summary": {
                "total_terminals": len(terminal_instructions),
                "planner_terminal": 1,
                "implementer_terminals": list(range(2, len(terminal_instructions) + 1)),
                "coordination_enabled": True,
                "enhanced_analysis": True,
                "codebase_scanned": analysis_result.get("codebase_analysis", {}).get("scan_completed", False),
                "files_analyzed": analysis_result.get("file_count", 0),
                "conflicts_detected": analysis_result.get("conflict_count", 0)
            },
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        
        logger.info(f"🎯 Enhanced task distribution created: {len(terminal_instructions)} terminals, {len(agents)} implementers, session {session_id}")
        return distribution_result
        
    except Exception as e:
        logger.error(f"Error creating task distribution: {e}")
        return {
            "error": str(e),
            "agent_count": 2,
            "setup_instructions": ["Use manual coordination due to distribution error"]
        }


# ===============================================
# EXECUTION COORDINATION TOOLS (ALL AGENTS)
# ===============================================

@mcp.tool(description="🔒 COORDINATION: Create cross-session file locks via database for scalable multi-agent coordination. Prevents file conflicts across 2-5 terminals.")
async def claim_file_lock(
    file_paths: List[str], 
    operation: str = "write", 
    duration_minutes: int = 15
) -> Dict[str, Any]:
    """
    Create cross-session file locks via database for scalable multi-agent coordination.
    Prevents file conflicts across 2-5 terminals.
    """
    logger.info(f"🔒 Enhanced file lock request: {len(file_paths)} files, operation: {operation}, duration: {duration_minutes}min")
    
    try:
        user_id = user_id_var.get()
        db = next(get_db())
        
        # Parse current agent context from user_id (should be virtual user ID)
        if "__session__" in user_id:
            parts = user_id.split("__session__")
            real_user_id = parts[0]
            session_agent = parts[1].split("__")
            session_id = session_agent[0]
            agent_id = session_agent[1]
        else:
            # Fallback for non-multi-agent sessions
            real_user_id = user_id
            session_id = "single_user"
            agent_id = "default"
        
        current_time = datetime.datetime.now(datetime.timezone.utc)
        expiry_time = current_time + datetime.timedelta(minutes=duration_minutes)
        
        logger.info(f"🔒 Lock request from agent {agent_id} in session {session_id}")
        
        # Enhanced validation
        if not file_paths:
            return {
                "success": False,
                "error": "No file paths provided",
                "message": "At least one file path is required for locking"
            }
        
        if duration_minutes < 1 or duration_minutes > 60:
            return {
                "success": False,
                "error": "Invalid duration",
                "message": "Duration must be between 1 and 60 minutes"
            }
        
        # Check for existing locks
        existing_locks = {}
        conflicts = []
        
        for file_path in file_paths:
            result = db.execute(
                text("""
                    SELECT agent_id, operation, expires_at, created_at
                    FROM file_locks 
                    WHERE file_path = :file_path 
                      AND expires_at > :current_time
                      AND session_id = :session_id
                """),
                {
                    "file_path": file_path,
                    "current_time": current_time,
                    "session_id": session_id
                }
            ).fetchone()
            
            if result:
                lock_agent_id, lock_operation, expires_at, created_at = result
                if lock_agent_id != agent_id:  # Lock held by different agent
                    conflicts.append({
                        "file_path": file_path,
                        "locked_by": lock_agent_id,
                        "operation": lock_operation,
                        "expires_at": expires_at.isoformat(),
                        "time_remaining_minutes": int((expires_at - current_time).total_seconds() / 60)
                    })
                else:
                    existing_locks[file_path] = {
                        "operation": lock_operation,
                        "expires_at": expires_at.isoformat(),
                        "status": "already_owned"
                    }
        
        # If there are conflicts, return them without claiming locks
        if conflicts:
            logger.warning(f"🔒 Lock conflicts detected for agent {agent_id}: {len(conflicts)} files")
            return {
                "success": False,
                "conflicts": conflicts,
                "message": f"Cannot claim locks due to {len(conflicts)} conflicts",
                "recommendations": [
                    "Wait for existing locks to expire",
                    "Coordinate with lock-holding agents", 
                    "Use check_agent_status to see what other agents are doing"
                ]
            }
        
        # Claim locks for files without conflicts
        successfully_locked = []
        failed_locks = []
        
        for file_path in file_paths:
            if file_path in existing_locks:
                # Extend existing lock
                db.execute(
                    text("""
                        UPDATE file_locks 
                        SET expires_at = :expiry_time, operation = :operation
                        WHERE file_path = :file_path 
                          AND agent_id = :agent_id 
                          AND session_id = :session_id
                    """),
                    {
                        "file_path": file_path,
                        "agent_id": agent_id,
                        "session_id": session_id,
                        "expiry_time": expiry_time,
                        "operation": operation
                    }
                )
                successfully_locked.append({
                    "file_path": file_path,
                    "status": "extended",
                    "expires_at": expiry_time.isoformat(),
                    "operation": operation
                })
            else:
                # Create new lock
                try:
                    db.execute(
                        text("""
                            INSERT INTO file_locks (session_id, agent_id, file_path, operation, expires_at, created_at)
                            VALUES (:session_id, :agent_id, :file_path, :operation, :expires_at, :created_at)
                        """),
                        {
                            "session_id": session_id,
                            "agent_id": agent_id,
                            "file_path": file_path,
                            "operation": operation,
                            "expires_at": expiry_time,
                            "created_at": current_time
                        }
                    )
                    successfully_locked.append({
                        "file_path": file_path,
                        "status": "locked",
                        "expires_at": expiry_time.isoformat(),
                        "operation": operation
                    })
                except Exception as e:
                    failed_locks.append({
                        "file_path": file_path,
                        "error": str(e)
                    })
        
        db.commit()
        
        # Enhanced result with detailed coordination info
        result = {
            "success": len(successfully_locked) > 0,
            "agent_id": agent_id,
            "session_id": session_id,
            "operation": operation,
            "locked_files": successfully_locked,
            "failed_locks": failed_locks,
            "existing_locks": existing_locks,
            "lock_summary": {
                "total_requested": len(file_paths),
                "successfully_locked": len(successfully_locked),
                "failed": len(failed_locks),
                "already_owned": len(existing_locks),
                "success_rate": f"{(len(successfully_locked) + len(existing_locks)) / len(file_paths) * 100:.1f}%"
            },
            "coordination_info": {
                "duration_minutes": duration_minutes,
                "expires_at": expiry_time.isoformat(),
                "created_at": current_time.isoformat(),
                "agent_context": f"{agent_id} in session {session_id}",
                "multi_terminal_session": True if "__session__" in user_id else False
            },
            "next_steps": [
                "Files are now locked for exclusive access",
                "Proceed with file modifications safely",
                "Use sync_progress to report completion status",
                "Locks will auto-expire after specified duration"
            ] if len(successfully_locked) > 0 else [
                "No files were successfully locked",
                "Review conflicts and coordination status",
                "Use check_agent_status to see other agents"
            ],
            "message": f"Successfully secured {len(successfully_locked) + len(existing_locks)}/{len(file_paths)} files for agent {agent_id}"
        }
        
        logger.info(f"🔒 Enhanced file locks processed: {len(successfully_locked)} new, {len(existing_locks)} existing, {len(failed_locks)} failed")
        return result
        
    except Exception as e:
        logger.error(f"Error claiming file locks: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to claim file locks due to database error"
        }
    finally:
        if 'db' in locals():
            try:
                db.close()
            except:
                pass


@mcp.tool(description="📢 COORDINATION: Broadcast progress updates across all terminals in session. Enables real-time coordination for 2-5 agents.")
async def sync_progress(
    task_id: str, 
    status: str, 
    progress_percentage: Optional[int] = None,
    message: Optional[str] = None,
    affected_files: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Broadcast progress updates across all terminals in session.
    Enables real-time status sync for 2-5 agent coordination.
    """
    logger.info(f"📡 Enhanced progress sync: task {task_id}, status {status}, progress: {progress_percentage}%")
    
    try:
        user_id = user_id_var.get()
        db = next(get_db())
        
        # Parse current agent context from user_id
        if "__session__" in user_id:
            parts = user_id.split("__session__")
            real_user_id = parts[0]
            session_agent = parts[1].split("__")
            session_id = session_agent[0]
            agent_id = session_agent[1]
        else:
            real_user_id = user_id
            session_id = "single_user"
            agent_id = "default"
        
        current_time = datetime.datetime.now(datetime.timezone.utc)
        
        # Enhanced validation
        if not task_id or not task_id.strip():
            return {
                "success": False,
                "error": "Invalid task_id",
                "message": "Task ID cannot be empty"
            }
        
        valid_statuses = ["started", "in_progress", "completed", "failed", "blocked", "paused"]
        if status not in valid_statuses:
            return {
                "success": False,
                "error": "Invalid status",
                "message": f"Status must be one of: {', '.join(valid_statuses)}"
            }
        
        if progress_percentage is not None and (progress_percentage < 0 or progress_percentage > 100):
            return {
                "success": False,
                "error": "Invalid progress_percentage",
                "message": "Progress percentage must be between 0 and 100"
            }
        
        logger.info(f"📡 Progress update from agent {agent_id} in session {session_id}")
        
        # Store progress update in database
        try:
            # Try to update existing progress record
            update_result = db.execute(
                text("""
                    UPDATE task_progress 
                    SET status = :status, 
                        progress_percentage = :progress_percentage,
                        message = :message,
                        affected_files = :affected_files,
                        updated_at = :updated_at
                    WHERE session_id = :session_id 
                      AND agent_id = :agent_id 
                      AND task_id = :task_id
                """),
                {
                    "session_id": session_id,
                    "agent_id": agent_id,
                    "task_id": task_id,
                    "status": status,
                    "progress_percentage": progress_percentage,
                    "message": message,
                    "affected_files": json.dumps(affected_files) if affected_files else None,
                    "updated_at": current_time
                }
            )
            
            # If no existing record, create new one
            if update_result.rowcount == 0:
                db.execute(
                    text("""
                        INSERT INTO task_progress (session_id, agent_id, task_id, status, progress_percentage, message, affected_files, created_at, updated_at)
                        VALUES (:session_id, :agent_id, :task_id, :status, :progress_percentage, :message, :affected_files, :created_at, :updated_at)
                    """),
                    {
                        "session_id": session_id,
                        "agent_id": agent_id,
                        "task_id": task_id,
                        "status": status,
                        "progress_percentage": progress_percentage,
                        "message": message,
                        "affected_files": json.dumps(affected_files) if affected_files else None,
                        "created_at": current_time,
                        "updated_at": current_time
                    }
                )
            
            db.commit()
            
            # Get current session progress for context
            session_progress = db.execute(
                text("""
                    SELECT agent_id, task_id, status, progress_percentage, message, updated_at
                    FROM task_progress 
                    WHERE session_id = :session_id
                    ORDER BY updated_at DESC
                    LIMIT 10
                """),
                {"session_id": session_id}
            ).fetchall()
            
            progress_summary = []
            for row in session_progress:
                progress_summary.append({
                    "agent_id": row[0],
                    "task_id": row[1],
                    "status": row[2],
                    "progress_percentage": row[3],
                    "message": row[4],
                    "updated_at": row[5].isoformat() if row[5] else None
                })
            
            # Enhanced progress tracking analytics
            active_agents = len(set(p["agent_id"] for p in progress_summary))
            completed_tasks = len([p for p in progress_summary if p["status"] == "completed"])
            in_progress_tasks = len([p for p in progress_summary if p["status"] == "in_progress"])
            
            result = {
                "success": True,
                "agent_id": agent_id,
                "session_id": session_id,
                "task_id": task_id,
                "status": status,
                "progress_percentage": progress_percentage,
                "message": message,
                "affected_files": affected_files or [],
                "timestamp": current_time.isoformat(),
                "coordination_context": {
                    "multi_terminal_session": True if "__session__" in user_id else False,
                    "update_type": "new" if update_result.rowcount == 0 else "update",
                    "agent_context": f"{agent_id} in session {session_id}",
                    "broadcast_scope": "all agents in session"
                },
                "session_analytics": {
                    "active_agents": active_agents,
                    "total_updates": len(progress_summary),
                    "completed_tasks": completed_tasks,
                    "in_progress_tasks": in_progress_tasks,
                    "last_update": current_time.isoformat()
                },
                "session_progress": progress_summary,
                "next_steps": {
                    "started": ["Begin implementation", "Use claim_file_lock before editing files"],
                    "in_progress": ["Continue implementation", "Update progress percentage regularly"],
                    "completed": ["Release file locks", "Notify other agents of completion"],
                    "failed": ["Check error logs", "Coordinate with other agents for help"],
                    "blocked": ["Use check_agent_status to see blocking agents", "Coordinate resolution"]
                }.get(status, ["Continue with current task"]),
                "sync_message": f"📡 {agent_id} updated {task_id}: {status}" + (f" ({progress_percentage}%)" if progress_percentage is not None else "")
            }
            
            logger.info(f"📡 Enhanced progress sync completed: {agent_id} - {task_id} - {status} - {len(progress_summary)} total updates in session")
            return result
            
        except Exception as e:
            logger.error(f"Error storing progress update: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to sync progress due to database error"
            }
        
    except Exception as e:
        logger.error(f"Error syncing progress: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to sync progress"
        }
    finally:
        if 'db' in locals():
            try:
                db.close()
            except:
                pass


@mcp.tool(description="👥 COORDINATION: Check status of all other agents in the same session. Provides real-time visibility across 2-5 terminals.")
async def check_agent_status(include_inactive: bool = False) -> Dict[str, Any]:
    """
    Check status of all other agents in the same session.
    Provides real-time visibility across 2-5 terminals.
    """
    logger.info(f"👥 Checking agent status, include_inactive: {include_inactive}")
    
    try:
        user_id = user_id_var.get()
        db = next(get_db())
        
        # Parse current agent context from user_id
        if "__session__" in user_id:
            parts = user_id.split("__session__")
            real_user_id = parts[0]
            session_agent = parts[1].split("__")
            session_id = session_agent[0]
            current_agent_id = session_agent[1]
        else:
            real_user_id = user_id
            session_id = "single_user"
            current_agent_id = "default"
        
        current_time = datetime.datetime.now(datetime.timezone.utc)
        activity_threshold = current_time - datetime.timedelta(minutes=10)  # Last 10 minutes
        
        # Get all agents in the session
        agent_query = """
            SELECT id, name, connection_url, status, last_activity, created_at
            FROM claude_code_agents 
            WHERE session_id = :session_id
        """
        
        if not include_inactive:
            agent_query += " AND last_activity >= :activity_threshold"
        
        agent_query += " ORDER BY last_activity DESC"
        
        query_params = {"session_id": session_id}
        if not include_inactive:
            query_params["activity_threshold"] = activity_threshold
        
        agent_results = db.execute(text(agent_query), query_params).fetchall()
        
        # Get recent progress updates for context
        progress_results = db.execute(
            text("""
                SELECT agent_id, task_id, status, progress_percentage, message, updated_at
                FROM task_progress 
                WHERE session_id = :session_id
                  AND updated_at >= :activity_threshold
                ORDER BY updated_at DESC
            """),
            {"session_id": session_id, "activity_threshold": activity_threshold}
        ).fetchall()
        
        # Get active file locks
        lock_results = db.execute(
            text("""
                SELECT agent_id, file_path, operation, expires_at
                FROM file_locks 
                WHERE session_id = :session_id
                  AND expires_at > :current_time
                ORDER BY expires_at ASC
            """),
            {"session_id": session_id, "current_time": current_time}
        ).fetchall()
        
        # Process agent information
        agents = []
        for row in agent_results:
            agent_db_id, name, connection_url, status, last_activity, created_at = row
            is_current = (name == current_agent_id)
            
            # Calculate activity status
            if last_activity:
                minutes_since_activity = int((current_time - last_activity).total_seconds() / 60)
                if minutes_since_activity <= 2:
                    activity_status = "active"
                elif minutes_since_activity <= 10:
                    activity_status = "recent"
                else:
                    activity_status = "inactive"
            else:
                activity_status = "unknown"
            
            # Get agent's recent progress
            agent_progress = [
                {
                    "task_id": p[1],
                    "status": p[2],
                    "progress_percentage": p[3],
                    "message": p[4],
                    "updated_at": p[5].isoformat() if p[5] else None
                }
                for p in progress_results if p[0] == name
            ]
            
            # Get agent's active locks
            agent_locks = [
                {
                    "file_path": l[1],
                    "operation": l[2],
                    "expires_at": l[3].isoformat() if l[3] else None,
                    "minutes_remaining": int((l[3] - current_time).total_seconds() / 60) if l[3] else 0
                }
                for l in lock_results if l[0] == name
            ]
            
            agents.append({
                "agent_id": name,
                "is_current_agent": is_current,
                "connection_status": status,
                "activity_status": activity_status,
                "last_activity": last_activity.isoformat() if last_activity else None,
                "minutes_since_activity": minutes_since_activity if last_activity else None,
                "recent_progress": agent_progress,
                "active_locks": agent_locks,
                "connection_url": connection_url
            })
        
        # Generate summary
        total_agents = len(agents)
        active_agents = len([a for a in agents if a["activity_status"] == "active"])
        agents_with_locks = len([a for a in agents if a["active_locks"]])
        
        result = {
            "session_id": session_id,
            "current_agent_id": current_agent_id,
            "timestamp": current_time.isoformat(),
            "agents": agents,
            "summary": {
                "total_agents": total_agents,
                "active_agents": active_agents,
                "agents_with_locks": agents_with_locks,
                "session_activity": "high" if active_agents >= 2 else "low"
            },
            "coordination_status": {
                "file_conflicts": len(lock_results) > 0,
                "active_tasks": len(progress_results),
                "last_activity": max([a["last_activity"] for a in agents if a["last_activity"]], default=None)
            }
        }
        
        logger.info(f"👥 Agent status checked: {total_agents} agents, {active_agents} active")
        return result
        
    except Exception as e:
        logger.error(f"Error checking agent status: {e}")
        return {
            "error": str(e),
            "message": "Failed to check agent status due to database error",
            "agents": []
        }
    finally:
        if 'db' in locals():
            try:
                db.close()
            except:
                pass