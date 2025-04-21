Preloading Configs
==================

Some complex commands *conditionally* depend on one or more configs based on the
*current* contents of other configs. The :func:`~coma.hooks.config_hook.preload()`
function is designed for this use case. Specifically, the idiomatic pattern is:

1. Create a :doc:`custom <../tutorials/hooks>` ``pre_config_hook`` that calls
   ``preload()`` on the whichever configs are needed to make the conditional
   decision for other configs.
2. Optionally, manipulate configs or other command parameters based on the conditional
   decision (as we'll see in the example below).

Preloading follows the :ref:`declarative hierarchy <config_declaration_hierarchy>`
for loading configs, but *skips* writing configs to file (even for configs that are
:meth:`serializable <coma.config.cli.ParamData.is_serializable>`). In other words, if
a config file exists, its contents *are* preloaded. But preloading *never* serializes.
Crudely, ``preload()`` is analogous to calling the :ref:`default <default_config_hook>`
``config_hook`` with ``write=False``.

Let's see ``preload()`` in action with an example where the command is using a
config-driven strategy pattern.

Config-Driven Strategy Pattern
------------------------------

For each strategy, we have a separate config containing configurable details
for strategy execution. These configs are precisely those we'll only need to
conditionally ``preload()``:

.. code-block:: python

    from dataclasses import dataclass

    @dataclass
    class Strat1:
        some: str = "strategy"
        config: str = "data"

    @dataclass
    class Strat2:
        other: str = "data"
        used: str = "for"
        alternative: str = "strategy"

We also have a ``StrategyBuilder`` config. This is the conditioning config
that determines which strategy option gets chosen at runtime. To add runtime
validation to the user's choice of strategy, we implement an Enum with the strategy
options and a ``MISSING`` option for when the user fails to provide an option:

.. code-block:: python

    from dataclasses import dataclass
    from enum import Enum, auto

    class Strategies(Enum):
        one = auto()
        two = auto()
        MISSING = auto()

    @dataclass
    class StrategyBuilder:
        strategy: Strategies = Strategies.MISSING
        more: str = "data"
        the: str = "builder"
        needs: str = "."


To make use of these strategy configs, we create a common ``Strategy`` interface for
them. In this example, it's a simple mock interface:

.. code-block:: python

    class Strategy:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def take_action(self):
            print(f"Do something with: {self.kwargs}")

Choosing a Strategy at Runtime
------------------------------

Next, we'll create a ``pre_config_hook`` that leverages ``preload()`` to instantiate
a strategy at runtime based on the user's input.

First, we ``preload()`` our ``StrategyBuilder`` config (line ``4``). This modifies
``data`` **inplace** by loading the specified config (``builder``) according to
the config :ref:`declaration hierarchy <config_declaration_hierarchy>`.

Next, we use :meth:`~coma.config.base.Config.get_latest()` (line ``6``) to retrieve
the :class:`~coma.config.base.Config` instance variant representing the latest rung of
the declaration hierarchy. In other words, if the user provides command line overrides
for ``StrategyBuilder``, we'll retrieve that. Otherwise, we'll fall back to the config
values stored in a ``builder.yaml`` file (if it exists). Otherwise, we'll fall back to
the default values.

Since the default ``builder.strategy`` value is ``MISSING``, we'll raise a
``ValueError`` (line ``8``) if the user fails to provide a strategy (either in
``builder.yaml`` or as a command line override). Otherwise, we choose a strategy config
based on the user's input (line ``10`` or line ``13``).

Next, we ``preload()`` the chosen config (line ``18``), then retrieve the latest
instance variant (line ``19``), then instantiate a ``Strategy`` based on this data
(line ``20``), and finally set the ``strategy`` command parameter (line ``21``; see
:ref:`below <preload_command_declaration>` to understand where this parameter is
declared).

Altogether:

.. code-block:: python
    :linenos:

    from coma import InvocationData, preload

    def pre_config_hook(data: InvocationData):
        preload(data, "builder")

        builder = data.parameters.get_config("builder").get_latest()
        if builder.strategy == Strategies.MISSING:
            raise ValueError("Missing strategy")
        elif builder.strategy == Strategies.one:
            strat_cfg_name = "strat1"
            drop_cfg_name = "strat2"  # Optional
        elif builder.strategy == Strategies.two:
            strat_cfg_name = "strat2"
            drop_cfg_name = "strat1"  # Optional
        else:
            raise ValueError(f"Unsupported strategy: {builder.strategy}")

        preload(data, strat_cfg_name)
        strat_cfg = data.parameters.get_config(strat_cfg_name).get_latest()
        strategy = Strategy(**strat_cfg)
        data.parameters.replace("strategy", strategy)
        data.parameters.delete(drop_cfg_name)  # Optional

We have also included a few optional steps (lines ``11``, ``14``, and ``22``). These
are not directly part of the strategy pattern. Instead, they implement additional
functionality just for the sake of demonstration.

Specifically, suppose that we want **only** the chosen strategy's config to get
serialized. This can sometimes be useful in practice if we've registered a
:ref:`non-standard <non_default_config_path>` serialization path for our configs.
After this ``pre_config_hook`` executes, the :ref:`default <default_config_hook>`
``config_hook`` will serialize **all** configs it is aware of (regardless of whether
they've been preloaded or not). On line ``22``, we are dynamically deleting the unused
strategy's config (based on line ``11`` or ``14``) from ``data.parameters`` so that
the ``config_hook`` is not aware of its existence and won't serialize it.

.. note::

    :meth:`Deleting <coma.config.cli.ParamData.delete>` only removes a parameter from
    ``data.parameters`` for *this* command invocation (thereby hiding it from later
    hooks). The parameter is **not** permanently removed. In particular, any existing
    config file is left untouched.

.. _preload_command_declaration:

Command Declaration
-------------------

Finally, we can put this all together in the command declaration. Both strategy configs
as well as the ``StrategyBuilder`` config are :ref:`supplemental <supplemental_configs>`
because we don't need them in the command itself. Instead, the command's signature
includes a ``strategy`` parameter that will contain an instance of the chosen strategy
(from line ``21`` of our ``pre_config_hook``). Notice that the command's other config
(``cfg``) is completely unaffected by the strategy pattern functionality:

.. code-block:: python

    from coma import command, wake
    from dataclasses import dataclass

    @dataclass
    class Config:
        non: str = "strategy"
        data: str = "that"
        cmd: str = "needs"

    @command(
        pre_config_hook=pre_config_hook,
        strat1=Strat1,
        strat2=Strat2,
        builder=StrategyBuilder,
    )
    def cmd(strategy: Strategy, cfg: Config):
        print("Running strategy...")
        strategy.take_action()
        print("Other config: ", cfg)

    if __name__ == "__main__":
        wake()

To invoke this command, the user must supply a strategy:

.. code-block:: console

    $ python main.py cmd
    Traceback (most recent call last):
    ...
    ValueError: Missing strategy
    $ python main.py cmd strategy=one
    Running strategy...
    Do something with: {'some': 'strategy', 'config': 'data'}
    Other config:  Config(non='strategy', data='that', cmd='needs')
    $ python main.py cmd strategy=two
    Running strategy...
    Do something with: {'other': 'data', 'used': 'for', 'alternative': 'strategy'}
    Other config:  Config(non='strategy', data='that', cmd='needs')

Complete Example
----------------

.. code-block:: python

    from coma import InvocationData, command, preload, wake
    from dataclasses import dataclass
    from enum import Enum, auto

    @dataclass
    class Strat1:
        some: str = "strategy"
        config: str = "data"

    @dataclass
    class Strat2:
        other: str = "data"
        used: str = "for"
        alternative: str = "strategy"

    class Strategies(Enum):
        one = auto()
        two = auto()
        MISSING = auto()

    @dataclass
    class StrategyBuilder:
        strategy: Strategies = Strategies.MISSING
        more: str = "data"
        the: str = "builder"
        needs: str = "."

    class Strategy:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def take_action(self):
            print(f"Do something with: {self.kwargs}")

    def pre_config_hook(data: InvocationData):
        preload(data, "builder")
        builder = data.parameters.get_config("builder").get_latest()
        if builder.strategy == Strategies.MISSING:
            raise ValueError("Missing strategy")
        elif builder.strategy == Strategies.one:
            strat_cfg_name = "strat1"
            drop_cfg_name = "strat2"  # Optional
        elif builder.strategy == Strategies.two:
            strat_cfg_name = "strat2"
            drop_cfg_name = "strat1"  # Optional
        else:
            raise ValueError(f"Unsupported strategy: {builder.strategy}")
        preload(data, strat_cfg_name)
        strat_cfg = data.parameters.get_config(strat_cfg_name).get_latest()
        strategy = Strategy(**strat_cfg)
        data.parameters.replace("strategy", strategy)
        data.parameters.delete(drop_cfg_name)  # Optional

    @dataclass
    class Config:
        non: str = "strategy"
        data: str = "that"
        cmd: str = "needs"

    @command(
        pre_config_hook=pre_config_hook,
        strat1=Strat1,
        strat2=Strat2,
        builder=StrategyBuilder,
    )
    def cmd(strategy: Strategy, cfg: Config):
        print("Running strategy...")
        strategy.take_action()
        print("Other config: ", cfg)

    if __name__ == "__main__":
        wake()
