"""Config hook utilities, factories, and defaults."""

from typing import Any, Callable, Dict, List, Optional

from omegaconf.errors import ValidationError

from ..config import default_default, default_dest, to_dict
from ..config.io import dump, Extension, maybe_add_ext, load

from .utils import hook, sequence


def single_load_and_write_factory(
    config_id: str,
    *,
    parser_attr_name: Optional[str] = None,
    default_file_path: Optional[str] = None,
    default_ext: Extension = Extension.YAML,
    raise_on_fnf: bool = False,
    write_on_fnf: bool = True,
    resolve: bool = False,
) -> Callable[..., Dict[str, Any]]:
    """Factory for creating a config hook that initializes a config object.

    The created config hook has the following behaviour:

        First, an attempt is made to load the config object corresponding to
        :obj:`config_id` from file.

            .. note::

                If a file path is provided as a command line argument (assuming
                the presence of :func:`~coma.hooks.parser_hook.multi_config` or
                equivalent functionality), that path is used. Otherwise,
                :obj:`default_file_path` is used as a default. If
                :obj:`default_file_path` is :obj:`None`, a sensible default is
                derived from :obj:`config_id` instead.

                In any case, if the provided or derived file path has no file
                extension, :obj:`default_ext` is used as a default extension.

        If loading the file fails due to a :obj:`FileNotFoundError`, then:

            If :obj:`raise_on_fnf` is :obj:`True`, the error is re-raised.

            If :obj:`raise_on_fnf` is :obj:`False`, a config object with default
            values is initialized, and then:

                If :obj:`write_on_fnf` is :obj:`True`, the newly-initialized
                config object with default values is written to the file.

                    If :obj:`resolve` is :obj:`True`, the underlying ``omegaconf``
                    handler attempts to resolve variable interpolation before writing.

        The created config hook raises:

            :KeyError:
                If :obj:`config_id` does not match any known config identifier
            :ValueError:
                If the file extension is not supported. See
                :class:`~coma.config.io.Extension` for supported types.
            :FileNotFoundError:
                If :obj:`raise_on_fnf` is :obj:`True` and the config file was not found
            :Others:
                As may be raised by the underlying ``omegaconf`` handler

    Example:

        Fail fast when encountering a :obj:`FileNotFoundError`::

            coma.initiate(..., config_hook=single_factory(..., raise_on_fnf=True))

    Args:
        config_id (str): A config identifier
        parser_attr_name (str): The :obj:`known_args` attribute representing
            this config's file path parser argument. If :obj:`None`, a sensible
            default is derived from :func:`~coma.config.utils.default_dest`.
        default_file_path (str): An optional default value for the config file
            path. If :obj:`None`, a sensible default is derived from
            :func:`~coma.config.utils.default_default`.
        default_ext (coma.config.io.Extension): The extension to use when the
            provided file path lacks one
        raise_on_fnf (bool): If :obj:`True`, raises a :obj:`FileNotFoundError`
            if the config file was not found. If :obj:`False`, a config object
            with default values is initialized instead of failing outright.
        write_on_fnf (bool): If the config file was not found and
            :obj:`raise_on_fnf` is :obj:`False`, then :obj:`write_on_fnf`
            indicates whether to write the config object to the provided file
        resolve (bool): If about to write a config object to file, then
            :obj:`resolve` indicates whether the underlying ``omegaconf``
            handler attempts to resolve variable interpolation beforehand

    Returns:
        A config hook

    See also:
        * :func:`~coma.config.utils.default_dest`
        * :func:`~coma.config.utils.default_default`
        * :func:`~coma.hooks.parser_hook.single_config_factory`
    """

    def try_load(config: Any, file_path=None) -> Any:
        try:
            return load(config, file_path)
        except ValidationError:
            raise ValueError(
                f"Config '{config_id}' of type '{config}' is not OmegaConf compatible."
            )

    @hook
    def _hook(known_args, configs: Dict[str, Any]) -> Dict[str, Any]:
        config = configs[config_id]
        default_ = default_file_path
        default_ = default_default(config_id) if default_ is None else default_
        attr = parser_attr_name
        attr = default_dest(config_id) if attr is None else attr
        file_path = getattr(known_args, attr, default_) or default_
        file_path = maybe_add_ext(file_path, default_ext)
        try:
            config = try_load(config, file_path)
        except FileNotFoundError:
            if raise_on_fnf:
                raise
            config = try_load(config)
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
) -> Callable[..., Dict[str, Any]]:
    """Factory for creating a config hook that is a sequence of single factory calls.

    Equivalent to calling :func:`~coma.hooks.config_hook.single_load_and_write_factory`
    for each config with the other arguments passed along. See
    :func:`~coma.hooks.config_hook.single_load_and_write_factory` for details.

    Returns:
        A config hook
    """

    @hook
    def _hook(known_args, configs: Dict[str, Any]) -> Dict[str, Any]:
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
            configs_list: List[Dict[str, Any]] = sequence(*fns, return_all=True)(
                known_args=known_args,
                configs=configs,
            )
        return to_dict(*[(cid, c) for cd in configs_list for cid, c in cd.items()])

    return _hook


default = multi_load_and_write_factory()
"""Default config hook function.

An alias for calling :func:`~coma.hooks.config_hook.multi_load_and_write_factory`
with default arguments.
"""
