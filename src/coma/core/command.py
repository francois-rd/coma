"""Register a command that might be invoked upon waking from a coma."""

from inspect import signature
from typing import Any, Callable, Optional

from boltons.funcutils import wraps

from .singleton import Coma, RegistrationData
from ..config import (
    Parameters,
    PersistenceManager,
    SignatureInspector,
    SignatureInspectorProtocol,
)
from ..hooks.base import Command, CommandName, AugmentedHook, SHARED
from ..hooks.management import Hooks


# Implementation note: hooks here default to SHARED and not None (even for those where
# the wake() default is None), so that users who update some hook in wake() have that
# automatically applied to each command. If None was the default here, then adding a
# hook to wake would require explicitly setting that hook to SHARED for *all* commands,
# which is the opposite of what we want. Default behavior: shared. If sharing is not
# desired for a specific command, set to that hook to None for just that command.
def command(
    cmd: Optional[Command] = None,
    *,
    name: Optional[CommandName] = None,
    parser_hook: AugmentedHook = SHARED,
    pre_config_hook: AugmentedHook = SHARED,
    config_hook: AugmentedHook = SHARED,
    post_config_hook: AugmentedHook = SHARED,
    pre_init_hook: AugmentedHook = SHARED,
    init_hook: AugmentedHook = SHARED,
    post_init_hook: AugmentedHook = SHARED,
    pre_run_hook: AugmentedHook = SHARED,
    run_hook: AugmentedHook = SHARED,
    post_run_hook: AugmentedHook = SHARED,
    signature_inspector: Optional[SignatureInspectorProtocol] = None,
    persistence_manager: Optional[PersistenceManager] = None,
    parser_kwargs: Optional[Parameters] = None,
    **supplemental_configs: Any,
):
    """
    Registers a command that might be invoked upon waking from a coma.

    Registers a command with `ArgumentParser.add_subparsers().add_parser()`_ using
    the given registration data (name, hooks, config declarations, persistence manager,
    and supplemental configs) and the given parser kwargs.

    .. note::

        ``coma``'s architecture follows the `Template`_ design pattern with `hooks`_
        intended to add or modify behavior. Pre-defined hooks specify ``coma``'s
        default behavior. Pre-defined hook factories enable one-line deployment of
        small tweaks on the core default behavior. ``coma`` has very few baked in
        assumptions. Nearly all behavior can be drastically changed with user-defined
        hooks. For detailed tutorials and usage examples of both the default behavior
        and implementation of user-defined hooks, see the extensive online docs.

    Usage modes:

        As a decorator:

        .. code-block:: python

            @command(name="command_name", ...)
            def my_cmd(...):
                ...

        As a normal function call:

        .. code-block:: python

            def my_cmd(main_cfg: SomeConfig, **extra_cli_configs):
                ...

            coma.command(name="command_name", cmd=my_cmd, ...)

        Both decorator and procedural modes also accept a class argument:

        .. code-block:: python

            @coma.command(name="command_name", ...)
            class MyCmd(...):
                def run(self):
                    ...

        or:

        .. code-block:: python

            class MyCmd(...):
                def run(self):
                    ...

            coma.command(name="command_name", cmd=MyCmd, ...)

        .. note::

            It is invalid to specify the :obj:`cmd` parameter in decorator mode.

        .. note::

            Throughout, we refer to **"the command"**, which applies regardless of
            usage mode (decorator or procedural) and regardless of whether the command
            object is a function or a class (:obj:`my_cmd` or :obj:`MyCmd`,
            respectively, in the above examples). The **"command signature"** refers
            directly to the function signature if the command is a function, or to the
            signature of the :obj:`__init__()` method if the command is a class.

        .. note::

            When the command is a function, it gets wrapped in a class internally.
            Therefore, unless you really know what you are doing, it is unwise to
            inspect or change the :attr:`~coma.hooks.base.HookData.command` in any
            user-supplied hooks. Instead, rely on the registered command
            :attr:`~coma.hooks.base.HookData.name` (which is guaranteed to be unique)
            to delegate reused functionality across the hooks.

    Details:

        The command's signature is inspected (using :obj:`signature_inspector`) to
        infer and separate :class:`~coma.config.base.Config` s from other parameters.
        A rich set of options exist for declaring which parameters are config or regular
        parameters. See :class:`~coma.config.cli.SignatureInspector` for details.

        Additional configs not present in the command signature can be supplied through
        :obj:`supplemental_configs`. These can be helpful for providing additional
        information to the hooks beyond what the command itself requires.

        All hooks default to the :data:`~coma.hooks.base.SHARED` sentinel, which
        means they get replaced at runtime with the corresponding shared hook from
        :func:`~coma.core.wake.wake()`. Setting a hook to :obj:`None` disables that
        hook entirely. Setting a hook to the :data:`~coma.hooks.base.DEFAULT` sentinel,
        means it gets replaced at runtime with the corresponding pre-defined default
        hook. Because all the shared hooks default to :obj:`DEFAULT`, :obj:`SHARED`
        and :obj:`DEFAULT` might feel interchangeable. However, once a shared hook in
        :obj:`wake()` is replaced with a user-defined hook, they act differently.
        Setting a hook to :obj:`DEFAULT` here recovers the default functionality for
        this specific command, whereas :obj:`SHARED` uses the user-defined replacement.

        .. note::

            Hooks can be "plain" objects as just described, or they can be (recursive)
            **sequences** of such "plain" objects. This syntax acts as a convenient
            shorthand that enables composing larger hooks from smaller components
            without having to define a wrapper hook whose only purpose is to compose
            component hooks.

    Args:
        name (:data:`~coma.hooks.base.CommandName`): Any (unique) valid command name
            according to ``argparse``. If :obj:`None`, :obj:`cmd.__name__.lower()`
            is used instead.
        cmd (:data:`~coma.hooks.base.Command`, optional): A command class or function.
            If :obj:`None`, use decorator mode. If given, use procedural mode.
        parser_hook (:data:`~coma.hooks.base.AugmentedHook`): An optional
            command-specific hook with parser hook semantics.
        pre_config_hook (:data:`~coma.hooks.base.AugmentedHook`): An optional
            command-specific hook with pre config hook semantics.
        config_hook (:data:`~coma.hooks.base.AugmentedHook`): An optional
            command-specific hook with config hook semantics.
        post_config_hook (:data:`~coma.hooks.base.AugmentedHook`): An optional
            command-specific hook with post config hook semantics.
        pre_init_hook (:data:`~coma.hooks.base.AugmentedHook`): An optional
            command-specific hook with pre init hook semantics.
        init_hook (:data:`~coma.hooks.base.AugmentedHook`): An optional
            command-specific hook with init hook semantics.
        post_init_hook (:data:`~coma.hooks.base.AugmentedHook`): An optional
            command-specific hook with post init hook semantics.
        pre_run_hook (:data:`~coma.hooks.base.AugmentedHook`): An optional
            command-specific hook with pre run hook semantics.
        run_hook (:data:`~coma.hooks.base.AugmentedHook`): An optional
            command-specific hook with run hook semantics.
        post_run_hook (:data:`~coma.hooks.base.AugmentedHook`): An optional
            command-specific hook with post run hook semantics.
        signature_inspector (:class:`~coma.config.cli.SignatureInspectorProtocol`, optional):
            The :obj:`SignatureInspectorProtocol` to use for inspecting the :obj:`cmd`
            object's signature. If :obj:`None`, a
            :class:`~coma.config.cli.SignatureInspector` with default
            parameters is used.
        persistence_manager (:class:`~coma.config.io.PersistenceManager`, optional):
            Manager for the serializing of configs. If :obj:`None`, a manager with
            default parameters is used.
        parser_kwargs (:data:`~coma.config.base.Parameters`, optional): Keyword
             arguments passed along to the :obj:`ArgumentParser` sub-parser that
             will be created just for this command.
        **supplemental_configs (typing.Any): Additional configs not present in the
            command signature. Any ``omegaconf``-compatible config type is valid.

    See also:
        * The online docs for detailed tutorials and examples.
        * :class:`~coma.config.cli.SignatureInspector`
        * :class:`~coma.config.cli.ParamData`
        * :class:`~coma.config.io.PersistenceManager`
        * :func:`~coma.core.wake.wake()`

    .. _Template:
        https://en.wikipedia.org/wiki/Template_method_pattern
    .. _hooks:
        https://en.wikipedia.org/wiki/Hooking
    .. _ArgumentParser.add_subparsers().add_parser():
        https://docs.python.org/3/library/argparse.html#sub-commands
    """

    def decorator(cmd_: Callable):
        data = RegistrationData(
            name=name or cmd_.__name__.lower(),
            command=_maybe_wrap_command(cmd_),
            hooks=Hooks(
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
            ),
            parameters=(signature_inspector or SignatureInspector())(
                signature(cmd_), supplemental_configs
            ),
            persistence_manager=persistence_manager or PersistenceManager(),
            parser_kwargs=parser_kwargs or {},
        )
        Coma.register(data)
        return cmd_

    # Apply the decorator.
    if cmd is None:
        return decorator
    decorator(cmd)

    # If cmd is given, we need to make sure the decorator syntax is not overloaded.
    def raise_error(extra_cmd: Any):
        cmd_def = _make_def_string(cmd)
        extra_cmd_def = _make_def_string(extra_cmd)
        raise ValueError(
            "Overloaded @command decorator with two commands:\n"
            f"@command(cmd={cmd.__name__}, ...)\n{extra_cmd_def}\n"
            "Either use the decorator syntax while leaving the 'cmd' parameter "
            "None:\n"
            f"@command(...)\n{extra_cmd_def}\n"
            "or use the procedural syntax while specifying the 'cmd' parameter:\n"
            f"{cmd_def}command(cmd={cmd.__name__}, ...)"
        )

    return raise_error


def _maybe_wrap_command(cmd: Any) -> Command:
    if isinstance(cmd, type):
        return cmd

    @wraps(cmd)
    def wrapper(*args, **kwargs):
        class Cmd:
            @staticmethod
            def run():
                return cmd(*args, **kwargs)

        return Cmd()

    return wrapper


def _make_def_string(cmd: Optional[Command]) -> str:
    if cmd is None:
        # This is disallowed in the language syntax regardless.
        raise ValueError("Cannot created definition from None")
    if isinstance(cmd, type):
        return f"class {cmd.__name__}:\n    ...\n"
    return f"def {cmd.__name__}(...):\n    ...\n"
