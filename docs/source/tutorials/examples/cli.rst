Command Line Config Overrides
=============================

.. _prefixingoverrides:

Prefixing Overrides
-------------------

Command line config overrides can sometimes clash. In this example, we have two
configs, both of which define the same :obj:`x` attribute:

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

    if __name__ == "__main__":
        coma.register("multiply", lambda c1, c2: print(c1.x * c2.x), Config1, Config2)
        coma.wake()

By default, ``coma`` enables the presence of :obj:`x` on the command line to
override *both* configs at once:

.. code-block:: console

    $ python main.py multiply x=3
    9

This lets :obj:`multiply` is essentially act as :obj:`square`. To prevent this,
we can override a specific config by *prefixing the override* with its identifier:

.. code-block:: console

    $ python main.py multiply config1:x=3 config2:x=4
    12

.. note::

    See :ref:`here <ontheflyhookredefinition>` for an alternative way to prevent
    these clashes.

By default, ``coma`` also supports prefix abbreviations: A prefix can be abbreviated
as long as the abbreviation is unambiguous (i.e., matches only one config identifier):

.. code-block:: python
    :emphasize-lines: 15
    :caption: main.py

    from dataclasses import dataclass

    import coma

    @dataclass
    class Config1:
        x: int

    @dataclass
    class Config2:
        x: int

    if __name__ == "__main__":
        coma.register("multiply", lambda c1, c2: print(c1.x * c2.x),
                      some_long_identifier=Config1, another_long_identifier=Config2)
        coma.wake()

This is enables convenient shorthands for command line overrides:

.. code-block:: console

    $ python main.py multiply some_long_identifier:x=3 another_long_identifier:x=4
    12
    $ python main.py multiply s:x=3 a:x=4
    12

Capturing Superfluous Overrides
-------------------------------

For rapid prototyping, it is often beneficial to capture superfluous command line
overrides. These can then be transferred to a proper config object once the codebase
is solidifying. In this example, we name this superfluous config :obj:`extras`:

.. code-block:: python
    :caption: main.py

    import coma


    if __name__ == "__main__":
        coma.initiate(
            extras={},
            init_hook=coma.hooks.init_hook.positional_factory("extras"),
            post_run_hook=coma.hooks.hook(
                lambda configs: print("extras =", configs["extras"])
            ),
        )
        coma.register("greet", lambda: print("Hello World!"))
        coma.wake()

This works because, as a plain :obj:`dict`, :obj:`extras` will accept any
*non-prefixed* arguments given on the command line:

.. code-block:: console

    $ python main.py greet
    Hello World!
    extras = {}
    $ python main.py greet foo=1 bar=baz
    Hello World!
    extras = {'foo': 1, 'bar': 'baz'}

.. note::

    We redefined the :obj:`init_hook` using
    :func:`~coma.hooks.init_hook.positional_factory`. This factory *skips* the
    given config identifiers when instantiating the command. Without this hook
    redefinition, the :obj:`lambda` defining the command would need to accept 1
    positional argument to accommodate :obj:`extras`.

.. note::

    We added a new :obj:`post_run_hook`. This hook is simply added to print out
    the attributes of the :obj:`extras` config after the command is executed.
