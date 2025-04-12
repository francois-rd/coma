"""Init hook default factory."""

from typing import Optional

from .base import Hook, InvocationData
from ..config import InstanceKey, OverridePolicy


def default_factory(
    policy: OverridePolicy = OverridePolicy.RAISE,
    instance_key: Optional[InstanceKey] = None,
) -> Hook:
    """
    Factory for creating an invocation hook with :obj:`init_hook` semantics.

    Essentially, creates and returns a hook function as a lightweight wrapper around
    :meth:`~coma.config.cli.ParamData.call_on()` called on the current value of the
    :attr:`~coma.hooks.base.InvocationData.command` object with the given :obj:`policy`
    and :obj:`instance_key`.

    Args:
        policy (:class:`~coma.config.cli.OverridePolicy`): Policy for dealing with
            any command-line argument whose name clashes with command parameters.
        instance_key (:data:`~coma.config.base.InstanceKey`, optional): Which
            :class:`~coma.config.base.Config` instance to use (across all given
            :obj:`Config` s), or :meth:`~coma.config.base.Config.get_latest()` if
            :obj:`None`.

    Returns:
        :data:`~coma.hooks.base.Hook`: A hook with :obj:`init_hook` semantics.

    See also:
        * :func:`coma.hooks.config_hook.default_factory()`
        * :func:`coma.hooks.run_hook.default_factory()`
    """

    def hook(data: InvocationData) -> None:
        data.command = data.parameters.call_on(data.command, policy, instance_key)

    return hook
