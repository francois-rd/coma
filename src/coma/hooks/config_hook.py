"""Core config hooks and utilities."""
from typing import Callable, List, Optional

from coma.config import (
    ConfigDict,
    ConfigID,
    default_default,
    default_dest,
    to_dict,
)
from coma.config.io import dump, Extension, maybe_add_ext, load

from .utils import hook, sequence


def single_load_and_write_factory(
    config_id: ConfigID,
    *,
    parser_attr_name: Optional[str] = None,
    default_file_path: Optional[str] = None,
    default_ext: Extension = Extension.YAML,
    raise_on_fnf: bool = False,
    write_on_fnf: bool = True,
    resolve: bool = False,
) -> Callable[..., ConfigDict]:
    """Factory for creating a config hook instantiating a configuration object.

    The created config hook has the following behaviour:

        First, an attempt is made to instantiate the configuration type
        corresponding to the :obj:`config_id` identifier from file.

            .. note::

                If a file path is provided as a command line argument, that
                path is used. Otherwise, :obj:`default_file_path` is used as
                a default. If :obj:`default_file_path` is `None`, a sensible
                default is derived from :obj:`config_id` instead.

                In any case, if the provided or derived file path has no file
                extension, the extension :obj:`default_ext` is used as a default.

        If loading the file fails due to a `FileNotFoundError`, then:

            If :obj:`raise_on_fnf` is `True`, the error is re-raised.

            If :obj:`raise_on_fnf` is `False`, a configuration object
            with default values is instantiated, and then:

                If :obj:`write_on_fnf` is `True`, the newly-instantiated
                configuration object with default values is written to the file.
                If :obj:`resolve` is `True`, the underlying OmegaConf handler
                attempts to resolve variable interpolation before writing.

        The created config hook raises:

            KeyError:
                If :obj:`config_id` does not correspond to a known configuration type
            ValueError:
                If the file extension is not supported. See
                :class:`coma.config.io.Extension` for supported types.
            FileNotFoundError:
                If :obj:`raise_on_fnf` is `True` and the configuration file was
                not found
            Others:
                As may be raised by the underlying OmegaConf handler

    Example:
        Fail fast when encountering a `FileNotFoundError`::

            coma.initiate(..., config_hook=single_factory(..., raise_on_fnf=True))

    Args:
        config_id: A configuration identifier
        parser_attr_name: The :obj:`known_args` attribute representing this
            configuration's file path parser argument. If `None`, derives a
            sensible default from :func:`coma.config.default_dest`.
        default_file_path: An optional default value for the configuration file
            path. If `None`, derives a sensible default from
            :func:`coma.config.default_file_path`.
        default_ext: The extension to use when the provided file path has none
        raise_on_fnf: If `True`, raises a `FileNotFoundError` if the
            configuration file was not found. If `False`, a configuration object
            with default values is instantiated instead of failing outright.
        write_on_fnf: If the configuration file was not found and
            :obj:`raise_on_fnf` is `False`, then :obj:`write_on_fnf` indicates
            whether to write the configurations to the provided file
        resolve: If about to write configurations to file, then :obj:`resolve`
            indicates whether the underlying OmegaConf handler attempts to
            resolve variable interpolation beforehand

    Returns:
        A config hook

    See also:
        * :func:`coma.config.default_dest`
        * :func:`coma.config.default_default`
        * :func:`coma.hooks.parser_hook.single_config_factory`
        * TODO(invoke; protocol) for details on config hooks
    """

    @hook
    def _hook(known_args, configs: ConfigDict) -> ConfigDict:
        config = configs[config_id]
        default_ = default_file_path
        default_ = default_default(config_id) if default_ is None else default_
        attr = parser_attr_name
        attr = default_dest(config_id) if attr is None else attr
        file_path = getattr(known_args, attr, default_) or default_
        file_path = maybe_add_ext(file_path, default_ext)
        try:
            config = load(config, file_path)
        except FileNotFoundError:
            if raise_on_fnf:
                raise
            config = load(config)
            if write_on_fnf:
                dump(config, file_path, resolve=resolve)
        return to_dict((config_id, config))

    return _hook


def multi_load_and_write_factory(
    *,
    default_ext: Extension = Extension.YAML,
    raise_on_fnf: bool = False,
    write_on_fnf: bool = True,
    resolve: bool = False,
) -> Callable[..., ConfigDict]:
    """Factory for creating a sequence of config hooks.

    Equivalent to calling :func:`~coma.hooks.config_hook.single_load_and_write_factory`
    for each configuration in :obj:`configs` with the other arguments passed along.

    See :func:`coma.hooks.config_hook.single_load_and_write_factory` for details.
    """

    @hook
    def _hook(known_args, configs: ConfigDict) -> ConfigDict:
        fns = []
        for config_id in configs:
            fns.append(
                single_load_and_write_factory(
                    config_id,
                    default_ext=default_ext,
                    raise_on_fnf=raise_on_fnf,
                    write_on_fnf=write_on_fnf,
                    resolve=resolve,
                )
            )
        configs_list = []
        if fns:
            configs_list: List[ConfigDict] = sequence(*fns, return_all=True)(
                known_args=known_args,
                configs=configs,
            )
        return to_dict(*[(cid, c) for cd in configs_list for cid, c in cd.items()])

    return _hook


default = multi_load_and_write_factory()
"""Default config hook function.

An alias for :func:`coma.hooks.config_hook.multi_load_and_write_factory` called
with default arguments.
"""
