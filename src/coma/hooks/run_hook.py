"""Run hook default factory."""

from .base import Hook, InvocationData


def default_factory(attr_name: str = "run") -> Hook:
    """
    Factory for creating a run hook that executes a command.

    Essentially, the attribute :obj:`attr_name` of the current value of the
    :attr:`~coma.hooks.base.HookData.command` object is called with no arguments,
    and its result is stored in :attr:`coma.hooks.base.InvocationData.result`.

    .. warning::

        If the command, at the time of registration via
        :func:`~coma.core.command.command()`, was a function (not a class), it is
        internally wrapped in a class that **always** has a :obj:`run()` method. As
        such, changing :obj:`attr_name` to anything else than :obj:`"run"` will fail for
        function-type commands and should **only** be changed for class-type commands.

    Example:

        Change the run method name from :obj:`"run"` to :obj:`"__call__"`::

            @coma.command(run_hook=default_factory("__call__"))
            class Command:
                def __call__(self):
                    ...

    Args:
        attr_name (str): The name of the command attribute to call.

    Returns:
        :data:`~coma.hooks.base.Hook`: A hook with :obj:`run_hook` semantics.

    See also:
        * :func:`coma.hooks.init_hook.default_factory()`
    """

    def hook(data: InvocationData) -> None:
        data.result = getattr(data.command, attr_name)()

    return hook
