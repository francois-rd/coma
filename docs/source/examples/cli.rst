Command Line Config Overrides
=============================

.. _prefixingoverrides:

Prefixing Overrides
-------------------

Command line config overrides can sometimes clash. In this example, we have two
configs, both of which define the same :obj:`x` attribute:

.. code-block:: python
    :caption: main.py

    from dataclasses import dataclass

    import coma

    @dataclass
    class Config1:
        x: int

    @dataclass
    class Config2:
        x: int

    if __name__ == "__main__":
        coma.register("multiply", lambda c1, c2: print(c1.x * c2.x), Config1, Config2)
        coma.wake()

By default, ``coma`` enables the presence of :obj:`x` on the command line to
override *both* configs at once:

.. code-block:: console

    $ python main.py multiply x=3
    9

This lets :obj:`multiply` is essentially act as :obj:`square`. To prevent this,
we can override a specific config by *prefixing the override* with its identifier
using the prefix delimiter (``::``):

.. code-block:: console

    $ python main.py multiply config1::x=3 config2::x=4
    12

.. note::

    See :ref:`here <ontheflyhookredefinition>` for an alternative way to prevent
    these clashes.

.. warning::

    The default prefix delimiter was changed to ``::`` in version ``>=2.0.0`` from ``:``
    in version ``<2.0.0`` in order to prevent clashes with dictionary command line
    config overrides. See :ref:`here <objectoverride>` for an example of dictionary
    config overrides. See :func:`~coma.config.cli.override_factory` and
    :func:`~coma.hooks.post_config_hook.multi_cli_override_factory` for setting a
    custom prefix delimiter. In particular, setting the custom delimiter back to ``:``
    enables backwards compatibility with version ``<2.0.0`` assuming dictionary
    overrides are not required.

By default, ``coma`` also supports prefix abbreviations. A prefix can be abbreviated
as long as the abbreviation is unambiguous (i.e., matches only one config identifier):

.. code-block:: python
    :caption: main.py

    from dataclasses import dataclass

    import coma

    @dataclass
    class Config1:
        x: int

    @dataclass
    class Config2:
        x: int

    if __name__ == "__main__":
        coma.register("multiply", lambda c1, c2: print(c1.x * c2.x),
                      some_long_identifier=Config1, another_long_identifier=Config2)
        coma.wake()

This is enables convenient shorthands for command line overrides:

.. code-block:: console

    $ python main.py multiply some_long_identifier::x=3 another_long_identifier::x=4
    12
    $ python main.py multiply s::x=3 a::x=4
    12

.. _objectoverride:

Overriding Structured Objects
-----------------------------

Config attributes in ``coma`` can be structured objects (lists or dicts). Since ``coma``
uses ``omegaconf`` configs under the hood, the behavior of these structured configs
follows that of ``omegaconf`` (``>=2.0.0``). In particular, when specifying these
attributes on the command line, the command line data either overrides (for lists and
existing dict keys) or merges (for new dict keys) with the default values.

.. note::

    See `here <https://stackoverflow.com/questions/61315623/omegaconf-can-i-influence-how-lists-are-merged>`_
    for an answer directly from ``omegaconf``'s developer.

Consider the following example, where :obj:`l` has type :obj:`list` with default value
:obj:`[1, 2]` and :obj:`d` has type :obj:`dict` with default value
:obj:`{'a' : {'b': 3}}`.

.. code-block:: python
    :caption: main.py

    from dataclasses import dataclass, field

    from omegaconf import OmegaConf

    import coma

    @dataclass
    class Config:
        l: list = field(default_factory=lambda: [1, 2])
        d: dict = field(default_factory=lambda: {'a': {'b': 3}})

    if __name__ == "__main__":
        coma.register("struct", lambda c: print(OmegaConf.to_yaml(c)), Config)
        coma.wake()

Without command line overrides, the default values are maintained, as expected:

.. code-block:: console

    $ python main.py struct
    l:
    - 1
    - 2
    d:
      a:
        b: 3

When overriding a plain Python list (**not** a nested ``omegaconf`` :obj:`ListConfig`
object), the default list is entirely overridden. There is no mechanism to merge the
default with the command line list data. Specify the overriding list on the command line
as follows:

.. code-block:: console

    $ python main.py struct l='[3, 4, 5]'
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

    $ python main.py struct l='[2]'
    l:
    - 2
    d:
      a:
        b: 3
    $ python main.py struct l='[]'
    l: []
    d:
      a:
        b: 3

When overriding a plain Python dictionary (**not** a nested ``omegaconf``
:obj:`DictConfig` object), key-value pairs with new keys are added (merged with) the
existing default value, whereas the value of existing keys is overridden. In both cases,
the command line construction can use ``omegaconf``'s dot-list notation syntax or a
dictionary syntax.

Merge new key-value pair :obj:`{'c': 4}` using dot-list notation:

.. code-block:: console

    $ python main.py struct d.c=4
    l:
    - 1
    - 2
    d:
      a:
        b: 3
      c: 4

Merge new key-value pair :obj:`{'c': 4}` using dictionary syntax:

.. code-block:: console

    $ python main.py struct d='{c: 4}'
    l:
    - 1
    - 2
    d:
      a:
        b: 3
      c: 4

Override existing key-value pair to :obj:`{'a' : {'b': 4}}` using dot-list notation:

.. code-block:: console

    $ python main.py struct d.a.b=4
    l:
    - 1
    - 2
    d:
      a:
        b: 4

Override existing key-value pair to :obj:`{'a' : {'b': 4}}` using dictionary syntax:

.. code-block:: console

    $ python main.py struct d='{a: {b: 4}}'
    l:
    - 1
    - 2
    d:
      a:
        b: 4

Although the dictionary syntax may seem verbose at first, it can helpful for overriding
and/or merging multiple key-value pairs at once (especially as the size of the override
grows), which the dot-list notation does not directly support. Compare:

.. code-block:: console

    $ python main.py struct d='{a: {b: 4}, c: 5}'
    l:
    - 1
    - 2
    d:
      a:
        b: 4
      c: 5
    $ python main.py struct d.a.b=4 d.c=5
    l:
    - 1
    - 2
    d:
      a:
        b: 4
      c: 5

.. note::

    Deletion of dictionary entries is not currently supported. In the following,
    ``omegaconf`` simply merges the empty dictionary with the default dictionary (i.e.,
    the default is left unchanged):

    .. code-block:: console

        $ python main.py struct d='{}'
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
is solidifying. In this example, we name this superfluous config :obj:`extras`:

.. code-block:: python
    :caption: main.py

    from omegaconf import OmegaConf

    import coma

    def greet(e: dict):
        print("Hello World!")
        print("extra attributes:")
        print(OmegaConf.to_yaml(e))

    if __name__ == "__main__":
        coma.register("greet", greet, extras={})
        coma.wake()

This works because, as a plain :obj:`dict`, :obj:`extras` will accept any
*non-prefixed* arguments given on the command line:

.. code-block:: console

    $ python main.py greet
    Hello World!
    extra attributes:
    {}
    $ python main.py greet a='{b: {c: 1}, d: 2}' foo=3 bar.baz=4
    Hello World!
    extra attributes:
    a:
      b:
        c: 1
      d: 2
    foo: 3
    bar:
      baz: 4


As a more advanced use case, we may want to capture superfluous configs as a global
object to avoid having to modify each existing command's definition to accept an extra
config. In the example below, we redefine the :obj:`init_hook` using
:func:`~coma.hooks.init_hook.positional_factory`. This factory *skips* the given config
identifiers when instantiating the command. In this case, we skip the config with the
:obj:`"extras"` identifier. Compared to the example above, with this new hook, the
:obj:`greet` command no longer needs to accept 1 positional argument to accommodate
:obj:`extras`.

.. note::

    We also added a new :obj:`post_run_hook` conveniently defined using ``coma``'s
    :doc:`hook <../tutorials/hooks/index>` decorator. This hook simply prints out
    the attributes of the :obj:`extras` config after the command is executed.


.. code-block:: python
    :caption: main.py

    from omegaconf import OmegaConf

    import coma

    @coma.hooks.hook
    def post_run_hook(configs):
        print("extra attributes:")
        print(OmegaConf.to_yaml(configs["extras"]))

    if __name__ == "__main__":
        coma.initiate(
            extras={},
            init_hook=coma.hooks.init_hook.positional_factory("extras"),
            post_run_hook=post_run_hook,
        )
        coma.register("greet", lambda: print("Hello World!"))
        coma.wake()

This produces the same results as the above example, except that the extra config
attributes are printed as part of the global :obj:`post_run_hook` rather than the
:obj:`greet` command:

.. code-block:: console

    $ python main.py greet
    Hello World!
    extra attributes:
    {}
    $ python main.py greet a='{b: {c: 1}, d: 2}' foo=3 bar.baz=4
    Hello World!
    extra attributes:
    a:
      b:
        c: 1
      d: 2
    foo: 3
    bar:
      baz: 4
