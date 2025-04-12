"""Utilities for overriding config attributes with command line arguments."""

from dataclasses import Field, dataclass, field, is_dataclass, make_dataclass
from inspect import Parameter, Signature, signature as sig
from collections import Counter
from enum import Enum
from typing import (
    Any,
    Callable,
    ClassVar,
    Literal,
    Optional,
    Protocol,
    Sequence,
    Union,
    get_origin,  # Requires Python >= 3.8
)
import warnings

from omegaconf.base import Container
from omegaconf import OmegaConf
import omegaconf

from .base import (
    Config,
    ConfigID,
    Configs,
    Identifier,
    InstanceKey,
    InstanceKeys,
    Parameters,
    ParamID,
    T,
)


_SPLIT = "="  # This is pulled from internals of OmegaConf implementation.
_EMPTY = object()  # Sentinel for missing parameter values.
_Inline = Sequence[Union[ParamID, tuple[ParamID, Callable[[], Any]]]]


class OverrideProtocol(Protocol):
    """
    Protocol for the function signature of :meth:`coma.config.cli.Override.__call__()`.
    To make use of other default ``coma`` components, user-defined alternative
    implementation should adhere to this same protocol.

    Protocol::

        Callable[[OverrideData, InstanceKey], None]

    with :class:`~coma.config.cli.OverrideData` and :data:`~coma.config.base.InstanceKey`
    """

    def __call__(
        self,
        data: "OverrideData",
        override_instance_key: InstanceKey = InstanceKeys.OVERRIDE,
    ) -> None:
        pass


class OverridePolicy(Enum):
    """
    Policy for handling cases where one parameter will override another in a
    Callable's signature. For example, suppose a function defined as::

        def fn(x, **kwargs):
            ...

    is invoked as::

        kwargs = dict(x=1, y=2)
        fn(x=3, **kwargs)

    How should :obj:`x` be treated?

    Attributes:
        SILENT_OVERRIDE: Silently override the parameter value. In the above example,
            the result is :obj:`x=1` since :obj:`kwargs["x"]` applies last.
        VERBOSE_OVERRIDE: Like :obj:`SILENT_OVERRIDE`, but emit a ``warning`` listing
            which parameter is overridden and what the old and new values are.
        SILENT_SKIP: Silently skip over any parameter whose value has already been
            assigned. In the above example, the result is :obj:`x=3` since
            :obj:`kwargs["x"]` is silently skipped.
        VERBOSE_SKIP: Like :obj:`SILENT_SKIP`, but emit a ``warning`` listing which
            parameter is being skipped and what the current and skipped values are.
        RAISE: Raise an error if an override is being attempted.
    """

    SILENT_OVERRIDE = 0
    VERBOSE_OVERRIDE = 1
    SILENT_SKIP = 2
    VERBOSE_SKIP = 3
    RAISE = 4


@dataclass
class OverrideData:
    """
    All relevant data for overriding a config instance.

    Attributes:
        config_id (:data:`~coma.config.base.ConfigID`): The identifier of the
            specific config in :obj:`configs` to possibly override.
        configs (:data:`~coma.config.base.Configs`): All configs that may be
            override-relevant. Configs that are not corresponding to :obj:`config_id`
            inform concerns of override exclusivity and uniqueness. See
            :class:`~coma.config.cli.Override` for details.
        instance_key (:data:`~coma.config.base.InstanceKey`, optional): The specific
            instance of the :obj:`config_id` config to override. If :obj:`None`, the
            latest is used instead. If not :obj:`None`, the same key is used to
            probe the other :obj:`configs` for override exclusivity and uniqueness.
            See :class:`~coma.config.cli.Override` for details.
        unknown_args (list[str]): The list of unknown command line arguments,
            some of which may specify overrides for this :obj:`config_id` config.
            Typically, this is the **second** return value of `parse_known_args()`_.

    .. _parse_known_args():
        https://docs.python.org/3/library/argparse.html#partial-parsing
    """

    config_id: ConfigID
    configs: Configs
    instance_key: Optional[InstanceKey]
    unknown_args: list[str]


@dataclass
class _OverrideData(OverrideData):
    shared: list[str] = field(default_factory=list)
    prefixed: list[str] = field(default_factory=list)

    @staticmethod
    def from_data(data: OverrideData) -> "_OverrideData":
        return _OverrideData(
            config_id=data.config_id,
            configs=data.configs,
            instance_key=data.instance_key,
            unknown_args=data.unknown_args,
        )


@dataclass
class Override(OverrideProtocol):
    """
    Attempts to override a config instance's attributes with command line arguments.

    Attributes:
        sep (str): The prefix separation string to use. Can be any string, though
            some options (such as :obj:`"="`, :obj:`":"`, :obj:`"{"`, :obj:`"}"`,
            :obj:`"["`, :obj:`"]"`, :obj:`","`, :obj:`"'"`, :obj:`'"'`, :obj:`"."`,
            :obj:`"$"`, etc.) will likely cause parsing errors. Use these with caution.
        exclusive_prefixed (bool): Whether prefixed overrides should match at
            most one config.
        exclusive_shared (bool): Whether shared overrides should match at
            most one config.
        unique_overrides (bool): Whether each override should be defined at most one.

    Similar to `from_dotlist()`_ followed by `merge()`_, but with additional
    features and support for list-like configs. In particular, ``omegaconf``
    always **overrides** list configs entirely when merging (discarding the original),
    whereas here we ensure top-level lists are extended instead. Non-top-level lists
    (for example, a list as one of the fields of a dict-like config) are treated as
    conventional ``omegaconf`` list configs (override instead of merge).

    Specifically, since ``coma`` commands accept an arbitrary number of configs,
    config attributes' names may end up clashing when using pure ``omegaconf``
    dot-list notation. To resolve these clashes, a prefix notation is introduced.

    **Prefix Notation**

        For a config with identifier :obj:`config_id`, any ``omegaconf`` dot-list
        notation can be prefixed with :obj:`config_id` followed by
        :attr:`~coma.config.cli.Override.sep` to uniquely link the override to
        the corresponding config.

        In addition, an attempt is made to match **all non-prefixed** arguments
        in dot-list notation to the config corresponding to :obj:`config_id`. These
        shared config overrides **are not consumed**, and so can be used to override
        multiple configs without duplication. However, this powerful feature can
        also be error-prone. To disable it, set
        :attr:`~coma.config.cli.Override.exclusive_shared` to :obj:`True`. This
        raises a :obj:`ValueError` if shared overrides match more than one config.

        .. note::

            If the config is not `structured`_, ``omegaconf`` will happily add
            *any* attributes to it. To prevent this, ensure that the config is
            structured (by instantiating it from a ``dataclass`` backend type
            or by using `structured()`_ or `set_struct()`_ on a ``dict``-based config).

        Finally, prefixes can be shortened to any leading substring. For example,
        :obj:`'long'` or even just :obj:`'l'` matches against the config identifier
        :obj:`'long_config_id'`. By default, prefixes have to be unambiguous (i.e.,
        have to match against at most one config identifier). To disable this, set
        :attr:`~coma.config.cli.Override.exclusive_prefixed` to :obj:`False`. Then,
        *all* matching configs to a given prefix will be overridden. *Be cautious*.

    To toggle whether each command line argument should itself be unique,
    set :attr:`~coma.config.cli.Override.unique_overrides` accordingly.

    .. note::

        The uniqueness of command line arguments is based on their (non-prefixed)
        string value of the field key, not on their effects on any config object. For
        example, :obj:`"x=1"` and :obj:`"x=2"` are not correctly determined as being
        not unique because :obj:`"x" == "x"`, whereas :obj:`"a.b=1"` and :obj:`"a[b]=2"`
        will slip by the uniqueness detection because :obj:`"a.b" != "a[b]"` (as a
        string value).

    .. note::

        Regardless of their ordering as command line arguments, **all** prefixed
        overrides are processed **before** all shared overrides. This is not a
        problem when :obj:`unique_overrides` is :obj:`False`, but can lead to an
        unexpected outcome when it is :obj:`True`. For example,  :obj:`"x=1"`
        *followed by* :obj:`"prefix::x=2"` will lead to a final value of :obj:`x == 1`.
        To avoid this unexpected outcome, makes sure to place all prefixed command line
        arguments before all shared arguments, or disable shared arguments entirely by
        setting :attr:`~coma.config.cli.Override.exclusive_shared` to :obj:`False`.

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

                @coma.command
                def enroll_student(person: Person, school: School):
                        ...

        Invoking on the command line (assuming :attr:`~coma.config.cli.Override.sep`
        is :obj:`"::"`):

            .. code-block:: console

                $ python main.py enroll_student p::name="..." s::name="..."

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

    sep: str = "::"
    exclusive_prefixed: bool = True
    exclusive_shared: bool = False
    unique_overrides: bool = True

    def __call__(
        self,
        data: OverrideData,
        override_instance_key: InstanceKey = InstanceKeys.OVERRIDE,
    ) -> None:
        """
        Attempts to override a config instance's attributes with command line arguments.

        Args:
            data (:class:`~coma.config.cli.OverrideData`): Data regarding which
                config to override and with which command line arguments.
            override_instance_key (:data:`~coma.config.base.InstanceKey`): The
                key at which to store the resulting overridden config instance.

        Raises:
             KeyError: If :attr:`~coma.config.cli.OverrideData.config_id` does not
                exist in :attr:`~coma.config.cli.OverrideData.configs`.
             ValueError: Various, including parsing errors and exclusivity violations.
             Others: As may be raised by the underlying ``omegaconf`` handler.
        """
        if not data.configs[data.config_id].has(override_instance_key):
            instance = self._do_override(self._populate_data(data))
            data.configs[data.config_id].set(override_instance_key, instance)

    def _populate_data(self, data: OverrideData) -> _OverrideData:
        data = _OverrideData.from_data(data)
        for arg in data.unknown_args:
            split = arg.split(sep=self.sep)
            if len(split) == 1:
                data.shared.append(split[0])
            elif len(split) == 2:
                self._populate_prefixed(split, data)
            elif len(split) > 2:
                raise ValueError(f"Too many separators ('{self.sep}') in: {arg}")
            else:
                raise ValueError(f"Unable to split '{arg}' using '{self.sep}'")
        return data

    def _populate_prefixed(self, split: list[str], data: _OverrideData) -> None:
        matches = [cid for cid in data.configs if cid.startswith(split[0])]
        if len(matches) == 0:
            raise ValueError(
                f"Unknown override prefix: '{split[0]}'. "
                f"Options are: {list(data.configs.keys())}"
            )
        if len(matches) > 1 and self.exclusive_prefixed:
            raise ValueError(
                f"Non-exclusive prefix '{split[0]}' matches configs: {matches}"
            )
        if data.config_id in matches:
            data.prefixed.append(split[1])

    def _do_override(self, data: _OverrideData) -> Any:
        instance = data.configs[data.config_id].get_or_latest(data.instance_key)
        if isinstance(instance, omegaconf.DictConfig):
            self._check_unique(data.shared + data.prefixed)

        # These are defined explicitly and so should be safe. If not, it signifies
        # user error, so raising an exception is expected and desired.
        if data.prefixed:
            instance = self._do_merge(
                data.config_id, instance, data.prefixed, strict=True
            )

        # Merge the shared args only if they match.
        for arg in data.shared:
            try:
                new_instance = self._do_merge(data.config_id, instance, [arg])
            except omegaconf.errors.ConfigKeyError:
                # This means the key in the dot list isn't compatible with the keys
                # in the config (only happens when config is backed by a dataclass).
                # But, since these are shared CLI overrides, they aren't necessarily
                # intended for this config, so we just skip over these mismatches.
                continue
            if new_instance is not instance and self.exclusive_shared:
                self._check_exclusive_shared(arg, data)
            instance = new_instance
        return instance

    def _do_merge(
        self,
        config_id: ConfigID,
        instance: Any,
        dot_list: list[str],
        strict: bool = False,
    ) -> Any:
        """
        Crucially, returns the *original* object if there is nothing to merge. That
        means the caller can check if anything was merged by checking whether the
        returned object 'is' the same object (not '==' but 'is'). This is an important
        distinction, because it is possible for the merged data to be identical to the
        original. So checking via '==' will miss that case and cause a subtle bug
        with respect to exclusivity checks.
        """
        # This is pulled from internals of OmegaConf implementation.
        # NOTE: Why do we need this check for list, but not for dict or dataclass?
        if not isinstance(instance, Container) and isinstance(instance, (list, tuple)):
            instance = OmegaConf.create(instance)

        if isinstance(instance, omegaconf.ListConfig):
            safe_dot_list = [arg for arg in dot_list if arg.find(_SPLIT) == -1]
            self._check_strict(config_id, dot_list, safe_dot_list, strict)
            if safe_dot_list:
                return instance + OmegaConf.create(safe_dot_list)
            return instance

        safe_dot_list = [arg for arg in dot_list if arg.find(_SPLIT) != -1]
        self._check_strict(config_id, dot_list, safe_dot_list, strict)
        self._check_unique(safe_dot_list)
        if not safe_dot_list:
            return instance
        try:
            return OmegaConf.merge(instance, OmegaConf.from_dotlist(safe_dot_list))
        except omegaconf.errors.ConfigTypeError:
            raise ValueError(
                f"Config '{config_id}' of type '{type(instance)}' with contents "
                f"'{instance}' can't be merged with: {dot_list}"
            )

    @staticmethod
    def _check_strict(
        config_id: ConfigID,
        original_dot_list: list[str],
        filtered_dot_list: list[str],
        strict: bool,
    ) -> None:
        if strict and original_dot_list != filtered_dot_list:
            extras = [x for x in original_dot_list if x not in filtered_dot_list]
            s = "" if len(extras) == 1 else "s"
            extras = f"'{extras[0]}'" if len(extras) == 1 else extras
            raise ValueError(
                f"Config '{config_id}' cannot accept override{s}: {extras}"
            )

    def _check_unique(self, dot_list: list[str]) -> None:
        if self.unique_overrides:
            counter = Counter([arg.split(_SPLIT)[0] for arg in dot_list])
            duplicates = [k for k, v in counter.most_common() if v > 1]
            if duplicates:
                s = "" if len(duplicates) == 1 else "s"
                d = f"'{duplicates[0]}'" if len(duplicates) == 1 else duplicates
                raise ValueError(f"Override{s} defined multiple times: {d}")

    def _check_exclusive_shared(self, arg: str, data: _OverrideData):
        matches = []
        for config_id, config in data.configs.items():
            if config_id == data.config_id:
                continue
            try:
                instance = config.get_or_latest(data.instance_key)
            except (KeyError, ValueError):
                continue
            try:
                if self._do_merge(config_id, instance, [arg]) is not instance:
                    matches.append(config_id)
            except omegaconf.errors.ConfigKeyError:
                continue
        if matches:
            matches.append(data.config_id)
            raise ValueError(
                f"Non-exclusive override. Override '{arg}' matches configs: {matches}"
            )


@dataclass
class ParamData:
    """
    Utilities for creating configs and other parameters from a Callable's
    signature, manipulating these, and calling the Callable using the result.

    Attributes:
        configs (:data:`~coma.config.base.Configs`): The configs pulled from
            the Callable's signature.
        supplemental_configs (:data:`~coma.config.base.Configs`): Any additional
            configs to manipulate that don't appear in the Callable's signature and
            won't be called on it. Helpful for providing additional information in
            the manipulation process.
        inline_identifier (:data:`~coma.config.base.ConfigID`): The identifier of
            the inline config (whether it exists or not).
        inline_config (:class:`~coma.config.base.Config`, optional): The special
            config collecting all inline parameter from the Callable's signature.
        other_parameters (:data:`~coma.config.base.Parameters`): Every non-config
            parameter in the Callable's signature.
        args_id (:data:`~coma.config.base.Identifier`, optional): The identifier of
            the variadic positional parameter (if any) of the Callable's signature.
            Depending on the signature's specifics, the associated data (if any)
            is either in :obj:`configs` or in :obj:`other_parameters`.
        kwargs_id (:data:`~coma.config.base.Identifier`): The identifier of the
            variadic keyword parameter (if any) of the Callable's signature.
            Depending on the signature's specifics, the associated data (if any)
            is either in :obj:`configs` or in :obj:`other_parameters`.

    See also:
        * :meth:`~coma.config.cli.ParamData.from_signature()`:
            For specifics on how the above attributes are inferred from the
            Callable's signature.
    """

    DEFAULT_INLINE_ID: ClassVar[ConfigID] = "inline"
    configs: Configs = field(default_factory=dict)
    supplemental_configs: Configs = field(default_factory=dict)
    inline_identifier: ConfigID = DEFAULT_INLINE_ID
    inline_config: Optional[Config] = None
    other_parameters: Parameters = field(default_factory=dict)
    args_id: Optional[Identifier] = None
    kwargs_id: Optional[Identifier] = None

    def get_inline_id(self) -> ConfigID:
        """Returns the identifier of the inline config (whether it exists or not)."""
        return self.inline_identifier.lower()

    def is_inline_id(self, config_id: ConfigID) -> bool:
        """Returns whether :obj:`config_id` is the identifier of the inline config."""
        return config_id.lower() == self.get_inline_id()

    def get_all_configs(self, include_inline: bool = True) -> Configs:
        """
        Returns all :obj:`configs` and :obj:`supplemental_configs`. If
        :obj:`include_inline` and an inline config exists, it is also returned.

        Args:
            include_inline (bool): Whether the inline config is also returned.
                Ignored if an inline config does not exist.

        Returns:
            :data:`~coma.config.base.Configs`: All configs, possibly including inline.
        """
        configs = {**self.configs, **self.supplemental_configs}
        if include_inline and self.inline_config is not None:
            configs[self.get_inline_id()] = self.inline_config
        return configs

    def is_serializable(self, config_id: ConfigID) -> bool:
        """
        Returns whether :obj:`config_id` corresponds to a serializable config.
        All configs are serializable except for variadic positional (:obj:`*args`),
        variadic keyword (:obj:`**kwargs`), and the special :obj:`inline_config`.

        Args:
            config_id (:data:`~coma.config.base.ConfigID`): A config identifier.

        Returns:
            bool: Whether :obj:`config_id` corresponds to a serializable config.
        """
        is_inline = self.is_inline_id(config_id)
        return config_id not in [self.args_id, self.kwargs_id] and not is_inline

    def select(self, *ids: Identifier, default: Any = _EMPTY) -> dict[Identifier, Any]:
        """
        Returns the objects associated with the selected :obj:`ids`, keyed by
        identifier. These can be in any of :obj:`configs`, :obj:`supplemental_configs`,
        :obj:`other_parameters`, or :obj:`inline_config`. For :obj:`inline_config`,
        only the aggregate inline config can be retrieved, not the individual
        parameters that collectively make it up. To retrieve it, use
        :meth:`~coma.config.cli.ParamData.get_inline_id()`.

        Args:
            *ids (:data:`~coma.config.base.Identifier`): Collection of identifiers
                for which to select data.
            default (typing.Any): If given, the value for identifiers in :obj:`ids`
                with no existing data is set to this value. If not given, raise a
                :obj:`KeyError` if data does not exist for at least one identifier.

        Returns:
            dict[:data:`~coma.config.base.Identifier`, typing.Any]: A mapping
            between the selected identifiers and their associated value.

        Raises:
            KeyError: If :obj:`default` is not specified, and data does not exist
                for at least one identifier in :obj:`ids`.
        """
        return {id_: self.get(id_, default=default) for id_ in ids}

    def select_config(self, *config_ids: ConfigID, default: Any = _EMPTY) -> Configs:
        """
        Returns the configs associated with the selected :obj:`config_ids`, keyed by
        identifier. These can be in any of :obj:`configs`, :obj:`supplemental_configs`,
        or :obj:`inline_config`. For :obj:`inline_config`, only the aggregate inline
        config can be retrieved, not the individual parameters that collectively make
        it up. To retrieve it, use :meth:`~coma.config.cli.ParamData.get_inline_id()`.

        Args:
            *config_ids (:data:`~coma.config.base.ConfigID`): Collection of config
                identifiers for which to select configs.
            default (typing.Any): If given, missing configs for identifiers in
                :obj:`config_ids` are set to this value. If not given, raise a
                :obj:`KeyError` if a config does not exist for at least one identifier.

        Returns:
            :data:`~coma.config.base.Configs`: A mapping between the selected config
            identifiers and their associated configs.

        Raises:
            KeyError: If :obj:`default` is not specified, and a config does not exist
                for at least one config identifier in :obj:`config_ids`; or if any
                identifier in :obj:`config_ids` refers to a parameter instead of a
                config.
        """
        return {id_: self.get_config(id_, default=default) for id_ in config_ids}

    def get(self, identifier: Identifier, default: Any = _EMPTY) -> Any:
        """
        Returns the object associated with :obj:`identifier`. This object can be in any
        of :obj:`configs`, :obj:`supplemental_configs`, :obj:`other_parameters`, or
        :obj:`inline_config`. For :obj:`inline_config`, only the aggregate inline config
        can be retrieved, not the individual parameters that collectively make it up. To
        retrieve it, use :meth:`~coma.config.cli.ParamData.get_inline_id()`.

        Args:
            identifier (:data:`~coma.config.base.Identifier`): The identifier
                for which to retrieve data.
            default (typing.Any): If given, returns this value if no data exists
                for :obj:`identifier`. If not given, raise a :obj:`KeyError` on
                missing data.

        Returns:
            typing.Any: The data associated with :obj:`identifier`, or :obj:`default`
            if no such data exists and :obj:`default` is given.

        Raises:
            KeyError: If :obj:`default` is not given, and data for :obj:`identifier`
                does not exist.
        """
        if self.is_inline_id(identifier):
            if self.inline_config is None and default is _EMPTY:
                raise KeyError(f"Inline config does not exist: '{identifier}'")
            return self.inline_config
        elif identifier in self.configs:
            return self.configs[identifier]
        elif identifier in self.supplemental_configs:
            return self.supplemental_configs[identifier]
        elif identifier in self.other_parameters:
            return self.other_parameters[identifier]
        elif default is _EMPTY:
            raise KeyError(f"No such config or parameter identifier: '{identifier}'")
        else:
            return default

    def get_config(self, config_id: ConfigID, default: Any = _EMPTY) -> Config:
        """
        Returns the config associated with :obj:`config_id`. The config can be in any
        of :obj:`configs`, :obj:`supplemental_configs`, or :obj:`inline_config`. For
        :obj:`inline_config`, only the aggregate inline config can be retrieved, not
        the individual parameters that collectively make it up. To retrieve it, use
        :meth:`~coma.config.cli.ParamData.get_inline_id()`.

        Args:
            config_id (:data:`~coma.config.base.ConfigID`): The config identifier
                for which to retrieve a config.
            default (typing.Any): If given, returns this value if no config exists
                for :obj:`config_id`. If not given, raise a :obj:`KeyError` on missing.

        Returns:
            :class:`~coma.config.base.Config`: The config associated with
            :obj:`config_id`, or :obj:`default` if no such config exists
            and :obj:`default` is given.

        Raises:
            KeyError: If :obj:`default` is not given, and a config for :obj:`config_id`
                does not exist; or if :obj:`config_id` refers to a parameter instead
                of a config.
        """
        if self.is_inline_id(config_id):
            if self.inline_config is None and default is _EMPTY:
                raise KeyError(f"Inline config does not exist: '{config_id}'")
            return self.inline_config
        elif config_id in self.configs:
            return self.configs[config_id]
        elif config_id in self.supplemental_configs:
            return self.supplemental_configs[config_id]
        elif config_id in self.other_parameters:
            raise KeyError(
                f"Identifier is for parameter not config: '{config_id}'. "
                f"Did you mean to call get() instead of get_config()?"
            )
        elif default is _EMPTY:
            raise KeyError(f"No such config identifier: '{config_id}'")
        else:
            return default

    def replace(self, identifier: Identifier, new_value: Any) -> None:
        """
        Replaces the data associated with :obj:`identifier`. This object can be in
        any of :obj:`configs`, :obj:`supplemental_configs`, or :obj:`other_parameters`,
        or :obj:`inline_config`. For :obj:`inline_config`, only the aggregate inline
        config can be replaced (as a whole), not the individual parameters that
        collectively make it up. Use :meth:`~coma.config.cli.ParamData.get_inline_id()`.

        Args:
            identifier (:data:`~coma.config.base.Identifier`): The identifier
                for which to replace the data.
            new_value (typing.Any): The new value.

        Raises:
            KeyError: If data for :obj:`identifier` does not already exist. To add
                new data for a new identifier, add an entry directly to the desired
                attribute dictionary.
        """
        if self.is_inline_id(identifier):
            self.inline_config = new_value
        if identifier in self.configs:
            self.configs[identifier] = new_value
        elif identifier in self.supplemental_configs:
            self.supplemental_configs[identifier] = new_value
        elif identifier in self.other_parameters:
            self.other_parameters[identifier] = new_value
        else:
            raise KeyError(f"No such config or parameter identifier: '{identifier}'")

    def delete(self, *ids: Identifier, raise_on_missing: bool = True) -> None:
        """
        Deletes the data associated with each identifier in :obj:`ids`. These can be in
        any of :obj:`configs`, :obj:`supplemental_configs`, or :obj:`other_parameters`,
        or :obj:`inline_config`. For :obj:`inline_config`, only the aggregate inline
        config can be deleted, not the individual parameters that collectively make it
        up. To delete it, use :meth:`~coma.config.cli.ParamData.get_inline_id()`.

        Args:
            *ids (:data:`~coma.config.base.Identifier`): Collection of identifiers
                for which to delete data.
            raise_on_missing (bool): If :obj:`True`, raise a :obj:`KeyError` if data
                does not already exist for at least one identifier in :obj:`ids`. If
                :obj:`False`, silently ignore missing identifiers.

        Raises:
            KeyError: If :obj:`raise_on_missing` is :obj:`True`, and data does not
                already exist for at least one identifier in :obj:`ids`.
        """
        for identifier in ids:
            if self.is_inline_id(identifier):
                self.inline_config = None
            elif self._maybe_delete(identifier, self.configs):
                continue
            elif self._maybe_delete(identifier, self.supplemental_configs):
                continue
            elif self._maybe_delete(identifier, self.other_parameters):
                continue
            elif raise_on_missing:
                raise KeyError(f"No such config or parameter ID: '{identifier}'")

    def _maybe_delete(self, id_: Identifier, options: dict[Identifier, Any]) -> bool:
        if id_ in options:
            del options[id_]
            if id_ == self.args_id:
                self.args_id = None
            if id_ == self.kwargs_id:
                self.kwargs_id = None
            return True
        return False

    @classmethod
    def from_signature(
        cls,
        signature: Signature,
        *,
        args_as_config: bool,
        kwargs_as_config: bool,
        inline_identifier: ConfigID,
        inline: Sequence[Union[ParamID, tuple[ParamID, Callable[[], Any]]]],
        **supplemental_configs: Any,
    ) -> "ParamData":
        """
        Returns a :class:`~coma.config.cli.ParamData` filled according to the
        specifics of :obj:`signature` and the various additional criteria. All
        :obj:`supplemental_configs` are invariably treated as configs and converted
        into :class:`~coma.config.base.Configs` without additional checks besides
        ensuring that the identifiers of supplemental configs do not clash with
        any identifiers in :obj:`signature` or with :obj:`inline_identifier`.

        The distinction between a config and some other parameter in :obj:`signature`
        is determined by inspecting its type annotation (if any), its default value (if
        any), its kind, and whether the parameter identifier is marked as :obj:`inline`.

        An inline parameter is a one-off config field. Specifically, all
        :obj:`inline` parameters are aggregated into a special
        :class:`~coma.config.cli.ParamData.inline_config`, which is backed by a
        programmatic ``dataclass``. This provides all the rigorous runtime type
        validation of a standard ``dataclass``-backed config without requiring
        a dataclass to be created just for those one-off fields. Moreover, inline
        configs are considered non-serializable by default.

        Configs take priority over other parameters: If a parameter **can** be
        considered a config (as per the criteria below), it **is** treated as one.
        A non-config parameter is assumed to be regular parameters **unless** it
        meets the inline criteria (below) in which case it **is** treated as inline.

        Criteria for interpreting a parameter as a config:

        1. The parameter has a type annotation that **exactly** matches one of ``list``,
            ``dict``, or any dataclass type. We refer to these as "config annotations".
        2. The parameter does **not** have a default value. Since configs employ a
            dedicated initialization protocol, default parameter values are not needed.

            .. note::

                This means that a convenient way to ensure that a config-annotated
                parameter is interpreted as a regular parameter is to give it a default.
                For example, :obj:`list_cfg: list` is interpreted as a config whereas
                :obj:`non_cfg_list: list = None` is interpreted as a regular parameter.
        3. The parameter's identifier in not found in :obj:`inline`. Even if the
            parameter has a config annotation, being in :obj:`inline` disqualifies.
        4. **Special case:** Because variadic positional (:obj:`*args`) and variadic
            keyword (:obj:`**kwargs`) parameters cannot be assigned defaults in Python,
            and because they can never be marked as :obj:`inline`, criteria (2) and
            (3) cannot be used. Instead, use the flags :obj:`args_as_config` and
            :obj:`kwargs_as_config`.

        Checklist for interpreting a parameter as inline:

        1. The parameter has a type annotation. A missing annotation is disqualifying.
        2. The parameter has a default value. A missing default value is disqualifying.
            See note below on mutable defaults.
        3. The default value is a valid instance of the annotation type. If not,
            the underlying ``omegaconf`` call will raise a :obj:`ValidationError`.
        4. The parameter's identifier is found in :obj:`inline`. If this is true, but
            one of the above criteria are violated, an error is raised.
        5. The parameter's kind is not variadic positional or variadic keyword. These
            two special cases can be configs or regular parameters, but never inline.

        Mutable inline defaults:

        Because it is un-Pythonic to provide a mutable default value, it can be tricky
        to set a good default value for inline parameters. So, items in :obj:`inline`
        can consist of either just a :data:`~coma.config.base.ParamID`s, or be 2-tuple
        where the first value is a :obj:`ParamID` and the second value is a
        :obj:`default_factory` conforming to the requirements of `dataclasses.field()`_.
        It is an error to give both a signature-level default and an inline-level
        default factory.

        Example:

            Even though :obj:`Data` is a ``dataclass``, it is not considered a config
            because of its non-config annotation and its :obj:`None` default value
            (either one of which is disqualifying on its own). On the other hand,
            :obj:`out_file` can be overridden on the command line because of its
            inline declaration. Any list-like command line arguments are not fed to
            :obj:`*args` because :obj:`args_as_config` is :obj:`False` whereas the
            opposite is true for :obj:`**kwargs` and dict-like command line arguments.

                .. code-block:: python
                    :caption: main.py

                    @dataclass
                    class Data:
                        x: int = 42

                    @dataclass
                    class Config:
                        y: float = 3.14

                    @coma.command(args_as_config=False, inline=["out_file"])
                    def cmd(
                            cfg: Config,
                            data: Optional[Data] = None,
                            out_file: str = "out.txt",
                            *args,
                            **kwargs,
                        ):
                        print("cfg is:", cfg)
                        print("data is:", data or Data())
                        print("out_file is:", out_file)
                        print("*args is:", args)
                        print("*kwargs is:", kwargs)

            Invoking on the command line with some overrides in the following:

                .. code-block:: console

                    $ python main.py cmd x=1 y=2 z inline::out_file=foo.txt
                    cfg is: Config(y=2.0)
                    data is: Data(x=42)
                    out_file is: "foo.txt"
                    *args is: ()
                    *kwargs is: {'x': 1, 'y': 2}

            Notice that:
                1. The list-like argument 'z' is not in :obj:`*args` because
                    :obj:`*args` is not a config.
                2. :obj:`**kwargs` includes both dict-like arguments.
                3. :obj:`out_file` is overridden.
                4. :obj:`out_file` is prefixed with the reserved "inline" config
                    identifier to prevent :obj:`**kwargs` from also containing an
                    "out_file" entry. This prevents a runtime error resulting from
                    "out_file" appearing multiple times in the Callable's parameter list.
                5. Because :obj:`cfg` is a config, it's :obj:`y` attribute was also
                    overridden (this is the default override model where overrides are
                    applied as widely as possible; to disable, see
                    :class:`~coma.config.cli.Override`).
                6. Because :obj:`data` is not a config, it's :obj:`x` attribute is not
                    overridden. In fact, because the default value of :obj:`data` is
                    not replaced in any :deco:`~coma.core.command.command` hook, its
                    value when invoking this command will invariably be :obj:`None`.

        Args:
            signature (inspect.Signature): The signature of the Callable from which
                to create and fill a :class:`~coma.config.cli.ParamData`.
            args_as_config (bool): Whether to treat the variadic positional parameter
                in :obj:`signature` (if any) as a list config or as a regular parameter.
            kwargs_as_config (bool): Whether to treat the variadic keyword parameter
                in :obj:`signature` (if any) as a dict config or as a regular parameter.
            inline_identifier (:data:`~coma.config.base.ConfigID`): The config
                identifier to use for the inline config.
            inline (typing.Sequence): The parameters in :obj:`signature` to mark as
                inline config parameters (if any). Items in this sequence must either
                be :data:`~coma.config.base.ParamID`s or be 2-tuple where the first
                value is a :obj:`ParamID` and the second value is a
                :obj:`default_factory` conforming to the requirements of
                `dataclasses.field()`_.
            **supplemental_configs (:data:`~coma.config.base.Parameters`): Any additional
                parameters not in :obj:`signature` to convert into configs.

        Returns:
            :class:`~coma.config.cli.ParamData`: Filled according to the specifics
                of :obj:`signature` and the various allowance criteria.

        Raises:
            ValueError: If any parameter identifier in :obj:`supplemental_configs`
                matches an existing parameter in :obj:`signature`; or if any parameter
                identifier or supplemental config identifier is the (case-insensitive)
                :obj:`inline_identifier`; or if any parameter is misspecified for its
                type (e.g., missing a default value on an inline parameter).

        .. _dataclasses.field():
            https://docs.python.org/3/library/dataclasses.html#dataclasses.field
        """
        data = cls(
            inline_identifier=inline_identifier,
            supplemental_configs=supplemental_configs,
        )
        cls._process_supplemental_configs(data)
        inline_data = {}
        for p in signature.parameters.values():
            data._check_reserved(p.name)
            if p.name in data.supplemental_configs:
                raise ValueError(f"Identifier also appears in supplemental: {p.name}")
            if p.kind == p.VAR_POSITIONAL:
                cls._process_args(data, p, args_as_config, inline)
            elif p.kind == p.VAR_KEYWORD:
                cls._process_kwargs(data, p, kwargs_as_config, inline)
            elif cls._is_marked_inline(p, inline):
                inline_data[p.name] = cls._get_inline_data(p, inline)
            elif cls._is_list_config(p, inline):
                cls._process_list(data, p, is_config=True)
            elif cls._is_dict_config(p, inline):
                cls._process_dict(data, p, is_config=True)
            elif cls._is_dataclass_config(p, inline):
                cls._process_struct(data, p, is_config=True)
            else:
                cls._process_any(data, p)
        cls._process_inline(data, inline_data, inline)
        return data

    def call_on(
        self,
        fn: Callable[..., T],
        policy: OverridePolicy,
        instance_key: Optional[InstanceKey] = None,
    ) -> T:
        """
        Calls :obj:`fn` using the current state of :obj:`self.configs` and
        :obj:`self.other_parameters`, returning the value of :obj:`fn`.

        Args:
            fn (typing.Callable): The Callable to call using internal signature data.
            policy (:class:`~coma.config.cli.OverridePolicy`): Policy for when some
                keyword-based parameter would override another parameter.
            instance_key (:data:`~coma.config.base.InstanceKey`, optional): The specific
                instance of the various :obj:`self.configs` to pass to :obj:`fn`. If
                :obj:`None`, the latest is used instead. If not :obj:`None`, the same
                key is used for all :obj:`self.configs` and must exist for all of them.

        Returns:
            The return value from calling :obj:`fn`.

        Raises:
            ValueError: If one of the parameters in the signature of :obj:`fn` cannot
                be filled by internal data; or if at least one of the configs was never
                instantiated; or if :obj:`policy` causes a raise on a parameter.
            KeyError: If :obj:`instance_key` is not a valid key for at least one config.
            Others: As may be raised by the underlying ``omegaconf`` implementation of
                the configs.
        """

        self_args, self_kwargs = self._collapse(policy, instance_key=instance_key)
        args, kwargs, args_reached, params_used = [], {}, False, []
        for p in sig(fn).parameters.values():
            non_variadic = p.kind not in [p.VAR_POSITIONAL, p.VAR_KEYWORD]
            missing_value = p.name not in self_kwargs or self_kwargs[p.name] is _EMPTY
            if non_variadic and missing_value:
                raise ValueError(f"Parameter was never filled: {p.name}")
            elif p.kind == p.POSITIONAL_ONLY:
                args.append(self_kwargs[p.name])
                params_used.append(p.name)
            elif p.kind == p.POSITIONAL_OR_KEYWORD:
                if args_reached:
                    kwargs[p.name] = self_kwargs[p.name]
                else:
                    args.append(self_kwargs[p.name])
                params_used.append(p.name)
            elif p.kind == p.VAR_POSITIONAL:
                args.extend(self_args)
                args_reached = True
            elif p.kind == p.KEYWORD_ONLY:
                kwargs[p.name] = self_kwargs[p.name]
                params_used.append(p.name)
            elif p.kind == p.VAR_KEYWORD:
                # Delay until after loop.
                continue
            else:
                # This should never happen unless the stdlib changes.
                raise ValueError(
                    f"Unsupported parameter type: {p.kind} (for parameter: {p.name})"
                )
        # Update 'VAR_KEYWORD' here.
        for name, value in self_kwargs.items():
            if name not in params_used:
                kwargs[name] = value
        return fn(*args, **kwargs)

    def _check_reserved(self, identifier: Identifier):
        if self.is_inline_id(identifier):
            raise ValueError(f"'{identifier}' is a reserved identifier.")
        return identifier

    @staticmethod
    def _process_supplemental_configs(data: "ParamData") -> None:
        supplemental_configs = {}
        for config_id, typ in data.supplemental_configs.items():
            data._check_reserved(config_id)
            if isinstance(typ, list) or isinstance(typ, dict) or is_dataclass(typ):
                supplemental_configs[config_id] = Config(typ)
            elif list in [typ, get_origin(typ)]:
                supplemental_configs[config_id] = Config([])
            elif dict in [typ, get_origin(typ)]:
                supplemental_configs[config_id] = Config({})
            else:
                raise ValueError(f"Unsupported type for '{config_id}': {typ}")
        data.supplemental_configs = supplemental_configs

    @classmethod
    def _is_marked_inline(
        cls,
        p: Parameter,
        inline: _Inline,
    ) -> bool:
        return any(p.name == (d[0] if isinstance(d, tuple) else d) for d in inline)

    @classmethod
    def _is_list_config(
        cls,
        p: Parameter,
        inline: _Inline,
    ) -> bool:
        return cls._is_list_or_dict_config(p, list, inline)

    @classmethod
    def _is_dict_config(
        cls,
        p: Parameter,
        inline: _Inline,
    ) -> bool:
        return cls._is_list_or_dict_config(p, dict, inline)

    @classmethod
    def _is_list_or_dict_config(
        cls,
        p: Parameter,
        which_type: type,
        inline: _Inline,
    ) -> bool:
        if cls._is_marked_inline(p, inline):
            return False
        if p.default is not p.empty:
            return False
        return which_type in [p.annotation, get_origin(p.annotation)]

    @classmethod
    def _is_dataclass_config(
        cls,
        p: Parameter,
        inline: _Inline,
    ) -> Optional[Any]:
        if cls._is_marked_inline(p, inline):
            return False
        if p.default is not p.empty:
            return False
        return is_dataclass(p.annotation)

    @staticmethod
    def _get_inline_data_for_param(
        p: Parameter,
        inline: _Inline,
    ) -> tuple[ParamID, Union[Literal["_EMPTY"], Callable[[], Any]]]:
        for d in inline:
            if isinstance(d, tuple):
                param_id, default_factory = d
            else:
                param_id, default_factory = d, _EMPTY
            if p.name == param_id:
                return param_id, default_factory
        raise ValueError(f"Parameter is missing inline data: {p.name}")

    @classmethod
    def _get_inline_data(
        cls,
        p: Parameter,
        inline: _Inline,
    ) -> tuple[type, Field]:
        param_id, default_factory = cls._get_inline_data_for_param(p, inline)
        if p.default is p.empty and default_factory is _EMPTY:
            raise ValueError(
                f"Missing mandatory default value for inline parameter: {p.name}"
            )
        if p.default is not p.empty and default_factory is not _EMPTY:
            raise ValueError(
                f"Duplicate default declaration for inline parameter '{p.name}': "
                f"value='{p.default}' and factory='{default_factory.__name__}'"
            )
        if p.annotation is p.empty:
            raise ValueError(
                f"Missing mandatory type annotation for inline parameter: {p.name}"
            )
        kwargs = {}
        if p.default is not p.empty:
            kwargs["default"] = p.default
        if default_factory is not _EMPTY:
            kwargs["default_factory"] = default_factory
        return p.annotation, field(**kwargs)

    @staticmethod
    def _process_any(
        data: "ParamData", p: Parameter, alt_default: Any = _EMPTY
    ) -> None:
        default = alt_default if p.default is p.empty else p.default
        data.other_parameters[p.name] = default

    @classmethod
    def _process_args(
        cls,
        data: "ParamData",
        p: Parameter,
        is_config: bool,
        inline: _Inline,
    ):
        if cls._is_marked_inline(p, inline):
            raise ValueError(f"Variadic positional params '{p.name}' cannot be inline.")
        cls._process_list(data, p, is_config=is_config, alt_default=[])
        data.args_id = p.name

    @classmethod
    def _process_kwargs(
        cls,
        data: "ParamData",
        p: Parameter,
        is_config: bool,
        inline: _Inline,
    ):
        if cls._is_marked_inline(p, inline):
            raise ValueError(f"Variadic keyword params '{p.name}' cannot be inline.")
        cls._process_dict(data, p, is_config=is_config, alt_default={})
        data.kwargs_id = p.name

    @classmethod
    def _process_list(
        cls, data: "ParamData", p: Parameter, is_config: bool, alt_default: Any = _EMPTY
    ) -> None:
        cls._process_maybe_config(data, p, is_config, [], alt_default)

    @classmethod
    def _process_dict(
        cls, data: "ParamData", p: Parameter, is_config: bool, alt_default: Any = _EMPTY
    ) -> None:
        cls._process_maybe_config(data, p, is_config, {}, alt_default)

    @classmethod
    def _process_struct(
        cls, data: "ParamData", p: Parameter, is_config: bool, alt_default: Any = _EMPTY
    ) -> None:
        cls._process_maybe_config(data, p, is_config, p.annotation, alt_default)

    @classmethod
    def _process_maybe_config(
        cls,
        data: "ParamData",
        p: Parameter,
        is_config: bool,
        val_if_config: Any,
        alt_default: Any = _EMPTY,
    ) -> None:
        if is_config:
            data.configs[p.name] = Config(val_if_config)
        else:
            cls._process_any(data, p, alt_default)

    @classmethod
    def _process_inline(
        cls,
        data: "ParamData",
        inline_data: dict[ParamID, tuple[type, Any]],
        inline: _Inline,
    ) -> None:
        inline_ids = [(d[0] if isinstance(d, tuple) else d) for d in inline]
        counter = Counter(inline_ids)
        duplicates = [k for k, v in counter.most_common() if v > 1]
        if duplicates:
            s = "" if len(duplicates) == 1 else "s"
            d = f"'{duplicates[0]}'" if len(duplicates) == 1 else duplicates
            raise ValueError(f"Inline parameter{s} declared multiple times: {d}")
        missing = [iid for iid in inline_ids if iid not in inline_data]
        if missing:
            s = "" if len(missing) == 1 else "s"
            d = f"'{missing[0]}'" if len(missing) == 1 else missing
            raise ValueError(f"Inline parameter{s} missing from signature: {d}")
        if inline_data:
            datacls = [(n, t, f) for n, (t, f) in inline_data.items()]
            data.inline_config = Config(make_dataclass(data.inline_identifier, datacls))

    def _collapse(
        self,
        policy: OverridePolicy,
        instance_key: Optional[InstanceKey] = None,
    ) -> tuple[list[str], Parameters]:
        args, kwargs = [], {}
        inline = {}
        if self.inline_config is not None:
            inline = self.inline_config.get_or_latest(instance_key)
        for name, value in inline.items():
            if self._skip(name, value, kwargs, policy):
                continue
            else:
                kwargs[name] = value

        for name, value in self.other_parameters.items():
            if self.args_id is not None and name == self.args_id:
                args = value
            elif self.kwargs_id is not None and name == self.kwargs_id:
                self._add(value, kwargs, policy)
            elif self._skip(name, value, kwargs, policy):
                continue
            else:
                kwargs[name] = value
        for name, value in self.configs.items():
            value = self._as_primitive(value, instance_key)
            if self.args_id is not None and name == self.args_id:
                args = value
            elif self.kwargs_id is not None and name == self.kwargs_id:
                self._add(value, kwargs, policy)
            elif self._skip(name, value, kwargs, policy):
                continue
            else:
                kwargs[name] = value
        return args, kwargs

    @staticmethod
    def _as_primitive(config: Config, key: Optional[InstanceKey]) -> Any:
        val = config.as_primitive(key or config.get_latest_key())
        return val

    def _add(
        self, new_params: Parameters, params: Parameters, policy: OverridePolicy
    ) -> None:
        for name, value in new_params.items():
            if self._skip(name, value, params, policy):
                continue
            params[name] = value

    @staticmethod
    def _skip(name: str, val: Any, params: Parameters, policy: OverridePolicy) -> bool:
        if name in params:
            if policy == OverridePolicy.RAISE:
                raise ValueError(f"Named parameter is defined more than once: {name}")
            elif policy == OverridePolicy.SILENT_SKIP:
                return True
            elif policy == OverridePolicy.VERBOSE_SKIP:
                warnings.warn(
                    f"Skipping override of parameter: {name}: "
                    f"current value={params[name]}; skipped value={val}"
                )
                return True
            elif policy == OverridePolicy.SILENT_OVERRIDE:
                return False
            elif policy == OverridePolicy.VERBOSE_OVERRIDE:
                warnings.warn(f"Overriding parameter: {name}: {params[name]} -> {val}")
                return False
            else:
                raise ValueError(f"Unsupported policy: {policy}")
