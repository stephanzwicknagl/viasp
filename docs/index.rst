=======================================
viASP: An interactive ASP visualizer
=======================================

viASP generates interactive explanations of ASP programs and their stable models. A step-by-step break-down shows how the atoms of the stable models are derived.

viASP can be used via the command line or its Python API.

..
   comment viASP uses the clingo python API, a Flask server and a Dash frontend to generate the visualizations.

.. image:: ./img/header.png

viASP allows exploration of ASP encodings in a variety of ways:

* Follow the derivation of answer sets step-by-step
* Explain the derivation of individual symbols with arrows
* Inspect iterations of recursive rules
* Visualize unsatisfiable programs
* Move rules to follow a preferred order
* Zoom in and out of parts of the graph

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   viasp/installation
   viasp/commandline
   viasp/usage
   viasp/api
   viasp/colorPalette
   viasp/contributing
