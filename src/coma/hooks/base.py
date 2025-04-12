"""Base of hook utilities implementation."""

from typing import Any, Callable, Optional, TypeVar, Union
from dataclasses import dataclass
from collections.abc import Sequence
from enum import Enum
import argparse


from ..config import ParamData, PersistenceManager

T = TypeVar("T")


# https://stackoverflow.com/questions/69239403/type-hinting-parameters-with-a-sentinel-value-as-the-default
class HookSentinels(Enum):
    """
    Type for sentinels for hooks.

    Attributes:
        DEFAULT: Replace a hook marked as this with a default hook.
        SHARED: Replace a command-specific hook marked as this with a shared hook.

    See also:
        * :meth:`~coma.hooks.management.Hooks.merge()`
    """

    DEFAULT = 0
    SHARED = 1


class GeneralSentinel(Enum):
    """Type for the sentinel of general use."""

    token = 0


DEFAULT = HookSentinels.DEFAULT
"""
Sentinel for marking a hook to either :func:`~coma.core.command.command()` or
:func:`~coma.core.wake.wake()` as being a default hook. The runtime value of
the hook will be replaced by the corresponding ``coma`` default.

Recall that a hook can also be defined as a (recursive) sequence. Each occurrence
of :obj:`DEFAULT` in said sequence will be replaced by the ``coma`` default.
"""

SHARED = HookSentinels.SHARED
"""
Sentinel for marking that a hook to :deco:`~coma.core.command.command` ought be
be replaced at runtime with the runtime value of the corresponding hook from
:func:`~coma.core.wake.wake()`.

Recall that a hook can also be defined as a (recursive) sequence. Each occurrence
of :obj:`SHARED` in said sequence will be replaced by the :obj:`wake()` value.

:obj:`SHARED` is not a legal value for :obj:`wake()` hooks to avoid infinite regress.
"""

SENTINEL = GeneralSentinel.token
"""
A convenient pre-defined sentinel for general use. Unlike other sentinels in ``coma``,
:obj:`SENTINEL` has no special semantic value beyond its existence as a sentinel.
"""

Hook = Callable[[T], Optional[T]]
"""
Base definition of a "raw" ``coma`` hook. A valid hook is typically a procedural
function (modifying its input parameter in place and returning :obj:`None`). However,
returning an instance of the same type :obj:`T` is also permitted to account for cases
where :obj:`T` is an immutable type. A non-:obj:`None` return value takes precedence:
it replaces the procedural parameter is all downstream hooks in a hook pipeline.
Typically, :obj:`T` is a subclass of :class:`~coma.hooks.base.HookData`.

Alias:
"""

HookOrSentinels = Union[Hook, HookSentinels, None]
"""
A :data:`~coma.hooks.base.Hook` or one of the valid hook sentinels:
:data:`~coma.hooks.base.DEFAULT`, :data:`~coma.hooks.base.SHARED`, or :obj:`None`.

Alias:
"""

AugmentedHook = Union[HookOrSentinels, Sequence[HookOrSentinels]]
"""
A :data:`~coma.hooks.base.HookOrSentinels`, or any (recursive) :obj:`Sequence`
thereof.

Example::

    parser_hook=(
        DEFAULT, (
            SHARED, (
                add_argument_factory(...),
                None,
            ),
        ),
        add_argument_factory(...),
    )
    
Alias:
"""

CommandName = str
"""
The name under which to register a command with ``coma``. The same value is used to
invoke the command on the command line. Any value allowed by ``argparse`` is allowed.
"""

Command = Union[Callable, type]
"""
Any function or any class with (by default) a no-argument :obj:`run()` method. Configs
are inferred from the command signature. See :func:`~coma.core.command.command()`.
"""


@dataclass
class HookData:
    """
    Base class for typical :data:`~coma.hooks.base.Hook` arguments.

    Attributes:
        name (:data:`~coma.hooks.base.CommandName`): The command name.
        command (:data:`~coma.hooks.base.Command`, optional): The command itself.
        parameters (:class:`~coma.config.cli.ParamData`): The command's parameters.
        persistence_manager (:class:`~coma.config.io.PersistenceManager`): The
            manager for serializing configs in :obj:`parameters`.
    """

    name: CommandName
    command: Command
    parameters: ParamData
    persistence_manager: PersistenceManager


@dataclass
class ParserData(HookData):
    """
    The :class:`~coma.hooks.base.HookData` for parser hooks.

    Attributes:
        parser (argparse.ArgumentParser): The sub-parser for this :obj:`command`.
    """

    parser: argparse.ArgumentParser


@dataclass
class InvocationData(HookData):
    """
    The :class:`~coma.hooks.base.HookData` for all invocation hooks.

    Attributes:
        known_args (typing.Any): The :obj:`namespace` of known command line arguments.
            Typically, this is the first return value of `parse_known_args()`_.
        unknown_args (list[str]): The list of unknown command line arguments.
            Typically, this is the second return value of `parse_known_args()`_.
        result (typing.Any, optional): The return value from invoking :obj:`command`.

    .. _parse_known_args():
        https://docs.python.org/3/library/argparse.html#partial-parsing
    """

    known_args: Any
    unknown_args: list[str]
    result: Optional[Any] = None


def identity(arg: T) -> T:
    """A no-op :data:`~coma.hooks.base.Hook`. For convenience."""
    return arg


class Pipe:
    """
    A convenience wrapper for sequences of :data:`~coma.hooks.base.Hook` s.

    Recursively composes functions, which can then be invoked with a single call.

    Args:
        *fns (typing.Union[:data:`~coma.hooks.base.Hook`, typing.Sequence[:data:`~coma.hooks.base.Hook`]]):
            The :data:`~coma.hooks.base.Hook`s to recursively compose (in order).
    """

    def __init__(self, *fns: Union[Hook, Sequence[Hook]]):
        self.fns = [(Pipe(*f) if isinstance(f, Sequence) else f) for f in fns]
        self.fns = self.fns or [identity]

    def __call__(self, arg: T) -> T:
        """Recursively calls the composed functions, returning the final result."""
        for f in self.fns:
            arg = f(arg) or arg
        return arg
