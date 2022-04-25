"""Core config hooks."""
import json

from dataclasses import asdict
from typing import Callable, Optional

from .utils import hook


def factory(
        attr_name: str = 'config_path',
        *,
        default_filepath: Optional[str] = None,
        fail_fast_on_fnf: bool = False,
        write_on_fnf: bool = True
) -> Callable:
    """Factory for instantiating a configuration object.

    If no ``config_class`` is provided, the underlying config hook returns
    `None`. Otherwise, an attempt is made to instantiate the ``config_class``
    from configs loaded from file. If this fails due to a ``FileNotFoundError``,
    then a configuration object may be instantiated using default values and the
    configurations may be written to file, depending on the values of
    `fail_fast_on_fnf` and `write_on_fnf`.

    Args:
        attr_name: The attribute of the configuration file path on the parser
            args object returned by :func:`argparse.ArgumentParser.parse_args`.
            See :func:`coma.core.hooks.parser_hook.config_factory` for details.
        default_filepath: An optional default value for the configuration file
            path. If `None`, uses the same default as
            :func:`coma.hooks.parser_hook.config_factory`.
        fail_fast_on_fnf: If `True`, raises a ``FileNotFoundError`` if the
            configuration file was not found. If `False`, a configuration object
            with default values is instantiated instead of failing outright.
        write_on_fnf: If the configuration file was not found and
            `fail_fast_on_fnf` is `False`, then `write_on_fnf` indicates whether
            to write the configurations to the provided configuration file.

    Returns:
        A valid config hook function (assuming args are valid).

    Raises:
        FileNotFoundError: If `fail_fast_on_fnf` is `True` and the configuration
            file was not found
        TypeError: If the configs loaded from file and the ``config_class``
            provided to the underlying config hook are incompatible

    See also:
        :func:`coma.hooks.parser_hook.config_factory`
        TODO(invoke; protocol) for details on config hooks
    """
    @hook
    def _hook(name, parser_args, config_class):
        if config_class is None:
            return None
        default_ = default_filepath or f"{name}.json"
        filename = getattr(parser_args, attr_name, default_) or default_
        try:
            with open(filename, 'r') as f:
                return config_class(**json.load(f))
        except FileNotFoundError:
            if fail_fast_on_fnf:
                raise
            config = config_class()
            if write_on_fnf:
                with open(filename, 'w') as f:
                    json.dump(asdict(config), f, indent=4)
            return config
    return _hook


default = factory()
"""Default config hook function.

See also:
    TODO(invoke; protocol) for details on config hooks
"""
