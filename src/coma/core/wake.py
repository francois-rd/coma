"""Wake from a coma."""

import warnings

from .initiate import get_initiated


def wake(args=None, namespace=None) -> None:
    """Wakes from a coma.

    Parses command line arguments and invokes the appropriate command using the
    :func:`~coma.core.register.register`\\ ed hooks.

    Example:
        Use :obj:`sys.argv` as source of command line arguments.

        .. code-block:: python

            coma.wake()

        Simulate command line arguments.

        .. code-block:: python

            coma.wake(args=...)

    Args:
        args: Passed to `ArgumentParser.parse_known_args()`_
        namespace: Passed to `ArgumentParser.parse_known_args()`_

    See also:
        * :func:`~coma.core.register.register`

    .. _ArgumentParser.parse_known_args():
        https://docs.python.org/3/library/argparse.html#partial-parsing
    """
    coma = get_initiated()
    for registration in coma.stored_registrations:
        registration()
    known_args, unknown_args = coma.parser.parse_known_args(args, namespace)
    if coma.names:
        try:
            known_args.func(known_args, unknown_args)
        except AttributeError as e:
            if any("func" in arg for arg in e.args):
                message = (
                    "Waking from a coma with no command given on the command line."
                )
                warnings.warn(message, stacklevel=2)
            else:
                raise
    else:
        warnings.warn("Waking from a coma with no commands registered.", stacklevel=2)
