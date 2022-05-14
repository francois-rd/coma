Forget
======

:func:`~coma.core.forget.forget` is a context manager designed for more advanced
use cases. It enables you to selectively forget global configs or hooks from an
:func:`~coma.core.initiate.initiate`\ d coma.

Forgetting Global Hooks
-----------------------

``coma``'s behavior can be easily tweaked, replaced, or extended using hooks.
These are covered in great detail :doc:`in their own tutorial <../hooks/index>`.
Here, the emphasis is on the difference between global and local hooks. Hooks
can be :func:`~coma.core.initiate.initiate`\ d globally to affect ``coma``'s
behavior towards all commands or :func:`~coma.core.register.register`\ ed
locally to only affect ``coma``'s behavior towards a specific command.

.. warning::

    Local hooks are **appended** to the list of global hooks. Local hooks
    **do not** override global hooks. When a local hook is being
    :func:`~coma.core.register.register`\ ed, the corresponding global hook can
    only be replaced using :func:`~coma.core.forget.forget`.

For example, suppose we have a class-based command with a :obj:`handle()` method
instead of the :obj:`run()` method that ``coma`` expects by default:

.. code-block:: python

    class HandleCommand:
        def handle(self):
            print("Hello Handle!")

In order to use this command, we need to tell ``coma`` to:

* Stop looking for :obj:`run()`. We will :func:`~coma.core.forget.forget` the existing global hook that does this.
* Start looking for :obj:`handle()` instead. We will :func:`~coma.core.register.register` a new local hook to do this.

.. code-block:: python
    :caption: main.py

    import coma

    class HandleCommand:
        def handle(self):
            print("Hello Handle!")

    class RunCommand:
        def run(self):
            print("Hello Run!")

    if __name__ == "__main__":
        with coma.forget(run_hook=True):
            coma.register("handle", HandleCommand,
                          run_hook=coma.hooks.run_hook.factory("handle"))
        coma.register("run", RunCommand)
        coma.wake()

In this example, we locally :func:`~coma.core.register.register`\ ed a
:obj:`run_hook` that tells ``coma`` to call :obj:`handle()` and we used the
:func:`~coma.core.forget.forget` context manager to get ``coma`` to temporarily
forget its default :obj:`run_hook`, which attempts to call :obj:`run()` instead.

.. note::

    ``coma`` provides **factory functions** for some of the more common hooks.
    In this example, we used :func:`coma.hooks.run_hook.factory`, which
    simply creates a function that in turn calls the provided attribute (in this
    case, :obj:`"handle"`) of the command object.

Because :func:`~coma.core.forget.forget` is a context manager, any commands
registered outside its context are unaffected. In this example, :obj:`RunCommand`
still functions normally.

.. code-block:: console

    $ python main.py handle
    Hello Handle!
    $ python main.py run
    Hello Run!

Forgetting Global Configs
-------------------------

As with hooks, configs can be :func:`~coma.core.initiate.initiate`\ d globally to all
commands or :func:`~coma.core.register.register`\ ed locally to a specific command.

Let's revisit the second of the :ref:`Multiple Configurations <multiconfigs>` examples
from the :doc:`introductory tutorial <../intro>` to see how we can implement it
differently with :func:`~coma.core.forget.forget`:

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

Notice how, in the original example, the :obj:`Receiver` config is
:func:`~coma.core.register.register`\ ed (locally) to both commands. Instead, we
can :func:`~coma.core.initiate.initiate` a coma with both configs so that they
are (globally) supplied to all commands, then :func:`~coma.core.forget.forget`
the :obj:`Greeting` config just for the :obj:`leave` command:

.. code-block:: python
    :emphasize-lines: 14-17
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
        coma.initiate(Greeting, Receiver)
        coma.register("greet", lambda g, r: print(g.message, r.entity))
        with coma.forget("greeting"):
            coma.register("leave", lambda r: print("Goodbye", r.entity))
        coma.wake()

Notice that :func:`~coma.core.forget.forget` takes the config identifier (in this case,
we used the default identifier, which is :obj:`"greeting"`), not the config itself.

.. note::

    Configs need to be uniquely identified per-command, but not across commands.