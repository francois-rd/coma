Defining Hooks
==============

``coma`` has a template-based architecture. Hooks not only implement ``coma``'s
default behavior, but also make it easy to tweak, replace, or extend that behavior.

.. _hook_semantics:

Hook Semantics
--------------

``coma`` has very few baked in assumptions. **All** of ``coma``'s default behavior
results from pre-defined hooks that have been chosen to fill its template slots.
Nearly all behavior can be drastically changed with user-defined hooks.

``coma`` has 10 total hook slots in its template. To help users decide which hooks to
define, each of these slots has *semantics* (the type of functionality that ``coma``
expects that particular hook slot will have). Most of these semantics are not hard
requirements, and hook implementations are free to vary wildly from their semantics.
That said, semantics provide a solid base from which to explore this space.

At the highest level, hooks belong to one of two semantic types: **parser** and
**invocation**.

Parser Hooks
^^^^^^^^^^^^

Parser hooks are the only type of hook that get executed at command *registration*
time (prior to command invocation). The ``parser_hook`` semantics are to add command
line flags via calls to `add_argument() <https://docs.python.org/3/library/argparse.html#the-add-argument-method>`_
on the underlying `ArgumentParser <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser>`_
bound to the command that will later be invoked.

Parser hooks for **all** declared commands are executed (at registration time).
This is needed so that ``argparse`` has all the necessary information to invoke
the correct command based on the provided command line arguments. This means that
parser hooks with side effects will **always** execute those side effects, even
if the command they are bound to isn't the one that ultimately gets invoked.

Invocation Hooks
^^^^^^^^^^^^^^^^

Invocation hooks are *stored* during command registration, but only get *executed*
if the command to which they are bound is invoked (i.e., is chosen by ``argparse``
based on the provided command line arguments). Invocation hooks, as their name
suggests, are responsible for completing all necessary steps involved in successfully
invoking the command to which they are bound.

Invocation hooks *semantics* further belong to one of three sub-types:

**Config:**

    Config hooks are meant to initialize or affect the config objects that are
    bound to a particular command.

.. _invocation_init_hook:

**Init:**

    Init hooks are meant to instantiate or affect the command object (either a
    function or a class).

    .. warning::

        Function-based command objects are internally wrapped in a
        programmatically-generated class, and it is this wrapper class that an
        init hook receives, not the raw function object. This unifies the
        interface, since (from the perspective of an init hook) all command
        objects are classes that ought to be instantiated.

**Run:**

    Run hooks are meant to execute or surround the execution of the command object
    after it has been instantiated (presumably by an init hook).

Each of the three invocation hook sub-types (**config**, **init**, and **run**) is
further split into three flavors:

**Pre:**

    Pre hooks are executed immediately *before* the **main hook** of the same type
    as a way to add additional behavior.

**Main:**

    Main hooks are generally meant to perform the bulk of the work for that semantic
    category (**config**, **init**, or **run**).

**Post:**

    Post hooks are executed immediately *after* the **main hook** of the same type
    as a way to add additional behavior.

Altogether, there are 9 **invocation hooks**. The following keywords are used in
:func:`@command <coma.core.command.command>` and :func:`~coma.core.wake.wake()`
to define :ref:`command <command_hooks>` and :ref:`shared <shared_hooks>` hooks,
respectively:

.. table::
    :widths: auto

    +------------+----------+--------+-------------------------+
    | Type       | Sub-Type | Flavor | Keyword                 |
    +============+==========+========+=========================+
    | parser     | N/A      | N/A    | :obj:`parser_hook`      |
    +------------+----------+--------+-------------------------+
    | invocation | config   | pre    | :obj:`pre_config_hook`  |
    |            |          +--------+-------------------------+
    |            |          | main   | :obj:`config_hook`      |
    |            +          +--------+-------------------------+
    |            |          | post   | :obj:`post_config_hook` |
    |            +----------+--------+-------------------------+
    |            | init     | pre    | :obj:`pre_init_hook`    |
    |            |          +--------+-------------------------+
    |            |          | main   | :obj:`init_hook`        |
    |            +          +--------+-------------------------+
    |            |          | post   | :obj:`post_init_hook`   |
    |            +----------+--------+-------------------------+
    |            | run      | pre    | :obj:`pre_run_hook`     |
    |            |          +--------+-------------------------+
    |            |          | main   | :obj:`run_hook`         |
    |            +          +--------+-------------------------+
    |            |          | post   | :obj:`post_run_hook`    |
    +------------+----------+--------+-------------------------+

.. _hook_pipeline:

Hook Pipeline
-------------

As stated above, **parser hooks** are executed when a command is registered,
whereas the **invocation hooks** are executed if, and only if, the command to
which they are bound is invoked by ``argparse``. The **invocation hook pipeline**
consists of executing all the **invocation hooks** (in order) one immediately
following the other, with no other code in between. In other words, the invocation
hooks make up the **entirety** of the code responsible for completing all necessary
steps involved in successfully invoking the command to which they are bound.

.. _hook_protocols:

Hook Protocol
-------------

To enable interoperability between hooks (especially in the hook pipeline), all
hooks must follow a specific protocol (i.e., function signature). All hooks,
regardless of semantics, must take *exactly* one parameter. For **parser hooks**,
this parameter is a :class:`~coma.hooks.base.ParserData` object, whereas it is an
:class:`~coma.hooks.base.InvocationData` object for **invocation hooks**. Both of
these inherit from :class:`~coma.hooks.base.HookData`, and it is perfectly acceptable
to subclass any of these to add additional attributes needed in custom hooks.

Hooks typically modify their input parameter *inplace* and return ``None``. However,
a hook can also return a new object (of the same type as its input parameter) derived
from the input parameter instead of making inplace modifications. Subsequent hooks in
the pipeline receive whichever object is the latest non-``None`` return object from a
preceding hook.

.. _default_hooks:

Default Hooks
-------------

Rather than being hardcoded, ``coma``'s default behavior is, almost entirely, a
result of having specific pre-defined hooks as default value in the definition of
:func:`~coma.core.wake.wake()` that :ref:`propagate <shared_hooks>` to all command
declarations unless explicitly :ref:`redefined <command_hooks>`. The upshot is
that there is almost no part of ``coma``'s default behavior that cannot be tweaked,
replaced, or extended through hooks.

That being said, ``coma``'s default hooks already provide extensive functionality.
Of ``coma``'s 10 total hooks, only 4 have pre-defined defaults: the ``parser_hook``,
the main ``config_hook``, the main ``init_hook``, and the main ``run_hook``. All
default hooks are generated from **factory functions** with default parameters.

.. _default_hook_factories:

.. note::

    Factories to enable behavioral tweaks as one-liners by redefining a default
    hook using its factory with a single changed parameter. For example,
    :func:`run_hook.default_factory() <coma.hooks.run_hook.default_factory>`
    can be used to change the command execution method name from the default
    ``run()`` to something else. See :doc:`here <../examples/coma>`.

    Browse the hooks' :doc:`package reference <../references/hooks/index>` to
    explore factory options. Factory function names always end with ``*_factory``.
    All the default factories are named ``default_factory`` and can be found in
    their respective hook-semantic module. For example, the default factory for
    ``run_hook`` is found in :func:`coma.hooks.run_hook.default_factory()`.

    If you are finding that the factory functions are insufficient, consider
    making use of the many config-related utilities found
    :doc:`here <../references/config/index>` to help you in writing your own
    custom hooks.

In the explanations below, ``data`` refers to the input parameter of the hook
(:class:`~coma.hooks.base.ParserData` for parser hooks and
:class:`~coma.hooks.base.InvocationData` for invocation hooks).

.. _default_parser_hook:

**Default Parser Hook:**

    The :func:`default <coma.hooks.parser_hook.default_factory>` ``parser_hook`` uses
    :attr:`data.persistence_manager <coma.hooks.base.HookData.persistence_manager>` to
    add, for each :meth:`serializable <coma.config.cli.ParamData.is_serializable>` config,
    a :meth:`parser path argument <coma.config.io.PersistenceManager.add_path_argument>`.
    This enables an explicit file path to the config file to be specified on the command
    line via a flag. By :ref:`default <persistence_registration>`, the flag is
    ``--{config_name}-path``, where ``config_name`` is the name of the corresponding
    config parameter in the :ref:`command signature <command_signature_inspection>`.

.. _default_config_hook:

**Default Main Config Hook:**

    The :func:`default <coma.hooks.config_hook.default_factory>` ``config_hook`` does
    all the heaving lifting for manifesting ``coma``'s default behavior regarding
    configs. It makes the following assumptions:

    * Configs are declarative. They should always follow the
      :ref:`declarative hierarchy <config_declaration_hierarchy>`.
    * Declared configs are required. This means that declared configs (both in the
      command's signature and any :ref:`supplemental configs <supplemental_configs>`)
      are *loaded* (based on the declarative hierarchy) by default.
    * Persistence of configs is typically desirable. This means that, by default, all
      :meth:`serializable <coma.config.cli.ParamData.is_serializable>` configs are
      serialized (to enable the middle step of the
      :ref:`declarative hierarchy <config_declaration_hierarchy>`), but skipping
      serialization for a particular config is easy.

    In short, for each config, this hook initializes the config based on the
    :ref:`declarative hierarchy <config_declaration_hierarchy>` protocol:

    * At minimum, each config is initialized from its base declaration.
    * :meth:`Serializable <coma.config.cli.ParamData.is_serializable>` configs are
      then loaded from file (if one exists) or written to file (otherwise) unless
      serialization has been explicitly toggled off for that particular config.
      Serialization interacts with the default ``parser_hook`` since it queries the same
      :attr:`data.persistence_manager <coma.hooks.base.HookData.persistence_manager>`
      to :meth:`get the file path <coma.config.io.PersistenceManager.get_file_path>`
      of each config based on its path declaration in the default ``parser_hook``.
      See :doc:`here <../examples/serialization>` for more details on config files.
    * For each config, an attempt is made to :doc:`override <../examples/cli>` its
      config attribute values with any command line arguments that fit ``omegaconf``'s
      `dot-list notation <https://omegaconf.readthedocs.io/en/2.1_branch/usage.html#from-a-dot-list>`_.

    .. note::

        Each config variant in the :ref:`declarative hierarchy <config_declaration_hierarchy>`
        is :class:`stored <coma.config.base.Config>` so that later hooks can access any
        variant (if needed). This is particularly helpful in cases where some configs
        need to be :doc:`preloaded <../examples/preload>` before others.

    The ``config_hook``'s :func:`default factory <coma.hooks.config_hook.default_factory>`
    includes many flags for tweaking the default behavior. For example, you can skip the
    override or the serialization of some configs but not others. Or you can raise a
    :obj:`FileNotFoundError` if a particular config file cannot be found. Or even
    :ref:`force <on_the_fly_hook_redefinition>` the serialization of the override
    values rather than the base config declaration.

.. _default_init_hook:

**Default Main Init Hook:**

    The :func:`default <coma.hooks.init_hook.default_factory>` ``init_hook``
    instantiates the :attr:`data.command <coma.hooks.base.HookData.command>`
    class by calling its ``__init__()`` method with all
    :ref:`declared parameters <command_signature_inspection>` (config, inline, and
    regular) filled in through the :meth:`~coma.config.cli.ParamData.call_on()`
    method of :attr:`data.parameters <coma.hooks.base.HookData.parameters>`. Then,
    the value of :attr:`data.command <coma.hooks.base.HookData.command>` (a class
    type) gets replaced **inplace** with the value of the instantiated object.

    .. warning::

        In user-defined hooks, be sure to **never** make decisions based on directly
        inspecting the ``data.command`` object. Not only are function-based commands
        :ref:`implicitly wrapped <invocation_init_hook>` in a class, but also the
        value of ``data.command`` changes from a class type to an instance of that
        class as part of this default init hook.

        Instead, use :attr:`data.name <coma.hooks.base.HookData.name>` if you need to
        determine which command is being invoked, since the command name is guaranteed
        to be **unique** across all declared commands.

**Default Main Run Hook:**

    The :func:`default <coma.hooks.run_hook.default_factory>` ``run_hook`` calls
    the :attr:`data.command <coma.hooks.base.HookData.command>` object's ``run()``
    (by default, though this can be :doc:`changed <../examples/coma>`) method
    with no parameters. This assumes that the ``init_hook`` has instantiated
    ``data.command`` from a class type to an instance.

.. _hooks_as_sequences:

Hooks as Sequences
------------------

Typically, a hook is a function with a signature based on the
:ref:`hook protocol <hook_protocols>`. However, there are three additional
(non-function) sentinel objects (``SHARED``, ``DEFAULT``, and ``None``) that have
:ref:`special meaning <hook_sentinel_summary>` as :ref:`command <command_hooks>`
and/or :ref:`shared <shared_hooks>` hook values. A valid "plain" hook can be any
single function adhering to the hook protocol or any single of these three sentinels.

In addition, any (recursively) nested **sequences** of these singular/plain values
is also a valid hook. Each item in these sequences is recursively inspected for the
presence of any of the three sentinels. These are replaced at runtime with their
:ref:`semantic equivalent <hook_sentinel_summary>` function. This is particularly
useful to :ref:`extend <command_hook_example>` ``coma``'s default behavior,
rather than outright replacing :ref:`replacing <on_the_fly_hook_redefinition>` it. To
emphasize the recursive potential of nested hook sequences, consider this toy example:

.. code-block:: python

    from coma import command, wake, DEFAULT

    @command(
        run_hook=(
            (
                None,
                lambda _: print("First"),
            ),
            lambda _: print("Second"),
            (
                (
                    (
                        (
                            DEFAULT,
                            lambda _: print("Fourth"),
                        ),
                    ),
                ),
            ),
            None,
            (),
            lambda _: print("Last"),
        ),
    )
    def nested():
        print("Third")

    if __name__ == "__main__":
        wake()

Let's see how ``coma`` resolves the nested sequences:

.. code-block:: console

    $ python main.py nested
    First
    Second
    Third
    Fourth
    Last

Notice that ``DEFAULT`` gets replaced at runtime with the default ``run_hook`` which
runs the command and prints ``Third`` at that position in the nested sequences.

Beyond this toy example, sequences are helpful in practice for decomposing a complex
hook function into a series of smaller ones. Often these component functions will be
hook variants created using :ref:`factories <default_hook_factories>`. Hook sequences
essentially wrap each component function into a higher-order function that executes the
components in order following the rules of the :ref:`hook protocol <hook_protocols>`.

As an extreme example, we could redefine the ``pre_config_hook`` of a command to
stuff the **entire** default :ref:`invocation pipeline <hook_pipeline>` into it
while setting the standard hooks to ``None``:

.. code-block:: python

    from coma import command, wake, config_hook, init_hook, run_hook

    @command(
        pre_config_hook=(
            config_hook.default_factory(),
            init_hook.default_factory(),
            run_hook.default_factory(),
        ),
        config_hook=None,
        init_hook=None,
        run_hook=None,
    )
    def cmd():
        print("No problem!")

    if __name__ == "__main__":
        wake()

This example also highlights the utility of ``pre`` and ``post`` hooks. They are really
just conceptual convenience functions. All functionality could *in principle* be placed
in a single hook sequence as shown here. The benefit of multiple hook types and
sub-types with differing semantics is to help *conceptually* separate concerns. Consider
that, in :ref:`this <command_hook_example>` example, we defined a ``pre_run_hook`` that
exits the program before running the command. In principle, we could have implemented
this same functionality by redefining the ``run_hook`` as ``(pre_run_hook, SHARED)``.
However, because the new functionality is an early exit (*before* running the command),
it feels conceptually cleaner to exit as as a separate ``pre_run_hook``, rather than as
an initial component of the ``run_hook`` in the invocation pipeline. This distinction
is purely conceptual. The resulting behavior is essentially equivalent.
