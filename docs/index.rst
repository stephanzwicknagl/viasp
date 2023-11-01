=======================================
viASP: An interactive ASP visualizer
=======================================

viASP generates interactive explanations of ASP programs and their stable models. A step-by-step break-down shows how the atoms of the stable models are derived.

To use viASP the programs have to executed them using the clingo python API.

..
   comment viASP uses the clingo python API, a Flask server and a Dash frontend to generate the visualizations.

.. image:: ./img/header.png

viASP allows you to explore the visualization in a variety of ways:

* Inspect iterations of recursive rules individually
* Explain the derivation of symbols with arrows
* Relax the constraints of unsatisfiable programs
* Toggle parts of the program
* Show the added symbols or all of them
* Inspect a single model
* Add #show statements on the fly
* Search models, signatures and rules.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   viasp/installation
   viasp/usage
   viasp/api
   viasp/contributing
