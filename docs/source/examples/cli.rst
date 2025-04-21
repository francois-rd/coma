Command Line Config Overrides
=============================

For each config in a command declaration, whether :ref:`standard <command_config_vs_regular>`,
:ref:`inline <command_inline_configs>`, or :ref:`supplemental <supplemental_configs>`,
an attempt is made to override its config attribute values with any command line
arguments that fit. We employ a variant of ``omegaconf``'s
`dot-list notation <https://omegaconf.readthedocs.io/en/2.1_branch/usage.html#from-a-dot-list>`_
syntax augmented with config :ref:`prefixes <prefixing_overrides>`.

Basic Overview
--------------

For the most part, we defer to the ``omegaconf`` (``>=2.0.0``)
`merge() <https://omegaconf.readthedocs.io/en/2.1_branch/usage.html#merging-configurations>`_
function for overriding config attributes. ``omegaconf`` uses plain Python objects to
back its configs. The supported types are ``list``, ``dict``, or any ``dataclass``
type. ``dataclass``-backed configs create so-called
`structured <https://omegaconf.readthedocs.io/en/2.1_branch/usage.html#from-structured-config>`_
configs. ``omegaconf`` rigorously type validates these configs at runtime based
on the underlying ``dataclass`` declaration. Besides this
:ref:`runtime validation <structured_configs>` aspect, structured configs behave
identically to ``dict``-like configs in terms of dot-list notation syntax.

For ``dict``-like command line overrides, ``omegaconf`` uses ``=`` as its key-value
separator in dot-list notation. This is built into ``omegaconf`` and we can't modify
it. ``omegaconf`` splits key-value strings on the first ``=`` (if any). Subsequent
occurrences of ``=`` are considered part of the value. If an override string does
not contain any ``=``, it is considered a ``list``-like override instead.

Let's examine each backing type in turn.

``list``-like Configs
^^^^^^^^^^^^^^^^^^^^^

``list``-like command line overrides are **appended** to all ``list``-list configs.
Consider this simple example:

.. code-block:: python

    from coma import command, wake

    @command
    def cmd(cfg: list):
        print(cfg)

    if __name__ == "__main__":
        wake()

Let's create a ``cfg.yaml`` file to see ``list``-like overrides in action:

.. code-block:: console

    $ echo '[a]' > cfg.yaml

The :ref:`declarative hierarchy <config_declaration_hierarchy>` for configs means
that ``cfg`` will first be loaded from ``cfg.yaml`` to have value ``['a']``. Then,
of the following command line arguments, those that are ``list``-like will be
appended to ``cfg``, resulting in:

.. code-block:: console

    $ python main.py cmd dict=like b c
    ['a', 'b', 'c']

Notice that ``dict=like`` does not get appended to ``cfg`` because it is a
``dict``-like command line override instead of a ``list``-like override.

``*args`` as Configs
""""""""""""""""""""

Variadic positional parameters (``*args``) are treated as
:ref:`non-serializable <command_non_serializable>` ``list``-like configs by default
(though this can be :ref:`toggled off <variadic_configs>`). They behave exactly like
any other ``list``-like config in terms of command line dot-list syntax. Then, once
the command is invoked, they behave exactly like Python variadic positional parameters:

.. code-block:: python

    from coma import command, wake

    @command
    def cmd(list_cfg: list, *args):
        print(list_cfg)
        print(args)

    if __name__ == "__main__":
        wake()

.. code-block:: console

    $ python main.py cmd a b c
    ['a', 'b', 'c']
    ('a', 'b', 'c')

Notice that both ``list``-like configs here accepted **all** ``list``-like overrides.
To choose which config receives which argument, :ref:`prefix <prefixing_overrides>`
them:

.. code-block:: console

    $ python main.py cmd list_cfg::a args::b args::c
    ['a']
    ('b', 'c')

``dict``-like Configs
^^^^^^^^^^^^^^^^^^^^^

``dict``-like configs can have arbitrarily nested structure, which is referenced
via ``omegaconf``'s dot-list notation. ``dict``-like configs accept **all**
``dict``-like command line overrides (consisting of key-value pairs), where the
key is a config attribute path in dot-list notation and the value is arbitrary.
Changing the config's structure is always allowed. If the key path already exists
in the config's structure, the new value **replaces** the existing one. If the key
path represents a new attribute, that new path is **merged** into the existing
config structure and given the new value. For example:

.. code-block:: python

    from coma import command, wake

    @command
    def cmd(cfg: dict):
        print(cfg)

    if __name__ == "__main__":
        wake()

Let's create a ``cfg.yaml`` file to see ``dict``-like overrides in action:

.. code-block:: console

    $ printf "foo:\n  bar: baz" > cfg.yaml

The :ref:`declarative hierarchy <config_declaration_hierarchy>` for configs means
that ``cfg`` will first be loaded from ``cfg.yaml`` to have value
``{'foo': {'bar': 'baz'}}``. Then, of the following command line arguments, those
that are ``dict``-like will replace or be merged into ``cfg``, resulting in:

.. code-block:: console

    $ python main.py cmd fizz=buzz list like
    {'foo': {'bar': 'baz'}, 'fizz': 'buzz'}
    $ python main.py cmd foo.bar=replace list like
    {'foo': {'bar': 'replace'}}
    $ python main.py cmd foo.new=merge list like
    {'foo': {'bar': 'baz', 'new': 'merge'}}

Notice that ``list`` and ``like`` never interact with ``cfg`` because they are
``list``-like command line overrides instead of a ``dict``-like overrides.

.. _kwargs_as_configs:

``**kwargs`` as Configs
"""""""""""""""""""""""

Variadic keyword parameters (``**kwargs``) are treated as
:ref:`non-serializable <command_non_serializable>` ``dict``-like configs by default
(though this can be :ref:`toggled off <variadic_configs>`). They behave exactly like
any other ``dict``-like config in terms of command line dot-list syntax. Then, once
the command is invoked, they behave exactly like Python variadic keyword parameters:

.. code-block:: python

    from coma import command, wake

    @command
    def cmd(dict_cfg: dict, **kwargs):
        print(dict_cfg)
        print(kwargs)

    if __name__ == "__main__":
        wake()

.. code-block:: console

    $ python main.py cmd a=b c=d
    {'a': 'b', 'c': 'd'}
    {'a': 'b', 'c': 'd'}

Notice that both ``dict``-like configs here accepted **all** ``dict``-like overrides.
To choose which config receives which argument, :ref:`prefix <prefixing_overrides>`
them:

.. code-block:: console

    $ python main.py cmd dict_cfg::a=b kwargs::c=d
    {'a': 'b'}
    {'c': 'd'}

Variadic keyword parameters have an additional constraint required by Python's syntax:
No key in ``**kwargs`` can match the name of a command parameter. To illustrate
the difference, let's first see how ``dict_cfg`` can easily accept a self-referential
key called ``"dict_cfg"``:

.. code-block:: console

    $ python main.py cmd dict_cfg::dict_cfg=OK
    {'dict_cfg': 'OK'}
    {}

But ``**kwargs`` cannot contain a key called ``"dict_cfg"`` because ``dict_cfg``
is already the name of a parameter to the ``cmd`` function:

.. code-block:: console

    $ python main.py cmd kwargs::dict_cfg=OK
    Traceback (most recent call last):
    ...
    ValueError: Named parameter is defined more than once: dict_cfg

.. note::

    Raising this ``ValueError`` is the default behavior and is the safest option. If
    your use case requires an alternative behavior (for example, forcibly overriding
    the value of ``dict_cfg`` with the contents of ``kwargs.dict_cfg``), other
    :class:`override policies <coma.config.cli.OverridePolicy>` exist. These can be
    set by :doc:`redefining <../tutorials/hooks>` the :ref:`default <default_init_hook>`
    ``init_hook``. *Be cautious.*

.. _structured_configs:

Structured Configs
^^^^^^^^^^^^^^^^^^

Structured configs behave exactly as ``dict``-like configs, except in one key aspect:
Attempting to alter their structure (e.g., by adding a new attribute) or attempting
to assign an invalid value to an existing attribute (e.g., type-mismatched) raises
an ``omegaconf`` :obj:`ValidationError`. Instead of crashing the program, ``coma``
simply **ignores** non-matching command line overrides for structured configs. For
example, if our config only has an ``x`` attribute:

.. code-block:: python

    from coma import command, wake
    from dataclasses import dataclass

    @dataclass
    class Config:
        x: int = 0

    @command
    def cmd(cfg: Config):
        print(cfg.x)

    if __name__ == "__main__":
        wake()

then, having ``x`` as a command line argument does override that attribute, whereas
any other command line argument, such as ``y``, is ignored:

.. code-block:: console

    $ python main.py cmd x=1 y=2
    1

.. _prefixing_overrides:

Prefixing Overrides
-------------------

Command line overrides can be shared between configs, which can be helpful in
certain instances. In the example below, we have two configs, both of which define
the same ``x`` attribute:

.. code-block:: python

    from coma import command, wake
    from dataclasses import dataclass

    @dataclass
    class Config1:
        x: int = 1

    @dataclass
    class Config2:
        x: int = 1

    @command
    def multiply(first: Config1, second: Config2):
        print(first.x * second.x)

    if __name__ == "__main__":
        wake()

By default, ``coma`` enables ``x`` as a command line argument to override *both*
configs at once:

.. code-block:: console

    $ python main.py multiply x=3
    9

This causes ``multiply`` to essentially act as ``square``. To prevent this, we can
target a specific config by *prefixing* the override's standard ``omegaconf`` dot-list
notation with the config's parameter name using the prefix delimiter (``::``):

.. code-block:: console

    $ python main.py multiply first::x=3 second::x=4
    12

By default, ``coma`` also supports prefix abbreviations. A prefix can be abbreviated
as long as the abbreviation is unambiguous (i.e., matches exactly one config name).
This enables convenient shorthands for command line overrides:

.. code-block:: console

    $ python main.py multiply f::x=3 s::x=4
    12

.. _inline_overrides:

Overriding Inline Configs
-------------------------

All :ref:`inline <command_inline_configs>` configs are aggregated into a special
:ref:`non-serializable <command_non_serializable>` :attr:`~coma.config.cli.ParamData.inline_config`
that is backed by a programmatically-created ``dataclass``. This provides all the
rigorous runtime type validation of a standard :ref:`structured <structured_configs>`
config without requiring a user-defined ``dataclass`` to be created just for these
one-off fields. By default, this implicit config uses ``"inline"`` as its
:attr:`name <coma.config.cli.ParamData.inline_identifier>`. To illustrate,
consider that the following two commands exhibit equivalent behavior:

.. code-block:: python

    from coma import SignatureInspector, command, wake, config_hook
    from dataclasses import dataclass

    @command(signature_inspector=SignatureInspector(inline=["x", "y"]))
    def proper_inline(x: int = 0, y: str = "foo"):
        print(x, y)

    @dataclass
    class MockInline:
        x: int = 0
        y: str = "foo"

    @command(
        config_hook=config_hook.default_factory(skip_write=["inline"]),
        signature_inspector=SignatureInspector(inline_identifier="unused"),
    )
    def mock_inline(inline: MockInline):
        print(inline.x, inline.y)

    if __name__ == "__main__":
        wake()

``mock_inline`` calls its config parameter ``inline``, which clashes with the
reserved name for the default inline config. So, we rename its identifier to
``"unused"``, since we won't be using it. The mocked ``inline`` config is a
regular config and so would get serialized by default. We disable that, rendering
it :ref:`non-serializable <command_non_serializable>`, by adding it to ``skip_write``
in a :ref:`redefined <default_config_hook>` ``config_hook``.

``mock_inline`` now behaves identically to ``proper_inline``:

.. code-block:: console

    $ python main.py proper_inline x=42 y=bar
    42 bar
    $ python main.py mock_inline x=42 y=bar
    42 bar

.. _object_overrides:

Overriding Nested Objects
-------------------------

Config attributes in ``coma`` can be deeply nested objects. Since ``coma`` delegates
to ``omegaconf`` for command line config overrides, the behavior of these overrides
follows that of ``omegaconf`` (``>=2.0.0``). In particular, command line arguments:

* replace ``list`` attributes with the command line values
* replace existing keys of ``dict`` attributes with the command line values
* merge new ``dict`` attribute key-value pairs into the existing dictionary

.. note::

    See `here <https://stackoverflow.com/questions/61315623/omegaconf-can-i-influence-how-lists-are-merged>`_
    for an answer directly from ``omegaconf``'s developer on why ``list`` attributes
    can only replace and not merge.

Consider the following example, where ``l`` has type ``list`` with default value
``[1, 2]`` and ``d`` has type ``dict`` with default value ``{'a' : {'b': 3}}``.

.. code-block:: python

    from coma import command, wake
    from dataclasses import dataclass, field
    from omegaconf import OmegaConf

    @dataclass
    class Config:
        l: list = field(default_factory=lambda: [1, 2])
        d: dict = field(default_factory=lambda: {'a': {'b': 3}})

    @command
    def nested(cfg: Config):
        print(OmegaConf.to_yaml(cfg))

    if __name__ == "__main__":
        wake()

Without command line overrides, the default values are maintained, as expected:

.. code-block:: console

    $ python main.py nested
    l:
    - 1
    - 2
    d:
      a:
        b: 3

Specifying ``l`` as a command line argument entirely replaces that config attribute:

.. code-block:: console

    $ python main.py nested l='[3, 4, 5]'
    l:
    - 3
    - 4
    - 5
    d:
      a:
        b: 3

To delete existing list entries, omit them from the command line, while continuing to
include existing list entries that ought to be kept:

.. code-block:: console

    $ python main.py nested l='[2]'  # Deletes 1 from the list.
    l:
    - 2
    d:
      a:
        b: 3
    $ python main.py nested l='[]'  # Deletes [1, 2] from the list.
    l: []
    d:
      a:
        b: 3

For ``d``, specifying existing keys replaces the value, whereas new keys are merged.
Typically, ``omegaconf``'s standard dot-list notation is used, but a dictionary syntax
is also supported:

1. Merge the new key-value pair :obj:`{'c': 4}` using dot-list notation:

   .. code-block:: console

       $ python main.py nested d.c=4
       l:
       - 1
       - 2
       d:
         a:
           b: 3
         c: 4

2. Merge the new key-value pair :obj:`{'c': 4}` using dictionary syntax:

   .. code-block:: console

       $ python main.py nested d='{c: 4}'
       l:
       - 1
       - 2
       d:
         a:
           b: 3
         c: 4

3. Replace an existing key-value pair with :obj:`{'a' : {'b': 4}}` using dot-list notation:

   .. code-block:: console

       $ python main.py nested d.a.b=4
       l:
       - 1
       - 2
       d:
         a:
           b: 4

4. Replace an existing key-value pair with :obj:`{'a' : {'b': 4}}` using dictionary syntax:

   .. code-block:: console

       $ python main.py nested d='{a: {b: 4}}'
       l:
       - 1
       - 2
       d:
         a:
           b: 4

Although the dictionary syntax may seem more verbose than the dot-list notation at
first, it can helpful for overriding and/or merging multiple key-value pairs at once
(especially as the size of the override grows), which is a feature that the dot-list
notation does not directly support:

.. code-block:: console

    $ python main.py nested d='{a: {b: 4}, c: 5}'
    l:
    - 1
    - 2
    d:
      a:
        b: 4
      c: 5
    $ python main.py nested d.a.b=4 d.c=5
    l:
    - 1
    - 2
    d:
      a:
        b: 4
      c: 5

.. note::

    Unlike with lists, deletion of dictionary entries is not supported by ``omegaconf``.
    In the following example, ``omegaconf`` simply merges the empty command line
    dictionary with the default dictionary, resulting in a new dictionary that is
    equivalent to the default one:

    .. code-block:: console

        $ python main.py nested d='{}'
        l:
        - 1
        - 2
        d:
          a:
            b: 3

Capturing Superfluous Overrides
-------------------------------

For rapid prototyping, it is often beneficial to capture superfluous command line
overrides. These can then be transferred to a proper config object once the codebase
is solidifying. Variadic keyword :ref:`config <kwargs_as_configs>` parameters
(``**kwargs``) are ideal for this:

.. code-block:: python

    from coma import command, wake
    from omegaconf import OmegaConf

    @command
    def greet(**kwargs):
        print("Hello World!")
        print("extra command line arguments:")
        print(OmegaConf.to_yaml(kwargs))

    if __name__ == "__main__":
        wake()

This works because ``**kwargs`` are a :ref:`non-serializable <command_non_serializable>`
``dict``-like config by :ref:`default <kwargs_as_configs>` that accept any
``dict``-like command line arguments:

.. code-block:: console

    $ python main.py greet
    Hello World!
    extra command line arguments:
    {}
    $ python main.py greet a='{b: {c: 1}, d: 2}' foo=3 bar.baz=4
    Hello World!
    extra command line arguments:
    a:
      b:
        c: 1
      d: 2
    foo: 3
    bar:
      baz: 4
