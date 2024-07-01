=======================================
viASP: An interactive ASP visualizer
=======================================

viASP generates interactive explanations of ASP programs and their stable models. A step-by-step break-down shows how the atoms of the stable models are derived.

viASP can be used via the command line or its Python API.

..
   comment viASP uses the clingo python API, a Flask server and a Dash frontend to generate the visualizations.

.. image:: ./img/header.png

Explore ASP programs and their answer sets with viASP:

* Follow the derivation of answer sets step-by-step
* Explain the derivation of individual atoms
* Inspect iterations of recursive rules
* Relax and visualize unsatisfiable programs
* Reorder rules
* Zoom in and out with Ctrl + mouse wheel

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   viasp/installation
   viasp/commandline
   viasp/usage
   viasp/api
   viasp/colorPalette
   viasp/contributing
