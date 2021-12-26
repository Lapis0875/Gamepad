from typing import Callable, Coroutine, Any, Union

__all__ = (
    'CoroutineFunction',
    'Function',
    'AnyFunction'
)

CoroutineFunction = Callable[..., Coroutine]
Function = Callable[..., Any]
AnyFunction = Union[CoroutineFunction, Function]
