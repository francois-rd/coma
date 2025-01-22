Command
=======

The :obj:`@command` decorator is a lightweight wrapper around
:func:`~coma.core.register.register`, which acts as a convenience for simple use cases.

The advantage of this decorator is to remove the boilerplate of
:func:`~coma.core.register.register`\ing a command when its registration is a one-to-one
mapping to the command signature. For example, consider the following multi-config
registration:

.. code-block:: python
    :emphasize-lines: 13, 20
    :caption: main.py

    from dataclasses import dataclass

    import coma

    @dataclass
    class Config1:
        ...

    @dataclass
    class Config2:
        ...

    def greet(cfg_1: Config1, cfg_2: Config2, cfg_3: dict):
        print("Hello World!")
        print(cfg_1)
        print(cfg_2)
        print(cfg_3)

    if __name__ == "__main__":
        coma.register("greet", greet, cfg_1=Config1, cfg_2=Config2, cfg_3={})
        coma.wake()

Notice that the function signature of :obj:`greet` is a one-to-one mapping to the
registration. Specifically, each parameter of the function signature is a config, and
the parameter name and type annotation of each config in the function signature matches
a config identifier and type pair in the registration. As such, we can use the
:obj:`@command` decorator to remove the boilerplate registration:

.. code-block:: python
    :emphasize-lines: 14, 22
    :caption: main.py

    from dataclasses import dataclass

    from coma import command
    import coma

    @dataclass
    class Config1:
        ...

    @dataclass
    class Config2:
        ...

    @command("greet")
    def greet(cfg_1: Config1, cfg_2: Config2, cfg_3: dict):
        print("Hello World!")
        print(cfg_1)
        print(cfg_2)
        print(cfg_3)

    if __name__ == "__main__":
        # Removed call to coma.register()
        coma.wake()

This decorator works in simple use cases. It does not work if the decorated object's
signature contains non-config parameters (which is a rare and advanced use case). It also
does not work with :func:`~coma.core.forget.forget` (a more common, if still slightly
advanced use case). For such advanced uses cases, an explicit call to
:func:`~coma.core.register.register` must be made instead.

.. note::

    When the command is defined as a class instead of a function, it is the signature
    of the class's __init__() method that must match the registration format.

Just like :func:`~coma.core.register.register`, the :obj:`@command` decorator accepts
local hooks and parser keywords arguments. These are passed directly to
:func:`~coma.core.register.register` without modification or processing:

.. code-block:: python
    :emphasize-lines: 6-19, 24
    :caption: main.py

    from dataclasses import dataclass

    from coma import command
    import coma

    @command(
        "greet",
        parser_hook=...,
        pre_config_hook=...,
        config_hook=...,
        post_config_hook=...,
        pre_init_hook=...,
        init_hook=...,
        post_init_hook=...,
        pre_run_hook=...,
        run_hook=...,
        post_run_hook=...,
        parser_kwargs=...,
    )
    def greet():
        print("Hello World!")

    if __name__ == "__main__":
        # Removed call to coma.register()
        coma.wake()

.. warning::

    Be aware that, under the hood, the :obj:`@command` decorator *delays* the call to
    :func:`~coma.core.register.register` until *after* the call to
    :func:`~coma.core.initiate.initiate`. This should not cause issues, but may lead to
    unintended side effects when mucking around with Python's ``inspect`` module.
