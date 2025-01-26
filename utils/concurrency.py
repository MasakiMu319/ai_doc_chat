import asyncio
from typing import TypeVar, Iterable, Iterator, AsyncIterator

T = TypeVar("T")


class _StopIteration(Exception):
    """
    We can't raise StopIteration from within a threadpool iterator catch it outside that context, so we coerce them into a different exception type.
    """

    pass


def _next(iterator: Iterator[T]) -> T:
    try:
        return next(iterator)
    except StopIteration:
        raise _StopIteration


async def iterate_in_threadpool(iterator: Iterable[T]) -> AsyncIterator[T]:
    as_iterator = iter(iterator)
    while True:
        try:
            yield await asyncio.to_thread(_next, as_iterator)
        except _StopIteration:
            break
