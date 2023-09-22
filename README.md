# viASP

[![Build and Test](https://github.com/stephanzwicknagl/viasp/actions/workflows/build_and_test.yml/badge.svg?branch=main)](https://github.com/stephanzwicknagl/viasp/actions/workflows/build_and_test.yml)

**viASP visualizes an interactive explanation of your ASP program and its stable models** 

Try it out in Binder!
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/stephanzwicknagl/viasp/main?filepath=examples%2FIntroduction%20to%20viASP.ipynb)

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

1. Clone the repository using `git clone https://github.com/stephanzwicknagl/viasp.git`
2. Install viasp in editable mode `pip install -q viasp viasp/backend viasp/frontend`


# Usage

## Quickstart

viASP has two parts, its frontend [Dash](https://dash.plotly.com) component and the backend server. Both can be started and intialized from a single python script. Simply run [`examples/quickstart.py`](examples/quickstart.py) with your encoding

   $ python quickstart.py encoding.lp

You can now inspect them using viASP at [http://127.0.0.1:8050/](http://127.0.0.1:8050/).

## API

If you have an encoding and stable models on hand without wanting to solve them again, you might want to use the viASP API directly. Adapt and run [`examples/quickstartAPI.py`](examples/quickstartAPI.py) with your encoding and stable models.

A full documentation of the API can be found [below](#api-reference).

## Adapting your scripts

If you want to adapt your scripts using the clingo python API, you can chose from interjecting API calls directly or using the Control proxy.

1. Initialize the viASP server using `app = startup.run()`
2. a.) Call the API to load the program and mark models, or 
   b.) Replace `clingo.Control` with `viasp.Control` and use `ctl.viasp.mark(model)` to select the models
3. Append `viasp.show()` and `app.run()` to the end of your script

# API Reference

| Name                            | Description and Parameters                                                                                                  |
|---------------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| load\_program\_file             | Load a (non-ground) program file into the viasp backend                                                                     |
|                                 | `str` *or* `List[str]`: path or list of paths to the program file                                               |
| load\_program\_string       | Load a (non-ground) program into the viasp backend                                                                          |
|                                 | `str`: the program to load                                                                                                |
| add\_program\_file          | Add a (non-ground) program file to the viasp backend                                                                        |
|                                 | `str`: name, `Sequence[str]`: parameters, `str`: path                                                                 |
|                                 | *or*                                                                                                                 |
|                                 | `str`: path                                                                                                               |
| add\_program\_string        | Add a (non-ground) program to the viasp backend                                                                             |
|                                 | `str`: name, `Sequence[str]`: parameters, `str`: program                                                              |
|                                 | *or*                                                                                                                 |
|                                 | `str`: program                                                                                                               |
|  mark\_from\_clingo\_model   | Mark a program from a clingo model                                                                                          |
|                                 | `clingo.solving.Model`: the model to mark                                                                                 |
| mark\_from\_string          | Parse a string of ASP facts and mark them as a model.                                                                       |
|                                 | `str`: The facts of the model to mark.                                                                                    |
| mark\_from\_file            | Parse a file containing a string of ASP facts and mark them as a model.                                                     |
|                                 | `str` *or* `List[str]` The path or list of paths to the file containing the facts of the model to mark.          |
| unmark\_from\_clingo\_model | Unmark a program from a clingo model                                                                                        |
|                                 | `clingo.solving.Model`: the model to unmark                                                                               |
| unmark\_from\_string   | Parse a string of ASP facts and unmark the corresponding model.                                                             |
|                                 | `str`: The facts of the model to unmark.                                                                                  |
| unmark\_from\_file       | Parse a file containing a string of ASP facts and unmark the corresponding model.                                           |
|                                 | `str` *or* `List[str]`: The path or list of paths to the file containing the facts of the model to unmark. |
| clear                      | Clear all marked models.                                                                                                    |
| show                        | Propagate the marked models to the backend and generate the graph.                                                          |
| get\_relaxed\_program       | Relax constraints in the marked models. Returns the relaxed program as a string.                                            |
|                                 | `str`: name of the head literal, `bool`: collect variables from body                                                      |
| relax\_constraints          | Relax constraints in the marked models. Returns a new viASP control object with the relaxed program loaded and all stable models marked. |
|                                 | `str`: name of the head literal, `bool`: collect variables from body |
| clingraph                   | Generate a clingraph from the marked models and the visualization encoding.                                                 |
|                                 | `str`: The path to the visualization encoding, `str`: The visualization engine. `str`: the graph type                    |
| register\_transformer       | Register a transformer to the backend. The backend transforms the program in the backend before further processing is made. |
|                                 | `clingo.ast.Transformer`: transformer, `str`: imports used by the transformer, `str`: path to the transformer            |

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
3. Install pip `conda install pip`
4. Install viasp in editable mode `pip install -e viasp -e viasp/backend -e viasp/frontend`

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
