"""Decorator for declaring a coma command without explicit calls to coma.register()."""

from typing import Callable, Optional, get_origin  # NOTE: requires Python >= 3.8
from inspect import signature

from .internal import store_registration
from .register import register


def command(
    name: str,
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
):
    """
    Decorator declaring the decorated object as a coma command.

    Acts as a lightweight wrapper around :func:`~coma.core.register.register`.

    Specifically, inspects the decorated object's signature (either the function
    signature if the object is a function, or the signature of the __init__() method
    if the object is a class), and calls :obj:`coma.register()` with its
    :obj:`**id_configs` keyword arguments field populated using the signature
    parameters.

    The name of each parameter is used as the config ID and the type hint annotation is
    used as the class type.

    Example:
        The following declaration:

        .. code-block:: python

            @dataclass
            class SomeConfig:
                ...

            @command("command_name")
            def some_command(structured_config: SomeConfig, dict_config: dict):
                ...

        is equivalent to:

        .. code-block:: python

            @dataclass
            class SomeConfig:
                ...

            def some_command(structured_cfg: SomeConfig, dict_cfg: dict):
                ...

            coma.register(
                "command_name", some_command, structured_cfg=SomeConfig, dict_cfg={}
            )

    The advantage of this decorator is to remove the boilerplate of registering a
    command when its registration is a one-to-one mapping to the command signature.
    As such, this decorator acts as a convenience wrapper for :obj:`coma.register()`.
    It works in simple use cases. It does not work if the decorated object's signature
    contains non-config parameters (which is a rare and advanced use case). It also
    doesn't work with :func:`~coma.core.forget.forget` (a more common, if still slightly
    advanced use case). For such advanced uses cases, an explicit call to
    :obj:`coma.register()` must be made instead.

    Args:
        name (str): Passed directly to :func:`~coma.core.register.register`.
        parser_hook (typing.Callable): See :func:`~coma.core.register.register`.
        pre_config_hook (typing.Callable): See :func:`~coma.core.register.register`.
        config_hook (typing.Callable): See :func:`~coma.core.register.register`.
        post_config_hook (typing.Callable): See :func:`~coma.core.register.register`.
        pre_init_hook (typing.Callable): See :func:`~coma.core.register.register`.
        init_hook (typing.Callable): See :func:`~coma.core.register.register`.
        post_init_hook (typing.Callable): See :func:`~coma.core.register.register`.
        pre_run_hook (typing.Callable): See :func:`~coma.core.register.register`.
        run_hook (typing.Callable): See :func:`~coma.core.register.register`.
        post_run_hook (typing.Callable): See :func:`~coma.core.register.register`.
        parser_kwargs (typing.Dict[str, typing.Any]): See
            :func:`~coma.core.register.register`.

    See also:
        * :func:`~coma.core.forget.forget`
        * :func:`~coma.core.register.register`

    """

    def decorator(command_: Callable):
        id_configs = {}
        fn = command_.__init__ if isinstance(command_, type) else command_
        for i, p in enumerate(signature(fn).parameters.values()):
            if i == 0 and isinstance(command_, type):
                # Skip 'self' argument if command is a class.
                continue

            # If the annotation is list, List, dict, or Dict, convert it to an object
            # of the same type. Otherwise, pass the type directly to OmegaConf.create().
            if p.annotation is list or get_origin(p.annotation) is list:
                id_configs[p.name] = []
            elif p.annotation is dict or get_origin(p.annotation) is dict:
                id_configs[p.name] = {}
            else:
                id_configs[p.name] = p.annotation
        store_registration(
            lambda: register(
                name,
                command_,
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
                parser_kwargs=parser_kwargs,
                **id_configs,
            )
        )
        return command_

    return decorator
