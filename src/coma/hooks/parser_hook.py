"""Core parser hooks and utilities."""
import argparse
from typing import Callable

from coma.config import (
    ConfigDict,
    ConfigID,
    default_default,
    default_flag,
    default_help,
)

from .utils import hook, sequence


def factory(*names_or_flags, **kwargs) -> Callable[..., None]:
    """Factory for a parser hook adding an :class:`argparse.ArgumentParser` argument.

    Example::

        coma.initiate(..., parser_hook=factory('-l', '--lines', type=int))

    Args:
        *names_or_flags: See :func:`argparse.ArgumentParser.add_argument`
        **kwargs: Passed to :func:`argparse.ArgumentParser.add_argument`

    Returns:
        A parser hook

    See also:
        * TODO(invoke; protocol) for details on parser hooks
    """

    @hook
    def _hook(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(*names_or_flags, **kwargs)

    return _hook


def single_config_factory(
    config_id: ConfigID, *names_or_flags, **kwargs
) -> Callable[..., None]:
    """Factory for adding a single configuration file path argument.

    If no arguments are provided, the following defaults are used for adding a
    argument to an :class:`argparse.ArgumentParser`::

        from coma.config import default_default, default_flag, default_help
        names_or_flags = [default_flag(config_id)]
        kwargs = {
            "type": str,
            "metavar": "FILE",
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
        config_id: A configuration identifier
        *names_or_flags: See :func:`~argparse.ArgumentParser.add_argument`
        **kwargs: Passed to :func:`~argparse.ArgumentParser.add_argument`

    Returns:
        A parser hook

    See also:
        * :func:`coma.hooks.config_hook.single_load_and_write_factory`
        * TODO(invoke; protocol) for details on parser hooks
    """

    @hook
    def _hook(parser: argparse.ArgumentParser) -> None:
        names_or_flags_ = names_or_flags or [default_flag(config_id)]
        kwargs.setdefault("type", str)
        kwargs.setdefault("metavar", "FILE")
        kwargs.setdefault("default", default_default(config_id))
        kwargs.setdefault("help", default_help(config_id))
        factory(*names_or_flags_, **kwargs)(parser=parser)

    return _hook


@hook
def multi_config(parser: argparse.ArgumentParser, configs: ConfigDict) -> None:
    """Hook for adding all configuration file path arguments.

    Equivalent to calling :func:`coma.hooks.parser_hook.single_config_factory`
    for each configuration in :obj:`configs`.

    Automatically adds file path arguments for all :obj:`configs` to an
    :class:`argparse.ArgumentParser`.

    Example::

        @dataclass
        class Config:
            ...
        coma.initiate(..., parser_hook=multi_config_parser_hook)

    Args:
        parser: See TODO(invoke; protocol) for details on this hook
        configs: See TODO(invoke; protocol) for details on this hook

    See also:
        * :func:`coma.hooks.parser_hook.single_config_factory`
        * TODO(invoke; protocol) for details on parser hooks
    """
    fns = [single_config_factory(cid) for cid in configs]
    if fns:
        sequence(*fns)(parser=parser)


default = multi_config
"""Default parser hook.

An alias for :func:`coma.hooks.parser_hook.multi_config`.
"""
