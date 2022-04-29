"""Core run hooks and utilities."""
from typing import Callable

from .utils import hook


def factory(run_fn_name: str = "run") -> Callable:
    """Factory for running a command.

    Example::

        class Command:
            ...
            def start(self):
                ...
        with coma.forget(run_hook=True):
            coma.register("cmd", Command, run_hook=factory("start"))

    Args:
        run_fn_name: The command attribute to call as the run function

    Returns:
        A run hook

    See also:
        * TODO(invoke; protocol) for details on run hooks
    """

    @hook
    def _hook(command):
        return getattr(command, run_fn_name)()

    return _hook


default = factory()
"""Default init hook function.

An alias for :func:`coma.hooks.run_hook.factory` called with default arguments.
"""
