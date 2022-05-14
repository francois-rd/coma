"""Temporarily forget selected global configs or hooks while in a coma."""
from contextlib import contextmanager
from typing import Iterator

from .initiate import get_initiated
from .internal import MaskHooks


@contextmanager
def forget(
    *config_ids: str,
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
    """Temporarily forget selected global configs or hooks while in a coma.

    A context manager that enables :func:`~coma.core.register.register`\\ ing
    commands while selectively forgetting global configs or hooks.

    Example::

        with coma.forget(...):
            coma.register(...)

    .. note::

        Configs are referenced by identifier whereas hooks are referenced by
        type. For configs that were :func:`~coma.core.initiate.initiate`\\ d or
        :func:`~coma.core.register.register`\\ ed without an explicit identifier,
        the automatically-derived identifier can be retrieved programmatically
        using :func:`~coma.config.utils.default_id`.

    Args:
        *config_ids (str): Identifiers of global configs to temporarily forget
        parser_hook (bool): Whether to ignore the global parser hook (if any)
        pre_config_hook (bool): Whether to ignore the global pre config hook (if any)
        config_hook (bool): Whether to ignore the global config hook (if any)
        post_config_hook (bool): Whether to ignore the global post config hook (if any)
        pre_init_hook (bool): Whether to ignore the global pre init hook (if any)
        init_hook (bool): Whether to ignore the global init hook (if any)
        post_init_hook (bool): Whether to ignore the global post init hook (if any)
        pre_run_hook (bool): Whether to ignore the global pre run hook (if any)
        run_hook (bool): Whether to ignore the global run hook (if any)
        post_run_hook (bool): Whether to ignore the global post run hook (if any)

    Returns:
        A generator yielding a single :obj:`None`

    Raises:
        KeyError: If any provided config identifier does not match any known config

    See also:
        * :func:`~coma.core.initiate.initiate`
        * :func:`~coma.core.register.register`
        * :func:`~coma.config.utils.default_id`
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
