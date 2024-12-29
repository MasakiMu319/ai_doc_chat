import logging
import functools
import typing as t
import asyncio

from utils.run_config import RunConfig

logger = logging.getLogger(__name__)

SubmittableType: t.TypeAlias = t.Union[
    t.Callable[..., t.Any], t.Coroutine[t.Any, t.Any, t.Any]
]


class Executor:
    def __init__(self, run_config: t.Optional[RunConfig] = None):
        self.run_config = run_config or RunConfig()
        self.jobs: asyncio.Queue = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(self.run_config.max_workers)
        self.tasks: t.List[asyncio.Task] = []
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        self.dispatcher_task: t.Optional[asyncio.Task] = None

    async def dispatcher(self):
        while True:
            func, args, kwargs = await self.jobs.get()
            await self.semaphore.acquire()
            task = asyncio.create_task(self.handle_task(func, args, kwargs))
            self.tasks.append(task)
            self.jobs.task_done()

    async def handle_task(
        self,
        func: SubmittableType,
        args,
        kwargs,
    ):
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                partial_func = functools.partial(func, *args, **kwargs)
                result = await self.loop.run_in_executor(None, partial_func)
            return result
        except Exception as e:
            logger.error(f"Error in task: {e}")
            raise e
        finally:
            self.semaphore.release()

    async def submit(
        self,
        func: SubmittableType,
        *args,
        **kwargs,
    ) -> None:
        logger.debug(f"Submitting task: {func.__name__}")
        await self.jobs.put((func, args, kwargs))

    async def results(self) -> t.List[t.Any]:
        await self.jobs.join()

        if self.dispatcher_task is not None:
            self.dispatcher_task.cancel()
            try:
                await self.dispatcher_task
            except asyncio.CancelledError:
                logger.error("Dispatcher task was cancelled")
                pass
            self.dispatcher_task = None

        results = []
        for task in self.tasks:
            try:
                result = await asyncio.wait_for(task, timeout=self.run_config.timeout)
                results.append(result)
            except asyncio.TimeoutError:
                logger.error("Task timed out")
                results.append(asyncio.TimeoutError("Task timed out"))
            except Exception as e:
                logger.error(f"Error in task: {e}")
                results.append(e)
        return results

    async def start(self):
        if self.dispatcher_task is None:
            self.dispatcher_task = asyncio.create_task(self.dispatcher())
            logger.debug("Dispatcher task started")

    async def shutdown(self):
        if self.dispatcher_task is not None:
            self.dispatcher_task.cancel()
            try:
                await self.dispatcher_task
            except asyncio.CancelledError:
                logger.error("Dispatcher task was cancelled")
                pass
            self.dispatcher_task = None
