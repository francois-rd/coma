"""Parser hook factories and defaults."""

from typing import Any

from .base import Hook, ParserData
from ..config import ConfigID


def add_argument_factory(*names_or_flags: str, **kwargs: Any) -> Hook:
    """
    Factory for creating a parser hook that adds an ``argparse`` argument.

    Essentially, creates and returns a hook function as a lightweight wrapper
    around `ArgumentParser.add_argument()`_ called on the current value of the
    :attr:`coma.hooks.base.ParserData.parser` object with the given
    :obj:`names_or_flags` and :obj:`kwargs`.

    .. note::

        The value of :obj:`parser` is assumed to be
        the sub-parser attached to the command currently being executed. Adding
        arguments to the global parser should be done directly on the :obj:`parser`
        object passed to :func:`~coma.core.wake.wake()`.

    Example:

        Add a command line flag specifying how many lines the command should read::

            coma.command(..., parser_hook=argument_factory('-l', '--lines', type=int))

    Args:
        *names_or_flags (str): Passed to :obj:`add_argument()`.
        **kwargs (Any): Passed to :obj:`add_argument()`.

    Returns:
        :data:`~coma.hooks.base.Hook`: A hook with :obj:`parser_hook` semantics.

    See also:
        * :func:`coma.hooks.parser_hook.default_factory()`

    .. _ArgumentParser.add_argument():
        https://docs.python.org/3/library/argparse.html#the-add-argument-method
    """

    def hook(data: ParserData) -> None:
        data.parser.add_argument(*names_or_flags, **kwargs)

    return hook


def default_factory(*config_ids: ConfigID) -> Hook:
    """
    Factory for creating a parser hook that adds a file path argument for each
    given :obj:`ConfigID` via `add_argument()`_.

    Equivalent to calling :meth:`~coma.config.io.PersistenceManager.add_path_argument()`
    for each :data:`~coma.config.base.ConfigID` in :obj:`config_ids` with default
    parameters.

    .. note::

        If :obj:`config_ids` is empty, defaults to **all** registered configs for
        the command being executed. In other words, only specify :obj:`config_ids`
        explicitly to **limit** the factory to only those configs.

    .. note::

        Any config identifier in :obj:`config_ids` corresponding to a config where
        :meth:`~coma.config.cli.ParamData.is_serializable()` is :obj:`False` is
        skipped, as these can never be initialized from or serialized to a file.

    Example:

        Add a file path argument only for :obj:`main_cfg` and not :obj:`no_path_cfg`::

            @dataclass
            class MainConfig:
                ...

            @coma.command(parser_hook=default_factory("main_cfg"))
            def my_cmd(main_cfg: MainConfig, no_path_cfg: dict):
                ...

    Args:
        *config_ids (:data:`~coma.config.base.ConfigID`): Configs for which to
            create a file path argument parser hook. If empty, do so for **all**
            configs registered with the command currently being executed.

    Returns:
        :data:`~coma.hooks.base.Hook`: A hook with :obj:`parser_hook` semantics.

    See also:
        * :func:`coma.hooks.config_hook.initialize_factory()`
        * :func:`coma.hooks.config_hook.default_factory()`
    """

    def hook(data: ParserData) -> None:
        for config_id in config_ids or data.parameters.get_all_configs():
            if data.parameters.is_serializable(config_id):
                data.persistence_manager.add_path_argument(data.parser, config_id)

    return hook
