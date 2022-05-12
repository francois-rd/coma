"""Core post config hooks and utilities."""
from typing import Any, Callable, Dict, List

from coma.config import to_dict
from coma.config.cli import override

from .utils import hook, sequence


def single_cli_override_factory(
    config_id: str, cli_override: Callable = override
) -> Callable[..., Dict[str, Any]]:
    """Factory for overriding a configuration's attributes with command line arguments.

    Overriding is achieved by calling :obj:`cli_override`, which, by default,
    is :func:`coma.config.cli.override`. Slight alternatives to can be created
    using :func:`coma.config.cli.override_factory`. Alternatively, a user-
    provided function can also be used.

    Example:
        Change separator to "~"::

            coma.initiate(..., post_config_hook=override_factory(sep="~"))

    Args:
        config_id: A configuration identifier
        cli_override: Function to override config attributes with command line args

    Returns:
        A post config hook

    See also:
        * :func:`coma.config.cli.override_factory`
        * :func:`coma.hooks.config_hook.single_load_and_write_factory`
        * TODO(invoke; protocol) for details on config hooks
    """

    @hook
    def _hook(unknown_args: List[str], configs: Dict[str, Any]) -> Dict[str, Any]:
        return to_dict((config_id, cli_override(config_id, configs, unknown_args)))

    return _hook


def multi_cli_override_factory(
    cli_override: Callable = override,
) -> Callable[..., Dict[str, Any]]:
    """Overrides multiple configs' attributes with corresponding command line arguments.

    Equivalent to calling
    :func:`~coma.hooks.post_config_hook.single_cli_override_factory`
    for each configuration with :obj:`cli_override` passed along.

    See :func:`coma.hooks.post_config_hook.single_cli_override_factory` for details.
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

An alias for :func:`coma.hooks.post_config_hook.multi_cli_override_factory`
called with default arguments.
"""
