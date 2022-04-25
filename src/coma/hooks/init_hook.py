"""Core init hooks."""
from .utils import hook


@hook
def default(pre_init_command, config):
    """Default init hook function.

    See also:
        TODO(invoke; protocol) for details on init hooks
    """
    return pre_init_command(config)
