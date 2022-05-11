10-Minute Tutorial
==================

``coma`` makes it easy to build configurable command-based programs in Python.

Commands
--------

Let's dive in with a classic :obj:`Hello World!` ``coma`` program:

.. code-block:: python
    :linenos:
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
    to :func:`~coma.core.register.register`. :func:`~coma.core.wake.wake` essentially
    tells ``coma`` "I'm done :func:`~coma.core.register.register`\ ing commands;
    please invoke whichever one was specified on the command line." In this case,
    :func:`~coma.core.wake.wake` saw that :obj:`greet` was specified on the command
    line and it invoked the registered command with a matching name.

In addition to anonymous functions, :obj:`command` can be any Python function:

.. code-block:: python
    :linenos:

    import coma

    def cmd():
        print("Hello World!")

    if __name__ == "__main__":
        coma.register("greet", cmd)
        coma.wake()

or any Python class with a no-parameter :obj:`run` method:

.. code-block:: python
    :linenos:

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
    :linenos:
    :caption: main.py

    import coma

    if __name__ == "__main__":
        coma.register("greet", lambda: print("Hello World!"))
        coma.register("leave", lambda: print("Goodbye!"))
        coma.wake()

This :func:`~coma.core.register.register`\ s two commands. We can call each in
turn to induce different program behavior:

.. code-block:: console

    $ python main.py greet
    Hello World!
    $ python main.py leave
    Goodbye!

Configurations
--------------

Commands alone are great, but config integration is what makes ``coma`` truly
powerful. The simplest ``omegaconf`` config is a dictionary:

.. code-block:: python
    :linenos:
    :caption: main.py

    import coma

    if __name__ == "__main__":
        coma.register("greet", lambda cfg: print(cfg.message), {"message": "Hello World!"})
        coma.wake()

.. note::

    The command now takes one positional argument, :obj:`cfg`. It will be bound
    to the config object when the command is invoked.

.. note::

    If the command is a Python class, the **constructor** should accept a positional
    argument, not the :obj:`run` method:

    .. code-block:: python
        :linenos:

        import coma

        class Cmd:
            def __init__(self, cfg):
                self.cfg = cfg

            def run(self):
                print(self.cfg.message)

        if __name__ == "__main__":
            coma.register("greet", Cmd, {"message": "Hello World!"})
            coma.wake()

    This separation between initialization and invocation is done so that stateful
    commands can be initialized based on config attributes, which is often useful.

With these simple configs, the program as before:

.. code-block:: console

    $ python main.py greet
    Hello World!

The only difference is that, by default, ``coma`` saves the config as a YAML file in the current
working directory:

.. code-block:: console

    $ ls
    dict.yaml
    main.py

By default, ``coma`` uses the config object's type's name to name the file
(:obj:`dict` in this example). This can be overridden by explicitly identifying
the config object using a keyword argument:

.. code-block:: python
    :linenos:
    :caption: main.py

    import coma

    if __name__ == "__main__":
        coma.register("greet", lambda cfg: print(cfg.message), greet={"message": "Hello World!"})
        coma.wake()

.. code-block:: console

    $ rm dict.yaml
    $ python main.py greet
    Hello World!
    $ ls
    greet.yaml
    main.py

The config files can be used to hardcode overrides to the default config attribute values:

.. code-block:: yaml
    :linenos:
    :caption: greet.yaml

    message: hardcoded message

.. code-block:: console

    $ python main.py greet
    hardcoded message

The config attributes can also be overridden on the command line using ``omegaconf``'s
`dot-list notation <https://omegaconf.readthedocs.io/en/2.1_branch/usage.html#from-a-dot-list>`_:

.. code-block:: console

    $ python main.py greet message="New Message"
    New Message

.. note::

    File-based configs override the defaults and command line-based configs
    override both the file-based and the defaults.

``omegaconf`` also supports `structured configs <https://omegaconf.readthedocs.io/en/2.1_branch/usage.html#from-structured-config>`_,
which enables runtime validation:

.. code-block:: python
    :linenos:
    :caption: main.py

    from dataclasses import dataclass

    import coma

    @dataclass
    class Config:
        message: str = "Hello World!"

    if __name__ == "__main__":
        coma.register("greet", lambda cfg: print(cfg.message), Config)
        coma.wake()

.. code-block:: console

    $ python main.py greet
    Hello World!

Multiple Configurations
-----------------------

Commands can take an arbitrary number of configs:

.. code-block:: python
    :linenos:
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

    The command now takes two positional arguments. Each will be bound in the
    given order to the supplied config objects when the command is invoked.

.. code-block:: console

    $ python main.py greet
    Hello World!

This example is, admittedly, somewhat contrived. However, multiple configs are
often useful in practice to separate large configurations into smaller,
more-manageable, more-maintainable, logically-separated components. Multiple
configs are also useful when only parts of a config are shared between commands:

.. code-block:: python
    :linenos:
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

.. code-block:: console

    $ python main.py greet
    Hello World!
    $ python main.py leave
    Goodbye World!

Where to go from here?
----------------------

You now have a solid foundation for writing Python programs with configurable commands! 🎉

For more advanced use cases, ``coma`` ofers many additional features, including:

* Customizing the underlying ``argparse`` objects.
* Adding command line arguments and flags to your program.
* Registering global configurations that are applied to every command.
* Using hooks to tweak, replace, or extend ``coma``'s default behavior.
* And more!

Check out the other tutorials to learn more.

Configs can be global (:func:`~coma.core.register.register`\ ed to all
commands) or local (:func:`~coma.core.register.register`\ ed to a specific command).