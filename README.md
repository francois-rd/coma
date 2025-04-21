# Coma

Configurable **co**mmand **ma**nagement for humans.

[![PyPI version fury.io](https://badge.fury.io/py/coma.svg)](https://pypi.org/project/coma/)
[![PyPI license](https://img.shields.io/pypi/l/coma.svg)](https://pypi.org/project/coma/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/coma.svg)](https://pypi.org/project/coma/)
[![PyPI status](https://img.shields.io/pypi/status/coma.svg)](https://pypi.org/project/coma/)

[![Code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/francois-rd/coma/)
[![Documentation Status](https://readthedocs.org/projects/coma/badge/?version=latest)](http://coma.readthedocs.io/?badge=latest)

## Introduction

``coma`` provides a *modular* and *declarative* interface for defining **commands**,
associated **configuration** files, and **initialization** routines. Configs and
initializations can be command-specific or injected as reusable components in
multiple commands.

```python
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
```

## Key Features

The declarations in the above example provide a rich command line interface for
invoking your program. Assuming this code is in a file called ``main.py``, you get:

### Direct command parameter access

A **command** (``push``) that is invoked by name and command **parameters** (``remote``
and ``data``) that are *directly* available as command line arguments (also by name):

```console
$ python main.py push \
    remote::server=127.0.0.1 remote::port=8000 \
    data::header=foo data::content=bar
Pushing data: {'header': 'foo', 'content': 'bar'}
To url: 127.0.0.1:8000
```

### Config serialization

Configs that are automatically serialized to file based on their name (config ``remote``
is saved to ``remote.yaml`` in this case), enabling long-term persistence:

```console
$ ls
main.py
remote.yaml
$ cat remote.yaml
server: localhost
port: 9001
```

Both YAML and JSON are supported!

### And lots more!

Including:

* Removing the boilerplate of [argparse](https://docs.python.org/3/library/argparse.html)
  while retaining full ``argparse`` interoperability and customizability for
  complex use cases.
* Providing a comprehensive set of hooks to easily tweak, replace, or extend
  ``coma``'s template-based default behavior.
* Integrating with [omegaconf](https://github.com/omry/omegaconf/)'s extremely
  rich and powerful configuration management features.

## Installation

```console
pip install coma
```

## Getting Started

Excited? Jump straight into the extensive tutorials and examples of the
[official documentation](https://coma.readthedocs.io/).

## Changelog

From version 2.1.0:

* Significant design changes that break backwards compatibility:
    * Removed `coma.register()`. Everything happens via the `@command` decorator.
    * Folded all `coma.initiate()` functionality into `coma.wake()`.
    * Simplified all hook protocols and added new utilities for user-defined hooks.
* Greatly improved command signature inspection:
    * More robust parsing and invocation of command parameters.
    * New `inline` config parameters!

From version 2.0.1:

* Changed `coma.wake()` from `warnings`-based to `Exception`-based error handling.

From version 1.0.1:

* Add `@command` decorator
* Changed default prefix separator from `:` to `::` to avoid conflict with dictionary notation
* Minor improvements and bug fixes
