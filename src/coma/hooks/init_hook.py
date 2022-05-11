"""Core init hooks and utilities."""
import inspect
from typing import Any, Callable

from coma.config import ConfigDict

from .utils import hook


def positional_factory(*skips: str) -> Callable:
    """Factory for initializing a :obj:`command` with some :obj:`configs`.

    Initializes a :obj:`command` with the values (i.e., configurations) but not
    the keys (i.e., configuration identifiers) of some :obj:`configs` given as
    positional arguments.

    Args:
        *skips: Undesired :obj:`configs` can be skipped by providing the
            appropriate config ids

    .. note::

        The underlying :obj:`configs` is assumed to be ordered such that the
        values are in insertion order.

    Returns:
        An init hook

    See also:
        * TODO(invoke; protocol) for details on init hooks
    """

    @hook
    def _hook(command: Callable, configs: ConfigDict) -> Any:
        return command(*[c for cid, c in configs.items() if cid not in skips])

    return _hook


def keyword_factory(*skips: str, force: bool = False) -> Callable:
    """Factory for initializing a :obj:`command` with some :obj:`configs`.

    Initializes a :obj:`command` with the values (i.e., configurations) but not
    the keys (i.e., configuration identifiers) of some :obj:`configs` given as
    keyword arguments based on matching :obj:`command` argument names.

    Args:
        *skips: Undesired :obj:`configs` can be skipped by providing the
            appropriate config ids
        force: For all un-skipped :obj:`configs`, whether to forcibly pass them
            to the :obj:`command`, even if no :obj:`command` argument matches a
            config id. In this case, Python will likely raise a `TypeError`
            unless the :obj:`command` is defined with variadic keyword arguments.

    Returns:
        An init hook

    See also:
        * TODO(invoke; protocol) for details on init hooks
    """

    @hook
    def _hook(command: Callable, configs: ConfigDict) -> Any:
        configs = {cid: c for cid, c in configs.items() if cid not in skips}
        if not force:
            args = inspect.getfullargspec(command).args
            configs = {cid: c for cid, c in configs.items() if cid in args}
        return command(**configs)

    return _hook


default = positional_factory()
"""Default init hook.

An alias for :func:`coma.hooks.init_hook.positional_factory` called with default
arguments.
"""
