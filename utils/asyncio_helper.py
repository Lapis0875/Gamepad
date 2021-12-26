import asyncio
from functools import wraps
from typing import Coroutine, Optional

from typings import CoroutineFunction, AnyFunction


__all__ = (
    'async_callback_handler',
    'async_schedule_task'
)


async def _scheduled_task(delay: int, coro: Coroutine):
    await asyncio.sleep(delay)
    await coro


async def async_callback_handler(coro: CoroutineFunction, callback: CoroutineFunction):
    result = await coro()
    await callback(result)


def async_schedule_task(delay: int, coro: CoroutineFunction, callback: Optional[AnyFunction]) -> asyncio.Task:
    if asyncio.iscoroutinefunction(callback):
        # Callback function is coroutine. Wrap into a single coroutine.
        coro = async_callback_handler(coro, callback)
        return asyncio.get_event_loop().create_task(_scheduled_task(delay, coro))
    else:
        # Callback function is function. Register as callback function in Task.
        task = asyncio.get_event_loop().create_task(_scheduled_task(delay, coro()))
        if callback is not None and callable(callback):
            task.add_done_callback(callback)
        return task

