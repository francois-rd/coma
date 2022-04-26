"""Initiate a coma."""
import argparse
from typing import Callable, Optional
import warnings

from coma import hooks
from coma.hooks.core import Hooks

from . import Coma, get_instance


def initiate(
    parser: Optional[argparse.ArgumentParser] = None,
    *,
    parser_hook: Optional[Callable] = hooks.parser_hook.default,
    pre_config_hook: Optional[Callable] = None,
    config_hook: Optional[Callable] = hooks.config_hook.default,
    pre_init_hook: Optional[Callable] = None,
    init_hook: Optional[Callable] = hooks.init_hook.default,
    pre_run_hook: Optional[Callable] = None,
    run_hook: Optional[Callable] = hooks.run_hook.default,
    post_run_hook: Optional[Callable] = None,
    **subparsers_kwargs
) -> None:
    """Initiates a coma.

    Starts up ``coma`` with an optional argument parser, optional hooks, and
    optional subparsers keyword arguments.

    Any optional hooks are applied globally to every registered subcommand.

    Args:
        parser: An argument parser for Coma. If `None`, an argument parser with
            default parameters is used
        parser_hook: See TODO(invoke; protocol) for details on this hook
        pre_config_hook: See TODO(invoke; protocol) for details on this hook
        config_hook: See TODO(invoke; protocol) for details on this hook
        pre_init_hook: See TODO(invoke; protocol) for details on this hook
        init_hook: See TODO(invoke; protocol) for details on this hook
        pre_run_hook: See TODO(invoke; protocol) for details on this hook
        run_hook: See TODO(invoke; protocol) for details on this hook
        post_run_hook: See TODO(invoke; protocol) for details on this hook
        **subparsers_kwargs: Keyword arguments to pass along to
            :func:`~argparse.ArgumentParser.add_subparsers`

    See also:
        :func:`~coma.core.register.register`
        :func:`~coma.core.forget.forget`
    """
    coma = get_instance()
    if coma.parser is not None:
        warnings.warn("Coma is already initiated. Ignoring.", stacklevel=2)
        return
    if parser is None:
        parser = argparse.ArgumentParser()
    coma.parser = parser
    coma.subparsers = parser.add_subparsers(**subparsers_kwargs)
    coma.hooks.append(
        Hooks(
            parser_hook=parser_hook,
            pre_config_hook=pre_config_hook,
            config_hook=config_hook,
            pre_init_hook=pre_init_hook,
            init_hook=init_hook,
            pre_run_hook=pre_run_hook,
            run_hook=run_hook,
            post_run_hook=post_run_hook,
        )
    )


def get_initiated() -> Coma:
    """Returns the ``coma`` singleton, initiating it first if needed."""
    coma = get_instance()
    if coma.parser is None:
        initiate()
    return coma
