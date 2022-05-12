"""Core implementation of the ``coma`` user interface.

See TODO(basic; advanced) for details.
"""
from typing import Any, Callable, Dict, List, Optional

# Lib/dataclasses in Python>=3.7
# dataclasses from https://pypi.org/project/dataclasses/ in Python>=3.6,<3.7
from dataclasses import dataclass, fields, replace

from coma.hooks import sequence


class Coma:
    """Singleton class for ``coma``.

    Attributes:
        parser (:class:`argparse.ArgumentParser`): The argument parser to use
        subparsers: The special action object returned by
            :func:`~argparse.ArgumentParser.add_subparsers`
        commands_registered (bool): Whether at least one sub-command was
            successfully added using `subparsers`
        hooks: A stack of :class:`Hooks`
        configs: A stack of :obj:`coma.config.ConfigDict`
    """

    coma: "Coma" = None

    def __init__(self):
        """See :class:`~coma.core.Coma`."""
        self.parser = None
        self.subparsers = None
        self.commands_registered: bool = False
        self.hooks: List[Hooks] = []
        self.configs: List[Dict[str, Any]] = []


def get_instance() -> Coma:
    """Returns the singleton of :class:`Coma`."""
    if Coma.coma is None:
        Coma.coma = Coma()
    return Coma.coma


@dataclass
class MaskHooks:
    """Whether a given hook should be masked or not when copying a :class:`Hooks`."""

    parser_hook: bool = False

    pre_config_hook: bool = False
    config_hook: bool = False
    post_config_hook: bool = False

    pre_init_hook: bool = False
    init_hook: bool = False
    post_init_hook: bool = False

    pre_run_hook: bool = False
    run_hook: bool = False
    post_run_hook: bool = False


@dataclass
class Hooks:
    """A collection of all hooks that ``coma`` accepts."""

    parser_hook: Optional[Callable] = None

    pre_config_hook: Optional[Callable] = None
    config_hook: Optional[Callable] = None
    post_config_hook: Optional[Callable] = None

    pre_init_hook: Optional[Callable] = None
    init_hook: Optional[Callable] = None
    post_init_hook: Optional[Callable] = None

    pre_run_hook: Optional[Callable] = None
    run_hook: Optional[Callable] = None
    post_run_hook: Optional[Callable] = None

    def copy(self, mask_hooks: Optional[MaskHooks] = None) -> "Hooks":
        """Creates a shallow copy with all the same hooks except those that are
        masked (if any).

        Args:
            mask_hooks: Which hooks to mask when making the copy

        Returns:
            A shallow copy
        """
        kwargs = {}
        if mask_hooks is not None:
            kwargs = {
                field.name: None
                for field in fields(self)
                if getattr(mask_hooks, field.name)
            }
        return replace(self, **kwargs)

    def merge(self, other: "Hooks") -> "Hooks":
        """Merges two :class:`Hooks` together.

        Creates a :func:`~coma.hooks.utils.sequence` if necessary.

        Args:
             other: Another Hooks object

        Returns:
            A merged Hooks object.
        """
        kwargs = {}
        for field in fields(self):
            self_field = getattr(self, field.name)
            other_field = getattr(other, field.name)
            if self_field is None:
                if other_field is None:
                    value = None
                else:
                    value = other_field
            else:
                if other_field is None:
                    value = self_field
                else:
                    value = sequence(self_field, other_field)
            kwargs[field.name] = value
        return Hooks(**kwargs)
