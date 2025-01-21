"""Run hook utilities, factories, and defaults."""

from typing import Callable

from .utils import hook


def factory(attr_name: str = "run") -> Callable:
    """Factory for creating a run hook that executes a command.

    Example::

        class Command:
            def start(self):
                ...

        with coma.forget(run_hook=True):
            coma.register("cmd", Command, run_hook=factory("start"))

    Args:
        attr_name (str): The name of the command attribute to call to execute it

    Returns:
        A run hook
    """

    @hook
    def _hook(command):
        return getattr(command, attr_name)()

    return _hook


default = factory()
"""Default init hook function.

An alias for calling :func:`coma.hooks.run_hook.factory` with default arguments.
"""
