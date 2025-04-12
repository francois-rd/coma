"""Base of config utilities implementation."""

from typing import Any, Optional, TypeVar
from dataclasses import dataclass, field

from omegaconf.basecontainer import BaseContainer
from omegaconf.base import SCMode
from omegaconf import OmegaConf


class InstanceKeys:
    """
    Collection of standard instance keys used for :class:`~coma.config.base.Config`
    in core ``coma``. User-defined keys beyond these can exist.

    Attributes:
        BASE: The base instance that results from direct initialization.
        FILE: The instance that results from loading a config from file.
        OVERRIDE: The instance that results from overriding another instance
            with command-line arguments.
    """

    BASE: "InstanceKey" = "BASE"
    FILE: "InstanceKey" = "FILE"
    OVERRIDE: "InstanceKey" = "OVERRIDE"


T = TypeVar("T")


InstanceKey = str
"""Type alias for instance keys."""

Identifier = str
"""Type alias for a valid Python identifier."""

ConfigID = Identifier
"""Type alias for config identifiers. Must be a valid Python identifier."""

Configs = dict[ConfigID, "Config"]
"""
Type alias for mapping between config identifiers and 
:class:`~coma.config.base.Config` s.
"""

ParamID = Identifier
"""Type alias for parameter identifiers. Must be a valid Python identifier."""

Parameters = dict[ParamID, Any]
"""Type alias for a mapping between parameter identifiers and values."""


@dataclass
class Config:
    """
    Wrapper for config data. Manages all viable instances of a config. Typically, a new
    instance *variant* is created whenever major changes to the config data are made.

    Attributes:
        back_end (typing.Any): The backing construct of the config. Must be an
            ``omegaconf``-supported type, which means either a ``list`` object, a
            ``dict`` object, or a ``dataclass`` type or object.
        instances (dict[:data:`~coma.config.base.InstanceKey`, typing.Any]): The
            collection of instance variants of :obj:`back_end` mapped by variant keys.
    """

    back_end: Any
    instances: dict[InstanceKey, Any] = field(default_factory=dict)

    def has(self, key: InstanceKey) -> bool:
        """Returns whether this Config has an instance corresponding to :obj:`key`."""
        return key in self.instances

    def get(self, key: InstanceKey) -> Any:
        """
        Returns the instance corresponding to :obj:`key`.

        Args:
            key (:data:`~coma.config.base.InstanceKey`): The instance key.

        Returns:
            typing.Any: The corresponding instance.

        Raises:
            KeyError: If no corresponding instance exists.
        """
        return self.instances[key]

    def set(self, key: InstanceKey, instance: Any, force_latest: bool = False) -> None:
        """
        Sets or updates the instance corresponding to :obj:`key`.

        Args:
            key (:data:`~coma.config.base.InstanceKey`): The instance variant key
                for which to set or update the instance data.
            instance (typing.Any): The instance data to set for :obj:`key`.
            force_latest (bool): Whether to force :obj:`key` to be interpreted
                as the latest (at least until the next call to :obj:`set()`).

        See also:
            * :meth:`~coma.config.base.Config.get_latest()`
            * :meth:`~coma.config.base.Config.get_latest_key()`
        """
        if force_latest:
            self.delete(key, raise_on_missing=False)
        self.instances[key] = instance

    def delete(self, key: InstanceKey, raise_on_missing: bool = False) -> None:
        """
        Deletes the instance corresponding to :obj:`key`.

        Args:
            key (:data:`~coma.config.base.InstanceKey`): The instance variant key
                for which to delete the instance data.
            raise_on_missing (bool): Whether to raise an error when no instance
                variant corresponding to :obj:`key` exists or no nothing silently.

        Raises:
            KeyError: If no instance corresponding to :obj:`key` exists and
                :obj:`raise_on_missing` is :obj:`True`.
        """
        if raise_on_missing or self.has(key):
            del self.instances[key]

    def get_latest(self) -> Any:
        """
        Returns the latest instance.

        .. note::

            This is the latest by *insertion* order. Newer overwrites of existing
            instances don't count as latest unless :obj:`force_latest` is :obj:`True`
            on calls to :meth:`~coma.config.base.Config.set()`.

        Raises:
            ValueError: If there are no instances at all and so no latest instance.

        See also:
            * :meth:`~coma.config.base.Config.get_latest_key()`
        """
        return self.instances[self.get_latest_key()]

    def get_latest_key(self) -> InstanceKey:
        """
        Returns the key of the latest instance.

        .. note::

            This is the latest by *insertion* order. Newer overwrites of existing
            instances don't count as latest unless :obj:`force_latest` is :obj:`True`
            on calls to :meth:`~coma.config.base.Config.set()`.

        Returns:
            :data:`~coma.config.base.InstanceKey`: The key corresponding to the
            latest instance to be set.

        Raises:
            ValueError: If there are no instances at all and so no latest instance.

        See also:
            * :meth:`~coma.config.base.Config.get_latest()`
        """
        try:
            return list(self.instances.keys())[-1]
        except IndexError:
            raise ValueError(f"No instances exist from which to retrieve the latest.")

    def get_or_latest(self, key: Optional[InstanceKey] = None) -> Any:
        """
        Returns the instance corresponding to :obj:`key` *unless* :obj:`key` is
        :obj:`None` in which case the latest instance is returned instead.

        Returns:
            typing.Any: The corresponding instance.

        Raises:
            KeyError: If :obj:`key` is not :obj:`None`, but no corresponding
                instance exists.
            ValueError: If :obj:`key` is :obj:`None`, but there are no instances
                at all and so no latest instance.

        See also:
            * :meth:`~coma.config.base.Config.get_latest()`
        """
        return self.get_latest() if key is None else self.get(key)

    def make_latest(self, key: InstanceKey) -> None:
        """
        Forces the given :obj:`key` to be interpreted as the latest (at least
        until a new key gets added).

        Raises:
            KeyError: If no corresponding instance exists.

        See also:
            * :meth:`~coma.config.base.Config.get_latest()`
        """
        self.set(key, self.get(key), force_latest=True)

    def is_primitive(self, key: InstanceKey) -> bool:
        """
        Returns whether the instance data corresponding to :obj:`key` is a
        primitive Python object (``list``, ``dict``, or ``dataclass``) as
        opposed to an ``omegaconf`` container object.

        Raises:
            KeyError: If no corresponding instance exists.
        """
        return not OmegaConf.is_config(self.get(key))

    def as_primitive(
        self,
        key: InstanceKey,
        *,
        resolve: bool = True,
        throw_on_missing: bool = True,
        enum_to_str: bool = False,
        structured_config_mode: SCMode = SCMode.INSTANTIATE,
    ) -> Any:
        """
        Returns the instance data corresponding to :obj:`key` as a primitive
        Python object (``list``, ``dict``, or ``dataclass``) instead of an
        ``omegaconf`` container object.

        If the instance is already primitive, returns it directly.

        Does not update the underlying instance. To do so, use
        :meth:`~coma.config.base.Config.set()`.

        Args:
            key (:data:`~coma.config.base.InstanceKey`): The instance variant
                key for which to convert the instance data into a primitive.
            resolve (bool): Passed to `OmegaConf.to_container()`_.
            throw_on_missing (bool): Passed to `OmegaConf.to_container()`_.
            enum_to_str (bool): Passed to `OmegaConf.to_container()`_.
            structured_config_mode (:class:`omegaconf.base.SCMode`): Passed to
                `OmegaConf.to_container()`_.

        Returns:
            typing.Any: The instance data for :obj:`key` as a Python primitive.

        Raises:
            KeyError: If no corresponding instance exists.
            Others: As may be raised by `OmegaConf.to_container()`_.

        .. _OmegaConf.to_container():
            https://omegaconf.readthedocs.io/en/2.1_branch/usage.html#omegaconf-to-container
        """
        if self.is_primitive(key):
            return self.get(key)
        return OmegaConf.to_container(
            self.get(key),
            resolve=resolve,
            throw_on_missing=throw_on_missing,
            enum_to_str=enum_to_str,
            structured_config_mode=structured_config_mode,
        )

    def from_primitive(
        self,
        key: InstanceKey,
        *,
        parent: Optional[BaseContainer] = None,
        flags: Optional[dict[str, bool]] = None,
    ) -> Any:
        """
        Returns the instance data corresponding to :obj:`key` as an ``omegaconf``
        container object instead of a primitive Python object (``list``, ``dict``,
        or ``dataclass``).

        If the instance is already an ``omegaconf`` container, returns it directly.

        Does not update the underlying instance. To do so, use
        :meth:`~coma.config.base.Config.set()`.

        Args:
            key (:data:`~coma.config.base.InstanceKey`): The instance variant
                key for which to convert the instance data into a primitive.
            parent (:class:`omegaconf.basecontainer.BaseContainer`, optional):
                Passed to `OmegaConf.create()`_.
            flags (dict[str, bool], optional): Passed to `OmegaConf.create()`_.

        Returns:
            typing.Any: The instance data for :obj:`key` as an ``omegaconf`` container.

        Raises:
            KeyError: If no corresponding instance exists.
            Others: As may be raised by `OmegaConf.create()`_.

        .. _OmegaConf.create():
            https://omegaconf.readthedocs.io/en/2.1_branch/usage.html#creating
        """
        if self.is_primitive(key):
            return OmegaConf.create(self.get(key), parent, flags)
        return self.get(key)
