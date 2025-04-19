"""Utilities for serializing configs to file."""

from argparse import ArgumentParser
from typing import Any, Optional
from enum import auto, Enum
from pathlib import Path
import json

import omegaconf
from omegaconf import OmegaConf

from .base import Config, ConfigID, InstanceKey, InstanceKeys


class Extension(Enum):
    """
    Supported config serialization file extensions:

    =========== ==============
    Value       Meaning
    =========== ==============
    :obj:`YAML` :obj:`".yaml"`
    ----------- --------------
    :obj:`YML`  :obj:`".yml"`
    ----------- --------------
    :obj:`JSON` :obj:`".json"`
    =========== ==============
    """

    YAML = auto()
    YML = auto()
    JSON = auto()


def maybe_add_ext(file_path: str, ext: Extension) -> str:
    """
    If :obj:`file_path` lacks a file extension, appends :obj:`ext`.

    Args:
        file_path (str): Any file path.
        ext (:class:`~coma.config.io.Extension`): An extension to possibly append.

    Returns:
        str: A file path with an extension if one was lacking.
    """
    path = Path(file_path)
    return str(path) if path.suffix else str(path.with_suffix(f".{ext.name.lower()}"))


def is_json_ext(file_path: str) -> bool:
    """
    Returns whether :obj:`file_path` has a JSON-like file extension.

    Args:
        file_path (str): Any file path.

    Return:
        bool: Whether :obj:`file_path` has a JSON-like file extension.
    """
    return _is_ext(Path(file_path), Extension.JSON)


def is_yaml_ext(file_path: str, *, strict: bool = False) -> bool:
    """
    Returns whether :obj:`file_path` has a YAML-like file extension.

    Args:
        file_path (str): Any file path.
        strict (bool): Whether to match :obj:`Extension.YAML` exactly or also
            allow matching against other valid YAML-like file extensions.

    Returns:
        bool: Whether :obj:`file_path` has a YAML-like file extension.
    """
    return is_ext(file_path, Extension.YAML, Extension.YML, strict=strict)


def is_yml_ext(file_path: str, *, strict: bool = False) -> bool:
    """
    Returns whether :obj:`file_path` has a YAML-like file extension.

    Args:
        file_path (str): Any file path.
        strict (bool): Whether to match :obj:`Extension.YML` exactly or also
            allow matching against other valid YAML-like file extensions.

    Returns:
        bool: Whether :obj:`file_path` has a YAML-like file extension.
    """
    return is_ext(file_path, Extension.YML, Extension.YAML, strict=strict)


def is_ext(
    file_path: str, which: Extension, *alts: Extension, strict: bool = False
) -> bool:
    """
    Returns whether :obj:`file_path` has a file extension from a specific set.

    Args:
        file_path (str): Any file path.
        which (:class:`~coma.config.io.Extension`): The primary file extension
            to test against.
        *alts (:class:`~coma.config.io.Extension`): A set of alternative file
            extensions to test against.
        strict (bool): Whether to match :obj:`which` exactly or also allow
            matching against any extensions in :obj:`alts`.

    Returns:
        bool: Whether :obj:`file_path` has a file extension from a specific set.
    """
    path = Path(file_path)
    if strict:
        return _is_ext(path, which)
    return _is_ext(path, which) or any([_is_ext(path, alt) for alt in alts])


def _is_ext(path: Path, which: Extension) -> bool:
    suffix = path.suffix
    return suffix[1:].lower() == which.name.lower() if suffix else False


def initialize(
    config: Config,
    file_path: Optional[str] = None,
    base_instance_key: InstanceKey = InstanceKeys.BASE,
    file_instance_key: InstanceKey = InstanceKeys.FILE,
) -> None:
    """
    Initializes a config object and possibly updates its attributes from file.

    Initializes a base config object from :obj:`config` using ``omegaconf``.
    If :obj:`file_path` is not :obj:`None`, attempts to also load a config object
    from file. If that succeeds, then attempts to update the base config object's
    attributes with attributes of the config object loaded from file.

    If either step has an already cached instance (based on the given instance keys),
    the cached value is used instead.

    Args:
        config (:class:`~coma.config.base.Config`): The config to initialize.
        file_path (:obj:`str`, optional): If not None, file path from which the base
            instance's attributes can be updated.
        base_instance_key (:data:`~coma.config.base.InstanceKey`): The instance key
            of the base config instance.
        file_instance_key (:data:`~coma.config.base.InstanceKey`): The instance key
            of the config instance updated from file data.

    Returns:
        None: The :obj:`config` object is updated in-place.

    Raises:
        ValueError: If :obj:`file_path` has an unsupported file extension.
        IOError: If there are issues relating to reading from :obj:`file_path`.
        Others: As may be raised by the underlying ``omegaconf`` handler.
    """
    if config.has(base_instance_key):
        default_config = config.get(base_instance_key)
    else:
        default_config = OmegaConf.create(config.back_end)
        config.set(base_instance_key, default_config)
    if file_path is None or config.has(file_instance_key):
        return
    if is_json_ext(file_path):
        with open(file_path, "r") as f:
            file_config = OmegaConf.create(json.load(f))
    elif is_yaml_ext(file_path):
        file_config = OmegaConf.load(file_path)
    else:
        raise ValueError(f"Config only supports YAML and JSON formats: {file_path}")

    if isinstance(default_config, omegaconf.ListConfig):
        if isinstance(file_config, omegaconf.DictConfig) and not {**file_config}:
            # User is asking for a ListConfig. OmegaConf.create() defaults to a
            # dict on empty (i.e., if the file does not exist or is an empty file).
            # Here, we detect that user (a) asks for a list and (b) the file config
            # is empty (for whatever reason), so we fix this edge case directly.
            file_config = OmegaConf.create([])
    if type(default_config) is not type(file_config):
        raise ValueError(
            f"Type mismatch between requested config and config loaded from file."
        )

    # Because of unsafe_merge(), we need to make a copy of default config here.
    file_config = OmegaConf.unsafe_merge(OmegaConf.create(default_config), file_config)
    config.set(file_instance_key, file_config)
    return


def write(
    config: Config,
    file_path: str,
    *,
    key: Optional[InstanceKey] = None,
    resolve: bool = False,
) -> None:
    """
    Serializes a config to file.

    Args:
        config (:class:`~coma.config.base.Config`): The config to serialize.
        file_path (str): A file path for serializing :obj:`config`.
        key (:data:`~coma.config.base.InstanceKey`, optional): The specific
            :obj:`config` instance to serialize. If :obj:`None`, the latest
            instance is used.
        resolve (bool): Whether the underlying ``omegaconf`` handler should
            `resolve variable interpolation`_ before serializing.

    Raises:
        ValueError: If :obj:`file_path` has an unsupported file extension.
        IOError: If there are issues relating to writing to :obj:`file_path`.
        Others: As may be raised by the underlying ``omegaconf`` handler.

    .. _resolve variable interpolation:
        https://omegaconf.readthedocs.io/en/2.1_branch/usage.html#variable-interpolation
    """
    key = key or config.get_latest_key()
    if is_json_ext(file_path):
        Path(file_path).resolve().parent.mkdir(parents=True, exist_ok=True)
        # Might seem like we can skip the create() and to_container() when already
        # a primitive, but that removes the ability to resolve and change enums.
        # It also prevents dataclass from being converted to plain dictionaries.
        config = config.from_primitive(key)
        container = OmegaConf.to_container(config, resolve=resolve, enum_to_str=True)
        with open(file_path, "w") as f:
            json.dump(container, f, indent=4)
    elif is_yaml_ext(file_path):
        Path(file_path).resolve().parent.mkdir(parents=True, exist_ok=True)
        # This, on the other hand, is perfectly OK to receive a primitive.
        OmegaConf.save(config.get(key), file_path, resolve=resolve)
    else:
        raise ValueError(f"Config only supports YAML and JSON formats: {file_path}")


class PersistenceManager:
    def __init__(self, default_extension: Extension = Extension.YAML):
        """
        Interface between ``argparse`` and config IO functionality.

        Args:
            default_extension (:class:`~coma.config.io.Extension`): The default file
                extension to use for all configs not explicitly registered.
        """
        self.configs = {}
        self.default_extension = default_extension

    def register(
        self,
        config_id: ConfigID,
        extension: Optional[Extension] = None,
        *names_or_flags: str,
        **kwargs: Any,
    ) -> "PersistenceManager":
        """
        Registers parameters defining a file path argument for :obj:`config_id`
        that can later be added to an ``argparse.ArgumentParser`` via
        :meth:`~coma.config.io.PersistenceManager.add_path_argument()`.

        Args:
            config_id (:data:`~coma.config.base.ConfigID`): The config identifier
                for which to register file path argument parameters.
            extension (:class:`~coma.config.io.Extension`, optional): The extension
                to use if the provided file path lacks one. If :obj:`None`, defaults
                to :attr:`~coma.config.io.PersistenceManager.default_extension`.
            *names_or_flags (str): Passed to `add_argument()`_. A sensible
                default is used if empty.
            **kwargs (Any): Passed to `add_argument()`_. A sensible default is
                used for many parameters if missing. For details, see
                :meth:`~coma.config.io.PersistenceManager.add_path_argument()`

        .. note::

            Registering a particular :obj:`config_id` does **not** guarantee/force that
            the config will be serialized, but rather only explicitly determines the
            parameters that get passed to `add_argument()`_ (instead of relying on the
            sensible defaults that are otherwise provided).

        Returns:
            :class:`~coma.config.io.PersistenceManager`: This persistence manager
            (to enable fluent interfacing).

        See also:
            * :meth:`~coma.config.io.PersistenceManager.get_file_path()`

        .. _add_argument():
            https://docs.python.org/3/library/argparse.html#the-add-argument-method
        """
        extension = extension or self.default_extension
        self.configs[config_id] = (extension, names_or_flags, kwargs)
        return self

    def _get_or_default(self, config_id: ConfigID) -> tuple[Extension, tuple, dict]:
        return self.configs.get(config_id, (self.default_extension, (), {}))

    def add_path_argument(self, parser: ArgumentParser, config_id: ConfigID) -> None:
        """
        Adds a file path argument for :obj:`config_id` to :obj:`parser`.

        Specifically, calls `add_argument()`_ on :obj:`parser` with the parameters
        :meth:`~coma.config.io.PersistenceManager.register()` ed for :obj:`config_id`.
        If :obj:`config_id` is unregistered, or if any of the following parameters
        are missing from the registration, sensible defaults are used instead when
        calling `add_argument()`_::

            names_or_flags: based on 'config_id'
            type: str
            metavar: "FILE"
            dest: 'config_id'
            default: based on 'config_id' + 'extension'
            help: based on 'config_id'

        Additional parameters beyond these can also be registered.

        .. note::

            These parameters enable the later retrieval of any user-specified file
            path using :meth:`~coma.config.io.PersistenceManager.get_file_path()`
            or a default file path if the user fails to explicitly give a one.

        Args:
            parser (argparse.ArgumentParser): The parser for which to add a
                file path arguments for the given :obj:`config_id`.
            config_id (:data:`~coma.config.base.ConfigID`): The config identifier
                for which to add file path arguments to :obj:`parser`.

        See also:
            * :meth:`~coma.config.io.PersistenceManager.register()`
            * :meth:`~coma.config.io.PersistenceManager.get_file_path()`

        .. _add_argument():
            https://docs.python.org/3/library/argparse.html#the-add-argument-method
        """
        extension, names_or_flags, kwargs = self._get_or_default(config_id)
        names_or_flags = names_or_flags or [f"--{config_id.replace('_', '-')}-path"]
        kwargs.setdefault("type", str)
        kwargs.setdefault("metavar", "FILE")
        kwargs.setdefault("default", self._default_default(config_id, extension))
        kwargs.setdefault("dest", self._default_dest(config_id))
        kwargs.setdefault("help", f"{config_id} file path")
        parser.add_argument(*names_or_flags, **kwargs)

    def get_file_path(self, config_id: ConfigID, known_args: Any) -> str:
        """
        Retrieves the file path for :obj:`config_id` from :obj:`known_args`.

        Assumes that :obj:`known_args` is the :obj:`namespace` return object
        (the **first** return value) of `parse_known_args()`_ from the :obj:`parser`
        on which a file path for :obj:`config_id` was added using
        :meth:`~coma.config.io.PersistenceManager.add_path_argument()`. However,
        a sensible default is returned even if no such prior call occurred.

        Args:
            config_id (:data:`~coma.config.base.ConfigID`): The config identifier
                for which to retrieve a file path from :obj:`known_args`.
            known_args (typing.Any): Typically, the :obj:`namespace` return object
                (the **first** return value) of `parse_known_args()`_.

        Returns:
            str: The retrieved file path for :obj:`config_id`.

        See also:
            * :meth:`~coma.config.io.PersistenceManager.register()`

        .. _parse_known_args():
            https://docs.python.org/3/library/argparse.html#partial-parsing
        """
        extension, _, kwargs = self._get_or_default(config_id)
        dest = kwargs.get("dest", self._default_dest(config_id))
        default = kwargs.get("default", self._default_default(config_id, extension))
        return maybe_add_ext(getattr(known_args, dest, default), extension)

    @staticmethod
    def _default_dest(config_id: ConfigID) -> str:
        return f"{config_id}_path"

    @staticmethod
    def _default_default(
        config_id: ConfigID, extension: Extension = Extension.YAML
    ) -> str:
        return maybe_add_ext(str(config_id), extension)
