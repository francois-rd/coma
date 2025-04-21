Config Serialization and Management
===================================

In a :ref:`prior tutorial <serialization_vs_management>`, we saw how ``coma``'s
config serialization and persistence management behavior is not baked in but rather
depends on which :class:`~coma.config.io.PersistenceManager` gets passed to
:func:`@command <coma.core.command.command>` when declaring a command.

In this extended example, we'll explore the functionality of the ``PersistenceManager``
and its implications for config serialization.

.. _yaml_over_json:

YAML over JSON
--------------

Let's start with a simple example:

.. code-block:: python

    from coma import command, wake
    from dataclasses import dataclass

    @dataclass
    class Config:
        message: str = "Hello World!"

    @command
    def greet(cfg: Config):
        print(cfg.message)

    if __name__ == "__main__":
        wake()

The ``PersistenceManager`` interacts with the :ref:`default <default_parser_hook>`
``parser_hook`` to add an ``argparse`` flag for setting the serialization file path
of configs (``cfg`` in this example) and interacts with the
:ref:`default <default_config_hook>` ``config_hook`` where the (possibly user-supplied)
file path is retrieved to perform serialization.
See :ref:`here <persistence_registration>` for details.

When instantiating a ``PersistenceManager``, a file type is chosen for all configs to
fall back to. By default, YAML is chosen because ``omegaconf`` only supports YAML.
However, ``coma`` does natively :ref:`support <favoring_json_configs>` JSON as well
via a JSON-YAML translation.

Since the above example uses a default ``PersistenceManager``, ``cfg`` will
fall back to a YAML serialization (``cfg.yaml``) by default:

.. code-block:: console
    :emphasize-lines: 4

    $ python main.py greet
    Hello World!
    $ ls
    cfg.yaml
    main.py
    $ cat cfg.yaml
    message: Hello World!

Even with a default ``PersistenceManager``, we can **force** serialization to JSON
by specifying an explicit file path for ``cfg`` with a ``.json`` file extension:

.. code-block:: console
    :emphasize-lines: 1, 4

    $ python main.py greet --cfg-path cfg.json
    Hello World!
    $ ls
    cfg.json
    cfg.yaml
    main.py
    $ cat cfg.json
    {
        "message": "Hello World!"
    }

.. note::

    By default, the ``PersistenceManager`` automatically adds the ``--cfg-path``
    flag through the :ref:`default <default_parser_hook>` ``parser_hook``. We'll
    explore non-default options :ref:`later <persistence_registration>`.

We now have two competing config files! Let's modify each one to distinguish them:

Let's update ``cfg.yaml`` to:

.. code-block:: yaml

    message: Hello YAML!

and ``cfg.json`` to:

.. code-block:: json

    {
        "message": "Hello JSON!"
    }

Now, if we run the program, we see that YAML is favored by default:

.. code-block:: console

    $ python main.py greet
    Hello YAML!

But, as before, we can **force** JSON to used instead:

.. code-block:: console

    $ python main.py greet --cfg-path cfg.json
    Hello JSON!

If we specify a file path without an extension, YAML will again be favored:

.. code-block:: console

    $ python main.py greet --cfg-path cfg
    Hello YAML!

Finally, if we *delete* the YAML file while *keeping* the JSON file, the
``PersistenceManager`` will **ignore the existing JSON file** (and ``cfg`` will be
serialized to a *new* YAML file instead) *unless* explicitly given a JSON file extension:

.. code-block:: console
    :emphasize-lines: 1, 6

    $ rm cfg.yaml
    $ python main.py greet --cfg-path cfg
    Hello World!
    $ ls
    cfg.json
    cfg.yaml
    main.py
    $ python main.py greet --cfg-path cfg.json
    Hello JSON!

.. admonition:: Summary:

    Because ``omegaconf`` only supports YAML, the default ``PersistenceManager``
    always *favors* YAML, while still *supporting* JSON. In the next section, we'll
    see how to reverse this.

.. _favoring_json_configs:

Favoring JSON
-------------

We can reverse the default preference of YAML over JSON by setting JSON as the
default file extension when instantiating a ``PersistenceManager``. Let's modify
the :ref:`previous example <yaml_over_json>` to achieve this:

.. code-block:: python
    :emphasize-lines: 1, 8

    from coma import Extension, PersistenceManager, command, wake
    from dataclasses import dataclass

    @dataclass
    class Config:
        message: str = "Hello World!"

    @command(persistence_manager=PersistenceManager(Extension.JSON))
    def greet(cfg: Config):
        print(cfg.message)

    if __name__ == "__main__":
        wake()


First, let's ensure that both YAML and JSON config files exist and are differentiated.

Update ``cfg.yaml`` (or create a file if none exists) to read:

.. code-block:: yaml

    message: Hello YAML!

And likewise for ``cfg.json``:

.. code-block:: json

    {
        "message": "Hello JSON!"
    }

Now, when running the program, we see that JSON is favored in all cases *unless* a
YAML file extension is explicitly provided:

.. code-block:: console

    $ python main.py greet
    Hello JSON!
    $ python main.py greet --cfg-path cfg
    Hello JSON!
    $ python main.py greet --cfg-path cfg.json
    Hello JSON!
    $ python main.py greet --cfg-path cfg.yaml
    Hello YAML!

.. _persistence_registration:

Registering a Config with the Persistence Manager
-------------------------------------------------

A ``PersistenceManager`` enables an individual config to be explicitly
:meth:`registered <coma.config.io.PersistenceManager.register>` with it. When no
registration is given, a sensible default is used. This default functionality
is what we've seen so far. Registering a specific config requires providing
new values to override one or more of these sensible defaults. Specifically:

* The file ``extension`` can optionally be set. If ``None``, the extension falls
  back to the ``PersistenceManager``'s default, which is :ref:`YAML <yaml_over_json>`
  by default, but can be set to :ref:`JSON <favoring_json_configs>`.
* ``argparse`` flag arguments can optionally be set. These are meant to provide a
  way for the user to set an explicit config file path to override the default.
  Specifically, provide any desired ``*names_or_flags`` and other keyword arguments to
  pass to `add_argument() <https://docs.python.org/3/library/argparse.html#the-add-argument-method>`_.
  For any of the following that are not provided, a sensible default is derived from
  the config's parameter name in the command signature (``cfg`` in the
  :ref:`previous example <yaml_over_json>`):

        ``*names_or_flags``:

            Defaults to ``--{config_name}-path`` (i.e., ``--cfg-path`` in the previous
            example). Any ``_`` in ``config_name`` are replaced with ``-``.

        ``type``:

            Defaults to ``str``.

        ``metavar``:

            Defaults to ``"FILE"``.

        ``dest``:

            Defaults to ``{config_name}_path``.

        ``default``:

            Defaults to ``{config_name}.{extension}``. If ``extension`` is ``None``, it
            falls back to the ``PersistenceManager``'s default.

        ``help``:

            Defaults to ``"{config_name} file path"``.

  Additional parameters beyond those listed above can also be provided via registration.
  These are just the parameters that have sensible defaults if omitted during registration.

These ``argparse`` flag arguments get added (via ``ArgumentParser.add_argument()``)
during the :ref:`default <default_parser_hook>` ``parser_hook``. Then, in the
:ref:`default <default_config_hook>` ``config_hook``, for each config, the
corresponding ``dest`` attribute of
:attr:`InvocationData.known_args <coma.hooks.base.InvocationData.known_args>`
is queried to retrieve the user-supplied file path (when the corresponding
``--{config_name}-path`` flag is explicitly provided as a command line argument).
If the corresponding flag omitted, we instead fall back to the corresponding
``default`` attribute of ``InvocationData.known_args``. For details, see
:meth:`~coma.config.io.PersistenceManager.get_file_path()`.

.. warning::

    :meth:`Registering <coma.config.io.PersistenceManager.register>` a particular
    config with a persistence manager does **not** guarantee/force that the config
    will be serialized, but rather only explicitly determines which parameters get
    passed to `add_argument() <https://docs.python.org/3/library/argparse.html#the-add-argument-method>`_.

    In particular, it is the responsibility of the :ref:`default <default_config_hook>`
    ``config_hook`` to perform the serialization. This default hook **always skips**
    :ref:`non-serializable <command_non_serializable>` configs *regardless* of whether
    they have been registered.

.. _non_default_config_path:

Let's expand the :ref:`previous example <yaml_over_json>` with a second config that
represents additional command data. Suppose we want this data to be serialized in
JSON format to a specific data directory under a specific (non-default) file name.
To do so, we register it with a JSON ``extension`` and a specific ``default`` that
points to the new data directory and file name. Since we don't register the existing
``cfg``, its management will fall back to the sensible defaults:

.. code-block:: python
    :emphasize-lines: 1, 9-11, 13, 15

    from coma import Extension, PersistenceManager, command, wake
    from dataclasses import dataclass

    @dataclass
    class Config:
        message: str = "Hello World!"

    @command(
        persistence_manager=PersistenceManager().register(
            "data", Extension.JSON, default="path/to/data/dir/greet.json"
        )
    )
    def greet(cfg: Config, data: dict):
        print(cfg.message)
        print("data is:", data)

    if __name__ == "__main__":
        wake()


Before running the program, let's create the data directory with ``mkdir``:

.. code-block:: console

    $ mkdir -p path/to/data/dir

and add a ``greet.json`` file to that directory with the following content:

.. code-block:: json

    {
        "some": "data",
        "for": "greet"
    }

Then, when running the program without specifying a file path for ``data``, we see that
``path/to/data/dir/greet.json`` gets loaded by default because of its registration:

.. code-block:: console

    $ python main.py greet
    Hello World!
    data is: {'some': 'data', 'for': 'greet'}

But, as in the :ref:`previous example <yaml_over_json>`, we can **still** force ``data``
to serialize elsewhere and in an alternative (in this case YAML) format if desired:

.. code-block:: console
    :emphasize-lines: 5

    $ python main.py greet --data-path data.yaml
    Hello World!
    data is: {}
    $ ls
    data.yaml
    main.py
    path/
    $ cat data.yaml
    {}
    $ cat path/to/data/dir/greet.json
    {
        "some": "data",
        "for": "greet"
    }
