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
a server.

.. code-block:: python
    :caption: main.py

    from dataclasses import dataclass
    from coma import command, wake

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

The above declarations provide a rich command line interface for invoking your
program. Assuming this code is in a file called :obj:`main.py`, you get:

1. A **command** that can be invoked by name (:obj:`push`) with command
   **parameters** (:obj:`remote` and :obj:`data`) *directly* available as
   command line arguments:

.. code-block:: console

    $ python main.py push \
        remote::server=127.0.0.1 remote::port=8000 \
        data::header=foo data::content=bar
    Pushing data: {'header': 'foo', 'content': 'bar'}
    To url: 127.0.0.1:8000

2. Config serialization based on its parameter name (:obj:`remote.yaml` in this case):

.. code-block:: console

    $ ls
    main.py
    remote.yaml
    $ cat remote.yaml
    server: localhost
    port: 9001

.. note::

    Notice that the saved config file :obj:`remote.yaml` contains the default
    config declaration, not any of the command line overrides. Updating the values
    in the saved file changes the defaults that are loaded on command invocation.

3. And lots more!

Including:

* Removing the boilerplate of
  `argparse <https://docs.python.org/3/library/argparse.html>`_
  while retaining full ``argparse`` interoperability and customizability for
  complex use cases.
* Providing a comprehensive set of
  `hooks <https://en.wikipedia.org/wiki/Hooking>`_
  to easily tweak, replace, or extend ``coma``'s
  `template <https://en.wikipedia.org/wiki/Template_method_pattern>`_-based
  design.

    .. note::

        ``coma`` has very few baked in assumptions. All of ``coma``'s default
        behavior results from pre-defined hooks. Nearly all behavior can be
        drastically changed with user-defined hooks. Factories enable tweaking
        the core default behavior without having to re-implement any hooks.
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
    :maxdepth: 2
    :caption: Tutorials and Examples

    tutorials/intro
    tutorials/core/index
    tutorials/hooks/index
    tutorials/examples/index

.. toctree::
    :maxdepth: 3
    :caption: Package Reference
    :titlesonly:

    references/index
