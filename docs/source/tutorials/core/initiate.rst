Initiate
========

The first step to using ``coma`` is always to :func:`~coma.core.initiate.initiate`
a new coma.

:func:`~coma.core.initiate.initiate` is always called exactly once, before any
calls to :func:`~coma.core.register.register`. Calling
:func:`~coma.core.initiate.initiate` explicitly is required only to initiate a
coma with non-default parameters (``coma`` implicitly calls
:func:`~coma.core.initiate.initiate` with default parameters otherwise).

``argparse`` Overrides
----------------------

By default, ``coma`` creates an `ArgumentParser <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser>`_
with default parameters. However, :func:`~coma.core.initiate.initiate` can
optionally accept a custom :obj:`ArgumentParser`:

.. code-block:: python
    :emphasize-lines: 6
    :caption: main.py

    import argparse

    import coma

    if __name__ == "__main__":
        coma.initiate(parser=argparse.ArgumentParser(description="My Program description."))
        coma.register("greet", lambda: print("Hello World!"))
        coma.wake()

Now, let's run this program with the :obj:`-h` flag to see the result:

.. code-block:: console
    :emphasize-lines: 4

    $ python main.py -h
    usage: main.py [-h] {greet} ...

    My Program description.

    positional arguments:
      {greet}

    optional arguments:
      -h, --help  show this help message and exit

You can also provide keyword arguments to override the default parameter values
to the internal `ArgumentParser.add_subparsers() <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_subparsers>`_
call through the :obj:`subparsers_kwargs` parameter to
:func:`~coma.core.initiate.initiate`:

.. code-block:: python

    coma.initiate(subparsers_kwargs=dict(help="sub-command help"))

.. _globalconfigs:

Global Configs
--------------

Configs can be :func:`~coma.core.initiate.initiate`\ d globally to all
commands or :func:`~coma.core.register.register`\ ed locally to a specific command.

Let's revisit the second of the :ref:`Multiple Configurations <multiconfigs>` examples
from the :doc:`introductory tutorial <../intro>` to see the difference:

.. code-block:: python
    :caption: main.py

    from dataclasses import dataclass

    import coma

    @dataclass
    class Greeting:
        message: str = "Hello"

    @dataclass
    class Receiver:
        entity: str = "World!"

    if __name__ == "__main__":
        coma.register("greet", lambda g, r: print(g.message, r.entity), Greeting, Receiver)
        coma.register("leave", lambda r: print("Goodbye", r.entity), Receiver)
        coma.wake()

Notice how, in the original example, the :obj:`Receiver` config is
:func:`~coma.core.register.register`\ ed (locally) to both commands. Instead, we
can :func:`~coma.core.initiate.initiate` a coma with this config so that it is
(globally) supplied to all commands:

.. code-block:: python
    :emphasize-lines: 14-16
    :caption: main.py

    from dataclasses import dataclass

    import coma

    @dataclass
    class Greeting:
        message: str = "Hello"

    @dataclass
    class Receiver:
        entity: str = "World!"

    if __name__ == "__main__":
        coma.initiate(Receiver)
        coma.register("greet", lambda r, g: print(g.message, r.entity), Greeting)
        coma.register("leave", lambda r: print("Goodbye", r.entity))
        coma.wake()

This produces the same overall effect, while being more
`DRY <https://en.wikipedia.org/wiki/Don%27t_repeat_yourself>`_.

.. note::

    Configs need to be uniquely identified per-command, but not across commands.

.. note::

    Each command parameter will be bound (in the given order) to the supplied
    config objects if the command is invoked. In this example, because
    :obj:`Receiver` is now supplied first instead of second to :obj:`greet`, the
    order of parameters to :obj:`greet` had to be swapped: :obj:`g, r` becomes
    :obj:`r, g`. See below for a nexample of how to prevent this.

Global Hooks
------------

``coma``'s behavior can be easily tweaked, replaced, or extended using hooks.
These are covered in great detail :doc:`in their own tutorial <../hooks/index>`.
Here, the emphasis is on the difference between global and local hooks: As with
configs, hooks can be :func:`~coma.core.initiate.initiate`\ d globally to affect
``coma``'s behavior towards all commands or :func:`~coma.core.register.register`\ ed
locally to only affect ``coma``'s behavior towards a specific command.

Let's revisit the :ref:`previous example <globalconfigs>`. Recall that the order
of parameters to :obj:`greet` had to be swapped: :obj:`g, r` became :obj:`r, g`.
Suppose we want to prevent this change. To do so, we can force ``coma`` to bind
configs to parameters differently by writing a custom :obj:`init_hook`:

.. code-block:: python
    :emphasize-lines: 13-15, 18, 19
    :caption: main.py

    from dataclasses import dataclass

    import coma

    @dataclass
    class Greeting:
        message: str = "Hello"

    @dataclass
    class Receiver:
        entity: str = "World!"

    @coma.hooks.hook
    def custom_init_hook(command, configs):
        return command(*reversed(list(configs.values())))

    if __name__ == "__main__":
        coma.initiate(Receiver, init_hook=custom_init_hook)
        coma.register("greet", lambda g, r: print(g.message, r.entity), Greeting)
        coma.register("leave", lambda r: print("Goodbye", r.entity))
        coma.wake()

The details of how the hook is defined aren't important for the moment. The
point is that ``coma``'s default behavior regarding config binding has been
replaced from positional matching to anti-positional matching, which is
sufficient in this simple example.
