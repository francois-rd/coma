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

.. py:function:: generic_protocol(name, parser, known_args, unknown_args, command, configs, run)

    Here, we list all possible protocol parameters, in the order in which they
    should be defined in the hook function's signature.

    .. note::

        Not every type of hook uses every protocol parameter. The
        :ref:`specificprotocols` are listed below. None of these specific
        differences affect the parameter ordering or naming shown here.

    :param name: The name given to a command when it is
        :func:`~coma.core.register.register`\ ed.
    :type name: str
    :param parser: The :obj:`ArgumentParser` created to handle command line arguments
        for a specific command when it is :func:`~coma.core.register.register`\ ed.
    :type parser: argparse.ArgumentParser
    :param known_args: The :obj:`Namespace` object (i.e., first object) returned by
        `parse_known_args() <https://docs.python.org/3/library/argparse.html#partial-parsing>`_
        if a specific command is invoked on the command line.
    :type known_args: argparse.Namespace
    :param unknown_args: The :class:`list` object (i.e., second object) returned by
        `parse_known_args() <https://docs.python.org/3/library/argparse.html#partial-parsing>`_
        if a specific command is invoked on the command line.
    :type unknown_args: typing.List[str]
    :param command: The command object itself that was
        :func:`~coma.core.register.register`\ ed if it is invoked on the command line.

        .. note::

            If the :func:`~coma.core.register.register`\ ed object was a class,
            it is left unchanged. If the :func:`~coma.core.register.register`\ ed
            object was a function, it is implicitly wrapped class. Before the
            :ref:`main init hook <hookpipeline>`, :obj:`command` is a class
            object. Afterwards, it is an instance object of that class.

        .. warning::

            Never make decisions based on the :obj:`type` of :obj:`command`, since it
            may be implicitly wrapped. Instead, use :obj:`name`, which is guaranteed
            to be unique across all :func:`~coma.core.register.register`\ ed commands.
    :type command: typing.Callable
    :param configs: A dictionary of identifier-configuration pairs representing
        all configs (both global and local) bound to a specific command if it is
        invoked on the command line.

        .. note::

            Before the :ref:`main config hook <hookpipeline>`, the values in
            the :obj:`configs` dictionary represent un-initialized config
            objects. Afterwards, they are initialized config objects.
    :type configs: coma.config.ConfigDict
    :param result: The value returned from executing the command if it is
        invoked on the command line.
    :type result: typing.Any
    :return: Some protocols return values; others do not. See the sections below
        for details on each protocol.
    :rtype: typing.Any


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
function signature (or are wrapped in the :obj:`@hook` decorator) to abstract
away some of the minutiae. Compare:

.. code-block:: python

    wrapper = coma.hooks.sequence(
        coma.hooks.parser_hook.factory("-a", type=int, default=123),
        coma.hooks.parser_hook.factory("-b", type=int, default=456),
    )

    coma.register(..., parser_hook=wrapper)

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

.. _specificprotocols:

Specific Protocols
------------------

Here, we list the specific protocol for each type of hook.

Parser Hooks
^^^^^^^^^^^^

Pre Config Hooks
^^^^^^^^^^^^^^^^

Config Hooks
^^^^^^^^^^^^

Post Config Hooks
^^^^^^^^^^^^^^^^^

Pre Init Hooks
^^^^^^^^^^^^^^

Init Hooks
^^^^^^^^^^

Post Init Hooks
^^^^^^^^^^^^^^^

Pre Run Hooks
^^^^^^^^^^^^^

Run Hooks
^^^^^^^^^

Post Run Hooks
^^^^^^^^^^^^^^

