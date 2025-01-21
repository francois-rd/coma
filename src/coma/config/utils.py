"""General config utilities."""

from collections import OrderedDict
import sys
from typing import Any, Dict, Tuple, Union

_dict_type = OrderedDict if sys.version_info < (3, 7) else dict


def default_id(config: Any) -> str:
    """Returns the default identifier of :obj:`config`.

    The default identifier is derived from :obj:`config`'s :obj:`type` name.

    Args:
        config: Any valid ``omegaconf`` config

    Returns:
        The default identifier of :obj:`config`
    """
    if not isinstance(config, type):
        config = type(config)
    return config.__name__.lower()


def default_dest(config_id: str) -> str:
    """Returns the default file path parser argument destination of :obj:`config_id`.

    Returns the default value for the :obj:`dest` keyword argument to
    `add_argument()`_ that will define the file path parser argument
    corresponding to :obj:`config_id`. This will also be the attribute
    of the :obj:`namespace` return object (first return value) of
    `parse_known_args()`_.

    Args:
        config_id: A config identifier

    Returns:
        The default file path parser argument attribute of :obj:`config_id`

    .. _add_argument():
        https://docs.python.org/3/library/argparse.html#the-add-argument-method
    .. _parse_known_args():
        https://docs.python.org/3/library/argparse.html#partial-parsing
    """
    return f"{config_id}_path"


def default_default(config_id: str) -> str:
    """Returns the default file path parser argument default value for :obj:`config_id`.

    Returns the default value for the :obj:`default` keyword argument to
    `add_argument()`_ that will define the file path parser argument
    corresponding to :obj:`config_id`.

    Args:
        config_id: A config identifier

    Returns:
        The default file path parser argument default value for :obj:`config_id`

    .. _add_argument():
        https://docs.python.org/3/library/argparse.html#the-add-argument-method
    """
    return f"{config_id}"


def default_flag(config_id: str) -> str:
    """Returns the default file path parser argument flag value for :obj:`config_id`.

    Returns the default value for the :obj:`names_or_flags` variadic argument to
    `add_argument()`_ that will define the file path parser argument
    corresponding to :obj:`config_id`.

    Args:
        config_id: A config identifier

    Returns:
        The default file path parser argument flag value for :obj:`config_id`

    .. _add_argument():
        https://docs.python.org/3/library/argparse.html#the-add-argument-method
    """
    return f"--{config_id}-path"


def default_help(config_id: str) -> str:
    """Returns the default file path parser argument help value for :obj:`config_id`.

    Returns the default value for the :obj:`help` keyword argument to
    `add_argument()`_ that will define the file path parser argument
    corresponding to :obj:`config_id`.

    Args:
        config_id: A config identifier

    Returns:
        The default file path parser argument help value for :obj:`config_id`

    .. _add_argument():
        https://docs.python.org/3/library/argparse.html#the-add-argument-method
    """
    return f"{config_id} file path"


def to_dict(*configs: Union[Any, Tuple[str, Any]]) -> Dict[str, Any]:
    """Converts configs provided in raw format to dictionary format.

    :obj:`configs` should be of the form :obj:`<conf>` or :obj:`(<id>, <conf>)`,
    where :obj:`<conf>` represents a config and :obj:`<id>` is any identifier
    for the config. If :obj:`<id>` is omitted, an identifier is derived from
    :obj:`<conf>`'s :obj:`type` name using
    :func:`~coma.config.utils.default_id`. That is, specifying just
    :obj:`<conf>` is a shorthand for ``(default_id(<conf>), <conf>)``.

    .. note::

        For each :func:`~coma.core.register.register`\\ ed command, both global
        and local config identifiers need to be unique for that command.

    Returns:
        Configs as a dictionary with :obj:`<id>` keys and :obj:`<conf>` values.

        .. note::

            The dictionary is guaranteed to be insertion-ordered (even in Python < 3.7).

    See also:
        * :func:`~coma.config.utils.default_id`
        * :func:`~coma.core.initiate.initiate`
        * :func:`~coma.core.register.register`
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
