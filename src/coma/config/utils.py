"""Config utilities."""
from collections import OrderedDict
import sys
from typing import Any, Dict, Tuple, TypeVar, Union


ConfigID = TypeVar("ConfigID")
ConfigDict = Dict[ConfigID, Any]
ConfigOrIdAndConfig = Union[Any, Tuple[ConfigID, Any]]


_dict_type = OrderedDict if sys.version_info < (3, 7) else dict


def default_id(config: Any) -> str:
    """Returns the default identifier of :obj:`config`.

    The default identifier is derived from :obj:`config`'s type's name.

    Args:
        config: Any configuration type or object

    Returns:
        The default identifier of :obj:`config`
    """
    if not isinstance(config, type):
        config = type(config)
    return config.__name__.lower()


def default_attr(config_id: ConfigID) -> str:
    """Returns the default file path parser argument attribute of :obj:`config_id`.

    Returns the attribute of the :func:`argparse.ArgumentParser.parse_known_args`
    return object representing the default file path parser argument
    corresponding to :obj:`config_id`.

    Args:
        config_id: A configuration identifier

    Returns:
        The default file path parser argument attribute of :obj:`config_id`
    """
    return f"{config_id}_path"


def default_default(config_id: ConfigID) -> str:
    """Returns the default file path parser argument default value for :obj:`config_id`.

    Returns the default value for the :obj:`default` keyword argument to
    :class:`argparse.ArgumentParser.add_argument` for the file path parser
    argument corresponding to :obj:`config_id`.

    Args:
        config_id: A configuration identifier

    Returns:
        The default file path parser argument default value for :obj:`config_id`
    """
    return f"{config_id}"


def default_flag(config_id: ConfigID) -> str:
    """Returns the default file path parser argument flag value for :obj:`config_id`.

    Returns the default value for the :obj:`names_or_flags` variadic argument to
    :class:`argparse.ArgumentParser.add_argument` for the file path parser
    argument corresponding to :obj:`config_id`.

    Args:
        config_id: A configuration identifier

    Returns:
        The default file path parser argument flag value for :obj:`config_id`
    """
    return f"--{config_id}-path"


def default_help(config_id: ConfigID) -> str:
    """Returns the default file path parser argument help value for :obj:`config_id`.

    Returns the default value for the :obj:`help` keyword argument to
    :class:`argparse.ArgumentParser.add_argument` for the file path parser
    argument corresponding to :obj:`config_id`.

    Args:
        config_id: A configuration identifier

    Returns:
        The default file path parser argument help value for :obj:`config_id`
    """
    return f"{config_id} file path"


def to_dict(*configs: ConfigOrIdAndConfig) -> ConfigDict:
    """Converts configurations provided in raw or tuple format to dictionary format.

    :obj:`configs` should be of the form `<conf>` or `(<id>, <conf>)`, where
    `<conf>` is a ``dataclass`` or `attrs`_ class or instance representing a
    configuration and `<id>` is any identifier for the configuration whose type
    can be used as a `dict` key. If `<id>` is omitted, an identifier is derived
    from `<conf>`'s type name using :func:`~coma.config.default_id`. That is,
    specifying just `<conf>` is a shorthand for `(default_id(<conf>), <conf>)`.

    .. note::

        For each :func:`~coma.core.register.register`ed sub-command,
        configuration identifiers need to be unique for that sub-command.

    .. note::

        `dataclasses`_ is a backport of ``dataclasses`` for Python 3.6

    Returns:
        Configurations in :class:`ConfigDict` format. That is, a dictionary with
        `<id>` keys and `<conf>` values.

        .. note::

            The dictionary is guaranteed to be insertion-ordered, even in Python < 3.7.

    See also:
        * :func:`~coma.config.default_id`
        * :func:`~coma.core.initiate.initiate`
        * :func:`~coma.core.register.register`

    .. _attrs:
        https://pypi.org/project/attrs/

    .. _dataclasses:
        https://pypi.org/project/dataclasses/
    """
    result = _dict_type()
    for config in configs:
        if isinstance(config, tuple):
            k, v = config
        else:
            k, v = default_id(config), config

        if k in result:
            raise KeyError(f"Configuration identifier is not unique: {k}")
        else:
            result[k] = v
    return result
