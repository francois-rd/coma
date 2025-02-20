Wake
====

The main use case for :func:`~coma.core.wake.wake` has been covered in the
:doc:`introductory tutorial <../intro>`. Specifically, after all commands have
been :func:`~coma.core.register.register`\ ed, :func:`~coma.core.wake.wake` is
used to wake from a coma.

An additional use case is simulating command line arguments using
:obj:`args` and :obj:`namespace`, which are simply passed to
`ArgumentParser.parse_known_args() <https://docs.python.org/3/library/argparse.html#partial-parsing>`_:

.. code-block:: python
    :caption: main.py

    import coma

    if __name__ == "__main__":
        coma.register("greet", lambda: print("Hello World!"))
        coma.wake(["greet"])

Running this program without providing command line arguments works because
:func:`~coma.core.wake.wake` is simulating :obj:`greet` as a command line argument:

.. code-block:: console

    $ python main.py
    Hello World!


Finally, :func:`~coma.core.wake.wake` raises a
:class:`~coma.core.wake.WakeException` when encountering a waking problem.
The main use case is to simply leave the exception unhandled as it gives useful
warnings (e.g., about missing command line arguments). A more advanced use case
involves catching the exception to wake with a default command:

.. code-block:: python
    :caption: main.py

    import coma

    if __name__ == "__main__":
        coma.register("greet", lambda: print("Hello World!"))
        coma.register("default", lambda: print("Default command."))
        try:
            coma.wake()
        except coma.WakeException:
            coma.wake(["default"])

Running this program without providing command line arguments simulates running
with :obj:`default` as a command line argument:

.. code-block:: console

    $ python main.py greet
    Hello World!
    $ python main.py
    Default command.
