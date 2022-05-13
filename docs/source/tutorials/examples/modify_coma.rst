Modifying ``coma`` to Fit Existing Code
=======================================

It is fairly easy to modify ``coma`` to fit the interface of an existing codebase
(rather than the other way around). For example, suppose we have an existing
command-like class that has a :obj:`start()` method instead of a :obj:`run()` method:

.. code-block:: python
    :emphasize-lines: 5

    class StartCommand:
        def __init__(self):
            self.foo = "bar"

        def start(self):
            print(f"foo = {self.foo}")

In general, there are at least four ways to get ``coma`` to work with existing
code. Below, we highlight these concepts through the :obj:`StartCommand` example.

Redefining Hooks
----------------

First, we can redefine the :obj:`run_hook` of :func:`~coma.core.initiate.initiate`
to call :obj:`start()` instead of :obj:`run()`:

.. code-block:: python
    :emphasize-lines: 11
    :caption: main.py

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

    Intenally, **function-based** commands will still be wrapped in a class that
    defines a :obj:`run()` method, regardless of any :obj:`run_hook` redefinition.
    As such, it is generally safer, if more verbose, to locally redefine the
    :obj:`run_hook` using :func:`~coma.core.register.register` and a
    :func:`~coma.core.forget.forget` context manager:

    .. code-block:: python
        :emphasize-lines: 11, 13
        :caption: main.py

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

    This approach ensures that other commands are not affected.


Wrapping with Functions
-----------------------

Second, the incompatible :obj:`StartCommand` can be wrapped in a function-based command:

.. code-block:: python
    :emphasize-lines: 11
    :caption: main.py

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

Third, the incompatible :obj:`StartCommand` can be wrapped in a compatible
class-based command:

.. code-block:: python
    :emphasize-lines: 10-12, 15
    :caption: main.py

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

Magic Approaches
----------------

If you're comfortable with a certain level of Python's black magic trickery,
you have even more options for ensuring interface compatibility:

.. code-block:: python
    :emphasize-lines: 11
    :caption: main.py

    import coma

    class StartCommand:
        def __init__(self):
            self.foo = "bar"

        def start(self):
            print(f"foo = {self.foo}")

    if __name__ == "__main__":
        setattr(StartCommand, "run", StartCommand.start)
        coma.register("start", StartCommand)
        coma.wake()

This approach can often be the most succinct, but using Python magic is
sometimes controversial.
