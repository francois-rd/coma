Declaring Commands
==================

Using ``coma`` primarily consists of registering commands using the
:func:`@command <coma.core.command.command>` decorator. The basic functionality
of ``@command`` is explained in the :doc:`introductory tutorial <intro>`.
Here, the emphasis is on more advanced use cases.

.. _command_hooks:

Command Hooks
-------------

``coma`` uses the `Template <https://en.wikipedia.org/wiki/Template_method_pattern>`_
design pattern, which leverages `hooks <https://en.wikipedia.org/wiki/Hooking>`_ to
implement, tweak, replace, or extend its behavior. See the dedicated
:doc:`hooks tutorial <hooks>` for details on ``coma``'s hook protocols.
In this tutorial, we'll assume prior knowledge of hooks, while demonstrating how
to use ``@command`` to replace ``coma``'s default hooks to alter its behavior for
a particular command declaration.

Specifically, any of ``coma``'s :ref:`10 total hooks <hook_semantics>` can be
redefined in ``@command`` using the corresponding keyword argument:

.. code-block:: python

    from coma import command

    @command(
        parser_hook = ...,
        pre_config_hook = ...,
        config_hook = ...,
        post_config_hook = ...,
        pre_init_hook = ...,
        init_hook = ...,
        post_init_hook = ...,
        pre_run_hook = ...,
        run_hook = ...,
        post_run_hook = ...,
    )
    def my_cmd(...):
        ...

Typically, a hook is a function with a :ref:`specific signature <hook_protocols>`.
However, there are three additional (non-function) sentinel objects that have special
meaning as command hook values.

Any hook in ``@command`` that is not explicitly redefined defaults to the
:data:`~coma.hooks.base.SHARED` sentinel. The goal of ``SHARED`` is to indicate that
that particular hook for this particular command ought be be replaced at runtime
with the value of the corresponding hook from :func:`~coma.core.wake.wake()`.
Nearly all of ``coma``'s default behavior results from pre-defined hooks declared
in ``wake()``. ``SHARED`` copies that functionality to every command declaration.

See :ref:`here <shared_hooks>` for the full details on shared hooks. The
relevant point here is that any hook declared in ``wake()`` is automatically
propagated to *every* command declaration, **not** because that behavior is baked
into ``coma``, but rather because each hook in ``@command`` defaults to ``SHARED``.

By explicitly redefining a ``@command`` hook to some value other than ``SHARED``,
we are able to affect just that particular command declaration. What if we redefine
one of the shared hooks in ``wake()`` to some user-defined hook, but we still want
to maintain the default hook behavior for a specific command? This can happen, for
example, if we want custom (non-default) behavior for most hooks, but we want to
retain the default behavior for a few hooks. This is where the next special sentinel
comes in: :data:`~coma.hooks.base.DEFAULT`. ``DEFAULT`` gets replaced at runtime
with the corresponding default hook **regardless** of the value of ``wake()``'s hook.

Finally, a particular hook can be disabled altogether by setting its value to ``None``.
Although ``None`` is a built in Python object, here it is being used as a sentinel to
mean "skip this hook" (though, in practice, we replace it with the no-op
:func:`~coma.hooks.base.identity()` function rather than truly skipping it).

The dedicated hooks tutorial also emphasizes that hooks can be single/plain values,
or they can be :ref:`nested sequences <hooks_as_sequences>` of such values. These
nested sequences (if any) are recursively inspected for the presence of any of these
three sentinels (``SHARED``, ``DEFAULT``, and ``None``). These are replaced at
runtime with their semantic equivalent function. This is particularly useful to
**add** behavior to the shared hook, rather than outright replacing it. For example:

.. code-block:: python

    from coma import command, SHARED

    @command(
        parser_hook = (SHARED, additional_hook),
        ...,
    )
    def my_cmd(...):
        ...

means the ``parser_hook`` for this command declaration will first call the shared
``parser_hook`` defined in ``wake()`` and then call ``additional_hook``. The order
here matters. Having ``SHARED`` *after* ``additional_hook`` calls them in the
reverse order.

.. _hook_sentinel_summary:

.. admonition:: Summary:

    * By default, an undefined ``@command``-level hook falls back to the corresponding
      ``SHARED`` hook defined in ``wake()``. In general, we think in terms of the
      ``wake()``-level hook as *propagating* to each command declaration by default
      (unless an explicit ``@command``-level definition is given).
    * By default, the hooks defined in ``wake()`` are precisely those that give
      ``coma`` its default behavior as explored throughout these tutorials. That is
      how each command declaration comes to inherit this same default behavior. It
      is not baked into ``@command``.
    * If a ``wake()``-level hook is redefined, the default ``coma`` behavior can be
      recovered in a particular command declaration by defining its ``@command``-level
      hook as ``DEFAULT``.
    * Setting a hook to ``None`` disables (skips) that particular hook. This is
      **the idiomatic way** to prevent a ``wake()``-level hook from propagating to
      a particular command.
    * Hook definitions can be plain/simple objects, or **sequences** thereof. In
      particular, setting a ``@command``-level hook to ``(SHARED, additional_hook)``
      is **the idiomatic way** to add additional behaviour to a particular command
      beyond what is specified in the shared hook. Note that the order here matters:
      ``(SHARED, additional_hook) != (additional_hook, SHARED)``.


Let's see how a few hooks can easily add functionality into a command beyond ``coma``'s
defaults. In this example, we define a ``parser_hook`` that adds a new ``--dry-run``
flag to the command line, as well as a ``pre_run_hook`` that exits the program early
(before the command is actually executed) if that flag is given on the command line:

.. _command_hook_example:

.. code-block:: python

    from coma import InvocationData, add_argument_factory, command, wake, SHARED

    parser_hook = add_argument_factory("--dry-run", action="store_true")

    def pre_run_hook(data: InvocationData):
        if data.known_args.dry_run:
            print(f"Early exit for command: {data.name}")
            quit()

    @command(
        parser_hook=(SHARED, parser_hook),
        pre_run_hook=(SHARED, pre_run_hook),
    )
    def greet():
        print("Hello World!")

    if __name__ == "__main__":
        wake()

Let's see this new functionality in action:

.. code-block:: console

    $ python main.py greet
    Hello World!
    $ python main.py greet --dry-run
    Early exit for command: greet

.. note::

    ``coma`` provides **factory functions** for some of the more common hooks. In this
    example, we used :func:`~coma.hooks.parser_hook.add_argument_factory`, which simply
    creates a ``parser_hook`` that in turn relays the provided parameters to the
    `add_argument() <https://docs.python.org/3/library/argparse.html#the-add-argument-method>`_
    method of the underlying `ArgumentParser <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser>`_
    bound to this command.

    Most hooks have factories to enable behavioral tweaks as one-liners as seen
    here. Browse the hooks' :doc:`package reference <../references/hooks/index>`
    for details. Factory function names always end with ``*_factory``.

.. _command_signature_inspection:

Command Signature Inspection
----------------------------

How does ``@command`` inspect the command signature to determine which command
parameters are configs and which are regular parameters?

``@command`` accepts an optional :class:`~coma.config.cli.SignatureInspectorProtocol`
to which the signature inspection is delegated. When no explicit signature inspector
is given, the default is a :class:`~coma.config.cli.SignatureInspector` with default
parameters. Here, we'll explore the parameter space of the ``SignatureInspector``.
This forms the basis of ``coma`` default behavior, but is *not* baked into
``@command``. In fact, tweaking the default (particularly with ``inline`` configs)
is quite common, as we will see.

``SignatureInspector`` is just a lightweight wrapper around
:meth:`ParamData.from_signature() <coma.config.cli.ParamData.from_signature()>`,
which does all the heavy lifting. We'll explore ``from_signature()``'s parameter
options in the upcoming :ref:`example <command_inspection_example>`. But first,
let's get a basic sense of how the command signature is inspected.

Configs vs Regular Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The distinction between :attr:`ParamData.configs <coma.config.cli.ParamData.configs>`
and :attr:`ParamData.other_parameters <coma.config.cli.ParamData.other_parameters>`
(which we will interchangeably call *regular* parameters) in a command's signature is
determined by inspecting its **type annotation** (if any), its **default value**
(if any), its `kind <https://docs.python.org/3/library/inspect.html#inspect.Parameter.kind>`_,
and whether the parameter is marked as ``inline`` (discussed in the
:ref:`next section <command_inline_configs>`).

**Configs take priority over regular parameters.** If a parameter *can* be considered
a config (as per the criteria below), it *is* treated as one. All parameters that
cannot be interpreted as configs are assumed to be regular parameters **unless**
marked as ``inline``.

Criteria for Interpreting a Parameter as a Config
"""""""""""""""""""""""""""""""""""""""""""""""""

1. The parameter has a type annotation that **exactly** matches one of ``list``,
   ``dict``, or any ``dataclass`` type. We refer to these as **config annotations**.

2. The parameter does **not** have a default value. Since configs enjoy a
   dedicated :ref:`declarative initialization protocol <config_declaration_hierarchy>`,
   default parameter values are not needed.

   .. note::

        This means that a convenient way to ensure that a config-annotated
        parameter is interpreted as a regular parameter is to give it a default.
        For example, ``list_cfg: list`` is interpreted as a config whereas
        ``non_cfg_list: list = None`` is interpreted as a regular parameter.

3. The parameter is **not** marked ``inline``. Even if the parameter otherwise
   conforms to criteria (1) and (2), being marked ``inline`` disqualifies.

4. **Special case:** Because variadic positional (``*args``) and variadic keyword
   (``**kwargs``) parameters cannot be assigned defaults in Python, and because
   they can :ref:`never <command_inline_configs>` be marked as ``inline``,
   criteria (2) and (3) cannot be used for them. Instead, use the special flags
   :attr:`SignatureInspector.args_as_config <coma.config.cli.SignatureInspector.args_as_config>`
   and
   :attr:`SignatureInspector.kwargs_as_config <coma.config.cli.SignatureInspector.kwargs_as_config>`
   which are passed directly to
   :meth:`ParamData.from_signature() <coma.config.cli.ParamData.from_signature()>`
   to toggle whether variadic parameters are interpreted as configs or regular
   parameters. By default, they **are** interpreted as configs.

See the :ref:`example <command_inspection_example>` below to get a better sense
of how this gets applied.

.. _command_inline_configs:

Inline Configs
^^^^^^^^^^^^^^

An ``inline`` parameter is a one-off config field. Specifically, all parameters marked
as :attr:`SignatureInspector.inline <coma.config.cli.SignatureInspector.inline>` are
aggregated into a special :attr:`~coma.config.cli.ParamData.inline_config`, which is
backed by a programmatically-created ``dataclass``. This provides all the rigorous
runtime type validation of a standard ``dataclass``-backed ``omegaconf`` config without
requiring a user-defined ``dataclass`` to be created just for these one-off fields.
Moreover, inline configs are considered **non-serializable**, whereas a user-defined
``dataclass`` aggregating the same fields would, by default, be serializable.

.. admonition:: On mutable inline default values:

    An ``inline`` parameter requires a default value (see criteria below). Because
    it is un-Pythonic to declare a **mutable** default value in a function definition,
    it can be tricky to set a good default value for ``inline`` parameters. For
    example, Python recommends a default value of ``inline_list: list | None = None``
    rather than ``inline_list: list = []`` because defaults are initialized during
    function definition, not function calling (which means ``[]`` is shared between
    calls).

    To circumvent this, each item in the ``SignatureInspector.inline`` container
    can consist of *either* just the name of the parameter to mark as ``inline``,
    *or* be 2-tuple where the first value is the parameter's name and the second
    value is a ``default_factory`` conforming to the requirements of the same
    argument to `dataclasses.field() <https://docs.python.org/3/library/dataclasses.html#dataclasses.field>`_.
    See the :ref:`example <command_inspection_example>` below for details.


Criteria for Interpreting a Parameter as ``inline``
"""""""""""""""""""""""""""""""""""""""""""""""""""

1. The parameter has a type annotation. A missing annotation is disqualifying.

2. The parameter has a default value. A missing default value is disqualifying.
   The default value can be specified directly in the command's signature, or it can
   be provided as a ``default_factory`` to ``SignatureInspector.inline``. It is an
   error to specify both a signature-level default and an inline-level default factory.

3. The default value is a valid instance of the annotation type. If not, the
   underlying ``omegaconf`` call will raise a :obj:`ValidationError`.

4. The parameter's name is found in ``SignatureInspector.inline``. If this is true,
   but one of the above criteria are violated, an error is raised. If this is false,
   the parameter is considered not marked as ``inline`` and is instead treated as a
   regular parameter.

5. The parameter's `kind <https://docs.python.org/3/library/inspect.html#inspect.Parameter.kind>`_
   is not variadic positional or variadic keyword. These two special cases can be
   configs or regular parameters, but never ``inline``. This is done to avoid duplicate
   parameter values when executing the command at runtime.

See the example below to get a better sense of how this gets applied.

.. _command_inspection_example:

Example
^^^^^^^

In the example below, even though ``Data`` is a ``dataclass``, it is *not* considered
a config because of its non-config annotation and its ``None`` default value (either
one of which is disqualifying on its own).

On the other hand, both ``out_file`` and ``my_list`` can be overridden on the command
line because of their inline declaration. Even though ``my_list`` has (a) a valid
config annotation type (``list``), and (b) no default value in the command signature,
it is interpreted as ``inline`` because of that inline declaration. Notice further
that because ``my_list`` is a mutable type, we specify a ``default_factory`` as part
of the inline declaration, rather than providing a mutable default directly in the
command signature. That is not necessary for ``out_file`` because strings are
immutable in Python.

List-like command line arguments are appended to ``my_list`` because it is
marked ``inline``. However, list-like arguments are not given to ``*args`` because
``args_as_config`` is ``False``. On the other hand, because ``kwargs_as_config`` is
``True`` (implicitly, by default), any dict-like command line arguments are given to
``**kwargs``.

.. code-block:: python

    from coma import SignatureInspector, command, wake
    from dataclasses import dataclass
    from typing import Optional

    @dataclass
    class Data:
        x: int = 42

    @dataclass
    class Config:
        y: float = 3.14

    @command(
        signature_inspector=SignatureInspector(
            args_as_config=False, inline=["out_file", ("my_list", list)],
        ),
    )
    def cmd(
            cfg: Config,
            my_list: list,
            data: Optional[Data] = None,
            out_file: str = "out.txt",
            *args,
            **kwargs,
        ):
        print("cfg is:", cfg)
        print("my_list is:", my_list)
        print("data is:", data or Data())
        print("out_file is:", out_file)
        print("*args is:", args)
        print("**kwargs is:", kwargs)

    if __name__ == "__main__":
        wake()

Invoking on the command line with some carefully-chosen overrides to highlight
these difference results in the following:

.. code-block:: console

    $ python main.py cmd x=1 y=2 z inline::out_file=foo.txt 'my_list=[bar]'
    cfg is: Config(y=2.0)
    my_list is: ['bar']
    data is: Data(x=42)
    out_file is: "foo.txt"
    *args is: ()
    **kwargs is: {'x': 1, 'y': 2}
    $ ls
    main.py
    cfg.yaml

Notice that:

1. The list-like argument ``'z'`` is not in ``*args`` because ``*args`` is not a config
   (otherwise, it would have been in ``*args``). It is also not in ``my_list`` because
   ``my_list`` is an inline config and so adding to ``my_list`` requires an explicit
   ``omegaconf`` dotlist notation to be used (``'my_list=[bar]'`` in this example).
   See :doc:`here <../examples/cli>` for further explanation.

2. ``**kwargs`` includes both dict-like arguments (``x`` and ``y``).

3. ``out_file`` is overridden. Unlike ``my_list``, we prefixed ``out_file`` with the
    inline config identifier (``"inline"``). See the next point for an explanation.

4. ``out_file`` is prefixed with the inline config identifier (``"inline"``) to
   prevent ``**kwargs`` from *also* containing an ``"out_file"`` field. This occurs
   because ``**kwargs`` is backed by a ``dict``, and ``omegaconf`` permits any fields
   in ``dict`` configs. See :doc:`here <../examples/cli>` for further explanation.
   The upshot relevant to this discussion is that including ``"out_file"`` in
   ``**kwargs`` would result in a runtime error from ``"out_file"`` appearing multiple
   times in the command's parameter list (which is a ``TypeError`` in Python).

5. Because ``cfg`` is a config, it's ``y`` attribute was overridden. Notice that both
   ``cfg``  and ``**kwargs`` accepted ``y``. This sharing of overrides is the default
   behavior in ``coma``. To disable it, see :class:`~coma.config.cli.Override`.

6. Because ``data`` is not a config, it's ``x`` attribute is not overridden. In fact,
   because the default value of ``data`` is not replaced in any :doc:`hooks <hooks>`,
   its value when invoking the command will invariably be ``None``. Use
   :meth:`ParamData.replace() <coma.config.cli.ParamData.replace()>` in a hook to
   change this. See :doc:`here <../examples/preload>` for an example.

7. Because ``inline`` configs and variadic configs are
   :ref:`non-serializable <command_non_serializable>`, the only config file that
   gets created from invoking the command is ``cfg.yaml``. Nothing gets written for
   ``my_list``, ``out_file``, or ``**kwargs``.

Supplemental Configs
^^^^^^^^^^^^^^^^^^^^

Supplemental configs are additional ``config`` parameters that required by the command
declaration but do *not* appear in the command's signature. These can be helpful for
providing additional configurable information to the :doc:`hooks <hooks>` beyond what
the command object itself requires.

Any object passed as :obj:`supplemental_configs` to ``@command`` are invariably
treated as configs and converted into :class:`~coma.config.base.Configs` without
additional ``SignatureInspector`` checks except for ensuring that no supplemental
config identifiers clash with any parameter names in the command signature (or
with the special
:attr:`ParamData.inline_identifier <coma.config.cli.ParamData.inline_identifier>`
for ``inline`` config fields).

In the example below, suppose we desperately want a supplemental config called
``"inline"``. That clashes with the default name of the ``inline_identifier``, so
we rename the ``inline_identifier`` to ``"param"`` while provide a supplemental
config named ``"inline"``. Although this supplemental config won't be available as
part of the command invocation, it is available in all the hooks via ``get_config()``
on :attr:`InvocationData.parameters <coma.hooks.base.HookData.parameters>`. See
:ref:`here <hook_protocols>` for details on :class:`~coma.hooks.base.InvocationData`.

.. code-block:: python

    from coma import SignatureInspector, command, wake

    @command(
        pre_init_hook=lambda data: print(
            "supplemental:", data.parameters.get_config("inline").get_latest()
        ),
        signature_inspector=SignatureInspector(
            inline_identifier="param", inline=[("cfg", dict)]
        ),
        inline=dict,
    )
    def cmd(cfg: dict):
        print("cfg:", cfg)

    if __name__ == "__main__":
        wake()

Invoking on the command line with some carefully-chosen overrides to highlight
these difference results in the following:

.. code-block:: console

    $ python main.py cmd inline::only=supplemental param::only=cfg
    supplemental: {'only': 'supplemental'}
    cfg: {'only': 'cfg'}


Config Serialization and Persistence Management
-----------------------------------------------

.. note::

    We refer to both config *serialization* and config *persistence management*. While
    these terms are closely related and mostly interchangeable, the subtle distinction
    is that *serialization* refers to **whether** a config file is written and **what**
    the contents of that file are, whereas *persistence management* refers to **where**
    the config file exists (if any) in the file system (both the path and the base file
    name) and **how** ``coma`` is made aware of this path (via ``argparse`` flags).


``@command`` accepts an optional :class:`~coma.config.io.PersistenceManager` that
manages the file paths of serializable configs as well as the ``argparse`` flags for
setting these file paths.

When no explicit persistence manager is given, the default is a ``PersistenceManager``
that favors ``.yaml`` file extensions. This is why config files in most tutorials
and examples in these docs are YAML files. It is *not* baked into ``@command``.

.. note::

    ``coma`` supports both YAML and JSON config file formats. For JSON examples,
    see :doc:`here <../examples/serialization>`.

A persistence manager allows you to :meth:`~coma.config.io.PersistenceManager.register`
an explicit file path and explicit ``argparse`` flag arguments for a specific config.
If no explicit registration is used, a sensible default is used. For details,
see :doc:`here <../examples/serialization>`.

.. warning::

    :meth:`Registering <coma.config.io.PersistenceManager.register>` a particular
    config with a persistence manager does **not** guarantee/force that the config
    will be serialized, but rather only explicitly determines which parameters get
    passed to `add_argument() <https://docs.python.org/3/library/argparse.html#the-add-argument-method>`_
    (overriding the sensible defaults that are otherwise provided).

.. _command_non_serializable:

Non-Serializable Configs
^^^^^^^^^^^^^^^^^^^^^^^^

``coma`` considers variadic positional (``*args``) and keyword (``**kwargs``) configs,
as well as all ``inline`` configs to be non-serializable. These configs will never be
serialized by ``coma``'s :ref:`default hooks <default_hooks>` **regardless** of
whether that config gets ``register()``\ ed with a persistence manager.

.. note::

    To force a non-serializable config to be serialized, write a custom hook that
    directly calls :func:`~coma.config.io.write()` on that config object.

Parameters to ``argparse``
--------------------------

By default, ``coma`` uses `ArgumentParser.add_subparsers().add_parser() <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_subparsers>`_
to create a new `ArgumentParser <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser>`_
with default parameters for each declared command. However, you can provide
keyword arguments to override the default parameter values to the internal
``add_parser()`` call through the ``parser_kwargs`` parameter to ``@command``.

For example, suppose you want to add `command aliases <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_subparsers>`_.
This can be achieved through the :obj:`aliases` keyword:

.. code-block:: python
    :emphasize-lines: 7

    from coma import command, wake

    if __name__ == "__main__":
        command(
            name="greet",
            cmd=lambda: print("Hello World!"),
            parser_kwargs=dict(aliases=["gr"]),
        )
        wake()

With this alias, :obj:`greet` can now be invoked with just :obj:`gr`:

.. code-block:: console

    $ python main.py gr
    Hello World!
