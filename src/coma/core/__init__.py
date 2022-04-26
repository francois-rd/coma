"""Core implementation of the ``coma`` user interface.

See TODO(basic; advanced) for details.
"""
from typing import List

from ..hooks.core import Hooks


class Coma:
    """Singleton class for ``coma``.

    Attributes:
        parser (:class:`argparse.ArgumentParser`): The argument parser to use
        subparsers: The special action object returned by
            :func:`~argparse.ArgumentParser.add_subparsers`
        commands_registered (bool): Whether at least one sub-command was
            successfully added using `subparsers`
        hooks (list): A stack of :class:`coma.hooks.core.Hooks`
    """

    coma: "Coma" = None

    def __init__(self):
        """See :class:`~coma.core.Coma`."""
        self.parser = None
        self.subparsers = None
        self.commands_registered: bool = False
        self.hooks: List[Hooks] = []

    @staticmethod
    def get_instance() -> "Coma":
        """Returns the singleton of :class:`~coma.core.Coma`."""
        if Coma.coma is None:
            Coma.coma = Coma()
        return Coma.coma
