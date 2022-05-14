"""Utilities for serializing configs to file."""
from enum import auto, Enum
import json
from pathlib import Path
from typing import Any, Optional

from omegaconf import OmegaConf


class Extension(Enum):
    """Supported config serialization file extensions:

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
    """If :obj:`file_path` lacks a file extension, appends :obj:`ext`.

    Args:
        file_path (str): Any file path
        ext (coma.config.io.Extension): An extension to possibly append

    Returns:
        A file path with an extension if one was lacking
    """
    path = Path(file_path)
    return str(path) if path.suffix else str(path.with_suffix(f".{ext.name.lower()}"))


def is_json_ext(file_path: str) -> bool:
    """Returns whether :obj:`file_path` has a JSON-like file extension.

    Args:
        file_path (str): Any file path

    Return:
        Whether :obj:`file_path` has a JSON-like file extension
    """
    return _is_ext(Path(file_path), Extension.JSON)


def is_yaml_ext(file_path: str, *, strict: bool = False) -> bool:
    """Returns whether :obj:`file_path` has a YAML-like file extension.

    Args:
        file_path (str): Any file path
        strict (bool): Whether to match :obj:`Extension.YAML` exactly or also
            allow matching against other valid YAML-like file extensions

    Returns:
        Whether :obj:`file_path` has a YAML-like file extension
    """
    return is_ext(file_path, Extension.YAML, Extension.YML, strict=strict)


def is_yml_ext(file_path: str, *, strict: bool = False) -> bool:
    """Returns whether :obj:`file_path` has a YAML-like file extension.

    Args:
        file_path (str): Any file path
        strict (bool): Whether to match :obj:`Extension.YML` exactly or also
            allow matching against other valid YAML-like file extensions

    Returns:
        Whether :obj:`file_path` has a YAML-like file extension
    """
    return is_ext(file_path, Extension.YML, Extension.YAML, strict=strict)


def is_ext(
    file_path: str, which: Extension, *alts: Extension, strict: bool = False
) -> bool:
    """Returns whether :obj:`file_path` has a file extension from a specific set.

    Args:
        file_path (str): Any file path
        which (coma.config.io.Extension): The primary file extension to test against
        *alts (coma.config.io.Extension): A set of alternative file extensions
            to test against
        strict (bool): Whether to match :obj:`which` exactly or also allow
            matching against any extensions in :obj:`alts`

    Returns:
        Whether :obj:`file_path` has a file extension from a specific set
    """
    path = Path(file_path)
    if strict:
        return _is_ext(path, which)
    return _is_ext(path, which) or any([_is_ext(path, alt) for alt in alts])


def _is_ext(path: Path, which: Extension) -> bool:
    suffix = path.suffix
    return suffix[1:].lower() == which.name.lower() if suffix else False


def load(config: Any, file_path: Optional[str] = None) -> Any:
    """Initializes a config object and possibly updates its attributes from file.

    Initializes a default config object from :obj:`config` using ``omegaconf``.
    If :obj:`file_path` is not :obj:`None`, attempts to also load a config object
    from file. If that succeeds, then attempts to update the default config
    object's attributes with attributes of the config object loaded from file.

    Args:
        config (typing.Any): Any config type or object to create a default config
        file_path (str): An optional file path from which default attributes can
            be updated

    Returns:
        A new config object, possibly updated from file

    Raises:
        ValueError: If :obj:`file_path` has an unsupported file extension
        IOError: If there are issues relating to reading from :obj:`file_path`
        Others: As may be raised by the underlying ``omegaconf`` handler
    """
    default_config = OmegaConf.create(config)
    if file_path is None:
        return default_config

    if is_json_ext(file_path):
        with open(file_path, "r") as f:
            dict_config = OmegaConf.create(json.load(f))
    elif is_yaml_ext(file_path):
        dict_config = OmegaConf.load(file_path)
    else:
        raise ValueError(f"Config only supports YAML and JSON formats: {file_path}")

    return OmegaConf.unsafe_merge(default_config, dict_config)


def dump(config: Any, file_path: str, *, resolve: bool = False) -> None:
    """Serializes a config to file.

    Args:
        config (typing.Any): Any valid ``omegaconf`` config object to serialize
        file_path (str): A file path for serializing :obj:`config`
        resolve (bool): Whether the underlying ``omegaconf`` handler should
            `resolve variable interpolation`_ in the configuration

    Raises:
        ValueError: If :obj:`file_path` has an unsupported file extension
        IOError: If there are issues relating to writing to :obj:`file_path`
        Others: As may be raised by the underlying ``omegaconf`` handler

    .. _resolve variable interpolation:
        https://omegaconf.readthedocs.io/en/2.1_branch/usage.html#variable-interpolation
    """
    if is_json_ext(file_path):
        as_dict = OmegaConf.to_container(config, resolve=resolve, enum_to_str=True)
        with open(file_path, "w") as f:
            json.dump(as_dict, f, indent=4)
    elif is_yaml_ext(file_path):
        OmegaConf.save(config, file_path, resolve=resolve)
    else:
        raise ValueError(f"Config only supports YAML and JSON formats: {file_path}")
