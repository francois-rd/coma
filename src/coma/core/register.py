"""Register a command that might be invoked upon waking from a coma."""

import argparse
from typing import Any, Callable, Dict, Optional

from boltons.funcutils import wraps

from ..config import to_dict

from .initiate import get_initiated
from .internal import Hooks


def register(
    name: str,
    command: Callable,
    *configs: Any,
    parser_hook: Optional[Callable] = None,
    pre_config_hook: Optional[Callable] = None,
    config_hook: Optional[Callable] = None,
    post_config_hook: Optional[Callable] = None,
    pre_init_hook: Optional[Callable] = None,
    init_hook: Optional[Callable] = None,
    post_init_hook: Optional[Callable] = None,
    pre_run_hook: Optional[Callable] = None,
    run_hook: Optional[Callable] = None,
    post_run_hook: Optional[Callable] = None,
    parser_kwargs: Optional[dict] = None,
    **id_configs: Any,
) -> None:
    """Registers a command that might be invoked upon waking from a coma.

    Registers a command with `ArgumentParser.add_subparsers().add_parser()`_,
    along with providing optional local configs and optional local hooks.

    .. note::

        Any provided local configs are **appended** to the list of global configs
        (rather than replacing them). See :func:`~coma.core.initiate.initiate`
        and :func:`~coma.core.forget.forget` for more details.

    Configs can be provided with or without an identifier. In the latter case,
    an identifier is derived automatically. See :func:`~coma.config.utils.to_dict`
    for additional details.

    Examples:

        Register function-based command with no configurations::

            coma.register("cmd", lambda: ...)

        Register function-based command with configurations::

            @dataclass
            class Config:
                ...
            coma.register("cmd", lambda cfg: ..., Config)

        Register class-based command with explicit configuration identifier::

            @dataclass
            class Config:
                ...
            class Command:
                def __init__(self, cfg):
                    ...
                def run(self):
                    ...
            coma.register("cmd", Command, a_non_default_id=Config)


    Args:
        name (str): Any (unique) valid command name according to ``argparse``
        command (typing.Callable): A command class or function
        *configs (typing.Any): Local configs with default identifiers
        parser_hook (typing.Callable): An optional local parser hook
        pre_config_hook (typing.Callable): An optional local pre config hook
        config_hook (typing.Callable): An optional local config hook
        post_config_hook (typing.Callable): An optional local post config hook
        pre_init_hook (typing.Callable): An optional local pre init hook
        init_hook (typing.Callable): An optional local init hook
        post_init_hook (typing.Callable): An optional local post init hook
        pre_run_hook (typing.Callable): An optional local pre run hook
        run_hook (typing.Callable): An optional local run hook
        post_run_hook (typing.Callable): An optional local post run hook
        parser_kwargs (typing.Dict[str, typing.Any]): Keyword arguments to pass
            along to the constructor of the sub-:obj:`ArgumentParser` created
            for :obj:`command`
        **id_configs (typing.Any): Local configs with explicit identifiers

    Raises:
        ValueError: If :obj:`name` is not unique
        KeyError: If config identifiers are not unique

    See also:
        * :func:`~coma.core.command.command`
        * :func:`~coma.core.initiate.initiate`
        * :func:`~coma.core.forget.forget`
        * :func:`~coma.core.wake.wake`
        * :func:`~coma.config.utils.to_dict`

    .. _ArgumentParser.add_subparsers().add_parser():
        https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_subparsers
    """
    coma = get_initiated()
    if name in coma.names:
        raise ValueError(f"Command name is already registered: {name}")

    if isinstance(command, type):
        command_ = command
    else:

        @wraps(command)
        def command_(*args, **kwargs):
            class C:
                @staticmethod
                def run():
                    return command(*args, **kwargs)

            return C()

    parser_kwargs = {} if parser_kwargs is None else parser_kwargs
    subparser = coma.subparsers.add_parser(name, **parser_kwargs)
    hooks = coma.hooks[-1].merge(
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
    configs = to_dict(*coma.configs[-1].items(), *configs, *id_configs.items())
    _do_register(name, command_, configs, subparser, hooks)
    coma.names.append(name)


def _do_register(
    name: str,
    command: Callable,
    configs: Dict[str, Any],
    subparser: argparse.ArgumentParser,
    hooks: Hooks,
) -> None:
    """Registers a command.

     Registers a command with ``argparse`` and implements ``coma``'s hook protocol.

    Args:
        name (str): Any (unique) valid command name according to ``argparse``
        command (typing.Callable): A command class or function
        configs (typing.Dict[str, typing.Any]): A mapping from config
            identifiers to configs
        subparser (argparse.ArgumentParser): The :obj:`ArgumentParser` for this command
        hooks: The hooks for this command
    """
    if hooks.parser_hook is not None:
        hooks.parser_hook(
            name=name,
            parser=subparser,
            command=command,
            configs=configs,
        )

    def invoke(known_args, unknown_args):
        # ============ Config ==============
        if hooks.pre_config_hook is not None:
            hooks.pre_config_hook(
                name=name,
                known_args=known_args,
                unknown_args=unknown_args,
                command=command,
                configs=configs,
            )
        configs_ = None
        if hooks.config_hook is not None:
            configs_ = hooks.config_hook(
                name=name,
                known_args=known_args,
                unknown_args=unknown_args,
                command=command,
                configs=configs,
            )
        if hooks.post_config_hook is not None:
            configs_ = hooks.post_config_hook(
                name=name,
                known_args=known_args,
                unknown_args=unknown_args,
                command=command,
                configs=configs_,
            )

        # ============ Init ==============
        if hooks.pre_init_hook is not None:
            hooks.pre_init_hook(
                name=name,
                known_args=known_args,
                unknown_args=unknown_args,
                command=command,
                configs=configs_,
            )
        command_ = None
        if hooks.init_hook is not None:
            command_ = hooks.init_hook(
                name=name,
                known_args=known_args,
                unknown_args=unknown_args,
                command=command,
                configs=configs_,
            )
        if hooks.post_init_hook is not None:
            command_ = hooks.post_init_hook(
                name=name,
                known_args=known_args,
                unknown_args=unknown_args,
                command=command_,
                configs=configs_,
            )

        # ============ Run ==============
        if hooks.pre_run_hook is not None:
            hooks.pre_run_hook(
                name=name,
                known_args=known_args,
                unknown_args=unknown_args,
                command=command_,
                configs=configs_,
            )
        result = None
        if hooks.run_hook is not None:
            result = hooks.run_hook(
                name=name,
                known_args=known_args,
                unknown_args=unknown_args,
                command=command_,
                configs=configs_,
            )
        if hooks.post_run_hook is not None:
            hooks.post_run_hook(
                name=name,
                known_args=known_args,
                unknown_args=unknown_args,
                command=command_,
                configs=configs_,
                result=result,
            )

    subparser.set_defaults(func=invoke)
