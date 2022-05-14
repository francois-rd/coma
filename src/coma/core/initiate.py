"""Initiate a coma."""
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
    """Initiates a coma.

    Starts up ``coma`` with an optional argument parser, optional global
    configs, optional global hooks, and optional subparsers keyword arguments.

    .. note::

        Any optional configs and/or hooks are applied **globally** to every
        :func:`~coma.core.register.register`\\ ed command, unless explicitly
        forgotten using the :func:`~coma.core.forget.forget` context manager.

    Configs can be provided with or without an identifier. In the latter case,
    an identifier is derived automatically. See :func:`~coma.config.utils.to_dict`
    for additional details.

    Example::

        @dataclass
        class Config1:
            ...

        @dataclass
        class Config2:
            ...
        coma.initiate(Config1, a_non_default_id=Config2, pre_run_hook=...)

    Args:
        *configs (typing.Any): Global configs with default identifiers
        parser (argparse.ArgumentParser): Top-level :obj:`ArgumentParser`. If
            :obj:`None`, an :obj:`ArgumentParser` with default parameters is used.
        parser_hook (typing.Callable): An optional global parser hook
        pre_config_hook (typing.Callable): An optional global pre config hook
        config_hook (typing.Callable): An optional global config hook
        post_config_hook (typing.Callable): An optional global post config hook
        pre_init_hook (typing.Callable): An optional global pre init hook
        init_hook (typing.Callable): An optional global init hook
        post_init_hook (typing.Callable): An optional global post init hook
        pre_run_hook (typing.Callable): An optional global pre run hook
        run_hook (typing.Callable): An optional global run hook
        post_run_hook (typing.Callable): An optional global post run hook
        subparsers_kwargs (typing.Dict[str, typing.Any]): Keyword arguments to
            pass along to `ArgumentParser.add_subparsers()`_
        **id_configs (typing.Any): Global configs with explicit identifiers

    Raises:
        KeyError: If config identifiers are not unique

    See also:
        * :func:`~coma.core.forget.forget`
        * :func:`~coma.core.register.register`
        * :func:`~coma.config.utils.to_dict`

    .. _ArgumentParser.add_subparsers():
        https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_subparsers
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
