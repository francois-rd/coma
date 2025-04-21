Fitting ``coma`` to Existing Code
=================================

In general, there are at least three ways to modify ``coma`` to fit the interface
of an existing codebase. We highlight these options using the following example:

.. code-block:: python
    :emphasize-lines: 5

    class StartCommand:
        def __init__(self):
            self.foo = "bar"

        def start(self):
            print(f"foo = {self.foo}")


In this example, we suppose that we have an **existing** command-like class called
``StartCommand`` that cannot be modified. Supposed further that ``StartCommand`` has
a ``start()`` method instead of the ``run()`` method that ``coma`` expects by default.

1. Redefining Hooks
-------------------

The first option is redefining the ``run_hook`` to call ``start()`` instead of
``run()`` for this command using the :ref:`run hook factory <default_hook_factories>`:

.. code-block:: python
    :emphasize-lines: 3

    from coma import command, wake, run_hook

    @command(name="start", run_hook=run_hook.default_factory("start"))
    class StartCommand:
        def __init__(self):
            self.foo = "bar"

        def start(self):
            print(f"foo = {self.foo}")

    if __name__ == "__main__":
        wake()


The program now runs as expected:

.. code-block:: console

    $ python main.py start
    foo = bar

.. warning::

    Internally, **function-based** commands will still be wrapped in a
    programmatically-generated class that **always** defines a ``run()`` method,
    regardless of any ``run_hook`` redefinition. As such, redefining ``run_hook``
    globally as a :ref:`shared hook <shared_hooks>` instead of locally as a
    :ref:`command hook <command_hooks>` will break function-based command declarations.

2. Wrapping with Functions
--------------------------

The second option is wrapping ``StartCommand`` in lightweight function-based command:

.. code-block:: python
    :emphasize-lines: 11

    from coma import command, wake

    class StartCommand:
        def __init__(self):
            self.foo = "bar"

        def start(self):
            print(f"foo = {self.foo}")

    if __name__ == "__main__":
        command(name="start", cmd=lambda: StartCommand().start())
        wake()


The benefit of this approach is in its simplicity. The drawback is the loss of
separation between command initialization and execution. It works well here only
because ``StartCommand`` has a no-argument ``__init__()`` method.

3. Wrapping with Classes
------------------------

The third option is wrapping the incompatible ``StartCommand`` in a compatible
class-based command:

.. code-block:: python
    :emphasize-lines: 10-13

    from coma import command, wake

    class StartCommand:
        def __init__(self):
            self.foo = "bar"

        def start(self):
            print(f"foo = {self.foo}")

    @command(name="start")
    class WrapperCommand(StartCommand):
        def run(self):
            self.start()

    if __name__ == "__main__":
        wake()

The benefit of this approach is that it maintains the separation between command
initialization and execution. The drawback is that it is slightly more verbose
than the function-based wrapper.
