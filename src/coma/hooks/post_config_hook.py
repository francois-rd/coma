"""Post config hook utilities, factories, and defaults."""

from typing import Any, Callable, Dict, List

from ..config import to_dict
from ..config.cli import override

from .utils import hook, sequence


def single_cli_override_factory(
    config_id: str, cli_override: Callable = override
) -> Callable[..., Dict[str, Any]]:
    """Factory for creating a post config hook that overrides a config's attributes.

    Overriding with command line arguments is achieved by calling :obj:`cli_override`,
    which is :func:`~coma.config.cli.override` by default. Slight alternatives
    can be created using :func:`~coma.config.cli.override_factory`.
    Alternatively, a custom function can also be used.

    Example:

        Change separator to :obj:`"~"`::

            coma.initiate(..., post_config_hook=override_factory(sep="~"))

    Args:
        config_id (str): A config identifier
        cli_override (typing.Callable): Function to override config attributes
            with command line arguments

    Returns:
        A post config hook

    See also:
        * :func:`~coma.config.cli.override_factory`
        * :func:`~coma.hooks.config_hook.single_load_and_write_factory`
    """

    @hook
    def _hook(unknown_args: List[str], configs: Dict[str, Any]) -> Dict[str, Any]:
        return to_dict((config_id, cli_override(config_id, configs, unknown_args)))

    return _hook


def multi_cli_override_factory(
    cli_override: Callable = override,
) -> Callable[..., Dict[str, Any]]:
    """Factory for creating a post config hook that overrides attributes of all configs.

    Equivalent to calling
    :func:`~coma.hooks.post_config_hook.single_cli_override_factory` for each
    config with :obj:`cli_override` passed along. See
    :func:`~coma.hooks.post_config_hook.single_cli_override_factory` for details.
    """

    @hook
    def _hook(unknown_args: List[str], configs: Dict[str, Any]) -> Dict[str, Any]:
        fns = [single_cli_override_factory(cid, cli_override) for cid in configs]
        configs_list = []
        if fns:
            configs_list: List[Dict[str, Any]] = sequence(*fns, return_all=True)(
                unknown_args=unknown_args,
                configs=configs,
            )
        return to_dict(*[(cid, c) for cd in configs_list for cid, c in cd.items()])

    return _hook


default = multi_cli_override_factory()
"""Default post config hook.

An alias for calling :func:`~coma.hooks.post_config_hook.multi_cli_override_factory`
with default arguments.
"""
