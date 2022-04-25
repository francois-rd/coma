"""Dataclasses for hook management."""
from dataclasses import dataclass
from dataclasses import fields
from dataclasses import replace
from typing import Callable, Optional

from .utils import sequence


@dataclass()
class MaskHooks:
    parser_hook: bool = False
    pre_config_hook: bool = False
    config_hook: bool = False
    pre_init_hook: bool = False
    init_hook: bool = False
    pre_run_hook: bool = False
    run_hook: bool = False
    post_run_hook: bool = False


@dataclass()
class Hooks:
    parser_hook: Optional[Callable] = None
    pre_config_hook: Optional[Callable] = None
    config_hook: Optional[Callable] = None
    pre_init_hook: Optional[Callable] = None
    init_hook: Optional[Callable] = None
    pre_run_hook: Optional[Callable] = None
    run_hook: Optional[Callable] = None
    post_run_hook: Optional[Callable] = None

    def copy(self, mask_hooks: Optional[MaskHooks] = None) -> 'Hooks':
        """Creates a shallow copy with all the same hooks except those that are
        masked (if any).

        Args:
            mask_hooks: Which hooks to mask when making the copy

        Returns:
            A shallow copy
        """
        kwargs = {}
        if mask_hooks is not None:
            kwargs = {field.name: None for field in fields(self)
                      if getattr(mask_hooks, field.name)}
        return replace(self, **kwargs)

    def merge(self, other: 'Hooks') -> 'Hooks':
        """Merges two :class:`~coma.hooks.core.Hooks` together.

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
