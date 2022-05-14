Config Serialization
====================

By default, ``coma`` favors YAML over JSON for its config serialization, since
`omegaconf <https://github.com/omry/omegaconf>`_ only supports YAML. However,
``coma`` does natively support JSON as well.

Default Behavior
----------------

To illustrate the default behavior, let's revisit an example from the
:doc:`introductory tutorial <../intro>`:

.. code-block:: python
    :caption: main.py

    from dataclasses import dataclass

    import coma

    @dataclass
    class Config:
        message: str = "Hello World!"

    if __name__ == "__main__":
        coma.register("greet", lambda cfg: print(cfg.message), Config)
        coma.wake()

Because :obj:`Config` has :obj:`type` name :obj:`config`, it will be serialized
to :obj:`config.yaml` by default:

.. code-block:: console

    $ python main.py greet
    Hello World!
    $ cat config.yaml
    message: Hello World!

We can force ``coma`` to serialize to JSON by specifying an explicit file path
for :obj:`Config`:

.. code-block:: console

    $ python main.py greet --config-path config.json
    Hello World!
    $ cat config.json
    {
        "message": "Hello World!"
    }

.. note::

    By default, ``coma`` automatically adds the :obj:`--config-path` flag
    through the default :obj:`parser_hook` of :func:`~coma.core.initiate.initiate`.
    Specifically, a flag of the form :obj:`--{config_id}-path` is added for
    each global and local config, where :obj:`{config_id}` is the corresponding
    config identifier.

Now we have two competing config files. Let's modify each one to distinguish them:

.. code-block:: yaml
    :emphasize-lines: 1
    :caption: config.yaml

    message: Hello YAML!

.. code-block:: json
    :emphasize-lines: 2
    :caption: config.json

    {
        "message": "Hello JSON!"
    }

Now, if we run the program, we see that YAML is favored:

.. code-block:: console

    $ python main.py greet
    Hello YAML!

But we can still force ``coma`` to use JSON instead:

.. code-block:: console

    $ python main.py greet --config-path config.json
    Hello JSON!

If we specify a file path without an extension, ``coma`` will again favor YAML:

.. code-block:: console

    $ python main.py greet --config-path config
    Hello YAML!

Finally, if we delete the YAML file while keeping the JSON file, ``coma`` will
*ignore the existing JSON file* (and create a new YAML file instead) unless
explicitly given a JSON file extension:

.. code-block:: console

    $ rm config.yaml
    $ python main.py greet --config-path config
    Hello World!
    $ python main.py greet --config-path config.json
    Hello JSON!

In summary, by default ``coma`` natively *supports* JSON, but YAML always
takes *precedence*.

Favoring JSON
-------------

We can reverse ``coma``'s default preference by setting JSON as the default file
extension through the :obj:`config_hook` of :func:`~coma.core.initiate.initiate`:

.. code-block:: python
    :emphasize-lines: 10-14
    :caption: main.py

    from dataclasses import dataclass

    import coma

    @dataclass
    class Config:
        message: str = "Hello World!"

    if __name__ == "__main__":
        coma.initiate(
            config_hook=coma.hooks.config_hook.multi_load_and_write_factory(
                default_ext=coma.config.io.Extension.JSON
            )
        )
        coma.register("greet", lambda cfg: print(cfg.message), Config)
        coma.wake()


First, let's ensure that both YAML and JSON config files exist and are differentiated:

.. code-block:: yaml
    :emphasize-lines: 1
    :caption: config.yaml

    message: Hello YAML!

.. code-block:: json
    :emphasize-lines: 2
    :caption: config.json

    {
        "message": "Hello JSON!"
    }

Now, when running the program, we see that JSON is favored in all cases, unless a
YAML file extension is explicitly provided:

.. code-block:: console

    $ python main.py greet
    Hello JSON!
    $ python main.py greet --config-path config
    Hello JSON!
    $ python main.py greet --config-path config.json
    Hello JSON!
    $ python main.py greet --config-path config.yaml
    Hello YAML!
