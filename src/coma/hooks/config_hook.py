"""Config hook utilities and factories."""

from typing import Container, Optional, Union
import os

from .base import Hook, InvocationData, GeneralSentinel, SENTINEL, identity
from ..config import (
    ConfigID,
    InstanceKey,
    InstanceKeys,
    Override,
    OverrideData,
    OverrideProtocol,
    initialize,
    write as do_write,
)


OverrideProtocolOrSentinels = Union[OverrideProtocol, GeneralSentinel, None]
"""
Callable to override config attributes with command line arguments, or
:data:`~coma.hooks.base.SENTINEL` to use :class:`~coma.config.cli.Override`
with default parameters, or :obj:`None` to disable overriding altogether.

Alias:
"""


def initialize_factory(config_id: ConfigID, raise_on_fnf: bool = False) -> Hook:
    """
    Factory for creating an invocation hook with :obj:`config_hook` semantics.

    Specifically, initializes the :class:`~coma.config.base.Config` corresponding
    to :obj:`config_id` from amongst the configs (or supplemental configs) in
    :attr:`coma.hooks.base.HookData.parameters`.

    The initialization leverages :func:`~coma.config.io.initialize()`. The
    :obj:`file_path` parameter to :obj:`initialize()` is derived by calling
    :meth:`~coma.config.io.PersistenceManager.get_file_path()` on the current
    value of the :attr:`~coma.hooks.base.HookData.persistence_manager`
    object, **except** if :obj:`config_id` corresponds to a config where
    :meth:`~coma.config.cli.ParamData.is_serializable()` is :obj:`False`,
    which is never initialized from file.

    If loading from file fails due to a :obj:`FileNotFoundError`, the error is
    re-raised if :obj:`raise_on_fnf` is :obj:`True`. If :obj:`raise_on_fnf` is
    :obj:`False`, a config with default values is initialized and the missing
    file is silently ignored.

    Example:

        Fail fast when encountering a :obj:`FileNotFoundError`::

            coma.command(..., config_hook=initialize_factory(..., raise_on_fnf=True))

    Args:
        config_id (:data:`~coma.config.base.ConfigID`): The identifier of the
            config to initialize.
        raise_on_fnf (bool): If :obj:`True`, raises a :obj:`FileNotFoundError`
            if the config file was not found. If :obj:`False`, a config object
            with default values is initialized instead of failing outright.

    Returns:
        :data:`~coma.hooks.base.Hook`: A hook with partial :obj:`config_hook` semantics.

    Raises:
        KeyError: If :obj:`config_id` does not match any known config or supplemental
            config.
        FileNotFoundError: If :obj:`raise_on_fnf` is :obj:`True` and the config
            file was not found.
        Others: As may be raised by the underlying ``omegaconf`` handler or by
            :func:`~coma.config.io.initialize()`.

    See also:
        * :func:`coma.hooks.parser_hook.default_factory()`
        * :func:`coma.hooks.config_hook.default_factory()`
        * :func:`coma.hooks.init_hook.default_factory()`
        * :func:`~coma.config.io.initialize()`
    """

    def hook(data: InvocationData) -> None:
        file_path = data.persistence_manager.get_file_path(config_id, data.known_args)
        if not data.parameters.is_serializable(config_id):
            file_path = None
        config = data.parameters.get(config_id)
        try:
            initialize(config, file_path)
        except FileNotFoundError:
            if raise_on_fnf:
                raise
            initialize(config)

    return hook


def write_factory(
    config_id: ConfigID,
    *,
    instance_key: Optional[InstanceKey] = None,
    resolve: bool = False,
    overwrite: bool = False,
) -> Hook:
    """
    Factory for creating an invocation hook with partial :obj:`config_hook` semantics.

    Specifically, serializes the :obj:`instance_key` instance of the
    :class:`~coma.config.base.Config` corresponding to :obj:`config_id`
    from amongst the configs (or supplemental configs) in
    :attr:`coma.hooks.base.HookData.parameters`.

    The serialization leverages :func:`~coma.config.io.write()`, with
    :obj:`instance_key` and :obj:`resolve` passed directly to it. The
    :obj:`file_path` parameter to :obj:`write()` is derived by calling
    :meth:`~coma.config.io.PersistenceManager.get_file_path()` on the current
    value of the :attr:`~coma.hooks.base.HookData.persistence_manager`
    object, **except** if :obj:`config_id` corresponds to a config where
    :meth:`~coma.config.cli.ParamData.is_serializable()` is :obj:`False`,
    which is never written to file.

    If the destination file already exists, new content is only written if
    :obj:`overwrite` is :obj:`True`.

    Example:

        Always write a specific config instance, rather than the latest::

            coma.command(..., config_hook=write_factory(..., instance_key="MY KEY"))

    Args:
        config_id (:data:`~coma.config.base.ConfigID`): The identifier of the
            config to serialize.
        instance_key (:data:`~coma.config.base.InstanceKey`, optional): The specific
            :class:`~coma.config.base.Config` instance to serialize. If :obj:`None`,
            the latest instance is used.
        resolve (bool): Passed directly to :func:`~coma.config.io.write()`.
        overwrite (bool): Whether to overwrite the file content whe the destination
            file already exists.

    Returns:
        :data:`~coma.hooks.base.Hook`: A hook with partial :obj:`config_hook` semantics.

    Raises:
        KeyError: If :obj:`config_id` does not match any known config or supplemental
            config.
        Others: As may be raised by the underlying ``omegaconf`` handler or by
            :func:`~coma.config.io.write()`.

    See also:
        * :func:`coma.hooks.parser_hook.default_factory()`
        * :func:`coma.hooks.config_hook.default_factory()`
        * :func:`~coma.config.io.write()`
    """

    def hook(data: InvocationData) -> None:
        if not data.parameters.is_serializable(config_id):
            return
        file_path = data.persistence_manager.get_file_path(config_id, data.known_args)
        if overwrite or not os.path.exists(file_path):
            config = data.parameters.get(config_id)
            do_write(config, file_path, key=instance_key, resolve=resolve)

    return hook


def override_factory(
    config_id: ConfigID,
    instance_key: Optional[InstanceKey] = None,
    override: OverrideProtocolOrSentinels = SENTINEL,
) -> Hook:
    """
    Factory for creating an invocation hook with partial :obj:`config_hook` semantics.

    Specifically, overrides the :obj:`instance_key` instance of the
    :class:`~coma.config.base.Config` corresponding to :obj:`config_id`
    from amongst the configs (or supplemental configs) in
    :attr:`coma.hooks.base.HookData.parameters` with command line arguments.

    Leverages :class:`~coma.config.cli.Override`, with :obj:`instance_key` passed
    directly to it. If :obj:`override` has value :data:`~coma.hooks.base.SENTINEL`,
    an :obj:`Override` with default parameters is used. Slight variations can be
    declared by directly setting :obj:`override` to a specific instance of
    :obj:`Override`. Alternatively, entirely custom implementations can also be
    provided so long as the provided object is a Callable with a signature that
    adheres to the :class:`~coma.config.cli.OverrideProtocol`. If :obj:`override`
    is :obj:`None`, returns immediately without performing any override.

    Example:

        Change separator to :obj:`"~"`::

            coma.command(..., config_hook=override_factory(..., override=Override(sep="~")))

    Args:
        config_id (:data:`~coma.config.base.ConfigID`): The identifier of the
            config to override.
        instance_key (:data:`~coma.config.base.InstanceKey`, optional): The specific
            :class:`~coma.config.base.Config` instance to override. If :obj:`None`,
            the latest instance is used.
        override (:data:`~coma.hooks.config_hook.OverrideProtocolOrSentinels`):
            Callable to override config attributes with command line arguments; or
            :data:`~coma.hooks.base.SENTINEL` to use :class:`~coma.config.cli.Override`
            with default parameters; or :obj:`None` to disable override altogether.

    Raises:
        KeyError: If :obj:`config_id` does not match any known config or supplemental
            config.
        Others: As may be raised by the underlying ``omegaconf`` handler or by
            :obj:`override`.

    Returns:
        :data:`~coma.hooks.base.Hook`: A hook with partial :obj:`config_hook` semantics.

    See also:
        * :func:`coma.hooks.config_hook.default_factory()`
        * :class:`~coma.config.cli.Override`
    """

    def hook(data: InvocationData) -> None:
        if override is None:
            return

        override_data = OverrideData(
            config_id=config_id,
            configs=data.parameters.get_all_configs(),
            instance_key=instance_key,
            unknown_args=data.unknown_args,
        )
        (Override() if override is SENTINEL else override)(override_data)

    return hook


def default_factory(
    *config_ids: ConfigID,
    raise_on_fnf: bool = False,
    override_instance_key: Optional[InstanceKey] = None,
    override: Optional[Union[OverrideProtocol, GeneralSentinel]] = SENTINEL,
    skip_write: Optional[Container[ConfigID]] = None,
    write: bool = True,
    write_instance_key: Optional[InstanceKey] = InstanceKeys.BASE,
    resolve: bool = False,
    overwrite: bool = False,
) -> Hook:
    """
    Factory for creating an invocation hook with :obj:`config_hook` semantics.

    .. note::

        If :obj:`config_ids` is empty, defaults to **all** registered configs for
        the command being executed. In other words, only specify :obj:`config_ids`
        explicitly to **limit** the factory to only those configs.

    Assumptions made in designing this config hook implementation:

        1. Configs are declarative. They follow the following declaration hierarchy:
            CLI override > file (if any) > code default.
        2. Configs are, by default, useful.
            This means, by default, declared configs (both standard and supplemental)
            are loaded (where "loaded" here means loaded based on the entire
            declarative hierarchy). However, the CLI override can be disabled by
            setting :obj:`override` to :obj:`None`.
        3. Persistence of configs is *typically* desirable.
            This means that, by default, configs are serialized (to enable the middle
            of the declarative hierarchy), but skipping serialization is made easy (use
            :obj:`skip_write` to disable for particular configs, or set :obj:`write` is
            :obj:`False` to disable for all configs).
        4. Configs often fall into neat groups that should be treated a particular way.
            For example, one group skips overriding, while another skips serializing.
            Both :obj:`config_ids` and :obj:`skip_write` enable such group declarations.

    This default factory is equivalent to:

        1. Calling :func:`~coma.hooks.config_hook.initialize_factory()` on
        the specified configs, passing in :obj:`raise_on_fnf` directly.

        2. Then, calling :func:`~coma.hooks.config_hook.override_factory()`, passing
        in :obj:`override_instance_key`, and :obj:`override` directly.

        3. Then, only if :obj:`write` is :obj:`True`,
        calling :func:`~coma.hooks.config_hook.write_factory()` on all specified
        configs **not** also in :obj:`skip_write`, passing in :obj:`write_instance_key`,
        :obj:`resolve`, and :obj:`overwrite` directly.

    Example:

        Override only one group and configs and serialize only another group::

            coma.command(
                ...,
                config_hook=(
                    default_factory("override", "only", "configs", write=False),
                    default_factory("write", "only", "configs", override=None),
                )
            )

    Args:
        *config_ids (:data:`~coma.config.base.ConfigID`): Configs on which to apply
            the config hook. If empty, do so for **all** configs registered with
            the command currently being executed.
        raise_on_fnf (bool):
            Passed directly to :func:`coma.hooks.config_hook.initialize_factory()`.
        override_instance_key (:data:`~coma.config.base.InstanceKey`, optional):
            Passed directly to :func:`coma.hooks.config_hook.override_factory()`.
        override (:data:`~coma.hooks.config_hook.OverrideProtocolOrSentinels`):
            Passed directly to :func:`coma.hooks.config_hook.override_factory()`.
        skip_write (typing.Container[:data:`~coma.config.base.ConfigID`], optional): If
            :obj:`write` is :obj:`True`, skip serialization for each of these configs.
        write (bool): Whether to serialize configs.
        write_instance_key (:data:`~coma.config.base.InstanceKey`, optional):
            Passed directly to :func:`coma.hooks.config_hook.write_factory()`.
        resolve (bool):
            Passed directly to :func:`coma.hooks.config_hook.write_factory()`.
        overwrite (bool):
            Passed directly to :func:`coma.hooks.config_hook.write_factory()`.

    Returns:
        :data:`~coma.hooks.base.Hook`: A hook with :obj:`config_hook` semantics.

    Raises:
        Various: As may be raised by the underlying components.

    See also:
        * :func:`coma.hooks.parser_hook.default_factory()`
        * :func:`coma.hooks.init_hook.default_factory()`
        * :func:`coma.hooks.config_hook.initialize_factory()`
        * :func:`coma.hooks.config_hook.override_factory()`
        * :func:`coma.hooks.config_hook.write_factory()`
    """

    def hook(data: InvocationData) -> None:
        # These loops have to be sequential. First init all, then override all, then
        # maybe write all, then convert to primitive.
        for config_id in config_ids or data.parameters.get_all_configs():
            initialize_factory(config_id, raise_on_fnf=raise_on_fnf)(data)
        for config_id in config_ids or data.parameters.get_all_configs():
            override_factory(config_id, override_instance_key, override)(data)
        for config_id in config_ids or data.parameters.get_all_configs():
            write_hook = write_factory(
                config_id,
                instance_key=write_instance_key,
                resolve=resolve,
                overwrite=overwrite,
            )
            if not write or config_id in (skip_write or []):
                write_hook = identity
            write_hook(data)

    return hook


def preload(
    data: InvocationData,
    *config_ids,
    limited: bool = False,
    raise_on_fnf: bool = False,
    override: Optional[Union[OverrideProtocol, GeneralSentinel]] = SENTINEL,
) -> None:
    """
    Convenience wrapper around :func:`coma.hooks.config_hook.default_factory()`.

    Configs are declarative. They follow the following declaration hierarchy:
    CLI override > file (if any) > code default. "Load" here means loading based
    on the entire declarative hierarchy. "Pre" here refers to the idea that this
    procedure is typically called in a user-defined :obj:`pre_config_hook` to
    load some configs (typically supplemental configs) as a preprocessing step
    before the main :obj:`config_hook`.

    Preloading **never** serializes any of the configs. CLI is enabled by default,
    but can be disabled by setting :obj:`override` to :obj:`None`. If :obj:`limited`
    is :obj:`True`, limit override exclusivity checks to just the :obj:`config_ids`.
    Otherwise, perform exclusivity checks on **all** configs in :obj:`data.parameters`
    (which requires initializing all configs).

    Example:

        Preload some supplemental configs in :obj:`pre_config_hook`::

            def pre_config_hook(data: InvocationData) -> InvocationData:
                preload_ids = ["supplemental_cfg_1", "supplemental_cfg_2"]
                preload(data, *preload_ids)
                cfgs = data.parameters.select(*preload_ids)
                do_something_with(cfgs)

                # This prevents further processing of these configs.
                data.parameters.delete(*preload_ids)

            @command(
                name="command_name",
                pre_config_hook=pre_config_hook,
                ...,
                supplemental_cfg_1=...,
                supplemental_cfg_2=...,
            )
            def my_cmd(...):
                ...

    Args:
        data (:class:`~coma.hooks.base.InvocationData`): Invocation data received
            as input to whichever invocation hook (typically :obj:`pre_config_hook`)
            :obj:`preload()` is being called in.
        *config_ids (:data:`~coma.config.base.ConfigID`): Configs to preload. If empty,
            do so for **all** configs in :obj:`data.parameters`.
            Passed directly to :func:`coma.hooks.config_hook.default_factory()`.
        limited (bool): Whether to limit override exclusivity checks to just the
            :obj:`config_ids`
        raise_on_fnf (bool): Passed directly to :func:`coma.hooks.config_hook.default_factory()`.
        override (:data:`~coma.hooks.config_hook.OverrideProtocolOrSentinels`):
            Passed directly to :func:`coma.hooks.config_hook.default_factory()`.

    Returns:
        None: :obj:`data` is modified in-place and preloaded configs should be
        retrieved directly from it.

    Raises:
        ValueError: If :obj:`limited` is :obj:`True` but :obj:`config_ids` is empty.
        Others: As may be raised by :func:`coma.hooks.config_hook.default_factory()`.

    See also:
        * :func:`coma.hooks.config_hook.default_factory()`
    """
    if limited and not config_ids:
        raise ValueError(f"In limited mode, at least one config ID must be provided.")
    kwargs = dict(raise_on_fnf=raise_on_fnf, write=False)
    if limited:
        # Restrict to just initializing and overriding the given configs.
        default_factory(*config_ids, override=override, **kwargs)(data)
    else:
        # Initialize every config, but don't enable override yet.
        default_factory(override=None, **kwargs)(data)
        # Restrict to just overriding the given configs.
        default_factory(*config_ids, override=override, **kwargs)(data)
