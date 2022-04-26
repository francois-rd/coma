"""Cause ``coma`` to temporarily forget certain hooks."""
from contextlib import contextmanager
from typing import Iterator

from .initiate import get_initiated
from ..hooks.core import MaskHooks


@contextmanager
def forget(
    *,
    parser_hook: bool = False,
    pre_config_hook: bool = False,
    config_hook: bool = False,
    pre_init_hook: bool = False,
    init_hook: bool = False,
    pre_run_hook: bool = False,
    run_hook: bool = False,
    post_run_hook: bool = False
) -> Iterator[None]:
    """Causes ``coma`` to temporarily forget certain hooks.

    A context manager that enables registering sub-commands while selectively
    ignoring global hooks. This is useful for overriding global hooks.

    Args:
        parser_hook: Whether to ignore this global hook (if any)
        pre_config_hook: Whether to ignore this global hook (if any)
        config_hook: Whether to ignore this global hook (if any)
        pre_init_hook: Whether to ignore this global hook (if any)
        init_hook: Whether to ignore this global hook (if any)
        pre_run_hook: Whether to ignore this global hook (if any)
        run_hook: Whether to ignore this global hook (if any)
        post_run_hook: Whether to ignore this global hook (if any)

    Returns:
        A Generator yielding a single `None`

    See also:
        :func:`~coma.core.initiate.initiate`
        :func:`~coma.core.register.register`
    """
    coma = get_initiated()
    coma.hooks.append(
        coma.hooks[-1].copy(
            MaskHooks(
                parser_hook=parser_hook,
                pre_config_hook=pre_config_hook,
                config_hook=config_hook,
                pre_init_hook=pre_init_hook,
                init_hook=init_hook,
                pre_run_hook=pre_run_hook,
                run_hook=run_hook,
                post_run_hook=post_run_hook,
            )
        )
    )
    try:
        yield
    finally:
        coma.hooks.pop()
