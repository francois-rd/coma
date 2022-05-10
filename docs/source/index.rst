Coma Documentation
==================

Configurable **co**\ mmand **ma**\ nagement for humans.

Introduction
------------

Commands (also known as sub-commands) are the ``commit`` and ``pull`` part of ``git commit`` and ``git pull`` (whereas ``git`` is the program). Commands can be seen as command-line meta-arguments: They drastically affect not only the behavior of the program, but also what additional command-line line arguments and flags are accepted.

``coma`` goes one step further. With it, commands determine which configuration files are loaded, enabling command-specific configs that don't affect the whole program.

Key Features
------------

``coma`` makes it easy to build configurable command-based programs in Python by:

* Removing the boilerplate of `argparse <https://docs.python.org/3/library/argparse.html>`_, while retaining full ``argparse`` interoperability and customizability for complex use cases.
* Providing a comprehensive set of `hooks <https://en.wikipedia.org/wiki/Hooking>`_ to easily tweak, replace, or add to ``coma``'s default behavior.
* Integrating with `omegaconf <https://github.com/omry/omegaconf>`_'s extremely rich and powerful configuration management features.

Installation
------------

.. code-block:: console

    pip install coma

Getting Started
---------------

Excited? Jump straight into the :doc:`tutorials/intro`.

Why Coma?
-------------

Why choose ``coma`` over another ``omegaconf``-based solution, like `hydra <https://hydra.cc>`_? ``hydra``, specifically, has the following limitations (all of which are features that ``coma`` supports!):

* **No commands.** Related functionality must be implemented as separate programs.
* **No command-line arguments or flags.** All program data must be provided through configurations.
* **No parallel/independent configs.** All configs must be hierarchical.

If these limitations aren't deal-breakers for you, then, by all means, use ``hydra`` (or any other framework). ``hydra``, in particular, certainly has a wonderfully rich feature set (including config groups, `which inspired its name <https://hydra.cc/docs/intro/>`_).

.. toctree::
    :caption: Tutorials

    tutorials/intro

.. toctree::
    :glob:
    :maxdepth: 3
    :caption: Package Reference
    :titlesonly:

    references/index
