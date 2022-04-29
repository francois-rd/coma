"""Core init hooks and utilities."""
from typing import Any, Callable

from coma.config import ConfigDict

from .utils import hook


@hook
def positional_only(command: Callable, configs: ConfigDict) -> Any:
    """Initializes :obj:`command` with :obj:`configs`.

    Initializes :obj:`command` with the values (but not the keys) of
    :obj:`configs` given as positional arguments.

    .. note::

        The underlying `dict` is assumed to be ordered such that the values are
        in insertion order.

    See also:
        * TODO(invoke; protocol) for details on init hooks
    """
    return command(*configs.values())


default = positional_only
"""Default init hook.

An alias for :func:`coma.hooks.init_hook.positional_only`.
"""
