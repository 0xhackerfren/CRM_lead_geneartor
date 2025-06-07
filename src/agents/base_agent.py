"""
Base Agent Framework for CRM Lead Generation.

This module defines the core agent interfaces, data structures, and registry
following the AI Agent Framework rules and system architecture.
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

class AgentFramework(Enum):
    """Available AI agent frameworks."""
    SMOL_AGENTS = "smol_agents"
    LANGCHAIN = "langchain"
    MANUAL = "manual"  # Fallback to rule-based processing

class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Task:
    """
    Task definition for agent processing.
    
    Represents a single unit of work that can be executed by an agent.
    """
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = ""
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Result:
    """
    Result of agent task execution.
    
    Contains the output and metadata from task processing.
    """
    task_id: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

class BaseAgent(ABC):
    """
    Abstract base class for all CRM agents.
    
    Defines the core interface that all agents must implement,
    following the system architecture rules.
    """
    
    def __init__(
        self, 
        name: str, 
        description: str = "",
        framework: AgentFramework = AgentFramework.SMOL_AGENTS
    ):
        self.name = name
        self.description = description
        self.framework = framework
        self.agent_id = str(uuid.uuid4())
        
        # Performance tracking
        self.stats = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'total_execution_time': 0.0,
            'average_execution_time': 0.0,
            'last_activity': None
        }
        
        # State management
        self.is_initialized = False
        self.is_running = False
        self.current_task: Optional[Task] = None
        
        # Setup logging
        self.logger = logging.getLogger(f"agent.{name}")
        
        self.logger.info(f"Agent {name} created with framework {framework.value}")
    
    @abstractmethod
    async def process(self, task: Task) -> Result:
        """
        Process a task and return the result.
        
        This is the main entry point for task execution.
        Each agent must implement this method.
        
        Args:
            task: Task to process
            
        Returns:
            Result of task execution
        """
        pass
    
    def initialize(self) -> bool:
        """
        Initialize the agent.
        
        Perform any setup required before the agent can process tasks.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            self.logger.info(f"Initializing agent {self.name}")
            
            # Perform agent-specific initialization
            self._setup_agent()
            
            self.is_initialized = True
            self.logger.info(f"Agent {self.name} initialized successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agent {self.name}: {e}")
            return False
    
    def _setup_agent(self):
        """
        Agent-specific setup logic.
        
        Override this method in subclasses to perform custom initialization.
        """
        pass
    
    async def execute_task(self, task: Task) -> Result:
        """
        Execute a task with error handling and performance tracking.
        
        This method wraps the process() method with common functionality
        like timing, error handling, and statistics tracking.
        
        Args:
            task: Task to execute
            
        Returns:
            Result of task execution
        """
        if not self.is_initialized:
            return Result(
                task_id=task.task_id,
                success=False,
                error="Agent not initialized"
            )
        
        start_time = datetime.now()
        execution_start = asyncio.get_event_loop().time()
        
        try:
            # Update task status
            task.status = TaskStatus.RUNNING
            task.started_at = start_time
            self.current_task = task
            self.is_running = True
            
            self.logger.info(f"Starting task {task.task_id}: {task.description}")
            
            # Process the task
            result = await self.process(task)
            
            # Calculate execution time
            execution_time = asyncio.get_event_loop().time() - execution_start
            result.execution_time = execution_time
            
            # Update task status
            task.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
            task.completed_at = datetime.now()
            
            # Update statistics
            self.stats['total_tasks'] += 1
            self.stats['total_execution_time'] += execution_time
            self.stats['last_activity'] = datetime.now()
            
            if result.success:
                self.stats['successful_tasks'] += 1
                self.logger.info(f"Task {task.task_id} completed successfully in {execution_time:.2f}s")
            else:
                self.stats['failed_tasks'] += 1
                self.logger.warning(f"Task {task.task_id} failed: {result.error}")
            
            # Update average execution time
            self.stats['average_execution_time'] = (
                self.stats['total_execution_time'] / self.stats['total_tasks']
            )
            
            return result
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - execution_start
            
            # Update task status
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            
            # Update statistics
            self.stats['total_tasks'] += 1
            self.stats['failed_tasks'] += 1
            self.stats['total_execution_time'] += execution_time
            self.stats['average_execution_time'] = (
                self.stats['total_execution_time'] / self.stats['total_tasks']
            )
            self.stats['last_activity'] = datetime.now()
            
            error_msg = f"Task execution failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            return Result(
                task_id=task.task_id,
                success=False,
                error=error_msg,
                execution_time=execution_time
            )
            
        finally:
            self.current_task = None
            self.is_running = False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status and performance metrics.
        
        Returns:
            Dictionary with status information
        """
        success_rate = (
            (self.stats['successful_tasks'] / self.stats['total_tasks'] * 100)
            if self.stats['total_tasks'] > 0 else 0
        )
        
        return {
            'agent_id': self.agent_id,
            'agent_name': self.name,
            'description': self.description,
            'framework': self.framework.value,
            'is_initialized': self.is_initialized,
            'is_running': self.is_running,
            'current_task': self.current_task.task_id if self.current_task else None,
            'performance_stats': {
                'total_tasks': self.stats['total_tasks'],
                'successful_tasks': self.stats['successful_tasks'],
                'failed_tasks': self.stats['failed_tasks'],
                'success_rate_percent': round(success_rate, 2),
                'average_execution_time': round(self.stats['average_execution_time'], 2),
                'last_activity': self.stats['last_activity']
            }
        }
    
    def reset_stats(self):
        """Reset performance statistics."""
        self.stats = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'total_execution_time': 0.0,
            'average_execution_time': 0.0,
            'last_activity': None
        }
        self.logger.info(f"Statistics reset for agent {self.name}")

class AgentRegistry:
    """
    Registry for managing multiple agents.
    
    Provides centralized management and coordination of agents.
    """
    
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self.logger = logging.getLogger("agent_registry")
    
    def register(self, agent: BaseAgent) -> bool:
        """
        Register an agent in the registry.
        
        Args:
            agent: Agent to register
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            if agent.name in self._agents:
                self.logger.warning(f"Agent {agent.name} already registered, replacing")
            
            self._agents[agent.name] = agent
            self.logger.info(f"Agent {agent.name} registered successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register agent {agent.name}: {e}")
            return False
    
    def unregister(self, agent_name: str) -> bool:
        """
        Unregister an agent from the registry.
        
        Args:
            agent_name: Name of agent to unregister
            
        Returns:
            True if unregistration successful, False otherwise
        """
        try:
            if agent_name in self._agents:
                del self._agents[agent_name]
                self.logger.info(f"Agent {agent_name} unregistered")
                return True
            else:
                self.logger.warning(f"Agent {agent_name} not found for unregistration")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to unregister agent {agent_name}: {e}")
            return False
    
    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """
        Get an agent by name.
        
        Args:
            agent_name: Name of agent to retrieve
            
        Returns:
            Agent instance or None if not found
        """
        return self._agents.get(agent_name)
    
    def list_agents(self) -> List[str]:
        """
        List all registered agent names.
        
        Returns:
            List of agent names
        """
        return list(self._agents.keys())
    
    def get_agent_status(self, agent_name: str = None) -> Dict[str, Any]:
        """
        Get status of one or all agents.
        
        Args:
            agent_name: Specific agent name, or None for all agents
            
        Returns:
            Status information
        """
        if agent_name:
            agent = self._agents.get(agent_name)
            if agent:
                return agent.get_status()
            else:
                return {'error': f'Agent {agent_name} not found'}
        else:
            return {
                'total_agents': len(self._agents),
                'agents': {name: agent.get_status() for name, agent in self._agents.items()}
            }
    
    async def execute_task(self, agent_name: str, task: Task) -> Result:
        """
        Execute a task on a specific agent.
        
        Args:
            agent_name: Name of agent to execute task
            task: Task to execute
            
        Returns:
            Result of task execution
        """
        agent = self._agents.get(agent_name)
        
        if not agent:
            return Result(
                task_id=task.task_id,
                success=False,
                error=f"Agent {agent_name} not found"
            )
        
        return await agent.execute_task(task)

# Global agent registry instance
_global_registry: Optional[AgentRegistry] = None

def get_agent_registry() -> AgentRegistry:
    """
    Get the global agent registry instance.
    
    Returns:
        Global agent registry
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = AgentRegistry()
    return _global_registry

def reset_agent_registry():
    """Reset the global agent registry."""
    global _global_registry
    _global_registry = AgentRegistry()

class TaskQueue:
    """
    Task queue for managing agent workloads.
    
    Provides priority-based task scheduling and execution.
    """
    
    def __init__(self, max_concurrent_tasks: int = 5):
        self.max_concurrent_tasks = max_concurrent_tasks
        self._pending_tasks: List[Task] = []
        self._running_tasks: Dict[str, Task] = {}
        self._completed_tasks: Dict[str, Result] = {}
        self.logger = logging.getLogger("task_queue")
    
    def add_task(self, task: Task) -> bool:
        """
        Add a task to the queue.
        
        Args:
            task: Task to add
            
        Returns:
            True if task added successfully
        """
        try:
            # Insert task in priority order
            inserted = False
            for i, existing_task in enumerate(self._pending_tasks):
                if task.priority.value > existing_task.priority.value:
                    self._pending_tasks.insert(i, task)
                    inserted = True
                    break
            
            if not inserted:
                self._pending_tasks.append(task)
            
            self.logger.info(f"Task {task.task_id} added to queue (priority: {task.priority.name})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add task {task.task_id}: {e}")
            return False
    
    def get_next_task(self) -> Optional[Task]:
        """
        Get the next highest priority task.
        
        Returns:
            Next task to execute or None if queue empty
        """
        if len(self._running_tasks) >= self.max_concurrent_tasks:
            return None
        
        if self._pending_tasks:
            task = self._pending_tasks.pop(0)
            self._running_tasks[task.task_id] = task
            return task
        
        return None
    
    def complete_task(self, task_id: str, result: Result):
        """
        Mark a task as completed.
        
        Args:
            task_id: ID of completed task
            result: Task execution result
        """
        if task_id in self._running_tasks:
            del self._running_tasks[task_id]
            self._completed_tasks[task_id] = result
            self.logger.info(f"Task {task_id} completed")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get current queue status.
        
        Returns:
            Queue status information
        """
        return {
            'pending_tasks': len(self._pending_tasks),
            'running_tasks': len(self._running_tasks),
            'completed_tasks': len(self._completed_tasks),
            'max_concurrent_tasks': self.max_concurrent_tasks,
            'next_task_priority': (
                self._pending_tasks[0].priority.name 
                if self._pending_tasks else None
            )
        } 