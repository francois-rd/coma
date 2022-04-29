"""Cause ``coma`` to temporarily ignore selected configurations or hooks."""
from contextlib import contextmanager
from typing import Iterator

from coma.config import ConfigID

from .initiate import get_initiated
from .internal import MaskHooks


@contextmanager
def forget(
    *config_ids: ConfigID,
    parser_hook: bool = False,
    pre_config_hook: bool = False,
    config_hook: bool = False,
    post_config_hook: bool = False,
    pre_init_hook: bool = False,
    init_hook: bool = False,
    post_init_hook: bool = False,
    pre_run_hook: bool = False,
    run_hook: bool = False,
    post_run_hook: bool = False,
) -> Iterator[None]:
    """Causes ``coma`` to temporarily ignore selected configurations or hooks.

    A context manager that enables :func:`~coma.core.register.register`ing
    sub-commands while selectively ignoring configurations or hooks.

    Example::

        with coma.forget(...):
            coma.register(...)

    .. note::

        Configurations are referenced by identifier whereas hooks are referenced
        by type. For configurations that were provided without an explicit
        identifier to :func:`~coma.core.initiate.initiate`, the automatically-
        derived identifier can be retrieved using :func:`~coma.config.default_id`.

    Args:
        *config_ids: Configurations identifiers of configurations to forget
        parser_hook: Whether to ignore this global hook (if any)
        pre_config_hook: Whether to ignore this global hook (if any)
        config_hook: Whether to ignore this global hook (if any)
        post_config_hook: Whether to ignore this global hook (if any)
        pre_init_hook: Whether to ignore this global hook (if any)
        init_hook: Whether to ignore this global hook (if any)
        post_init_hook: Whether to ignore this global hook (if any)
        pre_run_hook: Whether to ignore this global hook (if any)
        run_hook: Whether to ignore this global hook (if any)
        post_run_hook: Whether to ignore this global hook (if any)

    Returns:
        A Generator yielding a single `None`

    Raises:
        KeyError: If any provided configuration identifier does not correspond
            to a known configuration.

    See also:
        * :func:`~coma.config.default_id`
        * :func:`~coma.core.initiate.initiate`
        * :func:`~coma.core.register.register`
    """
    coma = get_initiated()
    masked_hooks = coma.hooks[-1].copy(
        MaskHooks(
            parser_hook=parser_hook,
            pre_config_hook=pre_config_hook,
            config_hook=config_hook,
            post_config_hook=post_config_hook,
            pre_init_hook=pre_init_hook,
            init_hook=init_hook,
            post_init_hook=post_init_hook,
            pre_run_hook=pre_run_hook,
            run_hook=run_hook,
            post_run_hook=post_run_hook,
        )
    )
    coma.hooks.append(masked_hooks)
    masked_configs = coma.configs[-1].copy()  # This preserves the dict type.
    for config_id in config_ids:
        del masked_configs[config_id]
    coma.configs.append(masked_configs)
    try:
        yield
    finally:
        coma.hooks.pop()
        coma.configs.pop()
