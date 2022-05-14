"""Wake ``coma``."""
import warnings

from .initiate import get_initiated


def wake(args=None, namespace=None) -> None:
    """Wakes ``coma``.

    Parses command line arguments and invokes the appropriate sub-command.

    Example:
        Use `sys.argv` as source of command line arguments.

        .. code-block:: python

            coma.wake()

        Simulate command line arguments.

        .. code-block:: python

            coma.wake(args=...)

    Args:
        args: Passed to :func:`~argparse.ArgumentParser.parse_args`
        namespace: Passed to :func:`~argparse.ArgumentParser.parse_args`

    See also:
        * :func:`~coma.core.register.register`
    """
    coma = get_initiated()
    known_args, unknown_args = coma.parser.parse_known_args(args, namespace)
    if coma.names:
        known_args.func(known_args, unknown_args)
    else:
        warnings.warn("Waking from a coma with no commands registered.", stacklevel=2)
