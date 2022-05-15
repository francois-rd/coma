"""Parser hook utilities, factories, and defaults."""
import argparse
from typing import Any, Callable, Dict

from coma.config import default_default, default_dest, default_flag, default_help

from .utils import hook, sequence


def factory(*names_or_flags, **kwargs) -> Callable[..., None]:
    """Factory for creating a parser hook that adds an ``argparse`` argument.

    Creates a parser hook that add an argument to the :obj:`ArgumentParser` of
    the hook protocol.

    Example::

        coma.initiate(..., parser_hook=factory('-l', '--lines', type=int))

    Args:
        *names_or_flags: Passed to `add_argument()`_
        **kwargs: Passed to `add_argument()`_

    Returns:
        A parser hook

    .. _add_argument():
        https://docs.python.org/3/library/argparse.html#the-add-argument-method
    """

    @hook
    def _hook(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(*names_or_flags, **kwargs)

    return _hook


def single_config_factory(
    config_id: str, *names_or_flags, **kwargs
) -> Callable[..., None]:
    """Factory for creating a parser hook that adds a single config file path argument.

    If no arguments are provided, the following defaults are used for
    `add_argument()`_::

        from coma.config import default_default, default_flag, default_help
        names_or_flags = [default_flag(config_id)]
        kwargs = {
            "type": str,
            "metavar": "FILE",
            "dest": default_dest(config_id)
            "default": default_default(config_id),
            "help": default_help(config_id),
        }

    Any of these defaults can be overridden by providing alternative arguments.
    Additional arguments beyond these can also be provided.

    Example::

        @dataclass
        class Config:
            ...

        cfg_id = default_id(Config)
        parser_hook = single_config_factory(cfg_id, metavar=cfg_id.upper())
        coma.register(..., parser_hook=parser_hook)

    Args:
        config_id (str): A config identifier
        *names_or_flags: Passed to `add_argument()`_
        **kwargs: Passed to `add_argument()`_

    Returns:
        A parser hook

    See also:
        * :func:`~coma.hooks.config_hook.single_load_and_write_factory`

    .. _add_argument():
        https://docs.python.org/3/library/argparse.html#the-add-argument-method
    """

    @hook
    def _hook(parser: argparse.ArgumentParser) -> None:
        names_or_flags_ = names_or_flags or [default_flag(config_id)]
        kwargs.setdefault("type", str)
        kwargs.setdefault("metavar", "FILE")
        kwargs.setdefault("default", default_default(config_id))
        kwargs.setdefault("dest", default_dest(config_id))
        kwargs.setdefault("help", default_help(config_id))
        factory(*names_or_flags_, **kwargs)(parser=parser)

    return _hook


@hook
def multi_config(parser: argparse.ArgumentParser, configs: Dict[str, Any]) -> None:
    """Parser hook for adding all config file path arguments.

    Equivalent to calling :func:`~coma.hooks.parser_hook.single_config_factory`
    for each config in :obj:`configs`.

    Automatically adds file path arguments for all :obj:`configs` using :obj:`parser`.

    Example::

        @dataclass
        class Config:
            ...

        coma.initiate(..., parser_hook=multi_config)

    Args:
        parser: The parser parameter of the parser hook protocol
        configs: The configs parameter of the parser hook protocol

    See also:
        * :func:`~coma.hooks.parser_hook.single_config_factory`
    """
    fns = [single_config_factory(cid) for cid in configs]
    if fns:
        sequence(*fns)(parser=parser)


default = multi_config
"""Default parser hook.

An alias for :func:`~coma.hooks.parser_hook.multi_config`.
"""
