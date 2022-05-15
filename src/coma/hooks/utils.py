"""General hook utilities."""
import functools
import inspect
from typing import Callable, TypeVar

from boltons import funcutils


_T = TypeVar("_T")


def hook(fn: Callable[..., _T]) -> Callable[..., _T]:
    """Decorator for ``coma`` hooks.

    Enables hook definitions with only a subset of all protocol parameters.

    Example::

        @hook
        def parser_hook(parser):  # "parser" is a subset of the parser hook protocol
            ...

    Args:
        fn (typing.Callable): Any function that implements a subset of a hook protocol

    Returns:
         A wrapped version of the function that is protocol-friendly
    """

    @functools.wraps(fn)  # Want to copy everything EXCEPT the function signature.
    def wrapper(**kwargs) -> _T:
        return fn(*[kwargs[arg] for arg in inspect.getfullargspec(fn).args])

    return wrapper


def sequence(hook_: Callable, *hooks: Callable, return_all: bool = False) -> Callable:
    """Wraps a sequence of hooks into a single function.

    Equivalent to calling all given hooks one at a time in sequence while passing
    them all the same parameters. The hooks, therefore, need to have compatible
    call signatures. The best way to achieve this is to decorate each hook with
    the :obj:`@hook` decorator and ensuring all hooks subset the same hook protocol.

    Example:

        Replace::

            @coma.hooks.hook
            def wrapper(parser):
                coma.hooks.parser_hook.factory("-a", default=123)(parser=parser)
                coma.hooks.parser_hook.factory("-b", default=456)(parser=parser)

            coma.register(..., parser_hook=wrapper)

        with::

            wrapper = coma.hooks.sequence(
                coma.hooks.parser_hook.factory("-a", default=123),
                coma.hooks.parser_hook.factory("-b", default=456),
            )

            coma.register(..., parser_hook=wrapper)

    Args:
        hook_ (typing.Callable): The first hook in the sequence
        *hooks (typing.Callable): The remaining hooks in the sequence
        return_all (bool): Whether to return all values or the last

    Returns:
        If :obj:`return_all` is :obj:`False`, the wrapper returns the value of
        the last hook. If :obj:`return_all` is :obj:`True`, the wrapper returns
        the value of all hooks in a list.

    See also:
        * :func:`~coma.hooks.utils.hook`
    """

    @funcutils.wraps(hook_)  # Want to copy everything INCLUDING the function signature.
    def wrapper(*args, **kwargs):
        rets = [hook_(*args, **kwargs)] + [h(*args, **kwargs) for h in hooks]
        if return_all:  # Always returns a list even for 1 item.
            return rets
        return rets[-1]

    return wrapper
