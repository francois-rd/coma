"""Core parser hooks."""
from typing import Callable

from .utils import hook


def factory(*names_or_flags, **kwargs) -> Callable:
    """Factory for adding an argument to an :class:`argparse.ArgumentParser`.

    Args:
        *names_or_flags: See :func:`argparse.ArgumentParser.add_argument`
        **kwargs: Passed to :func:`argparse.ArgumentParser.add_argument`

    Returns:
        A valid parser hook function (assuming args are valid).

    See also:
        TODO(invoke; protocol) for details on parser hooks
    """
    @hook
    def _hook(parser):
        parser.add_argument(*names_or_flags, **kwargs)
    return _hook


def config_factory(*names_or_flags, **kwargs) -> Callable:
    """Factory for adding a configuration file path argument.

    If no arguments are provided, the following defaults are used::

        names_or_flags = ['--config-path']
        kwargs = {
            'type': str,
            'metavar': 'FILE',
            'default': f"{name}.json",  # where name is the sub-command name
            'help': "config file path",
        }

    Any of these defaults can be overridden by providing alternative arguments.
    Additional arguments beyond these can also be provided.

    Args:
        *names_or_flags: See :func:`~argparse.ArgumentParser.add_argument`
        **kwargs: Passed to :func:`~argparse.ArgumentParser.add_argument`

    Returns:
        A valid parser hook function (assuming args are valid).

    See also:
        :func:`coma.hooks.config_hook.factory`
        TODO(invoke; protocol) for details on parser hooks
    """
    @hook
    def _hook(name, parser):
        names_or_flags_ = names_or_flags or ['--config-path']
        kwargs.setdefault('type', str)
        kwargs.setdefault('metavar', 'FILE')
        kwargs.setdefault('default', f"{name}.json")
        kwargs.setdefault('help', "config file path")
        factory(*names_or_flags_, **kwargs)(parser=parser)
    return _hook


default = config_factory()
"""Default parser hook function.

See also:
    TODO(invoke; protocol) for details on parser hooks.
"""
