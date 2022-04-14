"""
Asyncio Helpers
---------------
@author Lapis0875
"""
import asyncio
from typing import Coroutine, Optional

from typings import CoroutineFunction, AnyFunction


__all__ = (
    'async_callback_handler',
    'async_schedule_task'
)


async def _scheduled_task(delay: int, coro: Coroutine):
    """
    Delayed async task builder.
    :param delay: Delay as seconds.
    :param coro: Coroutine function to schedule.
    :return: Delayed coro.
    """
    await asyncio.sleep(delay)
    await coro


async def async_callback_handler(coro: CoroutineFunction, callback: CoroutineFunction):
    """
    Wraps coroutine function with callback function.
    Since asyncio.Task.add_done_callback() does not accepts async callback,
    this wraps coroutine function and async callback as a single coroutine function.
    :param coro: Coroutine function to schedule.
    :param callback: Async callback to add in coro.
    :return: Wrapped coroutine function.
    """
    result = await coro()
    await callback(result)


def async_schedule_task(delay: int, coro: CoroutineFunction, *, callback: Optional[AnyFunction] = None) -> asyncio.Task:
    """
    Schedule coroutine function in current running event loop.
    When callback function does not exist (None), or callback function is a sync function, this is equivalent with below:
        ```python
        task = asyncio.get_event_loop().create_task(delay, coro)
        # if callback
        task.add_done_callback(callback)
        ```
    This is specially designed to handle coroutine function as callback function, but it can handle normal function as a callback too.
    That's because I want to schedule task in a consistent way.
    :param delay: Delay of this schedule.
    :param coro: Coroutine function to schedule.
    :param callback: Callback function of given coroutine function. Can be either function or coroutine function. Can be None if not exist.
    :return: asyncio.Task object.
    """
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

