Wake Settings
=============

After all commands have been declared using
:func:`@command <coma.core.command.command>`, the last step is always to
:func:`~coma.core.wake.wake()` the program. ``wake()`` serves three functions:

1. Parameterizing the top-level `ArgumentParser <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser>`_
   that determines which declared command is invoked.
2. Adding shared hooks that propagate to all command declarations by default.
3. Waking the program by invoking the correct command (as determined in step 1).

Let's examine each in turn.

Parameters to ``argparse``
--------------------------

``wake()`` optionally accepts a custom `ArgumentParser <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser>`_
object via its ``parser`` parameter. When ``None`` is given, ``wake()`` defaults to
an ``ArgumentParser`` with default parameters.

.. code-block:: python
    :emphasize-lines: 6

    from coma import command, wake
    from argparse import ArgumentParser

    if __name__ == "__main__":
        command(name="greet", cmd=lambda: print("Hello World!"))
        wake(parser=ArgumentParser(description="My Program description."))

Let's run this program with the ``-h`` flag to see the result:

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
call through the ``subparsers_kwargs`` parameter to ``wake()``:

.. code-block:: python

    wake(subparsers_kwargs=dict(help="sub-command help"))

.. _shared_hooks:

Shared Hooks
------------

``coma``'s template-based design enables its behavior to be easily tweaked,
replaced, or extended using hooks. These are covered in detail in their own
:doc:`tutorial <hooks>`. Here, we emphasize the difference between *shared*
and :ref:`command <command_hooks>` hooks.

Any *command* hook that is not explicitly redefined for a particular
command declaration defaults to the corresponding hook from ``wake()`` at runtime.
In other words, any shared hook declared in ``wake()`` is automatically propagated
to **every** command declaration that does not explicitly redefine that hook. As
such, the *shared* hooks given to ``wake()`` have wide-reaching effects. Nearly all
of ``coma``'s default behavior results from pre-defined hooks declared in ``wake()``.

Typically, a hook is a function with a :ref:`specific signature <hook_protocols>`.
However, there are two additional (non-function) sentinel objects that have special
meaning as *shared* hook values: :data:`~coma.hooks.base.DEFAULT` and ``None``.
Specifically, of ``coma``'s :ref:`10 total hooks <hook_semantics>`, 4 default to
``DEFAULT`` in ``wake()`` while the other 6 default to ``None``:

.. code-block:: python

    # Definition of wake().
    def wake(
        ...,
        parser_hook = DEFAULT,
        pre_config_hook = None,
        config_hook = DEFAULT,
        post_config_hook = None,
        pre_init_hook = None,
        init_hook = DEFAULT,
        post_init_hook = None,
        pre_run_hook = None,
        run_hook = DEFAULT,
        post_run_hook = None,
        ...,
    ):
        ...

``DEFAULT`` gets replaced at runtime with the corresponding
:ref:`pre-defined default hook <default_hooks>` that gives ``coma`` its default
behavior. On the other hand, the propagation of a shared hook can be disabled by setting
its value to ``None``. Although ``None`` is a built in Python object, here it is being
used as a sentinel to mean "skip this hook" (though, in practice, we replace it with
the no-op :func:`~coma.hooks.base.identity()` function rather than truly skipping it).

In the :ref:`command hook example <command_hook_example>`, we saw how a few hooks
can easily extend the functionality of a particular command beyond ``coma``'s defaults.
In this example, we'll declare those same hooks to be **shared** hooks instead in
order to propagate that same extended functionality to *all* commands:

.. _shared_hook_example:

.. code-block:: python

    from coma import InvocationData, add_argument_factory, command, wake, DEFAULT

    parser_hook = add_argument_factory("--dry-run", action="store_true")

    def pre_run_hook(data: InvocationData):
        if data.known_args.dry_run:
            print(f"Early exit for command: {data.name}")
            quit()

    @command
    def greet():
        print("Hello World!")

    @command
    def leave():
        print("Goodbye World!")

    if __name__ == "__main__":
        wake(
            parser_hook=(DEFAULT, parser_hook),
            pre_run_hook=pre_run_hook,
        )

The definition of the custom hooks themselves have not changed compared to the
:ref:`command hook example <command_hook_example>`. The difference is that the hooks
are given to ``wake()`` instead of to ``@command``. This ensures the new functionality
propagates to all commands (both ``greet`` and ``leave``) without having to repeat
the hook redefinition for each one explicitly. Notice also that the ``parser_hook``
includes ``DEFAULT`` in its :ref:`sequence declaration <hooks_as_sequences>`. This
ensures that ``coma``'s default ``parser_hook`` is not replaced but rather extended.

Let's see this new functionality in action:

.. code-block:: console

    $ python main.py greet
    Hello World!
    $ python main.py greet --dry-run
    Early exit for command: greet
    $ python main.py leave
    Goodbye World!
    $ python main.py leave --dry-run
    Early exit for command: leave


Waking the Program
------------------

The main use case for :func:`~coma.core.wake.wake()` is to invoke the command
specified on the command line.

An additional use case is **simulating** command line arguments using the ``cli_args``
and (rarely) the ``cli_namespace`` parameters to ``wake()``. These parameters are
directly passed to `ArgumentParser.parse_known_args() <https://docs.python.org/3/library/argparse.html#partial-parsing>`_,
so the simulation behavior is identical to the one described there:

.. code-block:: python

    from coma import command, wake

    if __name__ == "__main__":
        command(name="greet", cmd=lambda: print("Hello World!"))
        wake(cli_args=["greet"])

Running this program without providing a command name as part of the command line
arguments works because ``wake()`` is simulating ``greet`` as a command line argument:

.. code-block:: console

    $ python main.py
    Hello World!

Simulated command line arguments are useful for invoking a default command. ``wake()``
raises a :class:`~coma.core.wake.WakeException` when encountering a waking problem.
In particular, waking without a program command specified on the command line results
in raising this error. Typically, we would simply leave the exception unhandled
as it gives useful warnings (e.g., about the fact that the command name is missing
from amongst the command line arguments). A more advanced use case involves catching
the exception and then waking with a default command:

.. code-block:: python

    from coma import WakeException, command, wake

    if __name__ == "__main__":
        command(name="greet", cmd=lambda: print("Hello World!"))
        command(name="default", cmd=lambda: print("Default command."))
        try:
            wake()
        except WakeException:
            wake(cli_args=["default"])

Running this program without providing command line arguments simulates running
``default`` as a command line argument:

.. code-block:: console
    :emphasize-lines: 5

    $ python main.py greet
    Hello World!
    $ python main.py default
    Default command.
    $ python main.py
    Default command.

Importing Commands from Other Modules
-------------------------------------

.. warning::

    A declared command (via :func:`@command <coma.core.command.command>`) is only
    *registered* with ``coma`` if the module in which the command is declared is
    *imported* at runtime. This is standard Python behavior: Non-imported code is
    not interpreted by the VM and not available at runtime. This is a bit obscured
    by the behind-the-scenes magic done by ``@command`` (which talks to a ``Coma``
    singleton object in the background). This magic only works if the declaration
    code runs (via being imported) at some point **before** the call to ``wake()``.

One way to ensure that all declared commands are properly registered with ``coma``
is to have a ``from . import module`` statement (for **every** ``module`` that
declares a command) in the top-level ``__init__.py`` of your codebase. That
forces each command module to be imported.

Alternatively, a common pattern is to put lightweight (one-line) ``@command`` wrappers
around calls to the main/workhorse functions all in a single module (typically, the
same module that calls ``wake()``). For example, supposed you define some commands in
modules called ``my_command.py`` and ``my_other_command.py``:

.. code-block:: python

    def my_cmd(...):
        ...

and

.. code-block:: python

    def my_other_cmd(...):
        ...


Then, inside ``main.py``, wrap these functions in ``@command`` declarations:

.. code-block:: python

    from coma import command, wake

    from my_command import my_cmd
    from my_other_command import my_other_cmd

    if __name__ == "__main__":
        command(cmd=my_cmd)
        command(cmd=my_other_cmd)
        wake()

Finally, a third alternative is to pass all declared commands scattered throughout
a codebase to the ``import_commands`` parameter of ``wake()``. The contents of
``import_commands`` is **fully** ignored by ``wake()``. However, it forces the Python
VM to import each of the provided modules, thus registering the declared commands.

.. note::

    Providing the imported commands to ``import_commands`` is not required (merely
    importing them is enough), but doing so prevents linters from complaining of
    unused import statements.

From the previous example, let's directly declare our functions as commands inside
their respective modules:

.. code-block:: python

    from coma import command

    @command
    def my_cmd(...):
        ...

and

.. code-block:: python

    from coma import command

    @command
    def my_other_cmd(...):
        ...

Then, inside ``main.py``, we import these commands and pass them to ``wake()``:

.. code-block:: python

    from coma import wake

    from my_command import my_cmd
    from my_other_command import my_other_cmd

    if __name__ == "__main__":
        wake(my_cmd, my_other_cmd)
