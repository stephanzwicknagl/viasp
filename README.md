# viASP

[![Build and Test](https://github.com/stephanzwicknagl/viasp/actions/workflows/build_and_test.yml/badge.svg?branch=main)](https://github.com/stephanzwicknagl/viasp/actions/workflows/build_and_test.yml)

**viASP visualizes an interactive explanation of your ASP program and its stable models** 

Try it out in Binder!
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/stephanzwicknagl/viasp/dash_update?filepath=examples%2Fintro_viasp.ipynb)



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

To use viASP you don't have to change your ASP programs at all. You only have to execute them using the clingo python
API.

# Installation

`pip install viasp`
will install all necessary dependencies.

## Usage

### Overview

viASP has two parts, its frontend [Dash](https://dash.plotly.com) component and the backend server. To get everything
running, do the following:

1. Start your dash app, a basic version can be found at [`examples/minimal_dash.py`](examples/minimal_dash.py). This will also automatically start the backend server.
2. Replace `clingo.Control` with `viasp.Control` in your python scripts and use `viasp.mark(model)` to select the models
   you want to show

### Quick start

If you don't have any scripts handy that use the python API of clingo, you can use our quickstart script.

Simply run [`examples/quickstart.py`](examples/quickstart.py).

It works very similar to the usual `clingo`, you can call it as `python quickstart.py encoding.lp` or
even `cat encoding | python quickstart.py`
If you want to filter the models you have to edit the script, however.

If you now run your ASP programs, you can inspect them using viASP at [http://127.0.0.1:8050/](http://127.0.0.1:8050/)
or what ever port you have set.

If you want to learn more about Dash, check out their [documentation](https://dash.plotly.com/layout).

## Limitations

viASP only works if you run your ASP programs using the python API, e.g.:

```python
from viasp import Control

program = """
1{rain; sprinkler}1.
wet :- rain.
wet :- sprinkler.
"""
ctl = Control(["0"])
ctl.add("base", [], program)
ctl.ground([("base", [])])
with ctl.solve(yield_=True) as handle:
    for model in handle:
        ctl.viasp.mark(model)
ctl.viasp.show()
```

# Contributing

## Installation

#### Requirements

- [Git](https://git-scm.com)
- [Node.JS](https://nodejs.org)
- [Python](https://www.python.org/)
- A suitable browser

#### Starting

1. Clone the repository using `git clone https://github.com/stephanzwicknagl/viasp.git --depth 1`
2. Create and activate a conda environment
4. Install pip `conda install pip`
6. Install viasp in editable mode `pip install -e viasp -e viasp/backend -e viasp/frontend`

## Developing the backend

1. Simply edit the code in the backend folder `viasp/backend/src`
3. Start viasp with your clingo program `python examples/App.py /your/program.lp`
## Developing the frontend

1. Move to frontend folder `cd viasp/frontend`
2. Run `npm i` to install all needed dependencies
3. Run `npx webpack` to pack the javascript
5. Start viasp with your clingo program `python examples/App.py 0 /your/program.lp`

Note: the JavaScript and css files are located in `/frontend/src/lib`. The frontend code needs to be packed before changes become visible to the webpage.


Code your heart out!
