Fitting ``coma`` to Existing Code
=================================

In general, there are at least four ways to modify ``coma`` to fit the interface
of an existing codebase. We highlight these options using the following example:

.. code-block:: python
    :emphasize-lines: 5

    class StartCommand:
        def __init__(self):
            self.foo = "bar"

        def start(self):
            print(f"foo = {self.foo}")


In this example, we suppose that an existing command-like class has a
:obj:`start()` method instead of the default :obj:`run()` method.

Redefining Hooks
----------------

The first option is redefining the :obj:`run_hook` of
:func:`~coma.core.initiate.initiate` to call :obj:`start()` instead of :obj:`run()`:

.. code-block:: python
    :emphasize-lines: 11

    import coma

    class StartCommand:
        def __init__(self):
            self.foo = "bar"

        def start(self):
            print(f"foo = {self.foo}")

    if __name__ == "__main__":
        coma.initiate(run_hook=coma.hooks.run_hook.factory("start"))
        coma.register("start", StartCommand)
        coma.wake()


The program now runs as expected:

.. code-block:: console

    $ python main.py start
    foo = bar

.. warning::

    Internally, **function-based** commands will still be wrapped in a class that
    defines a :obj:`run()` method, regardless of any :obj:`run_hook` redefinition.
    As such, it is generally safer, if more verbose, to locally redefine the
    :obj:`run_hook` using :func:`~coma.core.register.register` and a
    :func:`~coma.core.forget.forget` context manager:

    .. code-block:: python
        :emphasize-lines: 11, 13

        import coma

        class StartCommand:
            def __init__(self):
                self.foo = "bar"

            def start(self):
                print(f"foo = {self.foo}")

        if __name__ == "__main__":
            with coma.forget(run_hook=True):
                coma.register("start", StartCommand,
                              run_hook=coma.hooks.run_hook.factory("start"))
            coma.wake()

    This ensures that other commands are not affected. See forget.

Wrapping with Functions
-----------------------

The second option is wrapping :obj:`StartCommand` in a function-based command:

.. code-block:: python
    :emphasize-lines: 11

    import coma

    class StartCommand:
        def __init__(self):
            self.foo = "bar"

        def start(self):
            print(f"foo = {self.foo}")

    if __name__ == "__main__":
        coma.register("start", lambda: StartCommand().start())
        coma.wake()


The benefit of this approach is in its simplicity. The drawback is the loss of
separation between command initialization and execution.

Wrapping with Classes
---------------------

The third option is wrapping the incompatible :obj:`StartCommand` in a
compatible class-based command:

.. code-block:: python
    :emphasize-lines: 10-12, 15

    import coma

    class StartCommand:
        def __init__(self):
            self.foo = "bar"

        def start(self):
            print(f"foo = {self.foo}")

    class WrapperCommand(StartCommand):
        def run(self):
            self.start()

    if __name__ == "__main__":
        coma.register("start", WrapperCommand)
        coma.wake()

The benefit of this approach is that it maintains the separation between command
initialization and execution. The drawback is that it is slightly more verbose
than the function-based wrapper.

Adding Interface Elements
-------------------------

The fourth option is adding missing interface elements (in this case, an
attribute) to :obj:`StartCommand`:

.. code-block:: python
    :emphasize-lines: 11

    import coma

    class StartCommand:
        def __init__(self):
            self.foo = "bar"

        def start(self):
            print(f"foo = {self.foo}")

    if __name__ == "__main__":
        StartCommand.run = StartCommand.start
        coma.register("start", StartCommand)
        coma.wake()

For simple cases, this option is often the most succinct.
