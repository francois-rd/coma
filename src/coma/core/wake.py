"""Wake from a coma."""

from .initiate import get_initiated


class WakeException(Exception):
    """Raised when :func:`~coma.core.wake.wake` fails."""

    pass


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

    Raises:
        :func:`~coma.core.wake.WakeException`: When failing to wake from a coma.

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
                raise WakeException(
                    "Waking from a coma with no command given on the command line."
                )
            else:
                raise WakeException("Failed to wake.")
    else:
        raise WakeException("Waking from a coma with no commands registered.")
