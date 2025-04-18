Command Line Arguments
======================

Adding command line arguments is as an easy way to inject additional behavior into
a program. For an introduction, see the :ref:`command <command_hook_example>` and
:ref:`shared <shared_hook_example>` examples.

.. _commandlevelarguments:

Command-Level Arguments
-----------------------

Using command-level command line arguments is as an easy way to give a command
additional data or modifiers that, for whatever reason, don't belong in a
dedicated config object:

.. code-block:: python
    :caption: main.py

    import coma

    parser_hook = coma.hooks.sequence(
        coma.hooks.parser_hook.factory("a", type=int),
        coma.hooks.parser_hook.factory("-b", default=coma.SENTINEL),
    )

    @coma.hooks.hook
    def init_hook(known_args, command):
        if known_args.b is coma.SENTINEL:
            return command(known_args.a)
        else:
            return command(known_args.a, known_args.b)

    if __name__ == "__main__":
        with coma.forget(init_hook=True):
            coma.register("numbers", lambda a, b=456: print(a, b),
                          parser_hook=parser_hook, init_hook=init_hook)
        coma.register("greet", lambda: print("Hello World!"))
        coma.wake()

Here, :obj:`greet` acts in accordance with ``coma``'s default behavior, whereas
:obj:`numbers` is defined quite differently. First, we define a
:func:`~coma.hooks.utils.sequence` for the :obj:`parser_hook` made up of
:func:`~coma.hooks.parser_hook.factory` calls, each of which simply passes its
arguments to the underlying parser object. Next, we define a custom
:obj:`init_hook` that is aware of how to instantiate this non-standard command
object. Finally, we :func:`~coma.core.forget.forget` the default
:obj:`init_hook`, which doesn't know how to handle non-standard commands.

With these definitions, we can invoke the program's commands as follows:

.. code-block:: console

    $ python main.py greet
    Hello World!
    $ python main.py numbers 123
    123 456
    $ python main.py numbers 123 -b 321
    123 321

Using :obj:`coma.SENTINEL`
--------------------------

In the :ref:`previous example <commandlevelarguments>`, we used ``coma``'s
convenience sentinel object, :obj:`coma.SENTINEL`. Another way to implement the
same functionality would be:

.. code-block:: python
    :emphasize-lines: 5, 10

    import coma

    parser_hook = coma.hooks.sequence(
        coma.hooks.parser_hook.factory("a", type=int),
        coma.hooks.parser_hook.factory("-b", default=456),
    )

    @coma.hooks.hook
    def init_hook(known_args, command):
        return command(known_args.a, known_args.b)

    if __name__ == "__main__":
        with coma.forget(init_hook=True):
            coma.register("numbers", lambda a, b=456: print(a, b),
                          parser_hook=parser_hook, init_hook=init_hook)
        coma.register("greet", lambda: print("Hello World!"))
        coma.wake()

In terms of final program behavior, these two versions of the program are
essentially identical, yet the version without the sentinel is shorter. The
tradeoff is that the sentinel allows the default value of :obj:`b` to be defined
only once, rather than twice, which can be less error-prone.

.. note::

    It would also be possible to define the default value of :obj:`b` only once
    (in the :obj:`parser_hook`):

    .. code-block:: python

        coma.hooks.parser_hook.factory("-b", default=456)
        ...
        coma.register(..., lambda a, b: print(a, b), ...)

    The leads to another tradeoff: The full command definition is now spread out
    in the code, which can obscure the fact that :obj:`b` has a default value.

.. _ontheflyhookredefinition:

On-the-Fly Hook Redefinition
----------------------------

Command line arguments can also be used to redefine hooks on the fly. In this
example, we have two configs, both of which define the same :obj:`x` attribute.
We then define a new :obj:`-e` flag, which is used to toggle the :obj:`exclusive`
parameter of :func:`~coma.config.cli.override_factory`. In short, the presence
of this flag prevents any command line override involving :obj:`x` from
overriding more than one config attribute:

.. code-block:: python
    :caption: main.py

    from dataclasses import dataclass

    import coma

    @dataclass
    class Config1:
        x: int

    @dataclass
    class Config2:
        x: int

    excl = coma.hooks.parser_hook.factory("-e", dest="excl", action="store_true")

    @coma.hooks.hook
    def post_config_hook(known_args, unknown_args, configs):
        override = coma.config.cli.override_factory(exclusive=known_args.excl)
        multi_cli = coma.hooks.post_config_hook.multi_cli_override_factory(override)
        return multi_cli(unknown_args=unknown_args, configs=configs)

    if __name__ == "__main__":
        coma.initiate(Config1, Config2, post_config_hook=post_config_hook)
        coma.register("multiply", lambda c1, c2: print(c1.x * c2.x), parser_hook=excl)
        coma.wake()

Without the :obj:`-e` flag, we can use :obj:`x` on the command line to override
*both* configs at once:

.. code-block:: console

    $ python main.py multiply x=3
    9

This lets :obj:`multiply` is essentially act as :obj:`square`. We can prevent
this by setting the :obj:`-e` flag:

.. code-block:: console

    $ python main.py multiply x=3
    ...
    ValueError: Non-exclusive override: override: x=3 ; matched configs (possibly others too): ['config1', 'config2']

.. note::

    See :ref:`here <prefixingoverrides>` for additional details on this example.
