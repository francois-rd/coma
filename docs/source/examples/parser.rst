Command Line Arguments
======================

Adding command line arguments is as an easy way to inject additional behavior into
a program. For an introduction, see the :ref:`command <command_hook_example>` and
:ref:`shared <shared_hook_example>` examples.

.. _command_level_arguments:

Adding ``argparse`` Arguments
-----------------------------

Adding command line arguments is as an easy way to give a command additional data or
modifiers that, for whatever reason, don't belong in a dedicated config object. The
simplest approach to this leverages :ref:`inline configs <command_inline_configs>`.
However, inline configs don't appear as proper flags in the usage documentation (i.e.,
when invoking the command with the ``-h`` or ``--help`` command line flags) because
``argparse`` is not aware of them. Using command line flags resolves this:

.. code-block:: python

    from coma import InvocationData, add_argument_factory, command, wake

    def pre_init_hook(data: InvocationData):
        data.parameters.replace("a", data.known_args.a)
        if getattr(data.known_args, "b"):
            data.parameters.replace("b", data.known_args.b)

    if __name__ == "__main__":
        command(
            name="numbers",
            cmd=lambda a, b=456: print(a, b),
            parser_hook=(
                add_argument_factory("a", type=int),
                add_argument_factory("-b", type=int),
            ),
            pre_init_hook=pre_init_hook,
        )
        wake()

Here, the ``numbers`` command has a required parameter ``a`` and an optional parameter
``b``. For each, we define an ``argparse`` argument using
:func:`~coma.hooks.parser_hook.add_argument_factory()` (one required and one optional).
The ``argparse`` arguments need to be connected to the command parameters prior to
command initialization, so we add a ``pre_init_hook`` that does exactly that. Each
command parameter's value is :meth:`replaced <coma.config.cli.ParamData.replace>`
with the corresponding ``argparse`` argument.

.. note::

    Because ``b`` is an optional ``argparse`` argument, it does not necessarily exist
    in the :attr:`data.known_args <coma.hooks.base.InvocationData.known_args>` namespace
    object created by ``argparse``. Hence, we check its existence with ``getattr()``.

With these hook definitions, we can invoke the command as follows:

.. code-block:: console

    $ python main.py numbers 123
    123 456
    $ python main.py numbers 123 -b 321
    123 321
    $ python main.py numbers -h
    usage: example_parser.py numbers [-h] [-b B] a

    positional arguments:
      a

    optional arguments:
      -h, --help  show this help message and exit
      -b B

There are tradeoffs with using ``argparse`` arguments instead of
:ref:`inline configs <command_inline_configs>`. As mentioned, inline configs don't
appear in the usage message by default. However, you can always add inline configs
:ref:`manually <command_parameters_to_argparse>` to the usage string instead. One
benefit of inline configs is that they benefit from ``omegaconf``'s stronger runtime
type validation (compared to ``argparse``). Specifying inline configs is also
significantly less verbose, since we don't need to define a ``parser_hook`` or a
``pre_init_hook``.

On a similar note, every :ref:`non-serializable <command_non_serializable>` config
does not appear in the basic usage information. Consider updating the ``argparse``
usage string to include these details when creating a production-ready UI.

.. _on_the_fly_hook_redefinition:

On-the-Fly Hook Redefinition
----------------------------

Command line arguments can also be used to redefine hooks **on the fly**. In this
example, we define an ``--overwrite`` flag that is used to toggle whether the overridden
attribute values of ``Config`` during any particular command invocation ought to
themselves overwrite the values that were previously serialized in ``config.yaml``:

.. code-block:: python
    :linenos:

    from coma import InstanceKeys, InvocationData, add_argument_factory, command, wake, config_hook
    from dataclasses import dataclass

    @dataclass
    class Config:
        x: int = 0
        y: str = "foo"

    def conditional_config_hook(data: InvocationData):
        kwargs = {}
        if data.known_args.overwrite:
            kwargs = dict(
                write_instance_key=InstanceKeys.OVERRIDE,
                overwrite=True,
            )
        hook = config_hook.default_factory(**kwargs)
        hook(data)

    @command(
        parser_hook=add_argument_factory("--overwrite", action="store_true"),
        config_hook=conditional_config_hook,
    )
    def cmd(config: Config):
        print(config)

    if __name__ == "__main__":
        wake()

When the ``--overwrite`` flag is not given on the command line, the ``kwargs`` (line
``10``) to ``config_hook.default_factory`` (line ``16``) is empty, which reverts to
``coma``'s default behavior. But when ``--overwrite`` is given (line ``11``), we add
parameters to ``kwargs`` (lines ``12-15``) to tell ``config_hook.default_factory``
(line ``16``) to create a config hook that will overwrite (line ``14``) any existing
``config.yaml`` file with the override values (line ``13``) rather than the (default)
base values. Finally, we execute whichever of these hook variants gets created by the
factory (line ``17``), which modifies ``data`` inplace.

Let's see this new functionality in action:

.. code-block:: console

    $ python main.py cmd
    Config(x=0, y='foo')
    $ cat config.yaml
    x: 0
    y: foo
    $ python main.py cmd x=42 y=bar
    Config(x=42, y='bar')
    $ cat config.yaml
    x: 0
    y: foo
    $ python main.py cmd --overwrite x=42 y=bar
    Config(x=42, y='bar')
    $ cat config.yaml
    x: 42
    y: bar
    $ python main.py cmd
    Config(x=42, y='bar')  # Loads the overridden values from file.
