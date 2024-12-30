import logging
import functools
import typing as t
import asyncio
from dataclasses import dataclass
from typing import Optional, List, Union, Callable, Coroutine, Any

from utils.run_config import RunConfig

logger = logging.getLogger(__name__)

SubmittableType: t.TypeAlias = Union[Callable[..., Any], Coroutine[Any, Any, Any]]


@dataclass
class TaskResult:
    success: bool
    result: Any
    error: Optional[Exception] = None


class Executor:
    def __init__(self, run_config: Optional[RunConfig] = None):
        self.run_config = run_config or RunConfig()
        self.jobs: asyncio.Queue = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(self.run_config.max_workers)
        self.tasks: t.List[asyncio.Task] = []
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        self.dispatcher_task: t.Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

    async def dispatcher(self) -> None:
        """Continuously process tasks from the queue."""
        while True:
            func, args, kwargs = await self.jobs.get()
            logger.info(f"Starting task: {func.__name__}")
            await self.semaphore.acquire()
            task = asyncio.create_task(self.handle_task(func, args, kwargs))
            self.tasks.append(task)
            self.jobs.task_done()
            logger.debug(f"Task {func.__name__} added to processing queue")

    async def handle_task(
        self,
        func: SubmittableType,
        args: tuple,
        kwargs: dict,
    ) -> TaskResult:
        """Execute a single task and return its result."""
        try:
            logger.debug(f"Executing task: {func.__name__}")
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                partial_func = functools.partial(func, *args, **kwargs)
                result = await self.loop.run_in_executor(None, partial_func)
            logger.info(f"Task: {func.__name__} completed successfully")
            return TaskResult(success=True, result=result)
        except Exception as e:
            logger.error(f"Task: {func.__name__} failed: {str(e)}", exc_info=True)
            return TaskResult(success=False, result=None, error=e)
        finally:
            self.semaphore.release()
            logger.debug(f"Task: {func.__name__} resources released")

    async def submit(
        self,
        func: SubmittableType,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Submit a task for execution."""
        if self._shutdown_event.is_set():
            raise RuntimeError("Cannot submit tasks while shutting down")
        logger.debug(f"Submitting task: {func.__name__}")
        await self.jobs.put((func, args, kwargs))
        logger.debug(f"Task: {func.__name__} added to job queue")

    async def results(self) -> List[TaskResult]:
        """
        Wait for all tasks to complete and return their results.
        Please be aware that this method will block until all tasks are completed. So you'd better call it after you shut down the executor.
        """
        self._shutdown_event.set()
        logger.info("All tasks completed, collecting results")
        await self.jobs.join()

        if self.dispatcher_task is not None:
            self.dispatcher_task.cancel()
            try:
                await self.dispatcher_task
            except asyncio.CancelledError:
                logger.info("Dispatcher task cancelled successfully")
            self.dispatcher_task = None

        results: List[TaskResult] = []
        for task in self.tasks:
            try:
                task_result = await asyncio.wait_for(
                    task, timeout=self.run_config.timeout
                )
                results.append(task_result)
            except asyncio.TimeoutError:
                logger.error(f"Task {task.get_name()} timed out")
                results.append(
                    TaskResult(success=False, result=None, error=asyncio.TimeoutError())
                )
            except Exception as e:
                logger.error(f"Error collecting task result: {e}")
                results.append(TaskResult(success=False, result=None, error=e))

        logger.info(f"Collected results from {len(results)} tasks")
        return results

    async def cancel_task(self, task_id: int) -> bool:
        """Cancel a specific task by its index."""
        if 0 <= task_id < len(self.tasks):
            task = self.tasks[task_id]
            task.cancel()
            try:
                await task
                logger.info(f"Task {task_id} cancelled successfully")
                return True
            except asyncio.CancelledError:
                logger.info(f"Task {task_id} was already cancelled")
                return True
            except Exception as e:
                logger.error(f"Error cancelling task {task_id}: {e}")
                return False
        logger.warning(f"Invalid task ID: {task_id}")
        return False

    async def stream_results(self) -> t.AsyncIterator[TaskResult]:
        """
        Stream results as they become available.
        Please note that this method DOES NOT TEST! DON'T FORGET TO TEST IT BEFORE USING IT IN PRODUCTION!
        """
        while self.tasks:
            done, _ = await asyncio.wait(
                self.tasks,
                timeout=self.run_config.timeout,
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in done:
                try:
                    result = await task
                    yield result
                except asyncio.TimeoutError:
                    yield TaskResult(
                        success=False, result=None, error=asyncio.TimeoutError()
                    )
                except Exception as e:
                    yield TaskResult(success=False, result=None, error=e)
                finally:
                    self.tasks.remove(task)

    async def start(self) -> None:
        """Start the task dispatcher."""
        if self.dispatcher_task is None:
            # Reset the shutdown flag
            self._shutdown_event.clear()
            self.tasks.clear()
            self.dispatcher_task = asyncio.create_task(self.dispatcher())
            logger.info("Dispatcher task started")

    async def shutdown(self) -> None:
        """Shutdown the executor gracefully."""
        if self.dispatcher_task is not None:
            self.dispatcher_task.cancel()
            try:
                await self.dispatcher_task
            except asyncio.CancelledError:
                logger.info("Dispatcher task cancelled successfully")
            self.dispatcher_task = None
        logger.info("Executor shutdown complete")
