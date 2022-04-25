"""Wake from a coma."""
import warnings

from .initiate import get_initiated


def wake(args=None, namespace=None) -> None:
    """Wakes from a coma.

    Parses command line arguments and invokes the appropriate sub-command.

    Args:
        args: Passed to :func:`~argparse.ArgumentParser.parse_args`
        namespace: Passed to :func:`~argparse.ArgumentParser.parse_args`

    See also:
        :func:`~coma.core.register.register`
    """
    coma = get_initiated()
    parser_args = coma.parser.parse_args(args=args, namespace=namespace)
    if coma.commands_registered:
        parser_args.func(parser_args)
    else:
        warnings.warn("Waking from Coma with no commands.", stacklevel=2)
