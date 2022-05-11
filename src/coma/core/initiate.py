"""Initiate ``coma``."""
import argparse
from typing import Any, Callable, Optional
import warnings

from coma import hooks
from coma.config import to_dict

from .internal import Coma, Hooks, get_instance


def initiate(
    *configs: Any,
    parser: Optional[argparse.ArgumentParser] = None,
    parser_hook: Optional[Callable] = hooks.parser_hook.default,
    pre_config_hook: Optional[Callable] = None,
    config_hook: Optional[Callable] = hooks.config_hook.default,
    post_config_hook: Optional[Callable] = hooks.post_config_hook.default,
    pre_init_hook: Optional[Callable] = None,
    init_hook: Optional[Callable] = hooks.init_hook.default,
    post_init_hook: Optional[Callable] = None,
    pre_run_hook: Optional[Callable] = None,
    run_hook: Optional[Callable] = hooks.run_hook.default,
    post_run_hook: Optional[Callable] = None,
    subparsers_kwargs: Optional[dict] = None,
    **id_configs: Any,
) -> None:
    """Initiates ``coma``.

    Starts up ``coma`` with optional configurations, an optional argument
    parser, optional hooks, and optional subparsers keyword arguments.

    Any optional configurations and/or hooks are applied globally to every
    registered sub-command, unless explicitly forgotten using the
    :func:`~coma.core.forget.forget` context manager.

    Configurations can be provided with or without an identifier. In the latter
    case, an identifier is derived automatically. See :func:`coma.config.to_dict`
    for additional details.

    Example::

        @dataclass
        class Config1:
            ...

        @dataclass
        class Config2:
            ...
        coma.initiate(Config1, a_non_default_id=Config2, ...)

    Args:
        *configs: Global configurations with default identifiers
        parser: An argument parser for Coma. If `None`, an argument parser with
            default parameters is used.
        parser_hook: See TODO(invoke; protocol) for details on this hook
        pre_config_hook: See TODO(invoke; protocol) for details on this hook
        config_hook: See TODO(invoke; protocol) for details on this hook
        post_config_hook: See TODO(invoke; protocol) for details on this hook
        pre_init_hook: See TODO(invoke; protocol) for details on this hook
        init_hook: See TODO(invoke; protocol) for details on this hook
        post_init_hook: See TODO(invoke; protocol) for details on this hook
        pre_run_hook: See TODO(invoke; protocol) for details on this hook
        run_hook: See TODO(invoke; protocol) for details on this hook
        post_run_hook: See TODO(invoke; protocol) for details on this hook
        subparsers_kwargs: Keyword arguments to pass along to
            :func:`~argparse.ArgumentParser.add_subparsers`
        **id_configs: Global configurations with explicit identifiers

    Raises:
        KeyError: If configuration identifiers are not unique

    See also:
        * :func:`coma.config.to_dict`
        * :func:`~coma.core.forget.forget`
        * :func:`~coma.core.register.register`
    """
    coma = get_instance()
    if coma.parser is not None:
        warnings.warn("Coma is already initiated. Ignoring.", stacklevel=2)
        return
    if parser is None:
        parser = argparse.ArgumentParser()
    coma.parser = parser
    subparsers_kwargs = {} if subparsers_kwargs is None else subparsers_kwargs
    coma.subparsers = parser.add_subparsers(**subparsers_kwargs)
    coma.hooks.append(
        Hooks(
            parser_hook=parser_hook,
            pre_config_hook=pre_config_hook,
            config_hook=config_hook,
            post_config_hook=post_config_hook,
            pre_init_hook=pre_init_hook,
            init_hook=init_hook,
            post_init_hook=post_init_hook,
            pre_run_hook=pre_run_hook,
            run_hook=run_hook,
            post_run_hook=post_run_hook,
        )
    )
    coma.configs.append(to_dict(*configs, *id_configs.items()))


def get_initiated() -> Coma:
    """Returns the ``coma`` singleton, initiating it with defaults first if needed."""
    coma = get_instance()
    if coma.parser is None:
        initiate()
    return coma
