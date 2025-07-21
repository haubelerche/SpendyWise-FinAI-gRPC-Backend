"""
Background Task Management - gRPC Native Implementation
Replaced Celery/Redis with simpler asyncio-based task processing
Optimized for mobile backend simplicity
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Callable, Any 
from dataclasses import dataclass # crt dataclass for task representation
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Simple task representation"""
    id: str
    name: str
    func: Callable
    args: tuple
    kwargs: dict 
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


class SimpleTaskManager:
    """
    Simplified task manager for mobile backend
    Replaces Celery complexity with asyncio-based processing
    """
    
    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.tasks: Dict[str, Task] = {}
        self.queue: asyncio.Queue = asyncio.Queue()
        self.workers: List[asyncio.Task] = []
        self.running = False
        
    async def start(self):
        """Start the task processing workers"""
        if self.running:
            return
            
        self.running = True
        logger.info(f"Starting {self.max_workers} task workers")
        
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
    
    async def stop(self):
        """Stop all workers gracefully"""
        if not self.running:
            return
            
        self.running = False
        logger.info("Stopping task workers...")
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        
    async def _worker(self, name: str):
        """Worker coroutine to process tasks"""
        logger.info(f"Worker {name} started")
        
        try:
            while self.running:
                try:
                    # Get task from queue with timeout
                    task = await asyncio.wait_for(
                        self.queue.get(), 
                        timeout=1.0
                    )
                    
                    await self._execute_task(task)
                    self.queue.task_done()
                    
                except asyncio.TimeoutError:
                    continue  # No task available, continue loop
                except Exception as e:
                    logger.error(f"Worker {name} error: {e}")
                    
        except asyncio.CancelledError:
            logger.info(f"Worker {name} cancelled")
        finally:
            logger.info(f"Worker {name} stopped")
    
    async def _execute_task(self, task: Task):
        """Execute a single task"""
        try:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now(timezone.utc)
            
            logger.info(f"Executing task {task.id}: {task.name}")
            
            # Execute the task function
            if asyncio.iscoroutinefunction(task.func):
                result = await task.func(*task.args, **task.kwargs)
            else:
                result = task.func(*task.args, **task.kwargs)
            
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now(timezone.utc)
            
            logger.info(f"Task {task.id} completed successfully")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now(timezone.utc)
            
            logger.error(f"Task {task.id} failed: {e}")
    
    async def submit_task(
        self, 
        name: str, 
        func: Callable, 
        *args, 
        **kwargs
    ) -> str:
        """Submit a task for execution"""
        task_id = f"{name}_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        
        task = Task(
            id=task_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs
        )
        
        self.tasks[task_id] = task
        await self.queue.put(task)
        
        logger.info(f"Submitted task {task_id}: {name}")
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[Task]:
        """Get task status and result"""
        return self.tasks.get(task_id)
    
    async def wait_for_task(self, task_id: str, timeout: float = 30.0) -> Task:
        """Wait for a task to complete"""
        start_time = datetime.now(timezone.utc)
        
        while True:
            task = self.tasks.get(task_id)
            if not task:
                raise ValueError(f"Task {task_id} not found")
            
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                return task
            
            # Check timeout
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > timeout:
                raise TimeoutError(f"Task {task_id} timeout after {timeout}s")
            
            await asyncio.sleep(0.1)
    
    def cleanup_old_tasks(self, older_than_hours: int = 24):
        """Clean up old completed/failed tasks"""
        cutoff = datetime.now() - timedelta(hours=older_than_hours)
        
        to_remove = []
        for task_id, task in self.tasks.items():
            if (task.completed_at and task.completed_at < cutoff) or \
               (task.created_at < cutoff and task.status == TaskStatus.FAILED):
                to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.tasks[task_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old tasks")


# Global task manager instance
task_manager = SimpleTaskManager()


# Task decorators for common background operations
def background_task(name: str = None):
    """Decorator to mark functions as background tasks"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            task_name = name or func.__name__
            return await task_manager.submit_task(task_name, func, *args, **kwargs)
        
        wrapper._is_background_task = True
        wrapper._original_func = func
        return wrapper
    
    return decorator


# Common background tasks for mobile backend
@background_task("send_push_notification")
async def send_push_notification_task(device_tokens: List[str], message: dict):
    """Send push notifications in background"""
    from app.utils.push_notifications import PushNotificationManager
    
    push_manager = PushNotificationManager()
    notifications = [
        {
            "device_token": token,
            "title": message.get("title", ""),
            "body": message.get("body", ""),
            "data": message.get("data", {})
        }
        for token in device_tokens
    ]
    
    return await push_manager.send_batch_notifications(notifications)


@background_task("process_financial_insights")
async def process_financial_insights_task(user_id: int):
    """Process financial insights for user"""
    from app.services.insights_service import InsightsService
    
    insights_service = InsightsService()
    return await insights_service.generate_insights(user_id)


@background_task("sync_transaction_categories")
async def sync_transaction_categories_task(user_id: int, transactions: List[dict]):
    """Auto-categorize transactions using AI"""
    from app.services.ai_advisor_service import AIAdvisorService
    
    ai_service = AIAdvisorService()
    return await ai_service.categorize_transactions(user_id, transactions)


@background_task("cleanup_expired_sessions")
async def cleanup_expired_sessions_task():
    """Clean up expired user sessions"""
    # Implementation would clean up expired sessions
    logger.info("Cleaned up expired sessions")
    return {"cleaned": 0}


# Scheduler for periodic tasks (replaces Celery beat)
class SimpleScheduler:
    """Simple scheduler for periodic tasks"""
    
    def __init__(self, task_manager: SimpleTaskManager):
        self.task_manager = task_manager
        self.scheduled_tasks: Dict[str, dict] = {}
        self.running = False
        
    async def start(self):
        """Start the scheduler"""
        if self.running:
            return
            
        self.running = True
        asyncio.create_task(self._scheduler_loop())
        logger.info("Task scheduler started")
    
    async def stop(self):
        """Stop the scheduler"""
        self.running = False
        logger.info("Task scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                current_time = datetime.now()
                
                for task_id, task_info in self.scheduled_tasks.items():
                    if current_time >= task_info["next_run"]:
                        # Execute the task
                        await self.task_manager.submit_task(
                            task_info["name"],
                            task_info["func"],
                            *task_info["args"],
                            **task_info["kwargs"]
                        )
                        
                        # Update next run time
                        task_info["next_run"] = current_time + task_info["interval"]
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)
    
    def schedule_periodic(
        self, 
        name: str, 
        func: Callable, 
        interval_minutes: int,
        *args, 
        **kwargs
    ):
        """Schedule a periodic task"""
        task_id = f"periodic_{name}"
        
        self.scheduled_tasks[task_id] = {
            "name": name,
            "func": func,
            "args": args,
            "kwargs": kwargs,
            "interval": timedelta(minutes=interval_minutes),
            "next_run": datetime.now() + timedelta(minutes=interval_minutes)
        }
        
        logger.info(f"Scheduled periodic task: {name} (every {interval_minutes} minutes)")


# Global scheduler instance
scheduler = SimpleScheduler(task_manager)


# Initialize common periodic tasks
def setup_periodic_tasks():
    """Set up common periodic tasks"""
    # Clean up old tasks every hour
    scheduler.schedule_periodic(
        "cleanup_old_tasks",
        task_manager.cleanup_old_tasks,
        60  # Every hour
    )
    
    # Clean up expired sessions every 6 hours
    scheduler.schedule_periodic(
        "cleanup_expired_sessions",
        cleanup_expired_sessions_task._original_func,
        360  # Every 6 hours
    )
    
    logger.info("Periodic tasks configured")
