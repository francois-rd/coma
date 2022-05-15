"""Init hook utilities, factories, and defaults."""
import inspect
from typing import Any, Callable, Dict

from .utils import hook


def positional_factory(*skips: str) -> Callable:
    """Factory for creating an init hook that instantiates a command with some configs.

    Instantiates the command object by invoking it with all configs given as
    positional arguments.

    .. note::

        This works because the hook protocol assumes the configs dictionary is
        insertion-ordered.

    Args:
        *skips (str): Undesired configs can be skipped by providing the
            appropriate config identifiers

    Returns:
        An init hook
    """

    @hook
    def _hook(command: Callable, configs: Dict[str, Any]) -> Any:
        return command(*[c for cid, c in configs.items() if cid not in skips])

    return _hook


def keyword_factory(*skips: str, force: bool = False) -> Callable:
    """Factory for creating an init hook that instantiates a command with some configs.

    Instantiates the command object by invoking it with all configs given as keyword
    arguments based on matching parameter names in the command's function signature.

    Args:
        *skips (str): Undesired configs can be skipped by providing the
            appropriate config identifiers
        force (bool): For all un-skipped configs, whether to forcibly pass them
            to the command object, even if no parameter names in the command's
            function signature match a particular config identifier. In this
            case, :obj:`TypeError` will be raised unless the command's function
            signature includes variadic keyword arguments.

    Returns:
        An init hook
    """

    @hook
    def _hook(command: Callable, configs: Dict[str, Any]) -> Any:
        configs = {cid: c for cid, c in configs.items() if cid not in skips}
        if not force:
            args = inspect.getfullargspec(command).args
            configs = {cid: c for cid, c in configs.items() if cid in args}
        return command(**configs)

    return _hook


default = positional_factory()
"""Default init hook.

An alias for calling :func:`coma.hooks.init_hook.positional_factory` with
default arguments.
"""
