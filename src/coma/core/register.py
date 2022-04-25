"""Register a sub-command that might be invoked upon waking from a coma."""
import argparse
import inspect

from boltons.funcutils import wraps
from typing import Any, Callable, Optional, Union

from .initiate import get_initiated
from ..hooks.core import Hooks


def register(
        name: str,
        command_class_or_function: Callable,
        config_class: Optional[Union[type, Any]] = None,
        *,
        parser_hook: Optional[Callable] = None,
        pre_config_hook: Optional[Callable] = None,
        config_hook: Optional[Callable] = None,
        pre_init_hook: Optional[Callable] = None,
        init_hook: Optional[Callable] = None,
        pre_run_hook: Optional[Callable] = None,
        run_hook: Optional[Callable] = None,
        post_run_hook: Optional[Callable] = None,
        **parser_kwargs
) -> None:
    """Registers a sub-command that might be invoked upon waking from a coma.

    Registers a sub-command by name with argparse, with optional configs and
    optional hooks.

    Note:
        Any provided hooks are sequentially called after calling global hooks
        (rather than replacing calls to global hooks).

    Args:
        name: Any valid sub-command name according to `argparse`
        command_class_or_function: Typically, any class type or function that
            implements the sub-command according to the `coma` protocol. See
            TODO(config; run(); wraps, etc.) for protocol details.

            Note: Can be any callable in more advanced use cases. See
            TODO(advanced command) for details on advanced use cases.
        config_class: Typically, any (dataclass) class type that implements the
            configs for the sub-command.

            Note: Can be any object in more advanced use cases. See
            TODO(advanced config) for details on advanced use cases.
        parser_hook: See TODO(invoke; protocol) for details on this hook
        pre_config_hook: See TODO(invoke; protocol) for details on this hook
        config_hook: See TODO(invoke; protocol) for details on this hook
        pre_init_hook: See TODO(invoke; protocol) for details on this hook
        init_hook: See TODO(invoke; protocol) for details on this hook
        pre_run_hook: See TODO(invoke; protocol) for details on this hook
        run_hook: See TODO(invoke; protocol) for details on this hook
        post_run_hook: See TODO(invoke; protocol) for details on this hook
        **parser_kwargs: Keyword arguments to pass along to the constructor of
            the :class:`argparse.ArgumentParser` that handles this sub-command

    See also:
        :func:`~coma.core.initiate.initiate`
        :func:`~coma.core.wake.wake`
    """
    if inspect.isclass(command_class_or_function):
        pre_init_command = command_class_or_function
    else:
        @wraps(command_class_or_function)
        def pre_init_command(*args, **kwargs):
            class C:
                @staticmethod
                def run():
                    return command_class_or_function(*args, **kwargs)
            return C()

    coma = get_initiated()
    subparser = coma.subparsers.add_parser(name, **parser_kwargs)
    hooks = coma.hooks[-1].merge(Hooks(
        parser_hook=parser_hook,
        pre_config_hook=pre_config_hook,
        config_hook=config_hook,
        pre_init_hook=pre_init_hook,
        init_hook=init_hook,
        pre_run_hook=pre_run_hook,
        run_hook=run_hook,
        post_run_hook=post_run_hook
    ))
    _do_register(name, pre_init_command, config_class, subparser, hooks)
    coma.commands_registered = True


def _do_register(
        name: str,
        pre_init_command: Callable,
        config_class: Optional[Union[type, Any]],
        subparser: argparse.ArgumentParser,
        hooks: Hooks
) -> None:
    """Registers a sub-command with argparse.

    Args:
        name: Any valid sub-command name according to `argparse`
        pre_init_command: Typically, a callable wrapped in such a was that it
            can be called twice: once to initialize and once to run.

            Note: Can be any callable in more advanced use cases. See
            TODO(advanced command) for details on advanced use cases.
        config_class: Typically, any (dataclass) class type that implements the
            configs for the sub-command.

            Note: Can be any object in more advanced use cases. See
            TODO(advanced config) for details on advanced use cases.
        subparser: The argument parser handling this sub-command
        hooks: The hooks for this sub-command
    """
    if hooks.parser_hook is not None:
        hooks.parser_hook(
                name=name,
                parser=subparser,
                pre_init_command=pre_init_command,
                config_class=config_class
            )

    def invoke(parser_args):
        """Argparse handler for this sub-command."""
        if hooks.pre_config_hook is not None:
            hooks.pre_config_hook(
                name=name,
                parser_args=parser_args,
                pre_init_command=pre_init_command,
                config_class=config_class
            )
        config = None
        if hooks.config_hook is not None:
            config = hooks.config_hook(
                name=name,
                parser_args=parser_args,
                pre_init_command=pre_init_command,
                config_class=config_class
            )
        if hooks.pre_init_hook is not None:
            hooks.pre_init_hook(
                name=name,
                parser_args=parser_args,
                pre_init_command=pre_init_command,
                config=config
            )
        command = None
        if hooks.init_hook is not None:
            command = hooks.init_hook(
                name=name,
                parser_args=parser_args,
                pre_init_command=pre_init_command,
                config=config
            )
        if hooks.pre_run_hook is not None:
            hooks.pre_run_hook(
                name=name,
                parser_args=parser_args,
                command=command,
                config=config
            )
        ret = None
        if hooks.run_hook is not None:
            ret = hooks.run_hook(
                name=name,
                parser_args=parser_args,
                command=command,
                config=config
            )
        if hooks.post_run_hook is not None:
            hooks.post_run_hook(
                name=name,
                parser_args=parser_args,
                command=command,
                config=config,
                run_return=ret
            )
    subparser.set_defaults(func=invoke)
