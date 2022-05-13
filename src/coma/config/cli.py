from functools import partial
from typing import Any, Callable, Dict, List

from omegaconf import OmegaConf
from omegaconf.errors import ConfigKeyError


def override(
    config_id: str,
    configs: Dict[str, Any],
    unknown_args: List[str],
    *,
    sep: str = ":",
    exclusive: bool = False,
    raise_on_no_matches: bool = True,
    raise_on_many_matches: bool = True,
    raise_on_many_seps: bool = True,
    raise_on_empty_split: bool = True,
) -> Any:
    """Overrides a configuration's attributes with command line arguments.

    Similar to :func:`omegaconf.OmegaConf.from_dotlist` followed by
    :func:`omegaconf.OmegaConf.merge`, but with additional features.

    Specifically, since ``coma`` commands accept an arbitrary number of configs,
    config attributes may end up clashing when using pure ``omegaconf`` dot-list
    notation. To resolve these clashes, a prefix notation is introduced.

    Prefix Notation:

        For a configuration with identifier :obj:`config_id`, any ``omegaconf``
        dot-list notation can be prefixed with `config_id``sep` to uniquely link
        the dot-list notation to the corresponding configuration.

        In addition, an attempt is made to match any non-prefixed arguments in
        dot-list notation to the config corresponding to :obj:`config_id`. These
        shared config overrides are not consumed, and so can be used to override
        multiple configs without duplication. However, this feature is powerful
        but can also be error prone. To disable it, set :obj:`exclusive` to `True`.
        This raises a ValueError if shared overrides match more than one config.

        .. note::

            If the config not structured, ``omegaconf`` will happily add any
            missing fields to it. To prevent this, ensure that the config is
            structured (by using :func:`omegaconf.OmegaConf.structured` or
            :func:`omegaconf.OmegaConf.set_struct`).

        Finally, prefixes can be abbreviated so long as the abbreviation is unambiguous
        (i.e., so long as the prefix matches a unique configuration identifier).

    Examples:

        Resolving clashing dot-list notations with (abbreviated) prefixes:

            .. code-block:: python

                @dataclass
                class Person:
                    name: str
                    ...

                @dataclass
                class School:
                    name: str
                    ...

                class AddStudent:
                    def __init__(self, person, school):
                        ...
                    ...

                coma.register("add_student", AddStudent, Person, School)
                ...

            Invoking on the command line. Supposing a program file called ``admin.py``.

            .. code-block:: console

                $ python admin.py add_student p:name="..." s:name="..."

    Args:
        config_id: A configuration identifier for the configuration to target
        configs: A dictionary of (identifier, configuration) pairs
        unknown_args: Remainder of :func:`argparse.ArgumentParser.parse_known_args`
        sep: The prefix separation token to use
        exclusive: Whether shared overrides should match at most one configuration
        raise_on_no_matches: Whether to raise or suppress a ValueError if a
            prefix does not match any known configuration identifier
        raise_on_many_matches: Whether to raise or suppress a ValueError if a
            prefix ambiguous (i.e., matches more than one configuration identifier).
        raise_on_many_seps: Whether to raise or suppress a ValueError if more
            than one :obj:`sep` token is found within a single override argument
        raise_on_empty_split: Whether to raise or suppress a ValueError if no
            split is achieved. This can only happen if :obj:`sep` is `None` and
            one of the arguments consists entirely of whitespace.

    Returns:
        A new configuration object that possibly overrides some of the
        attributes of the configuration object corresponding to :obj:`config_id`
        with command line arguments

    Raises:
         KeyError: If :obj:`config_id` does not match any known configuration identifier
         ValueError: Various. See `raise_on_*` above.
         Others: As may be raised by the underlying ``omegaconf`` handler
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
    sep: str = ":",
    exclusive: bool = False,
    raise_on_no_matches: bool = True,
    raise_on_many_matches: bool = True,
    raise_on_many_seps: bool = True,
    raise_on_empty_split: bool = True,
) -> Callable:
    """Factory for creating slight variations of :func:`coma.config.cli.override`.

    Just a wrapper for partial calls to :func:`~coma.config.cli.override`.

    See :func:`~coma.config.cli.override` for details.
    """
    return partial(
        override,
        sep=sep,
        exclusive=exclusive,
        raise_on_no_matches=raise_on_no_matches,
        raise_on_many_matches=raise_on_many_matches,
        raise_on_many_seps=raise_on_many_seps,
        raise_on_empty_split=raise_on_empty_split,
    )
