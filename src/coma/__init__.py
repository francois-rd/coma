"""Command Management for humans."""
from . import config
from . import hooks
from .core import forget
from .core import initiate
from .core import register
from .core import wake

SENTINEL = object()
"""A convenient Sentinel object."""
