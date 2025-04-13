Coma
====

Configurable **co**\ mmand **ma**\ nagement for humans.

Introduction
------------

Commands (also known as sub-commands) are the ``commit`` and ``pull`` part of
``git commit`` and ``git pull`` (whereas ``git`` is the program).

With ``coma``, commands are each associated with modular configuration files and
initialization routines. This not only enables command-specific configs and
initializations that don't affect the whole program, but also facilitates sharing
common configs and initialization components between all commands with simple
declarative statements.

Example
^^^^^^^

Let's see how ``coma`` works with a simple mock example of pushing and pulling
data to and from a server.

Step 1: Declare configurations
""""""""""""""""""""""""""""""

Use plain ``list`` or ``dict`` for maximally-flexible configs, or ``dataclasses``
for structured configs that are rigorously type validated at runtime.

.. code-block:: python
    :caption: main.py

    from dataclasses import dataclass

    @dataclass
    class RemoteCfg:
        server: str = "localhost"
        port: int = 9001

    # Other config declarations as needed ...


Step 2: Declare commands
""""""""""""""""""""""""

Both functions and classes with a no-argument :obj:`run()` method work.

.. code-block:: python
    :caption: main.py

    from coma import command

    @command
    def push(remote: RemoteCfg, **data):
        print(f"Pushing data {data} to remote: {remote.server}:{remote.port}")

    @command
    class Pull:
        def __init__(self, remote: RemoteCfg):
            self.remote = remote

        def run(self):
            print(f"Pulling from remote: {self.remote.server}:{self.remote.port}")

Step 3: Launch.
"""""""""""""""

.. code-block:: python
    :caption: main.py

    from coma import wake

    if __name__ == "__main__":
        wake()


Step 4: Invoke.
"""""""""""""""

The above declarations provide a rich command line interface for invoking your
program. Assuming all this code is in a file called :obj:`main.py`, you get:

1. Two commands that can be invoked by name (:obj:`push` and :obj:`pull`)
   with command arguments for each directly available as command line arguments:

.. code-block:: console

    $ python main.py push \
        remote::server=127.0.0.1 remote::port=8000 \
        data::header=foo data::content=bar
    Pushing data {'header': 'foo', 'content': 'bar'} to remote: 127.0.0.1:8000

2. Config serialization:

.. code-block:: console

    $ ls
    main.py
    remote.yaml
    $ cat remote.yaml
    server: localhost
    port: 9001


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

Excited? Jump straight into the short introductory tutorial or learn by
browsing the many usage examples.


.. toctree::
    :maxdepth: 2
    :caption: Tutorials

    tutorials/intro
    tutorials/core/index
    tutorials/hooks/index
    tutorials/examples/index

.. toctree::
    :maxdepth: 3
    :caption: Package Reference
    :titlesonly:

    references/index
