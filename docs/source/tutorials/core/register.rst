Register
========

The meat of working with ``coma`` is to :func:`~coma.core.register.register` new
commands to an :func:`~coma.core.initiate.initiate`\ d coma.

The main use cases, including command naming, command objects, config objects,
config identifiers, and :func:`~coma.core.register.register`\ ing multiple
commands have all been covered in the :doc:`introductory tutorial <../intro>`.

Here, the emphasis is on local ``argparse`` overrides and local hooks as
additional use cases.

``argparse`` Overrides
----------------------

By default, ``coma`` uses `ArgumentParser.add_subparsers <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_subparsers>`_
to create a new `ArgumentParser <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser>`_
with default parameters for each :func:`~coma.core.register.register`\ ed command.
However, you can provide keyword arguments to override the defaults in the internal call
through the :obj:`parser_kwargs` parameter to :func:`~coma.core.register.register`.

For example, suppose you want to add `command aliases <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_subparsers>`_.
This can be achieved through the :obj:`aliases` keyword:

.. code-block:: python
    :emphasize-lines: 5
    :caption: main.py

    import coma

    if __name__ == "__main__":
        coma.register("greet", lambda: print("Hello World!"),
                      parser_kwargs=dict(aliases=["gr"]))
        coma.wake()

With this alias, :obj:`greet` can now be invoked with just :obj:`gr`:

.. code-block:: console

    $ python main.py gr
    Hello World!

.. _localhooks:

Local Hooks
-----------

``coma``'s behavior can be easily tweaked, replaced, or extended using hooks.
These are covered in great detail :doc:`in their own tutorial <../hooks/index>`.
Here, the emphasis is on the difference between global and local hooks.

As with configs, hooks can be :func:`~coma.core.initiate.initiate`\ d globally to affect
``coma``'s behavior towards all commands or :func:`~coma.core.register.register`\ ed
locally to only affect ``coma``'s behavior towards a specific command.

Let's see how a few local hooks can easily inject additional behavior into a program:

.. code-block:: python
    :emphasize-lines: 3, 5-9, 13
    :caption: main.py

    import coma

    parser_hook = coma.hooks.parser_hook.factory("--dry-run", action="store_true")

    @coma.hooks.hook
    def pre_run_hook(known_args):
        if known_args.dry_run:
            print("Early exit!")
            quit()

    if __name__ == "__main__":
        coma.register("greet", lambda: print("Hello World!"),
                      parser_hook=parser_hook, pre_run_hook=pre_run_hook)
        coma.wake()

In this example, we locally :func:`~coma.core.register.register`\ ed a
:obj:`parser_hook` that adds a new :obj:`--dry-run` flag to the command line as
well as a :obj:`pre_run_hook` that exits the program early (before the command
is actually executed) if the flag is given on the command line:

.. code-block:: console

    $ python main.py greet
    Hello World!
    $ python main.py greet --dry-run
    Early exit!

.. note::

    ``coma`` provides **factory functions** for some of the more common hooks.
    In this example, we used :func:`coma.hooks.parser_hook.factory`, which
    simply creates a function that in turn relays the provided parameters to the
    `add_argument() <https://docs.python.org/3/library/argparse.html#the-add-argument-method>`_
    method of the underlying `ArgumentParser <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser>`_
    bound to this command.

.. note::

    Local hooks are **appended** to the list of global hooks. Local hooks
    **do not** override global hooks. To override a global hook, use
    :func:`~coma.core.register.register` in conjunction with
    :func:`~coma.core.forget.forget`.
