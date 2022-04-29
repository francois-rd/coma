"""General hook utilities."""
import inspect
from typing import Callable, TypeVar

from boltons.funcutils import wraps


_T = TypeVar("_T")


def hook(fn: Callable[..., _T]) -> Callable[..., _T]:
    """Decorator for ``coma`` hooks.

    Enables hook definitions with only a subset of all protocol arguments. See
    TODO(invoke; protocol) for details on hook protocols.

    Example::

        @hook
        def parser_hook(parser):  # "parser" is a subset of the parser hook protocol
            ...

    Args:
        fn: Any callable that implements a subset of a hook protocol

    Returns:
         A new, protocol-friendly, wrapped version of the function
    """

    def wrapper(**kwargs) -> _T:
        return fn(*[kwargs[arg] for arg in inspect.getfullargspec(fn).args])

    return wrapper


def sequence(hook_: Callable, *hooks: Callable, return_all: bool = False) -> Callable:
    """Wraps a sequence of hooks into a single callable.

    Equivalent to calling all given hooks one at a time in a loop with the
    same arguments. The hooks, therefore, need to have compatible call
    signatures. The best way to achieve this is to decorate each hook with the
    :func:`~coma.hooks.utils.hook` decorator and ensuring all hooks subset the
    same protocol. See TODO(invoke; protocol) for details on hook protocols.

    Example::

        coma.initiate(parser_hook=sequence(parser_hook1, parser_hook2))

    Args:
        hook_: The first hook in the sequence
        *hooks: The remaining hooks in the sequence
        return_all: Whether to return all values or the last. See ``Returns``.

    Returns:
        If `return_all` is `False`, returns the value of the last hook.
        If `return_all` is `True`, returns the value of all hooks as a list.

    See also:
        * :func:`~coma.hooks.utils.hook`
    """

    @wraps(hook_)
    def wrapper(*args, **kwargs):
        rets = [hook_(*args, **kwargs)] + [h(*args, **kwargs) for h in hooks]
        if return_all:  # Always returns a list even for 1 item.
            return rets
        return rets[-1]

    return wrapper
