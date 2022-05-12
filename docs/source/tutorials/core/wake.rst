Wake
====

The main use case for :func:`~coma.core.wake.wake` has been covered in the
:doc:`introductory tutorial <../intro>`. After all commands have been
:func:`~coma.core.register.register`\ ed, :func:`~coma.core.wake.wake` is used
to wake from a coma.

:func:`~coma.core.wake.wake` is a fairly simple function. The only additional
use case is simulating command line arguments using :obj:`args` and
:obj:`namespace`, which are simply passed to
`ArgumentParser.parse_known_args <https://docs.python.org/3/library/argparse.html#partial-parsing>`_:

.. code-block:: python
    :caption: main.py

    import coma

    if __name__ == "__main__":
        coma.register("greet", lambda: print("Hello World!"))
        coma.wake(["greet"])

Run this program without providing command line arguments works because
:func:`~coma.core.wake.wake` is simulating :obj:`greet` as a command line argument:

.. code-block:: console

    $ python main.py
    Hello World!
