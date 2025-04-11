"""Backend singleton of ``coma`` implementation."""

from dataclasses import dataclass
from typing import TypeVar

from ..config import Parameters
from ..hooks.base import CommandName, HookData
from ..hooks.management import Hooks


T = TypeVar("T", bound=HookData)


@dataclass
class RegistrationData(HookData):
    """All data needed to register a command with ``coma``."""

    hooks: Hooks
    parser_kwargs: Parameters

    def to(self, other: type[T], **kwargs) -> T:
        """Convert this data to another HookData subtype."""
        return other(
            name=self.name,
            command=self.command,
            parameters=self.parameters,
            persistence_manager=self.persistence_manager,
            **kwargs,
        )


class Coma:
    """Singleton class for ``coma``.

    Attributes:
        _registrations (dict[:data:`~coma.hooks.base.CommandName`, :class:`~coma.core.singleton.RegistrationData]):
            Mapping between registered command names and the corresponding
            registration data.
    """

    _registrations: dict[CommandName, RegistrationData] = {}  # Singleton data.

    @classmethod
    def register(cls, data: RegistrationData) -> None:
        """
        Registers a new command via its data.

        Args:
            data (:class:`~coma.core.singleton.RegistrationData): The command
                registration data.

        Raises:
            ValueError: If a command with the same name is already registered.
        """
        if data.name in cls._registrations:
            raise ValueError(f"Command name is already registered: {data.name}")
        cls._registrations[data.name] = data

    @classmethod
    def get_registrations(cls) -> dict[CommandName, RegistrationData]:
        """Returns all current registrations."""
        return cls._registrations

    @classmethod
    def reset(cls) -> None:
        """Deletes all current registrations."""
        cls._registrations = {}
