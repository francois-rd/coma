Adding and Using Command Line Arguments
=======================================

Program-Level Arguments
-----------------------

Using program-level command line arguments is as an easy way to inject
additional behavior into the program. This example is similar to the one seen
:ref:`here <localhooks>`. The main difference is using global hooks instead of
local hooks to avoid repetition.

.. code-block:: python
    :caption: main.py

    import coma

    parser_hook = coma.hooks.parser_hook.factory("--dry-run", action="store_true")

    @coma.hooks.hook
    def pre_run_hook(known_args):
        if known_args.dry_run:
            print("Early exit!")
            quit()

    if __name__ == "__main__":
        coma.initiate(parser_hook=parser_hook, pre_run_hook=pre_run_hook)
        coma.register("greet", lambda: print("Hello World!"))
        coma.register("leave", lambda: print("Goodbye World!"))
        coma.wake()

In this example, the :obj:`parser_hook` adds a new :obj:`--dry-run` flag to the
command line. This flag is used by the :obj:`pre_run_hook` to exit the program
early (before the command is actually executed) if the flag is given on the
command line. Because these are global hooks, this behavior is present
regardless of the command that is invoked:

.. code-block:: console

    $ python main.py greet
    Hello World!
    $ python main.py leave
    Goodbye World!
    $ python main.py greet --dry-run
    Early exit!
    $ python main.py leave --dry-run
    Early exit!

Command-Level Arguments
-----------------------

Using command-level command line arguments is as an easy way to give additional
data to a command without having to define a config for it:

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

Here, :obj:`greet` functions in accordance with the default ``coma`` behaviour,
whereas :obj:`numbers` is defined quite differently. First, we define a
:func:`~coma.hooks.sequence` of :obj:`parser_hook`'s using the factory function
that adds arguments to the underlying parser object. Next, we define a custom
:obj:`init_hook` that is aware of how to instantiate the command object. Finally,
we :func:`~coma.core.forget.forget` the default :obj:`init_hook`, which doesn't
know how to handle extra command line arguments.

With these definitions, we can invoke the program's commands as follows:

.. code-block:: console

    $ python main.py greet
    Hello World!
    $ python main.py numbers 123
    123 456
    $ python main.py numbers 123 -b 321
    123 321

Using :obj:`coma.SENTINEL`
^^^^^^^^^^^^^^^^^^^^^^^^^^

We used the convenience sentinel :obj:`coma.SENTINEL` in the above example.
Another way to implement the same functionality would be:

.. code-block:: python
    :caption: main.py

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
essentially identical, yet the version without the sentinel is shorter. So why
ever use :obj:`coma.SENTINEL`? The sentinel allows the default value of :obj:`b`
to be defined only once, rather than twice, which can be less error-prone.

.. note::

    It would also be possible to define the default value of :obj:`b` only once
    by placing its value only in the :obj:`parser_hook`:

    .. code-block:: python

        coma.hooks.parser_hook.factory("-b", default=456)
        ...
        coma.register(..., lambda a, b: print(a, b), ...)

    but this separate the command definition from the definition of :obj:`b`'s
    default value, which can easily obscure the fact that :obj:`b` even has a
    default value.

On-the-Fly Hook Redefinition
----------------------------

Command line arguments can also be used to define hooks on the fly. In this example,
we have two configs, both of which define the same :obj:`x` attribute. We then
define a new :obj:`-e` flag, which is used to toggle the :obj:`exclusive` parameter
of :func:`~coma.config.cli.override_factory`. When present, this flag prevents the
any command line override involving :obj:`x` from overriding more than one config
attribute:

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

We can use :obj:`x` on the command line to override both configs at once:

.. code-block:: console

    $ python main.py multiply x=3
    9

In this case, :obj:`multiply` is essentially implementing :obj:`square`. We can
prevent this by setting the :obj:`-e` flag:

.. code-block:: console

    $ python main.py multiply x=3
    ...
    ValueError: Non-exclusive override: override: x=3 ; matched configs (possibly others too): ['config1', 'config2']

.. note::

    See :ref:`clashingoverrides` for additional details on this example.
