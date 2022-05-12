Protocols
=========

As seen in the :doc:`./intro`, ``coma`` uses a hook pipeline, both to implement
its default behavior and to enable customization. To makes this work, the
various hooks must follow a pre-defined protocol for their function signature
(for both the parameters and the return type).

Introduction
------------

The hook protocols are fairly similar across all hook types, but there are a
number of variations depending on the type. We begin by enumerating the shared
aspects of the various protocols.

Function Signature
^^^^^^^^^^^^^^^^^^

All protocols require the corresponding hook function signatures to define
`positional-or-keyword <https://docs.python.org/3/library/inspect.html#inspect.Parameter>`_
parameters. For example, we can define and invoke some (hypothetical) hook function as:

.. code-block:: python

    def some_hook(a, b, c):
        ...
    some_hook(a=..., b=..., c=...)

This is fine because the hook function parameters are defined as positional-or-keyword.

.. note::

    Technically, the requirement is that the hook function parameters are not
    positional-only, not variadic (positional or keyword), and not keyword-only.
    In practice, that means they have to be positional-or-keyword.

In addition to the above, **all** protocol parameters must be:

    * Defined in the hook function's signature.
    * Ordered correctly in the hook function's signature.
    * Named (i.e., spelled) correctly in the hook function's signature.

Protocol Parameters
^^^^^^^^^^^^^^^^^^^

Here, we list all possible protocol parameters.

.. note::

    Not every type of hook uses every protocol parameter. The type-specific
    protocols are listed in the sections below.

:name:
    blah
:configs:
    blah
:etc:
    blah

:obj:`@hook` Decorator
^^^^^^^^^^^^^^^^^^^^^^

For many hooks, only a subset of the corresponding protocol parameters is needed
to implement its logic. It can therefore be cumbersome to define a function with
multiple unused parameters just to satisfy the hook protocol. The :obj:`@hook`
decorator solves this problem, as it allows hook functions to be defined with
a subset of the protocol parameters. For example:

.. code-block:: python

    @coma.hooks.hook
    def name_hook(name):
        ...

defines a hook that only requires the command's :obj:`name` and ignores all
other protocol parameters.

.. note::

    The :obj:`@hook` decorator only alleviates the requirement that all protocol
    parameters are defined in the hook function's signature. Other requirements,
    such as having the correct ordering and spelling of parameters, remain active.

:obj:`sequence()` Function
^^^^^^^^^^^^^^^^^^^^^^^^^^

Technically, each hook type in the hook pipeline accepts at most one function.
However, it is often beneficial to decompose a large hook function into a
series of smaller ones. These component functions must then be wrapped with
a higher-order function that executes them in order, while binding all
parameters using keywords.

While this wrapping can always be done manually, a convenience wrapper,
:func:`~coma.hooks.sequence`, can be used when all hooks share the exact same
function signature (not just the same protocol!) to abstract away some of the
minutiae. Compare:

.. code-block:: python

    coma.register(...,
        parser_hook=coma.hooks.sequence(
            coma.hooks.parser_hook.factory("-a", type=int, default=123),
            coma.hooks.parser_hook.factory("-b", type=int, default=456),
        )
    )

with:

.. code-block:: python

    @coma.hooks.hook
    def wrapper(parser):
        coma.hooks.parser_hook.factory("-a", type=int, default=123)(parser=parser)
        coma.hooks.parser_hook.factory("-b", type=int, default=456)(parser=parser)

    coma.register(..., parser_hook=wrapper)

The former isn't shorter, but it removes the minutiae of adding
:obj:`(parser=parser)` to each wrapped hook function and removes the need to
decorate the wrapper function with the :obj:`@hook` decorator.

Parser Hooks
------------

Pre Config Hooks
----------------

Config Hooks
------------

Post Config Hooks
-----------------

Pre Init Hooks
--------------

Init Hooks
----------

Post Init Hooks
---------------

Pre Run Hooks
-------------

Run Hooks
---------

Post Run Hooks
--------------

