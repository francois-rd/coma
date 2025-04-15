Introduction
============

``coma`` makes it easy to build configurable command-based programs in Python.

``coma`` uses the `Template <https://en.wikipedia.org/wiki/Template_method_pattern>`_
design pattern, which leverages `hooks <https://en.wikipedia.org/wiki/Hooking>`_ to
implement, tweak, replace, or extend its behavior.

In this tutorial, we'll explore ``coma``'s **default** behavior. Nearly all of it
results from :doc:`pre-defined hooks <hooks/intro>`. ``coma`` has very few baked
in assumptions, so its behavior can be drastically changed with user-defined hooks.
We'll highlight these alternatives in later tutorials.

Commands
--------

For now, let's dive in with a classic :obj:`Hello World!` program:

.. code-block:: python

    from coma import command, wake

    @command
    def greet():
        print("Hello World!")

    if __name__ == "__main__":
        wake()


``coma``'s interface consists of only two functions:

    :func:`@command <coma.core.command.command>`: This decorator declares a
    ``Callable`` as a command. The command declaration can be tweaked via additional
    arguments passed to ``@command``. We'll explore these a little later.

    :func:`~coma.core.wake.wake`: This function registers all declared commands
    with `argparse <https://docs.python.org/3/library/argparse.html>`_ so
    that commands can be invoked via the command line.

Let's do that now by running this program on the command line:

.. code-block:: console

    $ python main.py greet
    Hello World!

.. note::

    Throughout this tutorial, we always assume the program code is in a file
    called :obj:`main.py`, so that we can run it on the command line using
    ``python main.py <command-name>``.

In addition to functions, :obj:`@command` can also decorate any Python class
with a no-argument :obj:`run()` method:

.. code-block:: python

    from coma import command, wake

    @command
    class Greet:
        def run(self):
            print("Hello World!")

    if __name__ == "__main__":
        wake()

The inferred command name is, by default, the lowercase name of the decorated
``Callable`` (function or class). As with many facets of command declaration,
this can be tweaked using one of the many additional parameters to ``@command``.
In this case, we will provide an explicit command name via the ``name`` parameter:

.. code-block:: python

    from coma import command, wake

    @command(name="greet")
    def an_absurdly_long_funtion_name_that_isnt_suitable_for_the_command_line():
        print("Hello World!")

    if __name__ == "__main__":
        wake()

The ``@command`` decorator can also be called as a regular function,
``command()``, to register a command procedurally:

.. code-block:: python

    from coma import command, wake

    if __name__ == "__main__":
        command(name="greet", cmd=lambda: print("Hello World!"))
        wake()


Multiple Commands
-----------------

``coma`` is intended to manage multiple commands as part of building complex programs.
Let's extend our previous example:

.. code-block:: python

    from coma import command, wake

    @command
    def greet():
        print("Hello World!")

    @command
    def leave():
        print("Goodbye World!")

    if __name__ == "__main__":
        wake()

This registers two commands, each with a different program behavior:

.. code-block:: console

    $ python main.py greet
    Hello World!
    $ python main.py leave
    Goodbye World!

Mixing function-based and class-based command declarations is perfectly acceptable.

Configurations
--------------

What makes ``coma`` truly powerful is its integration with
`omegaconf <https://github.com/omry/omegaconf>`_'s extremely rich configuration
management features. ``omegaconf``'s tutorials are excellent, so we won't explore all
its features here (only the basics needed to understand its integration with ``coma``).

At a high level, ``omegaconf`` configs are backed by either plain Python ``list``
and ``dict`` objects, or by Python ``dataclasses``. ``list`` and ``dict`` configs
are maximally flexible: They accept any objects that normal Python ``list`` and
``dict`` do. ``dataclasses``-backed configs, on the other hand, are known as
`structured <https://omegaconf.readthedocs.io/en/2.1_branch/usage.html#from-structured-config>`_
configs. ``omegaconf`` rigorously type validates these configs at runtime based
on the underlying ``dataclass`` declaration.

In ``coma``, it is command **parameters** that *declare* which configs a particular
command requires. Let's declare a ``Recipient`` config for our running example:

.. code-block:: python

    from dataclasses import dataclass
    from coma import command, wake

    @dataclass
    class Recipient:
        entity: str = "World"

    @command
    def greet(recipient: Recipient):
        print(f"Hello {recipient.entity}!")

    @command
    def leave(recipient: Recipient):
        print(f"Goodbye {recipient.entity}!")

    if __name__ == "__main__":
        wake()

.. note::

    The ``@command`` decarator provides a rich interface for tweaking which command
    parameters are configs and which are regular parameters. It also enables inline
    config parameters. Additionally, variadic parameters (``*args`` and ``**kwargs``)
    can be configs if desired. See the :doc:`advanced tutorial <core/command>` for more.

Invoking on the command line, we get:

.. code-block:: console

    $ python main.py greet
    Hello World!
    $ python main.py leave
    Goodbye World!

Notice that the output is the same as before, because the default value of
``recipient.entity`` is ``World``. That default value is used (unsurprisingly)
by default when invoking a command. We can **override** this default by supplying
an alternative value on the command line using the config name as a prefix
(``recipient``), followed by the prefix delimiter (``::``), followed by the config
attribute path (``entity``) specified in ``omegaconf``'s
`dot-list notation <https://omegaconf.readthedocs.io/en/2.1_branch/usage.html#from-a-dot-list>`_
format, followed by ``omegaconf``'s value delimiter (``=``), followed by
the new attribute value (``coma``):

.. code-block:: console

    $ python main.py greet recipient::entity=coma
    Hello coma!
    $ python main.py leave recipient::entity=coma
    Goodbye coma!

.. note::

    The config name **prefix** can be shortened or even entirely omitted if the config
    attribute being referred to is unambiguous. That is the case in this example, since
    we only have a single config. So the following are all equivalent in this example:

    .. code-block:: console

        $ python main.py greet recipient::entity=coma
        Hello coma!
        $ python main.py greet r::entity=coma
        Hello coma!
        $ python main.py greet entity=coma
        Hello coma!

    See :doc:`here <../examples/cli>` for full details on command line overrides.

.. note::

    If the command is a Python class, it is the ``__init__()`` method that declares
    which configs the command will require (not the :obj:`run()` method):

    .. code-block:: python
        :emphasize-lines: 10

        from dataclasses import dataclass
        from import command, wake

        @dataclass
        class Recipient:
            entity: str = "World"

        @command
        class Greet:
            def __init__(self, recipient: Recipient):
                self.recipient = recipient

            def run(self):
                print(f"Hello {self.recipient.entity}!")

        if __name__ == "__main__":
            coma.wake()

    This separation between initialization (via ``__init__()``) and execution
    (via ``run()``) is done so that stateful commands can be initialized based
    on config attributes, which is typically more straightforward than delaying
    part of the initialization until ``run()`` is called, which would be the case
    if the latter required config declaration.


Config Serialization
--------------------

Most configs are automatically serializable, meaning they are saved to file the
**first time** a command is invoked. By default, the file name is based on the
config's parameter name in the command declaration (config ``recipient`` is
saved to ``recipient.yaml`` in our example):

.. code-block:: console

    $ ls
    main.py
    recipient.yaml
    $ cat recipient.yaml
    entity: World

Notice that it is the **default** config value that gets saved to file, not any
subsequent command line overrides. Configs in ``coma`` adhere to a
**declaration hierarchy**:

.. admonition:: Config Declaration Hierarchy:

    command line override > file (if config is serializable) > code default

As such, updating ``recipient.yaml`` changes the config attributes that are loaded
on command invocation (when no command line overrides are provided). Suppose we
update ``recipient.yaml`` to contain the following:

.. code-block:: yaml

    entity: coma

Invoking the commands now clearly demonstrates the declaration hierarchy:

.. code-block:: console

    $ python main.py greet  # No command line override. Load from file.
    Hello coma!
    $ python main.py leave entity=foo  # Command line override.
    Goodbye foo!

Config serialization enables configs to be shared between commands. We've done
this implicitly in the running example, since both ``greet`` and ``leave`` share
``recipient``. This is one of ``coma``'s most powerful features, as it allows complex
programs to **declare modular configs once** and then **share them everywhere**
without having repeat definitions.

However, sometimes we do want to have a separate config for each command. ``coma``
also supports this use case. Simply use **unique** config names across the command
declarations:

.. code-block:: python
    :emphasize-lines: 13

    from dataclasses import dataclass
    from coma import command, wake

    @dataclass
    class Recipient:
        entity: str = "World"

    @command
    def greet(greet_recipient: Recipient):
        print(f"Hello {greet_recipient.entity}!")

    @command
    def leave(leave_recipient: Recipient):
        print(f"Goodbye {leave_recipient.entity}!")

    if __name__ == "__main__":
        wake()

Now, we have two *independent* config files:

.. code-block:: console

    $ ls
    main.py
    greet_recipient.yaml
    leave_recipient.yaml

Updating ``greet_recipient.yaml`` only affects ``greet``. Updating
``leave_recipient.yaml`` only affects ``leave``. See this
:doc:`advanced example <../examples/serialization>` for even more details.

.. _multiconfigs:

Multiple Configurations
-----------------------

``coma`` enables commands to take an arbitrary number of independent configs.
Multiple configs are often useful in practice to separate otherwise-large configs
into smaller components, especially if only *some* of those components are shared
between commands. Let's declare two new configs (``Salutation`` and ``Parting``) in
our running example, while reverting ``Recipient`` to be shared between ``leave``
and ``greet``:

.. code-block:: python

    from dataclasses import dataclass
    from coma import command, wake

    @dataclass
    class Salutation:
        phrase: str = "Hello"

    @dataclass
    class Parting:
        phrase: str = "Goodbye"

    @dataclass
    class Recipient:
        entity: str = "World"

    @command
    def greet(salutation: Salutation, recipient: Recipient):
        print(f"{salutation.phrase} {recipient.entity}!")

    @command
    def leave(parting: Parting, recipient: Recipient):
        print(f"{parting.phrase} {recipient.entity}!")

    if __name__ == "__main__":
        wake()


We can invoke both commands as before. They share ``recipient`` so any changes
to ``recipient.yaml`` are reflected in both commands. Changes to the other configs
only affect the respective command. Command line overrides are not serialized (by
default) so overrides to one command do not affect the other:

.. code-block:: console

    $ python main.py greet phrase=Hey entity=coma
    Hey coma!
    $ python main.py leave
    Goodbye World!


Next Steps
----------

🎉 You now have a solid foundation for writing Python programs with *modular*
configurable commands using ``coma``'s *declarative* interface! 🎉

``coma`` offers many additional features, including:

* Customizing the underlying ``argparse`` objects.
* Adding command line arguments and flags to your program.
* Using hooks to tweak, replace, or extend ``coma``'s default behavior.
* Registering shared hooks that are declared once and applied to every command.
* And lots more!

Read the other tutorials and usage examples to learn more.
