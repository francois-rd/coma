"""Utilities for managing recursive sequences of shared and command-specific hooks."""

from dataclasses import dataclass, fields
from collections.abc import Sequence

from . import config_hook
from . import init_hook
from . import run_hook
from . import parser_hook

from .base import AugmentedHook, Hook, Pipe, DEFAULT, SHARED, T, identity


@dataclass
class Hooks:
    """A collection of all hooks that ``coma`` accepts."""

    parser_hook: AugmentedHook = None

    pre_config_hook: AugmentedHook = None
    config_hook: AugmentedHook = None
    post_config_hook: AugmentedHook = None

    pre_init_hook: AugmentedHook = None
    init_hook: AugmentedHook = None
    post_init_hook: AugmentedHook = None

    pre_run_hook: AugmentedHook = None
    run_hook: AugmentedHook = None
    post_run_hook: AugmentedHook = None

    @staticmethod
    def merge(shared_hooks: "Hooks", command_hooks: "Hooks") -> "Hooks":
        """
        Returns a merged :obj:`Hooks` where the :obj:`shared_hooks` form the base and
        the :obj:`command_hooks` (which take precedence) are able to override this base.

        Specifically, each hook in :obj:`command_hooks` can be either a plain
        :data:`~coma.hooks.base.HookOrSentinels` or a :obj:`Sequence`
        thereof. If plain, the hook is transformed as below. If a sequence, each
        item in that sequence is recursively transformed as below, with the result
        being a new sequence of transformed items in the same order.

        Transformation process for a plain hook item in :obj:`command_hooks`:

            1. If the hook is :obj:`None` (not :func:`~coma.hooks.base.identity`),
            then set the merged hook to :obj:`identity` regardless of the value
            of the corresponding hook in :obj:`shared_hooks`.
            2. If the hook is the :data:`~coma.hooks.base.SHARED` sentinel, then set
            the merged hook to the corresponding hook from :obj:`shared_hooks`.
            3. If the hook is the :data:`~coma.hooks.base.DEFAULT` sentinel, then set
            the merged hook to the corresponding default hook regardless of the
            value of the corresponding hook in :obj:`shared_hooks`.
            4. For all other values of hook (including :obj:`identity`), set the
               merged hook to said value (unchanged).

        When case (2) applies, the corresponding hook in :obj:`shared_hooks` is also
        recursively transformed according to this process, that a shared hook
        **cannot** be set to the :obj:`SHARED` sentinel to avoid infinite regress.

        Returns:
            Hooks: The merged hooks.

        Raises:
            ValueError: If a shared hook is or contains the :obj:`SHARED` sentinel.
        """
        kwargs = {}
        for f in fields(Hooks):
            # Command hook takes precedence but can be replaced by the (cleaned up)
            # shared hook wherever the SHARED sentinel is detected.
            shared_hook = getattr(shared_hooks, f.name)
            shared_hook = Hooks._cleanup(shared_hook, f.name, raise_on_shared=True)
            command_hook = getattr(command_hooks, f.name)
            kwargs[f.name] = Hooks._cleanup(command_hook, f.name, shared=shared_hook)
        return Hooks(**kwargs)

    @classmethod
    def _cleanup(
        cls,
        fn: AugmentedHook,
        field_name: str,
        shared: Hook = identity,
        raise_on_shared: bool = False,
    ) -> Hook:
        if fn is None:
            return identity
        if fn is DEFAULT:
            return getattr(_DEFAULT_HOOKS, field_name)
        if fn is SHARED:
            if raise_on_shared:
                raise ValueError(
                    f"Shared hook cannot itself be the SHARED sentinel: {field_name}"
                )
            return shared
        if isinstance(fn, Sequence):
            fns = [cls._cleanup(f, field_name, shared, raise_on_shared) for f in fn]
            return Pipe(*fns) if fns else identity
        return fn

    def parse(self, arg: T) -> None:
        """Calls the parser hook on :obj:`arg`."""
        self._cleanup(self.parser_hook, "parser_hook", raise_on_shared=True)(arg)

    def invoke(self, arg: T) -> None:
        """Calls the entire invocation hook pipeline in order on :obj:`arg`."""
        fns = [
            self._cleanup(getattr(self, f.name), f.name, raise_on_shared=True)
            for f in fields(self)
            if f.name != "parser_hook"
        ]
        Pipe(*fns)(arg)


_DEFAULT_HOOKS = Hooks(
    parser_hook=parser_hook.default_factory(),
    pre_config_hook=identity,
    config_hook=config_hook.default_factory(),
    post_config_hook=identity,
    pre_init_hook=identity,
    init_hook=init_hook.default_factory(),
    post_init_hook=identity,
    pre_run_hook=identity,
    run_hook=run_hook.default_factory(),
    post_run_hook=identity,
)
