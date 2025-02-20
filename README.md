# Coma

Configurable **co**mmand **ma**nagement for humans.

[![PyPI version fury.io](https://badge.fury.io/py/coma.svg)](https://pypi.org/project/coma/)
[![PyPI license](https://img.shields.io/pypi/l/coma.svg)](https://pypi.org/project/coma/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/coma.svg)](https://pypi.org/project/coma/)
[![PyPI status](https://img.shields.io/pypi/status/coma.svg)](https://pypi.org/project/coma/)

[![Code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/francois-rd/coma/)
[![Documentation Status](https://readthedocs.org/projects/coma/badge/?version=latest)](http://coma.readthedocs.io/?badge=latest)

## Key Features

``coma`` makes it easy to build configurable command-based programs in Python by:

* Removing the boilerplate of [argparse](https://docs.python.org/3/library/argparse.html), while retaining full ``argparse`` interoperability and customizability for complex use cases.
* Providing a comprehensive set of [hooks](https://en.wikipedia.org/wiki/Hooking) to easily tweak, replace, or extend ``coma``'s default behavior.
* Integrating with [omegaconf](https://github.com/omry/omegaconf/) 's extremely rich and powerful configuration management features.

## Installation

```console
pip install coma
```

## Getting Started

The [documentation](https://coma.readthedocs.io/) on ReadTheDocs includes a short
**introductory tutorial** and much more! 

## Changelog

From version 2.0.1:
* Changed `coma.wake()` from `warnings`-based to `Exception`-based error handling.  

From version 1.0.1:
* Add `@command` decorator
* Changed default prefix separator from `:` to `::` to avoid conflict with dictionary notation
* Minor improvements and bug fixes