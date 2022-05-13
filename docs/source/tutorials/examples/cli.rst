Command Line Config Overrides
=============================

.. _clashingoverrides:

Clashing Overrides
------------------

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

We can use :obj:`x` on the command line to override both configs at once:

.. code-block:: console

    $ python main.py multiply x=3
    9

In this case, :obj:`multiply` is essentially implementing :obj:`square`. To prevent
this, we can override a specific config by prefixing the override with its identifier:

.. code-block:: console

    $ python main.py multiply config1:x=3 config2:x=4
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
non-prefixed arguments given on the command line:

.. code-block:: console

    $ python main.py greet
    Hello World!
    extras = {}
    $ python main.py greet foo=1 bar=baz
    Hello World!
    extras = {'foo': 1, 'bar': 'baz'}

.. note::

    We redefined the :obj:`init_hook` using
    :func:`~coma.hooks.init_hook.positional_factory`. This factory accepts any
    number of config identifiers. These identifiers are then skipped when
    instantiating the command. Without this hook redefinition, the :obj:`lambda`
    defining the command would need to accept 1 positional argument to
    accommodate :obj:`extras`.

.. note::

    We added a new :obj:`post_run_hook` using :obj:`@hook` decorator. This hook
    is simply added to print out the attributes of the :obj:`extras` config.
