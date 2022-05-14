Introduction
============

Hooks make it easy to tweak, replace, or extend ``coma``.

.. _typesofhooks:

Types of Hooks
--------------

At the highest level, hooks belong to one of two types:

:parser:
    Parser hooks are called when a command is :func:`~coma.core.register.register`\ ed
    and are meant to `add_arguments() <https://docs.python.org/3/library/argparse.html#the-add-argument-method>`_
    to the underlying `ArgumentParser <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser>`_
    bound to the command.
:invocation:
    Invocation hooks are called by :func:`~coma.core.wake.wake` if, and only if,
    the command to which they are globally :func:`~coma.core.initiate.initiate`\ d
    or locally :func:`~coma.core.register.register`\ ed is invoked.

**Invocation hooks** further belong to one of three sub-types:

:config:
    A config hook is meant to initialize or affect the config objects that are
    globally :func:`~coma.core.initiate.initiate`\ d or locally
    :func:`~coma.core.register.register`\ ed to a command.
:init:
    An init hook is meant to instantiate or affect the command itself.

    .. warning::

        For function-based commands, the function is internally wrapped in
        another object, and it is this wrapper object that an init hook receives.
:run:
    A run hook is meant to execute or surround the execution of the command.

For all three hook sub-types above (**config**, **init**, and **run**), each is
further split into three sub-sub-types:

:pre:
    A pre hook is called immediately *before* a **main hook** as a way to
    add additional behavior.
:main:
    A main hook is generally meant to perform the bulk of the work.
:post:
    A post hook is called immediately *after* a **main hook** as a way to
    add additional behavior.

Altogether, there are 9 **invocation hooks**.

.. _hookpipeline:

Hook Pipeline
-------------

As stated above, **parser hooks** are called at the time a command is
:func:`~coma.core.register.register`\ ed, whereas the **invocation hooks** are
called if, and only if, the corresponding command is invoked.

The following keywords are used to :func:`~coma.core.initiate.initiate`,
:func:`~coma.core.register.register`, and/or :func:`~coma.core.forget.forget` hooks:

.. table::
    :widths: auto

    +------------+----------+--------------+-------------------------+
    | Type       | Sub-Type | Sub-Sub-Type | Keyword                 |
    +============+==========+==============+=========================+
    | parser     | N/A      | N/A          | :obj:`parser_hook`      |
    +------------+----------+--------------+-------------------------+
    | invocation | config   | pre          | :obj:`pre_config_hook`  |
    |            |          +--------------+-------------------------+
    |            |          | main         | :obj:`config_hook`      |
    |            +          +--------------+-------------------------+
    |            |          | post         | :obj:`post_config_hook` |
    |            +----------+--------------+-------------------------+
    |            | init     | pre          | :obj:`pre_init_hook`    |
    |            |          +--------------+-------------------------+
    |            |          | main         | :obj:`init_hook`        |
    |            +          +--------------+-------------------------+
    |            |          | post         | :obj:`post_init_hook`   |
    |            +----------+--------------+-------------------------+
    |            | run      | pre          | :obj:`pre_run_hook`     |
    |            |          +--------------+-------------------------+
    |            |          | main         | :obj:`run_hook`         |
    |            +          +--------------+-------------------------+
    |            |          | post         | :obj:`post_run_hook`    |
    +------------+----------+--------------+-------------------------+

The **invocation hook pipeline** consists of calling all the **invocation hooks**,
in the order listed here, one immediately following the other, with no other code in
between. In other words, the invocation hooks make up the entirety of the hook pipeline.

Default Hook Pipeline
---------------------

Rather than being hard-coded, ``coma``'s default behavior is, almost entirely, a
result of having certain specific default hooks :func:`~coma.core.initiate.initiate`\ d.
The upshot is that there is almost no part of ``coma``'s default behavior that cannot
be tweaked, replaced, or extended through clever use of hooks.

The default hooks are:

:parser:
    The default :obj:`parser_hook` is :func:`coma.hooks.parser_hook.default`.
    This hook uses `add_argument() <https://docs.python.org/3/library/argparse.html#the-add-argument-method>`_
    to add, for each config, a parser argument of the form :obj:`--{config_id}-path`
    where :obj:`{config_id}` is the config's identifier. This enables an explicit
    file path to the serialized config to be specified on the command line.
:pre config:
    N/A
:main config:
    The default :obj:`config_hook` is :func:`coma.hooks.config_hook.default`.
    This hook does a lot of the heaving lifting for manifesting ``coma``'s
    default behavior regarding configs. In short, for each config, this hook:

        * Attempts to load the config from file. This can interact with the default :obj:`parser_hook`.
        * If the config file isn't found, a config object with default attribute values is instantiated, and the default config object is serialized.

    .. note::

        YAML is used for serialization by default (since it is the only format
        that ``omegaconf`` supports), but ``coma`` also natively supports JSON. See
        :doc:`here <../examples/serialization>` for full details on configuration files.
:post config:
    The default :obj:`post_config_hook` is :func:`coma.hooks.post_config_hook.default`.
    This hook is responsible for overriding config attribute values with any that are
    specified on the command line in ``omegaconf``'s `dot-list notation <https://omegaconf.readthedocs.io/en/2.1_branch/usage.html#from-a-dot-list>`_.
    See :doc:`here <../examples/cli>` for full details on command line overrides.
:pre init:
    N/A
:main init:
    The default :obj:`init_hook` is :func:`coma.hooks.init_hook.default`. This hook
    initializes the command object using all configs, in order, as positional arguments.
:post init:
    N/A
:pre run:
    N/A
:main run:
    The default :obj:`run_hook` is :func:`coma.hooks.run_hook.default`. This
    hook calls the command object's :obj:`run()` method with no parameters.
:post run:
    N/A

.. note::

    For each of the default hooks, **factory functions** are provided that can create
    new variations on these defaults. For example, :func:`coma.hooks.run_hook.factory`
    can be used to change the command execution method name from :obj:`run()` to
    something else. See :doc:`here <../../references/hooks/index>` to explore all
    factory options.

.. note::

    If you are finding that the factory functions for the **parser hook**,
    **main config hook**, and/or **post config hook** are insufficient, consider
    making use of the many config-related utilities found
    :doc:`here <../../references/config/index>` to help you in writing your own
    custom hooks.

Global and Local Hooks
----------------------

Hooks can be :func:`~coma.core.initiate.initiate`\ d globally to affect ``coma``'s
behavior towards all commands or :func:`~coma.core.register.register`\ ed locally
to only affect ``coma``'s behavior towards a specific command.

.. warning::

    Local hooks are **appended** to the list of global hooks. Local hooks **do not**
    override global hooks. To override a global hook, use
    :func:`~coma.core.register.register` in conjunction with
    :func:`~coma.core.forget.forget`. See :doc:`here <../core/forget>` for details.
