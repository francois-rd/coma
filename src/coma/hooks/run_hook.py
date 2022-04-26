"""Core run hooks."""
from typing import Callable

from .utils import hook


def factory(run_fn_name: str = "run") -> Callable:
    """Factory for running a command.

    Args:
        run_fn_name: The command attribute to call as the run function

    Returns:
        A valid run hook function (assuming args are valid).

    See also:
        TODO(invoke; protocol) for details on run hooks
    """

    @hook
    def _hook(command):
        return getattr(command, run_fn_name)()

    return _hook


default = factory()
"""Default init hook function.

See also:
    TODO(invoke; protocol) for details on run hooks
"""
