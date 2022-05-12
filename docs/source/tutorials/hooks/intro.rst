Introduction
============

Hooks make it easy to tweak, replace, or extend ``coma``.

Types of Hooks
--------------

At the highest level, hooks belong to one of two types:

:parser hooks:
    These hooks are called when a command is :func:`~coma.core.register.register`\ ed
    and are meant to `add arguments <https://docs.python.org/3/library/argparse.html#the-add-argument-method>`_
    to the underlying `ArgumentParser <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser>`_
    bound to the command.
:invocation hooks:
    These hooks are called by :func:`~coma.core.wake.wake` if, and only if, the
    command to which they are globally :func:`~coma.core.initiate.initiate`\ d
    or locally :func:`~coma.core.register.register`\ ed is invoked.

**Invocation hooks** further belong to one of three sub-types:

:config hooks:
    These hooks are meant to instantiate all config objects that are
    are globally :func:`~coma.core.initiate.initiate`\ d or locally
    :func:`~coma.core.register.register`\ ed to a command.
:init hooks:
    These hooks are meant to instantiate the command itself. For class-based
    commands, these hooks are meant to instantiate the class. For function-based
    commands, the function is internally wrapped in a class, and it is this
    wrapper class that is meant to get instantiated.
:run hooks:
    These hooks are meant to run the command. For class-based commands, these
    hooks are meant to call the command object's :obj:`run()` method. For
    function-based commands, these hooks are meant to call the function itself.

For all three hook sub-types above (**config**, **init**, and **run** **hooks**),
each is further split into three sub-sub-types:

:pre hooks:
    These hooks are called immediately *before* the **main hooks** as a way to
    prepend additional behavior.
:main hooks:
    These hooks are called immediately *after* the **pre hooks** are meant to
    perform the bulk of the hook's work. These hooks correspond to the
    **config**, **init**, and **run** **hooks** as described above.
:post hooks:
    These hooks are called immediately *after* the **main hooks** as a way to
    append additional behavior.

Altogether, there are 9 **invocation hooks**.

Hook Pipeline
-------------

As stated above, **parser hooks** are called at the time a command is
:func:`~coma.core.register.register`\ ed, whereas the **invocation hooks** are
called if, and only if, the corresponding command is invoked.

All **parser hooks** are :func:`~coma.core.initiate.initiate`\ d,
:func:`~coma.core.register.register`\ ed, and/or
:func:`~coma.core.forget.forget`\ -et+otten through the :obj:`parser_hook` keyword.

All **invocation hooks** are :func:`~coma.core.initiate.initiate`\ d,
:func:`~coma.core.register.register`\ ed, and/or
:func:`~coma.core.forget.forget`\ -et+otten through the following keywords:

:pre config hooks: :obj:`pre_config_hook`
:main config hooks: :obj:`config_hook`
:post config hooks: :obj:`post_config_hook`
:pre init hooks: :obj:`pre_init_hook`
:main init hooks: :obj:`init_hook`
:post init hooks: :obj:`post_init_hook`
:pre run hooks: :obj:`pre_config_hook`
:main run hooks: :obj:`run_hook`
:post run hooks: :obj:`post_run_hook`

These are called in the listed order, one immediately following the other, and
they make up the entirety of the invocation pipeline.

Default Hook Pipeline
---------------------

Rather than hard-coding its behavior, ``coma``'s default behavior is, almost entirely, a
result of having certain specific default hooks :func:`~coma.core.initiate.initiate`\ d.
The upshot is that, there is almost no part of ``coma``'s default behavior that cannot
be tweaked, replaced, or extended through clever use of hooks. The default hooks are:

:parser hooks:
    The default :obj:`parser_hook` is :func:`coma.hooks.parser_hook.default`.
    This hook uses `add_argument() <https://docs.python.org/3/library/argparse.html#the-add-argument-method>`_
    to add, for each config, a parser argument of the form :obj:`--{config_id}-path`
    where :obj:`{config_id}` is the config's identifier. This enables an explicit
    file path to the serialized config to be specified on the command line.
:pre config hooks:
    N/A
:main config hooks:
    The default :obj:`config_hook` is :func:`coma.hooks.config_hook.default`.
    This hook does a lot of the heaving lifting for manifesting ``coma``'s
    default behavior regarding configs. In short, for each config, this hook:

        * Attempts to load the config from file. This can interact with the default :obj:`parser_hook`.
        * If the config file isn't found, a config object with default attribute values is instantiated, and the default config object is serialized.

    YAML is used for serialization by default (since it is the only format that
    ``omegaconf`` supports), but ``coma`` also natively supports JSON.
:post config hooks:
    The default :obj:`post_config_hook` is :func:`coma.hooks.post_config_hook.default`.
    This hook is responsible for overriding config attribute values with any that are
    specified on the command line in ``omegaconf``'s `dot-list notation <https://omegaconf.readthedocs.io/en/2.1_branch/usage.html#from-a-dot-list>`_.
:pre init hooks:
    N/A
:main init hooks:
    The default :obj:`init_hook` is :func:`coma.hooks.init_hook.default`. This
    hook initializes the command object by providing its constructor with all
    configs, in order, as positional arguments.
:post init hooks:
    N/A
:pre run hooks:
    N/A
:main run hooks:
    The default :obj:`run_hook` is :func:`coma.hooks.run_hook.default`. This
    hook calls the command object's :obj:`run()` method with no parameters.
:post run hooks:
    N/A

.. note::

    For each of the default hooks, **factory functions** are provided that can create
    new variations on these defaults. For example, :func:`coma.hooks.run_hook.factory`
    can be used to change the command execution method name from :obj:`run()` to
    something else. See :doc:`here <../../references/hooks/index>` to explore all
    factory options.
