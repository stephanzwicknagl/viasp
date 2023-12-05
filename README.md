# viASP

[![Build and Test](https://github.com/potassco/viasp/actions/workflows/build_and_test.yml/badge.svg?branch=main)](https://github.com/potassco/viasp/actions/workflows/build_and_test.yml) [![Documentation Status](https://readthedocs.org/projects/viasp/badge/?version=latest)](https://viasp.readthedocs.io/en/latest/?badge=latest)

## viASP generates an interactive visualization of your ASP program and its stable models

Try it out in Binder!
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/potassco/viasp/main?filepath=examples%2FIntroduction%20to%20viASP.ipynb)

![Example visualization](docs/img/header.png)

viASP allows you to explore the visualization in a variety of ways:

* Inspect iterations of recursive rules individually
* Explain the derivation of symbols with arrows
* Relax the constraints of unsatisfiable programs
* Toggle parts of the program
* Show the added symbols or all of them
* Inspect a single model
* Add `#show` statements on the fly
* Search models, signatures and rules.

## Installation

viASP is available on [PyPI](https://pypi.org/project/viasp/). You can install it with pip:

```bash
pip install viasp
```

## Usage

To start a visualization from the command line, run:

```bash
viasp path/to/encoding.lp
```

Check out the [documentation](https://viasp.readthedocs.io/en/latest/) to see more on how to use viASP.

## Examples

An introduction to viASP's features is given in the [notebook](https://mybinder.org/v2/gh/stephanzwicknagl/viasp/main?filepath=examples%2FIntroduction%20to%20viASP.ipynb). The [examples folder](https://github.com/stephanzwicknagl/viasp/tree/main/examples) shows a variety of scripts that run viASP.

## Contributing

See the [documentation page](https://viasp.readthedocs.io/en/latest/viasp/contributing.html#contributing) to see how to contribute.
