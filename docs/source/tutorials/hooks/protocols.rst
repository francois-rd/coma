Protocols
=========

``coma`` uses a :ref:`hook pipeline <hookpipeline>`, both to implement its
default behavior and to enable customization. To make this work, the various
:ref:`types of hook <typesofhooks>` must each follow a pre-defined protocol
(i.e., function signature) for both their parameters and their return value.

The hook protocols are fairly similar across all hook types, but there are a
number of variations depending on the type. We begin by enumerating the shared
aspects of the various protocols.

Function Signature
------------------

All protocols require the corresponding hook function signatures to define
`positional-or-keyword <https://docs.python.org/3/library/inspect.html#inspect.Parameter.kind>`_
parameters. For example, we can define and invoke some (hypothetical) hook function as:

.. code-block:: python

    def some_hook(a, b, c):
        ...

    some_hook(a=..., b=..., c=...)

This is fine because the hook function parameters are defined as
positional-or-keyword. These requirement is needed because hook parameters are
bound positionally by keyword.

.. note::

    Technically, the requirement is that the hook function parameters are not
    positional-only, not variadic (positional or keyword), and not keyword-only.
    In practice, that means they have to be positional-or-keyword.

In addition to the above, **all** protocol parameters must be:

    * **Defined** in the hook function's signature.
    * **Ordered** correctly in the hook function's signature.
    * **Named** (i.e., spelled) correctly in the hook function's signature.

.. _protocolparameters:

Protocol Parameters
-------------------

.. py:function:: generic_protocol(name, parser, known_args, unknown_args, command, configs, result)

    Here, we list all possible protocol parameters, in the order in which they
    should be defined in the hook function's signature.

    .. note::

        Not every type of hook uses every protocol parameter. The protocols
        specific to each hook type are listed :ref:`below <specificprotocols>`.
        **None of these specific differences affect the parameter ordering or naming shown here.**

    :param name: The name given to a command when it is
        :func:`~coma.core.register.register`\ ed.
    :type name: str
    :param parser: The :obj:`ArgumentParser` created to add command line arguments
        for a specific command when it is :func:`~coma.core.register.register`\ ed
        and subsequently parse actual command line arguments if the command is
        invoked on the command line.
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
            object was a function, it is implicitly wrapped in another object. The
            :ref:`main init hook <hookpipeline>` is meant to instantiate :obj:`command`.

        .. warning::

            Never make decisions based on the :obj:`type` of :obj:`command`, since it
            may be implicitly wrapped. Instead, use :obj:`name`, which is guaranteed
            to be unique across all :func:`~coma.core.register.register`\ ed commands.
    :type command: typing.Union[typing.Callable, typing.Any]
    :param configs: A dictionary of identifier-configuration pairs representing
        all configs (both global and local) bound to a specific command if it is
        invoked on the command line.

        .. note::

            Before the :ref:`main config hook <hookpipeline>`, the values in the
            :obj:`configs` dictionary are assumed to be uninitialized config
            objects. Afterwards, they are assumed to be initialized config objects.
    :type configs: typing.Dict[str, typing.Any]
    :param result: The value returned from executing the command if it is
        invoked on the command line.
    :type result: typing.Any
    :return: Some protocols return values; others do not. See
        :ref:`below <specificprotocols>` for details on each protocol.
    :rtype: typing.Any


:obj:`@hook` Decorator
----------------------

For many hooks, only a subset of the corresponding protocol parameters are needed
to implement their logic. It can therefore be cumbersome to define a function with
multiple unused parameters just to satisfy the hook protocol. The :obj:`@hook`
decorator (:func:`coma.hooks.hook`) solves this problem, as it allows hook
functions to be defined with a subset of the protocol parameters. For example:

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
--------------------------

Each :ref:`type of hook <typesofhooks>` must be implemented as a single function.
However, it is often beneficial to decompose a large hook function into a series of
smaller ones. These component functions must then be wrapped with a higher-order
function that executes them in order, while binding all parameters using keywords.

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
``(parser=parser)`` to each wrapped hook function and removes the need to
decorate the wrapper function with the :obj:`@hook` decorator.

.. _specificprotocols:

Specific Protocols
------------------

Here, we list the specific protocol and intended semantics for each
:ref:`type of hook <typesofhooks>`. See :ref:`protocolparameters` for details on
each parameter.

Parser
^^^^^^

.. py:function:: parser_hook_protocol(name, parser, command, configs)

    :Semantics: This protocol adds command line arguments using :obj:`parser`.

    :return: The return value of a parser hook (if any) is always ignored.
    :rtype: None

Pre Config
^^^^^^^^^^

.. py:function:: pre_config_hook_protocol(name, known_args, unknown_args, command, configs)

    :Semantics: This protocol is the first invocation hook to be executed.

    :return: The return value of a pre config hook (if any) is always ignored.
    :rtype: None

Config
^^^^^^

.. py:function:: config_hook_protocol(name, known_args, unknown_args, command, configs)

    :Semantics: The values in the :obj:`configs` dictionary represent uninitialized
        config objects. This protocol initializes them and returns them
        **in the same order**.

    :return: The return value of a config hook is an initialized configs dictionary.
    :rtype: typing.Dict[str, typing.Any]

Post Config
^^^^^^^^^^^

.. py:function:: post_config_hook_protocol(name, known_args, unknown_args, command, configs)

    :Semantics: This protocol takes the initialized configs objects and returns
        these same objects (possibly modified in some way) **in the same order**.

    :return: The return value of post config hooks is the configs dictionary.
    :rtype: typing.Dict[str, typing.Any]

Pre Init
^^^^^^^^

.. py:function:: pre_init_hook_protocol(name, known_args, unknown_args, command, configs)

    :Semantics: This protocol's hook is executed after all the config hooks and
        before the main init hook.

    :return: The return value of a pre init hook (if any) is always ignored.
    :rtype: None

Init
^^^^

.. py:function:: init_hook_protocol(name, known_args, unknown_args, command, configs)

    :Semantics: This protocol instantiates :obj:`command` using the
        :obj:`configs`, returning the resulting instance object.

        .. note::

            If the :func:`~coma.core.register.register`\ ed command object was a class,
            it was left unchanged. If the :func:`~coma.core.register.register`\ ed
            command object was a function, it was implicitly wrapped in another
            object. Either way, :obj:`command` acts as though it is a class object
            that can be instantiated.

    :return: The return value of an init hook is an instantiated command object.
    :rtype: typing.Any

Post Init
^^^^^^^^^

.. py:function:: post_init_hook_protocol(name, known_args, unknown_args, command, configs)

    :Semantics: This protocol takes the instantiated command object and returns
        the same object (possibly modified in some way).

    :return: The return value of a post init hook is the instantiated command object.
    :rtype: typing.Any

Pre Run
^^^^^^^

.. py:function:: pre_run_hook_protocol(name, known_args, unknown_args, command, configs)

    :Semantics: This protocol's hook is executed after all the config and init
        hooks and before the main run hook.

    :return: The return value of a pre run hook (if any) is always ignored.
    :rtype: None

Run
^^^

.. py:function:: run_hook_protocol(name, known_args, unknown_args, command, configs)

    :Semantics: This protocol executes the instantiated :obj:`command` object,
        then returns the resulting value.

    :return: The return value of a run hook is the value resulting from
        executing the instantiated command object.
    :rtype: typing.Any

Post Run
^^^^^^^^

.. py:function:: post_run_hook_protocol(name, known_args, unknown_args, command, configs, result)

    :Semantics: This protocol is the last invocation hook to be executed.

    :return: The return value of a post run hook (if any) is always ignored.
    :rtype: None
