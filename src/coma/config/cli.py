"""Utilities for overriding config attributes with command line arguments."""

from functools import partial
from typing import Any, Callable, Dict, List

from omegaconf import OmegaConf
from omegaconf.errors import ConfigKeyError


def override(
    config_id: str,
    configs: Dict[str, Any],
    unknown_args: List[str],
    *,
    sep: str = "::",
    exclusive: bool = False,
    raise_on_no_matches: bool = True,
    raise_on_many_matches: bool = True,
    raise_on_many_seps: bool = True,
    raise_on_empty_split: bool = True,
) -> Any:
    """Overrides a config's attribute values with command line arguments.

    Similar to `from_dotlist()`_ followed by `merge()`_, but with additional features.

    Specifically, since ``coma`` commands accept an arbitrary number of configs,
    config attributes' names may end up clashing when using pure ``omegaconf``
    dot-list notation. To resolve these clashes, a prefix notation is introduced.

    **Prefix Notation**

        For a config with identifier :obj:`config_id`, any ``omegaconf``
        dot-list notation can be prefixed with :obj:`config_id` followed by
        :obj:`sep` to uniquely link the override to the corresponding config.

        In addition, an attempt is made to match **all non-prefixed** arguments
        in dot-list notation to the config corresponding to :obj:`config_id`. These
        shared config overrides **are not consumed**, and so can be used to override
        multiple configs without duplication. However, this powerful feature can
        also be error-prone. To disable it, set :obj:`exclusive` to :obj:`True`. This
        raises a :obj:`ValueError` if shared overrides match more than one config.

        .. note::

            If the config is not `structured`_, ``omegaconf`` will happily add
            any attributes to it. To prevent this, ensure that the config is
            structured (using `structured()`_ or `set_struct()`_).

        Finally, prefixes can be abbreviated as long as the abbreviation is
        unambiguous (i.e., matches a unique config identifier).

    Examples:

        Resolving clashing dot-list notations with (abbreviated) prefixes:

            .. code-block:: python
                :caption: main.py

                @dataclass
                class Person:
                    name: str

                @dataclass
                class School:
                    name: str

                class AddStudent:
                    def __init__(self, person, school):
                        ...

                    def run(self):
                        ...

                ...
                coma.register("add_student", AddStudent, Person, School)

            Invoking on the command line (assuming :obj:`sep` is '::'):

            .. code-block:: console

                $ python main.py add_student p::name="..." s::name="..."

    Args:
        config_id (str): A config identifier for the config to target
        configs (typing.Dict[str, typing.Any]): A dictionary of (id-config) pairs
        unknown_args (typing.List[str]): Remainder (second return value) of
            `parse_known_args()`_
        sep (str): The prefix separation token to use
        exclusive (bool): Whether shared overrides should match at most one config
        raise_on_no_matches (bool): Whether to raise or suppress a :obj:`ValueError`
            if a prefix does not match any known config identifier
        raise_on_many_matches (bool): Whether to raise or suppress a :obj:`ValueError`
            if a prefix ambiguous (i.e., matches more than one config identifier)
        raise_on_many_seps (bool): Whether to raise or suppress a :obj:`ValueError` if
            more than one :obj:`sep` token is found within a single override argument
        raise_on_empty_split (bool): Whether to raise or suppress a :obj:`ValueError`
            if no split is achieved. This can only happen if :obj:`sep` is :obj:`None`
            and one of the arguments consists entirely of whitespace.

    Returns:
        A new config object that uses command line arguments to overrides the
        attributes of the config object originally corresponding to :obj:`config_id`

    Raises:
         KeyError: If :obj:`config_id` does not match any known config identifier
         ValueError: Various. See the :obj:`raise_on_*` above.
         Others: As may be raised by the underlying ``omegaconf`` handler

    .. _from_dotlist():
        https://omegaconf.readthedocs.io/en/2.1_branch/usage.html#from-a-dot-list
    .. _merge():
        https://omegaconf.readthedocs.io/en/2.1_branch/usage.html#omegaconf-merge
    .. _structured:
        https://omegaconf.readthedocs.io/en/2.1_branch/usage.html#from-structured-config
    .. _structured():
        https://omegaconf.readthedocs.io/en/2.1_branch/usage.html#from-structured-config
    .. _set_struct():
        https://omegaconf.readthedocs.io/en/2.1_branch/usage.html#struct-flag
    .. _parse_known_args():
        https://docs.python.org/3/library/argparse.html#partial-parsing
    """
    config = configs[config_id]
    shared, prefixed = [], []
    for arg in unknown_args:
        split = arg.split(sep=sep)
        if len(split) == 1:
            shared.append(split[0])
        elif len(split) == 2:
            matches = [cid for cid in configs if cid.startswith(split[0])]
            if len(matches) == 1:
                if matches[0] == config_id:  # Ignoring mismatches on purpose.
                    prefixed.append(split[1])
            elif len(matches) > 1:
                if raise_on_many_matches:
                    raise ValueError(
                        f"Too many matches: override: {arg} ;"
                        f" matched configs: {matches}"
                    )
            else:
                if raise_on_no_matches:
                    raise ValueError(f"Unknown override prefix: {split[0]}")
        elif len(split) > 2:
            if raise_on_many_seps:
                raise ValueError(f"Too many separators: override: {arg} ; sep: {sep}")
        else:
            if raise_on_empty_split:
                raise ValueError(f"Empty split: override: {arg} ; sep: {sep}")

    # These are defined explicitly and so should be safe. If not, it signifies
    # user error, so raising an exception is expected and desired.
    if prefixed:
        config = OmegaConf.merge(config, OmegaConf.from_dotlist(prefixed))

    # Merge the shared args only if they match.
    for arg in shared:
        try:
            config = OmegaConf.merge(config, OmegaConf.from_dotlist([arg]))
        except ConfigKeyError:
            pass
        else:
            if exclusive:
                for cid, c in configs.items():
                    if cid != config_id:
                        try:
                            OmegaConf.merge(c, OmegaConf.from_dotlist([arg]))
                        except ConfigKeyError:
                            pass
                        else:
                            raise ValueError(
                                f"Non-exclusive override: override: {arg} ; matched"
                                f" configs (possibly others too): {[config_id, cid]}"
                            )
    return config


def override_factory(
    *,
    sep: str = "::",
    exclusive: bool = False,
    raise_on_no_matches: bool = True,
    raise_on_many_matches: bool = True,
    raise_on_many_seps: bool = True,
    raise_on_empty_split: bool = True,
) -> Callable:
    """Factory for creating slight variations of :func:`~coma.config.cli.override`."""
    return partial(
        override,
        sep=sep,
        exclusive=exclusive,
        raise_on_no_matches=raise_on_no_matches,
        raise_on_many_matches=raise_on_many_matches,
        raise_on_many_seps=raise_on_many_seps,
        raise_on_empty_split=raise_on_empty_split,
    )
