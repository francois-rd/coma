"""Wake from a coma."""

import argparse
import sys
from typing import Any, Callable, Optional, Sequence

from .singleton import Coma, RegistrationData
from ..hooks.base import AugmentedHook, InvocationData, ParserData, DEFAULT
from ..hooks.management import Hooks


class WakeException(Exception):
    """Raised when :func:`~coma.core.wake.wake()` fails."""

    pass


def wake(
    parser: Optional[argparse.ArgumentParser] = None,
    *import_commands: Any,  # noqa: Purposefully unused.
    cli_args: Optional[Sequence[str]] = None,
    cli_namespace: Optional[Any] = None,
    parser_hook: AugmentedHook = DEFAULT,
    pre_config_hook: AugmentedHook = None,
    config_hook: AugmentedHook = DEFAULT,
    post_config_hook: AugmentedHook = None,
    pre_init_hook: AugmentedHook = None,
    init_hook: AugmentedHook = DEFAULT,
    post_init_hook: AugmentedHook = None,
    pre_run_hook: AugmentedHook = None,
    run_hook: AugmentedHook = DEFAULT,
    post_run_hook: AugmentedHook = None,
    **subparsers_kwargs,
) -> None:
    """
    Wakes from a coma.

    Starts up ``coma`` with an optional argument parser, optional shared hooks,
    and optional subparsers keyword arguments. Any shared hooks are applied
    **globally** to every registered command.

    .. note::

        ``coma``'s architecture follows the `Template`_ design pattern with `hooks`_
        intended to add or modify behavior. Pre-defined hooks specify ``coma``'s
        default behavior. Pre-defined hook factories enable one-line deployment of
        small tweaks on the core default behavior. ``coma`` has very few baked in
        assumptions. Nearly all behavior can be drastically changed with user-defined
        hooks. For detailed tutorials and usage examples of both the default behavior
        and implementation of user-defined hooks, see the extensive online docs.

    All hooks default to the :data:`~coma.hooks.base.DEFAULT` sentinel, which means
    they get replaced at runtime with the corresponding pre-defined default hook.
    Setting a hook to :obj:`None` disables it. The :data:`~coma.hooks.base.SHARED`
    sentinel is not allowed in :obj:`wake()` since it would lead to infinite regress.
    See :func:`~coma.core.command.command()` for usage of :obj:`SHARED`.

    .. note::

        Hooks can be "plain" objects as just described, or they can be (recursive)
        **sequences** of such "plain" objects. This syntax acts as a convenient
        shorthand that enables composing larger hooks from smaller components
        without having to define a wrapper hook whose only purpose is to compose
        component hooks.

    .. note::

        A command is only registered (via :func:`~coma.core.command.command()`)
        if the module in which the command is declared is imported at runtime. This
        is standard Python behavior: non-imported code is not interpreted by the VM
        and not available at runtime. This is a bit obscured by the behind-the-scenes
        magic done by :obj:`command()`. But this magic only works if the command code
        runs (via being imported) at some point before the call to :obj:`wake()`.

        One way to achieve this is by having a :obj:`from . import module` statement
        in the top-level :obj:`__init__.py` for **every** module with a command. That
        forces each command module to be imported. Alternatively, a common pattern is
        to put lightweight (one-line) :obj:`command()` wrappers around calls to the
        main/workhorse functions all in a single module (typically, the same module
        that calls :obj:`wake()`). Finally, a third alternative is to pass all commands
        scattered throughout a codebase to :obj:`*import_commands`. The contents of
        :obj:`*import_commands` is **fully** ignored by :obj:`wake()`. However, it
        forces the Python VM to import each of the provided modules, thus registering
        the commands. Providing the imported commands to :obj:`*import_commands` is
        not required (merely importing them is enough), but doing so prevents linters
        from complaining of unused import statements.

    Example::

        @coma.command
        def cmf(...):
            ...

        if __name__ == "__main__":
            coma.wake(parser=..., parser_hook=..., ...)

    Args:
        parser (:class:`argparse.ArgumentParser`, optional): Top-level
            :obj:`ArgumentParser` to use. If :obj:`None`, an :obj:`ArgumentParser`
            with default parameters is used instead.
        *import_commands (typing.Any): **Fully** ignored. Optional mechanism to
            forcibly import commands scattered throughout a codebase.
        cli_args (typing.Sequence[str], optional): Command line arguments to
            use with :obj:`parser`. If :obj:`None`, :obj:`sys.argv` is used instead.
        cli_namespace (typing.Any, optional): The namespace object to pass
            to `parse_known_args()`_. If :obj:`None`, use the ``argparse`` default.
        parser_hook (:data:`~coma.hooks.base.AugmentedHook`): An optional shared
            hook with parser hook semantics.
        pre_config_hook (:data:`~coma.hooks.base.AugmentedHook`): An optional shared
            hook with pre config hook semantics.
        config_hook (:data:`~coma.hooks.base.AugmentedHook`): An optional shared
            hook with config hook semantics.
        post_config_hook (:data:`~coma.hooks.base.AugmentedHook`): An optional shared
            hook with post config hook semantics.
        pre_init_hook (:data:`~coma.hooks.base.AugmentedHook`): An optional shared
            hook with pre init hook semantics.
        init_hook (:data:`~coma.hooks.base.AugmentedHook`): An optional shared
            hook with init hook semantics.
        post_init_hook (:data:`~coma.hooks.base.AugmentedHook`): An optional shared
            hook with post init hook semantics.
        pre_run_hook (:data:`~coma.hooks.base.AugmentedHook`): An optional shared
            hook with pre run hook semantics.
        run_hook (:data:`~coma.hooks.base.AugmentedHook`): An optional shared
            hook with run hook semantics.
        post_run_hook (:data:`~coma.hooks.base.AugmentedHook`): An optional shared
            hook with post run hook semantics.
        **subparsers_kwargs (typing.Any): Keyword arguments to
            pass along to `ArgumentParser.add_subparsers()`_

    Raises:
        WakeException: If no commands are registered or the command line arguments
            fail to invoke a command.
        ValueError: If any :data:`~coma.hooks.base.Hook` argument is or contains the
            :data:`~coma.hooks.base.SHARED` sentinel, which would lead to infinite
            regress.
        Others: As may be raised by ``argparse`` or any of the hooks or commands.

    See also:
        * The online docs for detailed tutorials and examples.
        * :func:`~coma.core.command.command()`

    .. _ArgumentParser.add_subparsers():
        https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_subparsers
    .. _parse_known_args():
        https://docs.python.org/3/library/argparse.html#partial-parsing
    .. _Template:
        https://en.wikipedia.org/wiki/Template_method_pattern
    .. _hooks:
        https://en.wikipedia.org/wiki/Hooking
    """
    if not Coma.get_registrations():
        raise WakeException(
            "Waking from a coma with no commands registered. At least one call to "
            "'@command' is required before waking."
        )
    parser = parser or argparse.ArgumentParser()
    subparsers = parser.add_subparsers(**subparsers_kwargs)
    shared_hooks = Hooks(
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
    for data in Coma.get_registrations().values():
        subparser = subparsers.add_parser(data.name, **data.parser_kwargs)
        hooks = Hooks.merge(shared_hooks, data.hooks)
        hooks.parse(data.to(ParserData, parser=subparser))
        subparser.set_defaults(func=invoke_factory(data, hooks))
    known_args, unknown_args = parser.parse_known_args(cli_args, cli_namespace)
    try:
        known_args.func(known_args, unknown_args)
    except AttributeError as e:
        if any("func" in arg for arg in e.args):
            raise WakeException(
                "Waking from a coma with no command given on the command line. "
                f"Invoke with: {sys.argv[0]} <command-name>"
            )
        raise


def invoke_factory(data: RegistrationData, hooks: Hooks) -> Callable:
    def invoke(known_args: Any, unknown_args: list[str]):
        inv = data.to(InvocationData, known_args=known_args, unknown_args=unknown_args)
        hooks.invoke(inv)

    return invoke
