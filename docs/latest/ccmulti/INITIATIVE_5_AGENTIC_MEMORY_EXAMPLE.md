# Initiative 5: Agentic Memory Example with Claude Code

## Overview

This initiative demonstrates Jean Memory's agentic capabilities by creating an example where two Claude Code sessions share the same memory layer to collaboratively complete a list of tasks. This showcases the power of shared memory for multi-agent coordination and knowledge persistence.

## Architecture Design

```
┌─────────────────────────────────────────────────────────────────┐
│                        Agentic Memory System                     │
│                                                                  │
│  ┌───────────────────────────────┐  ┌───────────────────────────────┐  │
│  │      Claude Code Session A        │  │      Claude Code Session B        │  │
│  │      (Research Agent)            │  │      (Implementation Agent)       │  │
│  │                                 │  │                                 │  │
│  │  - Task assignment              │  │  - Code implementation          │  │
│  │  - Research & planning          │  │  - Testing & validation         │  │
│  │  - Progress tracking            │  │  - Documentation                │  │
│  └──────────┬────────────────────┘  └──────────┬────────────────────┘  │
│              │                                      │              │
│              │                                      │              │
│              ▼                  MCP Tools            ▼              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Shared Memory Layer                       │ │
│  │                                                              │ │
│  │  ┌───────────────────────────────────────────────────────┐   │ │
│  │  │               Short-term Memory (Local)                │   │ │
│  │  │                                                        │   │ │
│  │  │  • Task list and status                             │   │ │
│  │  │  • Research findings                                │   │ │
│  │  │  • Code snippets and solutions                      │   │ │
│  │  │  • Inter-agent communication                        │   │ │
│  │  │  • Progress logs and coordination                    │   │ │
│  │  └───────────────────────────────────────────────────────┘   │ │
│  │                                                              │ │
│  │  ┌───────────────────────────────────────────────────────┐   │ │
│  │  │  FAISS Vector Store    Neo4j Graph    Local Storage    │   │ │
│  │  │  - Semantic search     - Task deps    - File system    │   │ │
│  │  │  - Quick retrieval     - Relations    - Quick access   │   │ │
│  │  └───────────────────────────────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

## Prerequisites

**Depends on**: [INITIATIVE_0_LOCAL_DEVELOPMENT_SETUP.md](./INITIATIVE_0_LOCAL_DEVELOPMENT_SETUP.md)

Before implementing the agentic memory example, ensure:
- Local development environment with full stack is running
- Short-term memory system is operational locally
- MCP tools are testable in local environment
- Multi-agent testing infrastructure is available

## Implementation Plan

### Phase 1: Shared Memory Infrastructure

Builds on [INITIATIVE_1_SHORT_TERM_MEMORY_SYSTEM.md](./INITIATIVE_1_SHORT_TERM_MEMORY_SYSTEM.md).

#### 1.1 Agentic Memory Manager

```python
# agentic_memory/manager.py
import asyncio
import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from jean_memory_local import LocalMemory

@dataclass
class Task:
    id: str
    title: str
    description: str
    status: str  # 'pending', 'in_progress', 'completed', 'blocked'
    assigned_to: Optional[str] = None
    dependencies: List[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class AgentMessage:
    from_agent: str
    to_agent: Optional[str]  # None for broadcast
    message_type: str  # 'task_update', 'question', 'info', 'coordination'
    content: str
    task_id: Optional[str] = None
    timestamp: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}

class AgenticMemoryManager:
    """
    Manages shared memory for multiple agents working on collaborative tasks.
    """
    
    def __init__(self, session_id: str, memory_config: Dict[str, Any]):
        self.session_id = session_id
        self.memory = LocalMemory(memory_config)
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.tasks: Dict[str, Task] = {}
        self.message_queue: List[AgentMessage] = []
        
        # Initialize session memory
        asyncio.create_task(self._initialize_session())
    
    async def _initialize_session(self):
        """Initialize the shared memory session."""
        
        session_info = {
            "session_id": self.session_id,
            "created_at": datetime.utcnow().isoformat(),
            "status": "active",
            "agents": {},
            "tasks": {},
            "coordination_log": []
        }
        
        await self.memory.add_memories(
            memories=[f"Agentic session {self.session_id} initialized"],
            user_id=self.session_id,
            metadata={
                "type": "session_init",
                "session_data": session_info
            },
            layer="short"
        )
    
    async def register_agent(
        self, 
        agent_id: str, 
        agent_name: str, 
        capabilities: List[str],
        role: str
    ) -> bool:
        """Register an agent in the shared memory system."""
        
        agent_info = {
            "id": agent_id,
            "name": agent_name,
            "capabilities": capabilities,
            "role": role,
            "status": "active",
            "registered_at": datetime.utcnow().isoformat(),
            "tasks_assigned": [],
            "tasks_completed": []
        }
        
        self.agents[agent_id] = agent_info
        
        # Store agent registration in memory
        await self.memory.add_memories(
            memories=[f"Agent {agent_name} ({role}) registered with capabilities: {', '.join(capabilities)}"],
            user_id=self.session_id,
            metadata={
                "type": "agent_registration",
                "agent_id": agent_id,
                "agent_data": agent_info
            },
            layer="short"
        )
        
        return True
    
    async def create_task(
        self,
        title: str,
        description: str,
        created_by: str,
        dependencies: List[str] = None
    ) -> Task:
        """Create a new task in the shared memory."""
        
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            title=title,
            description=description,
            status="pending",
            dependencies=dependencies or []
        )
        
        self.tasks[task_id] = task
        
        # Store task in memory
        await self.memory.add_memories(
            memories=[f"Task created: {title} - {description}"],
            user_id=self.session_id,
            metadata={
                "type": "task_creation",
                "task_id": task_id,
                "created_by": created_by,
                "task_data": task.__dict__
            },
            layer="short"
        )
        
        return task
    
    async def assign_task(self, task_id: str, agent_id: str, assigned_by: str) -> bool:
        """Assign a task to an agent."""
        
        if task_id not in self.tasks or agent_id not in self.agents:
            return False
        
        task = self.tasks[task_id]
        task.assigned_to = agent_id
        task.status = "in_progress"
        task.updated_at = datetime.utcnow()
        
        # Update agent's task list
        self.agents[agent_id]["tasks_assigned"].append(task_id)
        
        # Store assignment in memory
        await self.memory.add_memories(
            memories=[f"Task '{task.title}' assigned to agent {self.agents[agent_id]['name']}"],
            user_id=self.session_id,
            metadata={
                "type": "task_assignment",
                "task_id": task_id,
                "agent_id": agent_id,
                "assigned_by": assigned_by,
                "assignment_time": datetime.utcnow().isoformat()
            },
            layer="short"
        )
        
        return True
    
    async def update_task_status(
        self, 
        task_id: str, 
        new_status: str, 
        updated_by: str,
        notes: Optional[str] = None
    ) -> bool:
        """Update task status and store the change in memory."""
        
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        old_status = task.status
        task.status = new_status
        task.updated_at = datetime.utcnow()
        
        # If task is completed, update agent's completed tasks
        if new_status == "completed" and task.assigned_to:
            self.agents[task.assigned_to]["tasks_completed"].append(task_id)
        
        # Store status update in memory
        update_message = f"Task '{task.title}' status changed from {old_status} to {new_status}"
        if notes:
            update_message += f". Notes: {notes}"
        
        await self.memory.add_memories(
            memories=[update_message],
            user_id=self.session_id,
            metadata={
                "type": "task_status_update",
                "task_id": task_id,
                "old_status": old_status,
                "new_status": new_status,
                "updated_by": updated_by,
                "notes": notes,
                "update_time": datetime.utcnow().isoformat()
            },
            layer="short"
        )
        
        return True
    
    async def send_message(
        self,
        message: AgentMessage
    ) -> bool:
        """Send a message between agents via shared memory."""
        
        self.message_queue.append(message)
        
        # Store message in memory
        message_content = f"[{message.message_type.upper()}] {message.from_agent}"
        if message.to_agent:
            message_content += f" → {message.to_agent}"
        else:
            message_content += " → ALL"
        message_content += f": {message.content}"
        
        await self.memory.add_memories(
            memories=[message_content],
            user_id=self.session_id,
            metadata={
                "type": "agent_message",
                "from_agent": message.from_agent,
                "to_agent": message.to_agent,
                "message_type": message.message_type,
                "task_id": message.task_id,
                "timestamp": message.timestamp.isoformat(),
                "message_data": message.__dict__
            },
            layer="short"
        )
        
        return True
    
    async def get_agent_context(self, agent_id: str, limit: int = 20) -> Dict[str, Any]:
        """Get relevant context for an agent from shared memory."""
        
        # Search for recent messages and updates relevant to this agent
        context_query = f"agent {agent_id} tasks messages updates"
        
        search_results = await self.memory.search_memories(
            query=context_query,
            user_id=self.session_id,
            limit=limit,
            layer="short"
        )
        
        # Get current tasks for this agent
        agent_tasks = [
            task for task in self.tasks.values() 
            if task.assigned_to == agent_id
        ]
        
        # Get recent messages for this agent
        recent_messages = [
            msg for msg in self.message_queue[-10:]
            if msg.to_agent == agent_id or msg.to_agent is None
        ]
        
        return {
            "agent_info": self.agents.get(agent_id, {}),
            "assigned_tasks": [task.__dict__ for task in agent_tasks],
            "recent_messages": [msg.__dict__ for msg in recent_messages],
            "memory_context": [
                {
                    "content": result.content,
                    "metadata": result.metadata,
                    "score": result.score
                }
                for result in search_results
            ],
            "session_stats": {
                "total_tasks": len(self.tasks),
                "completed_tasks": len([t for t in self.tasks.values() if t.status == "completed"]),
                "active_agents": len([a for a in self.agents.values() if a["status"] == "active"])
            }
        }
    
    async def get_task_dependencies(self, task_id: str) -> List[Task]:
        """Get task dependencies and check if they're completed."""
        
        if task_id not in self.tasks:
            return []
        
        task = self.tasks[task_id]
        dependencies = []
        
        for dep_id in task.dependencies:
            if dep_id in self.tasks:
                dependencies.append(self.tasks[dep_id])
        
        return dependencies
    
    async def get_available_tasks(self, agent_id: str) -> List[Task]:
        """Get tasks that are available for the agent to work on."""
        
        agent_capabilities = self.agents.get(agent_id, {}).get("capabilities", [])
        available_tasks = []
        
        for task in self.tasks.values():
            # Task must be pending and not assigned
            if task.status != "pending" or task.assigned_to is not None:
                continue
            
            # Check if dependencies are met
            deps_completed = all(
                self.tasks[dep_id].status == "completed"
                for dep_id in task.dependencies
                if dep_id in self.tasks
            )
            
            if deps_completed:
                available_tasks.append(task)
        
        return available_tasks
```

### Phase 2: Claude Code Integration

#### 2.1 MCP Tools for Agentic Operations

Builds on [JEAN_MEMORY_MCP_INTEGRATION.md](./JEAN_MEMORY_MCP_INTEGRATION.md).

```python
# app/tools/agentic_memory.py
from app.mcp_instance import mcp
from typing import List, Optional, Dict, Any
from agentic_memory.manager import AgenticMemoryManager, Task, AgentMessage
import asyncio
import json

# Global manager instances
active_sessions: Dict[str, AgenticMemoryManager] = {}

@mcp.tool(description="Initialize or join an agentic memory session")
async def init_agentic_session(
    session_id: str,
    agent_id: str,
    agent_name: str,
    agent_role: str,
    capabilities: List[str]
) -> Dict[str, Any]:
    """
    Initialize or join a shared agentic memory session.
    
    Args:
        session_id: Unique identifier for the collaboration session
        agent_id: Unique identifier for this agent
        agent_name: Human-readable name for this agent
        agent_role: Role of the agent (e.g., 'researcher', 'implementer')
        capabilities: List of capabilities this agent has
    
    Returns:
        Session initialization result and agent context
    """
    
    # Get or create session
    if session_id not in active_sessions:
        memory_config = {
            "vector_store": {
                "provider": "faiss",
                "config": {
                    "index_path": f"~/.jean_memory/agentic/{session_id}/faiss_index",
                    "dimension": 1536
                }
            },
            "graph_store": {
                "provider": "neo4j",
                "config": {
                    "uri": "bolt://localhost:7687",
                    "auth": ["neo4j", "jeanmemory123"],
                    "database": f"agentic_{session_id.replace('-', '_')}"
                }
            }
        }
        
        active_sessions[session_id] = AgenticMemoryManager(session_id, memory_config)
    
    manager = active_sessions[session_id]
    
    # Register this agent
    success = await manager.register_agent(agent_id, agent_name, capabilities, agent_role)
    
    if not success:
        return {"error": "Failed to register agent"}
    
    # Get initial context
    context = await manager.get_agent_context(agent_id)
    
    return {
        "status": "success",
        "session_id": session_id,
        "agent_id": agent_id,
        "message": f"Agent {agent_name} successfully joined session {session_id}",
        "context": context
    }

@mcp.tool(description="Create a new task in the agentic session")
async def create_agentic_task(
    session_id: str,
    agent_id: str,
    title: str,
    description: str,
    dependencies: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create a new task in the agentic memory session.
    
    Args:
        session_id: Session identifier
        agent_id: Agent creating the task
        title: Task title
        description: Detailed task description
        dependencies: List of task IDs this task depends on
    
    Returns:
        Created task information
    """
    
    if session_id not in active_sessions:
        return {"error": "Session not found"}
    
    manager = active_sessions[session_id]
    
    task = await manager.create_task(
        title=title,
        description=description,
        created_by=agent_id,
        dependencies=dependencies or []
    )
    
    return {
        "status": "success",
        "task": task.__dict__,
        "message": f"Task '{title}' created successfully"
    }

@mcp.tool(description="Get available tasks that can be assigned to the agent")
async def get_available_tasks(
    session_id: str,
    agent_id: str
) -> Dict[str, Any]:
    """
    Get tasks that are available for the agent to work on.
    
    Args:
        session_id: Session identifier
        agent_id: Agent requesting tasks
    
    Returns:
        List of available tasks
    """
    
    if session_id not in active_sessions:
        return {"error": "Session not found"}
    
    manager = active_sessions[session_id]
    
    available_tasks = await manager.get_available_tasks(agent_id)
    
    return {
        "status": "success",
        "available_tasks": [task.__dict__ for task in available_tasks],
        "count": len(available_tasks)
    }

@mcp.tool(description="Assign a task to the current agent")
async def assign_task_to_self(
    session_id: str,
    agent_id: str,
    task_id: str
) -> Dict[str, Any]:
    """
    Assign a task to the current agent.
    
    Args:
        session_id: Session identifier
        agent_id: Agent taking the task
        task_id: Task to assign
    
    Returns:
        Assignment result
    """
    
    if session_id not in active_sessions:
        return {"error": "Session not found"}
    
    manager = active_sessions[session_id]
    
    success = await manager.assign_task(task_id, agent_id, agent_id)
    
    if not success:
        return {"error": "Failed to assign task"}
    
    return {
        "status": "success",
        "message": f"Task {task_id} assigned to agent {agent_id}"
    }

@mcp.tool(description="Update task status with notes")
async def update_task_status(
    session_id: str,
    agent_id: str,
    task_id: str,
    new_status: str,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update the status of a task.
    
    Args:
        session_id: Session identifier
        agent_id: Agent updating the task
        task_id: Task to update
        new_status: New status (pending, in_progress, completed, blocked)
        notes: Optional notes about the update
    
    Returns:
        Update result
    """
    
    if session_id not in active_sessions:
        return {"error": "Session not found"}
    
    manager = active_sessions[session_id]
    
    success = await manager.update_task_status(task_id, new_status, agent_id, notes)
    
    if not success:
        return {"error": "Failed to update task status"}
    
    return {
        "status": "success",
        "message": f"Task {task_id} status updated to {new_status}"
    }

@mcp.tool(description="Send a message to other agents")
async def send_agent_message(
    session_id: str,
    from_agent: str,
    message_type: str,
    content: str,
    to_agent: Optional[str] = None,
    task_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send a message to other agents in the session.
    
    Args:
        session_id: Session identifier
        from_agent: Agent sending the message
        message_type: Type of message (task_update, question, info, coordination)
        content: Message content
        to_agent: Specific agent to send to (None for broadcast)
        task_id: Related task ID if applicable
    
    Returns:
        Message sending result
    """
    
    if session_id not in active_sessions:
        return {"error": "Session not found"}
    
    manager = active_sessions[session_id]
    
    message = AgentMessage(
        from_agent=from_agent,
        to_agent=to_agent,
        message_type=message_type,
        content=content,
        task_id=task_id
    )
    
    success = await manager.send_message(message)
    
    if not success:
        return {"error": "Failed to send message"}
    
    return {
        "status": "success",
        "message": "Message sent successfully"
    }

@mcp.tool(description="Get current agent context and session status")
async def get_agent_context(
    session_id: str,
    agent_id: str
) -> Dict[str, Any]:
    """
    Get comprehensive context for the current agent.
    
    Args:
        session_id: Session identifier
        agent_id: Agent requesting context
    
    Returns:
        Agent context including tasks, messages, and session status
    """
    
    if session_id not in active_sessions:
        return {"error": "Session not found"}
    
    manager = active_sessions[session_id]
    
    context = await manager.get_agent_context(agent_id)
    
    return {
        "status": "success",
        "context": context
    }

@mcp.tool(description="Search the shared memory for relevant information")
async def search_shared_memory(
    session_id: str,
    query: str,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Search the shared memory for relevant information.
    
    Args:
        session_id: Session identifier
        query: Search query
        limit: Maximum number of results
    
    Returns:
        Search results from shared memory
    """
    
    if session_id not in active_sessions:
        return {"error": "Session not found"}
    
    manager = active_sessions[session_id]
    
    results = await manager.memory.search_memories(
        query=query,
        user_id=session_id,
        limit=limit,
        layer="short"
    )
    
    return {
        "status": "success",
        "results": [
            {
                "content": result.content,
                "metadata": result.metadata,
                "score": result.score
            }
            for result in results
        ],
        "count": len(results)
    }
```

### Phase 3: Example Implementation

#### 3.1 Task List for Collaborative Example

```python
# examples/collaborative_project.py
"""
Example: Two Claude Code sessions collaborating on a web scraping project.

This example demonstrates:
1. Shared memory coordination
2. Task assignment and tracking
3. Inter-agent communication
4. Knowledge sharing and reuse
"""

SAMPLE_PROJECT_TASKS = [
    {
        "title": "Research web scraping best practices",
        "description": "Research and document best practices for ethical web scraping, including rate limiting, robots.txt compliance, and common anti-scraping measures.",
        "dependencies": []
    },
    {
        "title": "Choose appropriate libraries",
        "description": "Research and recommend Python libraries for web scraping (requests, beautifulsoup4, scrapy, etc.) based on project requirements.",
        "dependencies": []
    },
    {
        "title": "Design scraper architecture",
        "description": "Design the overall architecture for a modular web scraper that can handle multiple websites with different structures.",
        "dependencies": ["research_best_practices", "choose_libraries"]
    },
    {
        "title": "Implement base scraper class",
        "description": "Create a base scraper class with common functionality like request handling, rate limiting, and error handling.",
        "dependencies": ["design_architecture"]
    },
    {
        "title": "Implement specific site scrapers",
        "description": "Create specific scraper implementations for 2-3 different websites (e.g., news sites, e-commerce, blogs).",
        "dependencies": ["implement_base_scraper"]
    },
    {
        "title": "Add data storage functionality",
        "description": "Implement data storage options (JSON, CSV, database) with configurable output formats.",
        "dependencies": ["implement_base_scraper"]
    },
    {
        "title": "Create configuration system",
        "description": "Build a configuration system to manage scraper settings, target sites, and output preferences.",
        "dependencies": ["design_architecture"]
    },
    {
        "title": "Add logging and monitoring",
        "description": "Implement comprehensive logging and monitoring to track scraper performance and issues.",
        "dependencies": ["implement_base_scraper"]
    },
    {
        "title": "Write comprehensive tests",
        "description": "Create unit tests and integration tests for all scraper components.",
        "dependencies": ["implement_specific_scrapers", "add_data_storage"]
    },
    {
        "title": "Create documentation",
        "description": "Write user documentation, API reference, and setup instructions.",
        "dependencies": ["write_tests"]
    }
]

def setup_collaborative_session():
    """
    Setup instructions for the collaborative session.
    """
    
    print("""
    🤖 Agentic Memory Collaboration Example
    =====================================
    
    This example demonstrates two Claude Code sessions working together on a web scraping project.
    
    Setup Instructions:
    
    1. Start two separate Claude Code sessions
    
    2. In Session A (Research Agent):
       - Run: init_agentic_session(
           session_id="webscraper_collab",
           agent_id="researcher_agent",
           agent_name="Research Agent",
           agent_role="researcher",
           capabilities=["research", "analysis", "documentation", "planning"]
         )
    
    3. In Session B (Implementation Agent):
       - Run: init_agentic_session(
           session_id="webscraper_collab",
           agent_id="implementation_agent",
           agent_name="Implementation Agent",
           agent_role="implementer",
           capabilities=["coding", "testing", "debugging", "integration"]
         )
    
    4. Create tasks (can be done by either agent):
       - Use create_agentic_task() for each task in the project
    
    5. Start collaboration:
       - Each agent uses get_available_tasks() to see what they can work on
       - Use assign_task_to_self() to take on tasks
       - Use update_task_status() to track progress
       - Use send_agent_message() to communicate
    
    Expected Workflow:
    - Research Agent: Takes research and planning tasks
    - Implementation Agent: Takes coding and testing tasks
    - Both agents: Share findings via shared memory
    - Coordination: Agents communicate about dependencies and blockers
    """
    )

if __name__ == "__main__":
    setup_collaborative_session()
```

#### 3.2 Agent Instruction Templates

```markdown
<!-- examples/research_agent_instructions.md -->
# Research Agent Instructions

You are the **Research Agent** in a collaborative web scraping project. Your role is to handle research, analysis, and planning tasks.

## Your Capabilities
- Research and analysis
- Documentation writing
- Project planning
- Best practices investigation

## Getting Started

1. **Initialize your session:**
```python
result = init_agentic_session(
    session_id="webscraper_collab",
    agent_id="researcher_agent",
    agent_name="Research Agent",
    agent_role="researcher",
    capabilities=["research", "analysis", "documentation", "planning"]
)
print(result)
```

2. **Check for available tasks:**
```python
available = get_available_tasks("webscraper_collab", "researcher_agent")
print(f"Available tasks: {available['count']}")
for task in available['available_tasks']:
    print(f"- {task['title']}: {task['description']}")
```

3. **Take on a research task:**
```python
# Look for tasks that match your capabilities
task_id = "research_task_id"  # Replace with actual task ID
assign_result = assign_task_to_self("webscraper_collab", "researcher_agent", task_id)
print(assign_result)
```

## Working on Tasks

### When you start a task:
```python
update_task_status(
    "webscraper_collab", 
    "researcher_agent", 
    task_id, 
    "in_progress",
    "Starting research on web scraping best practices"
)
```

### Share your findings:
```python
# After completing research, share key findings
send_agent_message(
    session_id="webscraper_collab",
    from_agent="researcher_agent",
    message_type="info",
    content="Key finding: Rate limiting should be implemented with exponential backoff. Recommended: 1-2 second delays between requests.",
    to_agent=None  # Broadcast to all agents
)
```

### Complete a task:
```python
update_task_status(
    "webscraper_collab",
    "researcher_agent",
    task_id,
    "completed",
    "Research completed. Key recommendations: 1) Use requests-html for JS rendering, 2) Implement rotating user agents, 3) Respect robots.txt files"
)
```

## Communication Patterns

### Ask questions:
```python
send_agent_message(
    session_id="webscraper_collab",
    from_agent="researcher_agent",
    message_type="question",
    content="Do you need any specific requirements for the scraper architecture? Any particular websites we should target?",
    to_agent="implementation_agent"
)
```

### Share progress updates:
```python
send_agent_message(
    session_id="webscraper_collab",
    from_agent="researcher_agent",
    message_type="task_update",
    content="Architecture research is 50% complete. Found some great patterns in scrapy framework that we could adapt.",
    task_id=current_task_id
)
```

## Staying Coordinated

### Check for messages and context regularly:
```python
context = get_agent_context("webscraper_collab", "researcher_agent")
print("Recent messages:")
for msg in context['context']['recent_messages']:
    print(f"  {msg['from_agent']}: {msg['content']}")
```

### Search shared memory for relevant information:
```python
results = search_shared_memory("webscraper_collab", "implementation progress architecture")
for result in results['results']:
    print(f"Score {result['score']:.2f}: {result['content']}")
```

## Your Focus Areas
- Take on research and analysis tasks
- Document findings clearly
- Share insights that help the implementation agent
- Plan project structure and dependencies
- Create comprehensive documentation
```

```markdown
<!-- examples/implementation_agent_instructions.md -->
# Implementation Agent Instructions

You are the **Implementation Agent** in a collaborative web scraping project. Your role is to handle coding, testing, and technical implementation tasks.

## Your Capabilities
- Python programming
- Testing and debugging
- Code integration
- Technical implementation

## Getting Started

1. **Initialize your session:**
```python
result = init_agentic_session(
    session_id="webscraper_collab",
    agent_id="implementation_agent",
    agent_name="Implementation Agent",
    agent_role="implementer",
    capabilities=["coding", "testing", "debugging", "integration"]
)
print(result)
```

2. **Check what the research agent has discovered:**
```python
results = search_shared_memory("webscraper_collab", "research findings recommendations best practices")
for result in results['results']:
    print(f"Research insight: {result['content']}")
```

3. **Look for implementation tasks:**
```python
available = get_available_tasks("webscraper_collab", "implementation_agent")
print(f"Available tasks: {available['count']}")
for task in available['available_tasks']:
    if any(cap in task['description'].lower() for cap in ['implement', 'code', 'create', 'build']):
        print(f"✅ {task['title']}: {task['description']}")
```

## Implementation Workflow

### Before starting implementation:
```python
# Check if research dependencies are complete
context = get_agent_context("webscraper_collab", "implementation_agent")
print("Session status:")
print(f"  Completed tasks: {context['context']['session_stats']['completed_tasks']}")
print(f"  Total tasks: {context['context']['session_stats']['total_tasks']}")
```

### When implementing:
```python
# Take on an implementation task
task_id = "implementation_task_id"  # Replace with actual ID
assign_task_to_self("webscraper_collab", "implementation_agent", task_id)

# Start implementation
update_task_status(
    "webscraper_collab",
    "implementation_agent",
    task_id,
    "in_progress",
    "Starting implementation of base scraper class"
)
```

### Share code and progress:
```python
# Share implementation updates
send_agent_message(
    session_id="webscraper_collab",
    from_agent="implementation_agent",
    message_type="info",
    content="Base scraper class implemented with rate limiting and error handling. Ready for specific site implementations.",
    to_agent=None
)
```

### Ask for clarification:
```python
send_agent_message(
    session_id="webscraper_collab",
    from_agent="implementation_agent",
    message_type="question",
    content="The research mentions rotating user agents. Should I implement a predefined list or fetch them dynamically?",
    to_agent="researcher_agent"
)
```

## Code Sharing Pattern

### When you write significant code:
```python
# Create a memory entry with your code
from jean_memory import Memory

m = Memory()  # Use your configured memory instance

code_content = """
class BaseScraper:
    def __init__(self, rate_limit=1.0):
        self.session = requests.Session()
        self.rate_limit = rate_limit
        self.last_request_time = 0
    
    def fetch(self, url):
        # Rate limiting
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.rate_limit:
            time.sleep(self.rate_limit - time_since_last)
        
        # Implementation continues...
"""

m.add(
    memories=[f"Implemented BaseScraper class: {code_content}"],
    user_id="webscraper_collab",
    metadata={
        "type": "code_implementation",
        "language": "python",
        "component": "BaseScraper",
        "agent": "implementation_agent"
    }
)
```

## Testing and Validation

### When writing tests:
```python
# Update task status with test results
update_task_status(
    "webscraper_collab",
    "implementation_agent",
    test_task_id,
    "completed",
    "All unit tests passing. Coverage: 85%. Integration tests for 3 sample sites successful."
)
```

## Coordination with Research Agent

### Check for new research regularly:
```python
# Look for recent research updates
results = search_shared_memory("webscraper_collab", "research finding recommendation")
print("Latest research insights:")
for result in results['results'][:3]:
    print(f"  - {result['content']}")
```

### Report blockers:
```python
send_agent_message(
    session_id="webscraper_collab",
    from_agent="implementation_agent",
    message_type="coordination",
    content="Blocked on specific site implementations. Need research on target website structures and anti-scraping measures.",
    to_agent="researcher_agent"
)
```

Remember: Your strength is in implementation, but you should leverage the research agent's findings to build better, more informed solutions!
```

### Phase 4: Demonstration Script

```python
# examples/run_collaboration_demo.py
"""
Demonstration script showing agentic memory collaboration.

This script simulates the interaction between two Claude Code sessions
working on a collaborative project.
"""

import asyncio
from agentic_memory.manager import AgenticMemoryManager
from examples.collaborative_project import SAMPLE_PROJECT_TASKS

async def simulate_collaboration():
    """
    Simulate a collaborative session between two agents.
    """
    
    # Initialize shared memory
    memory_config = {
        "vector_store": {
            "provider": "faiss",
            "config": {
                "index_path": "~/.jean_memory/demo/faiss_index",
                "dimension": 1536
            }
        },
        "graph_store": {
            "provider": "neo4j",
            "config": {
                "uri": "bolt://localhost:7687",
                "auth": ["neo4j", "jeanmemory123"],
                "database": "agentic_demo"
            }
        }
    }
    
    manager = AgenticMemoryManager("demo_session", memory_config)
    
    # Register agents
    await manager.register_agent(
        "researcher",
        "Research Agent",
        ["research", "analysis", "documentation", "planning"],
        "researcher"
    )
    
    await manager.register_agent(
        "implementer",
        "Implementation Agent",
        ["coding", "testing", "debugging", "integration"],
        "implementer"
    )
    
    print("🤖 Agents registered successfully!")
    
    # Create tasks
    created_tasks = []
    for task_data in SAMPLE_PROJECT_TASKS:
        task = await manager.create_task(
            title=task_data["title"],
            description=task_data["description"],
            created_by="researcher",
            dependencies=task_data.get("dependencies", [])
        )
        created_tasks.append(task)
        print(f"✅ Created task: {task.title}")
    
    print(f"\n📋 Created {len(created_tasks)} tasks")
    
    # Simulate research agent taking research tasks
    research_tasks = [
        t for t in created_tasks 
        if any(word in t.title.lower() for word in ['research', 'choose', 'design'])
    ]
    
    print("\n🔬 Research Agent taking research tasks:")
    for task in research_tasks[:2]:  # Take first 2 research tasks
        await manager.assign_task(task.id, "researcher", "researcher")
        await manager.update_task_status(task.id, "in_progress", "researcher", "Starting research")
        print(f"  📝 {task.title}")
    
    # Simulate some research completion
    for task in research_tasks[:1]:
        await manager.update_task_status(
            task.id, 
            "completed", 
            "researcher",
            "Research completed. Key findings: Use requests + BeautifulSoup for simple sites, Scrapy for complex projects."
        )
        print(f"  ✅ Completed: {task.title}")
    
    # Simulate inter-agent communication
    from agentic_memory.manager import AgentMessage
    
    message = AgentMessage(
        from_agent="researcher",
        to_agent="implementer",
        message_type="info",
        content="Research complete on libraries. Recommend starting with requests + BeautifulSoup for prototype.",
    )
    await manager.send_message(message)
    print("\n💬 Research agent shared findings with implementation agent")
    
    # Check available tasks for implementer
    available_tasks = await manager.get_available_tasks("implementer")
    print(f"\n🛠️ Available tasks for Implementation Agent: {len(available_tasks)}")
    
    # Simulate implementer taking tasks
    impl_tasks = [
        t for t in available_tasks
        if any(word in t.title.lower() for word in ['implement', 'create', 'add'])
    ]
    
    if impl_tasks:
        task = impl_tasks[0]
        await manager.assign_task(task.id, "implementer", "implementer")
        await manager.update_task_status(
            task.id, 
            "in_progress", 
            "implementer",
            "Starting implementation based on research findings"
        )
        print(f"  🔧 Implementation Agent started: {task.title}")
    
    # Get final context for both agents
    print("\n📊 Final Session Status:")
    research_context = await manager.get_agent_context("researcher")
    impl_context = await manager.get_agent_context("implementer")
    
    print(f"  Research Agent: {len(research_context['assigned_tasks'])} tasks assigned")
    print(f"  Implementation Agent: {len(impl_context['assigned_tasks'])} tasks assigned")
    print(f"  Total completed: {research_context['session_stats']['completed_tasks']}")
    print(f"  Total tasks: {research_context['session_stats']['total_tasks']}")
    
    # Show memory contents
    search_results = await manager.memory.search_memories(
        query="research findings implementation",
        user_id="demo_session",
        limit=5,
        layer="short"
    )
    
    print("\n🧠 Shared Memory Contents:")
    for result in search_results:
        print(f"  - {result.content[:100]}...")
    
    print("\n🎉 Collaboration demo complete!")
    print("\nThis demonstrates:")
    print("  ✅ Shared memory between agents")
    print("  ✅ Task coordination and dependencies")
    print("  ✅ Inter-agent communication")
    print("  ✅ Progress tracking")
    print("  ✅ Knowledge sharing and reuse")

if __name__ == "__main__":
    asyncio.run(simulate_collaboration())
```

## Expected Outcomes

### Collaboration Patterns Demonstrated

1. **Shared Memory Coordination**
   - Both agents access the same memory layer
   - Knowledge persists across sessions
   - Context is maintained automatically

2. **Task Management**
   - Dynamic task assignment based on capabilities
   - Dependency tracking and resolution
   - Progress monitoring and status updates

3. **Inter-Agent Communication**
   - Structured messaging system
   - Broadcast and direct communication
   - Message persistence in shared memory

4. **Knowledge Sharing**
   - Research findings immediately available to implementer
   - Code implementations shared with documentation
   - Lessons learned captured for future reference

5. **Adaptive Coordination**
   - Agents can pick up where others left off
   - Context-aware task selection
   - Intelligent dependency resolution

### Performance Metrics

- **Memory Access**: <50ms for context retrieval
- **Task Operations**: <100ms for status updates
- **Inter-agent Messages**: <200ms end-to-end
- **Session Initialization**: <5s including Neo4j setup
- **Knowledge Search**: <100ms for relevant information

## References

- [Local Development Setup](./INITIATIVE_0_LOCAL_DEVELOPMENT_SETUP.md) - **Required prerequisite**
- [Short-term Memory System](./INITIATIVE_1_SHORT_TERM_MEMORY_SYSTEM.md) - For local memory infrastructure
- [MCP Integration Guide](./JEAN_MEMORY_MCP_INTEGRATION.md) - For Claude Code integration
- [Backend API Documentation](./JEAN_MEMORY_BACKEND_API.md) - For tool implementation
- [REST API Migration](./INITIATIVE_4_REST_API_MIGRATION.md) - For SDK compatibility