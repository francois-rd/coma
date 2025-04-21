Coma
====

Configurable **co**\ mmand **ma**\ nagement for humans.

Introduction
------------

Commands (also known as sub-commands) are the ``commit`` and ``pull`` part of
``git commit`` and ``git pull`` (whereas ``git`` is the program).

``coma`` provides a *modular* and *declarative* interface for defining **commands**,
associated **configuration** files, and **initialization** routines. Configs and
initializations can be command-specific or injected as reusable components in
multiple commands.

Example
-------

Let's see ``coma`` in action with a simple mock command for pushing data to
a server:

.. code-block:: python

    from coma import command, wake
    from dataclasses import dataclass

    # Step 1: Declare one or more configurations.
    @dataclass
    class RemoteCfg:
        server: str = "localhost"
        port: int = 9001

    # Step 2: Declare one or more commands.
    @command
    def push(remote: RemoteCfg, **data):
        # Code for pushing data to remote. Mocked here as print statements.
        print(f"Pushing data: {data}")
        print(f"To url: {remote.server}:{remote.port}")

    # Step 3: Launch!
    if __name__ == "__main__":
        wake()


Key Features
------------

The declarations in the above example provide a rich command line interface for
invoking your program.

.. note::

    Throughout this documentation, we always assume the program code is in a
    file called ``main.py``, so that we can run it on the command line using
    ``python main.py <command-name>``.

Assuming this code is in a file called ``main.py``, you get:

Direct command parameter access
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The **command** (``push``) is invoked by name. Command **parameters** (``remote``
and ``data``) are *directly* available as command line arguments (also by name):

.. code-block:: console

    $ python main.py push \
        remote::server=127.0.0.1 remote::port=8000 \
        data::header=foo data::content=bar
    Pushing data: {'header': 'foo', 'content': 'bar'}
    To url: 127.0.0.1:8000

Config serialization
^^^^^^^^^^^^^^^^^^^^

Command parameters that represent configs are automatically serialized to file based
on their name (config ``remote`` is saved to ``remote.yaml`` in this case), enabling
long-term persistence:

.. code-block:: console

    $ ls
    main.py
    remote.yaml
    $ cat remote.yaml
    server: localhost
    port: 9001

Both YAML and JSON are supported. Updating ``remote.yaml`` changes the config
values that are loaded on command invocation.

And lots more!
^^^^^^^^^^^^^^

Including:

* Removing the boilerplate of
  `argparse <https://docs.python.org/3/library/argparse.html>`_
  while retaining full ``argparse`` interoperability and customizability for
  complex use cases.
* Providing a comprehensive set of hooks to easily tweak, replace, or extend
  ``coma``'s template-based default behavior.

  .. note::

      ``coma`` has very few baked in assumptions. **All** of ``coma``'s default
      behavior results from :ref:`pre-defined hooks <default_hooks>`. Nearly all
      behavior can be drastically changed with user-defined hooks. Factories enable
      tweaking the core default behavior without having to re-implement any hooks.
* Integrating with `omegaconf <https://github.com/omry/omegaconf>`_'s extremely
  rich and powerful configuration management features.


Installation
------------

.. code-block:: console

    pip install coma


Getting Started
---------------

Excited? Jump straight into the tutorials or learn by browsing the many usage examples.


.. toctree::
    :maxdepth: 1
    :caption: Tutorials

    tutorials/intro
    tutorials/command
    tutorials/wake
    tutorials/hooks

.. toctree::
    :maxdepth: 1
    :caption: Examples

    examples/parser
    examples/cli
    examples/serialization
    examples/preload
    examples/coma

.. toctree::
    :maxdepth: 2
    :caption: Package Reference
    :titlesonly:

    references/index
