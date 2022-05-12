Introduction
============

``coma`` makes it easy to build configurable command-based programs in Python.

Commands
--------

Let's dive in with a classic :obj:`Hello World!` program:

.. code-block:: python
    :caption: main.py

    import coma

    if __name__ == "__main__":
        coma.register("greet", lambda: print("Hello World!"))
        coma.wake()

Now, let's run this program:

.. code-block:: console

    $ python main.py greet
    Hello World!

.. note::

    The meat of working with ``coma`` is the :func:`~coma.core.register.register`
    function. It has two required parameters:

    :name: the name of a command (:obj:`greet` in this example)
    :command: the command itself (an anonymous function in this example)

.. note::

    The :func:`~coma.core.wake.wake` function should always follow the last call
    to :func:`~coma.core.register.register`. Calling :func:`~coma.core.wake.wake`
    tells ``coma`` that all commands have been :func:`~coma.core.register.register`\ ed.
    Coma will then attempt to invoke whichever one was specified on the command
    line. In this example, :obj:`greet` was specified on the command line and so
    the :func:`~coma.core.register.register`\ ed command with that name was invoked.

In addition to anonymous functions, :obj:`command` can be any Python function:

.. code-block:: python

    import coma

    def cmd():
        print("Hello World!")

    if __name__ == "__main__":
        coma.register("greet", cmd)
        coma.wake()

or any Python class with a no-parameter :obj:`run()` method:

.. code-block:: python

    import coma

    class Cmd:
        def run(self):
            print("Hello World!")

    if __name__ == "__main__":
        coma.register("greet", Cmd)
        coma.wake()

Multiple Commands
-----------------

``coma`` is intended to manage multiple commands as part of building complex programs.
Let's extend our previous example:

.. code-block:: python
    :caption: main.py

    import coma

    if __name__ == "__main__":
        coma.register("greet", lambda: print("Hello World!"))
        coma.register("leave", lambda: print("Goodbye!"))
        coma.wake()

This :func:`~coma.core.register.register`\ s two commands. By calling each in
turn, we induce different program behavior:

.. code-block:: console

    $ python main.py greet
    Hello World!
    $ python main.py leave
    Goodbye!

Configurations
--------------

Commands alone are great, but ``omegaconf`` integration is what makes ``coma``
truly powerful. The simplest ``omegaconf`` config object is a plain dictionary:

.. code-block:: python
    :caption: main.py

    import coma

    if __name__ == "__main__":
        coma.register("greet", lambda cfg: print(cfg.message), {"message": "Hello World!"})
        coma.wake()

.. note::

    The command now takes one positional argument (:obj:`cfg` in this example).
    It will be bound to the config object if the command is invoked.

.. note::

    If the command is a Python class, it is the **constructor** that should have
    a positional config argument, not the :obj:`run` method:

    .. code-block:: python

        import coma

        class Cmd:
            def __init__(self, cfg):
                self.cfg = cfg

            def run(self):
                print(self.cfg.message)

        if __name__ == "__main__":
            coma.register("greet", Cmd, {"message": "Hello World!"})
            coma.wake()

    This separation between initialization and execution is done so that stateful
    commands can be initialized based on config attributes, which is typically
    more straightforward than delaying part of the initialization until :obj:`run`
    is called.

The program essentially runs as before:

.. code-block:: console

    $ python main.py greet
    Hello World!

The only difference is that, by default, ``coma`` serializes the config to a
YAML file in the current working directory:

.. code-block:: console

    $ ls
    dict.yaml
    main.py

By default, ``coma`` uses the config object's :obj:`type`'s name (:obj:`dict` in
this example) to identify the config and derive a file name. This can be
overridden by explicitly identifying the config object using a keyword argument:

.. code-block:: python
    :caption: main.py

    import coma

    if __name__ == "__main__":
        coma.register("greet", lambda cfg: print(cfg.message),
                      greet={"message": "Hello World!"})
        coma.wake()

Now the config will be serialized to :obj:`greet.yaml`:

.. code-block:: console

    $ rm dict.yaml
    $ python main.py greet
    Hello World!
    $ ls
    greet.yaml
    main.py

Config files can be used to hardcode attribute values that override the default
config attribute values. For example, changing :obj:`greet.yaml` to:

.. code-block:: yaml
    :caption: greet.yaml

    message: hardcoded message

leads to the following program execution:

.. code-block:: console

    $ python main.py greet
    hardcoded message

Config attribute values can also be overridden on the command line using ``omegaconf``'s
`dot-list notation <https://omegaconf.readthedocs.io/en/2.1_branch/usage.html#from-a-dot-list>`_:

.. code-block:: console

    $ python main.py greet message="New Message"
    New Message

.. note::

    See :func:`coma.config.cli.override` for full details on command line overrides.

.. note::

    Serialized configs override default configs and command line-based configs override
    *both* serialized and default configs: :obj:`default < serialized < command line`.

``coma`` supports any valid ``omegaconf`` config object. In particular,
`structured configs <https://omegaconf.readthedocs.io/en/2.1_branch/usage.html#from-structured-config>`_
are useful for enabling runtime validation:

.. code-block:: python
    :caption: main.py

    from dataclasses import dataclass

    import coma

    @dataclass
    class Config:
        message: str = "Hello World!"

    if __name__ == "__main__":
        coma.register("greet", lambda cfg: print(cfg.message), Config)
        coma.wake()

.. note::

    Because :obj:`Config` has :obj:`type` name :obj:`config`, the config object
    will be serialized to :obj:`config.yaml`.

.. code-block:: console

    $ python main.py greet
    Hello World!

.. _multiconfigs:

Multiple Configurations
-----------------------

Commands can take an arbitrary number of configs:

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
        coma.wake()

.. note::

    In this example, the command now takes two positional arguments. Each will be bound
    (in the given order) to the supplied config objects if the command is invoked.

.. code-block:: console

    $ python main.py greet
    Hello World!

Multiple configs are often useful in practice to separate otherwise-large configs
into smaller components, especially if some components are shared between commands:

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

.. note::

    It is perfectly acceptable for both :obj:`greet` and :obj:`leave` to share
    the :obj:`Receiver` config: Configs need to be uniquely identified per-command,
    but not across commands. To disable this sharing (so that each command has its
    own serialized copy of the config), use unique identifiers:

    .. code-block:: python

        coma.register("greet", ..., Greeting, greet_receiver=Receiver)
        coma.register("leave", ..., leave_receiver=Receiver)

We invoke both commands in turn as before:

.. code-block:: console

    $ python main.py greet
    Hello World!
    $ python main.py leave
    Goodbye World!

Where To Go From Here?
----------------------

You now have a solid foundation for writing Python programs with configurable commands! 🎉

For more advanced use cases, ``coma`` ofers many additional features, including:

* Customizing the underlying ``argparse`` objects.
* Adding command line arguments and flags to your program.
* Registering global configurations that are applied to every command.
* Using hooks to tweak, replace, or extend ``coma``'s default behavior.
* And more!

Check out the other tutorials to learn more.
