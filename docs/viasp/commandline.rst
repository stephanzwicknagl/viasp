##########################
Command line functionality
##########################

viASP provides command line functionality to generate graphs from files. The graphs can then be inspected in the browser.


To use viASP from the command line, simply run

.. code-block:: bash

    $ viasp encoding.lp

You can now inspect the visualization at http://localhost:8050/. To stop the server, press ``CTRL+C``.


The command line usage is described below. Additionally, all options can be found by running

.. code-block:: bash

    $ viasp --help


****************
Loading Programs
****************

Loading from files
==================

Consider the file `hamiltonian.lp <https://github.com/potassco/viasp/blob/main/examples/hamiltonian.lp>`__

.. code-block:: prolog

    node(1..4). start(1).
    edge(1,2). edge(2,3). edge(2,4). edge(3,1).
    edge(3,4). edge(4,1). edge(4,3). 

    { hc(V,U) } :- edge(V,U).
    reached(V)  :- hc(S,V), start(S).
    reached(V)  :- reached(U), hc(U,V).
    :- node(V), not reached(V).
    :- hc(V,U), hc(V,W), U!=W.
    :- hc(U,V), hc(W,V), U!=W.


To load the program, pass the path to the file as an argument.

.. code-block:: bash

    $ viasp hamiltonian.lp


For programs split into multiple files, all of them can be loaded at once.

.. code-block:: bash

    $ viasp hamiltonian.lp model1.lp

The output prints the stable models of the program and information about the viasp server and frontend url

.. code-block:: bash
    
    Starting backend at http://localhost:5050
    Answer:    
    node(1) node(2) node(3) node(4) edge(1,2) edge(2,3) edge(2,4) edge(3,1) edge(3,4) edge(4,1) edge(4,3) hc(1,2) hc(2,3) hc(3,4) hc(4,1) start(1) reached(2) reached(3) reached(4) reached(1)
    SAT
    [INFO] (2023-12-01 12:38:44) Set models.
    [INFO] (2023-12-01 12:38:44) Reconstructing in progress.
    [INFO] (2023-12-01 12:38:44) Drawing in progress.
    Dash is running on http://localhost:8050/

    Press CTRL+C to quit


To define how many models should be included at most, use the ``--models`` or ``-n`` option. By default, all models are included.

.. code-block:: bash

    $ viasp hamiltonian.lp -n 1


Loading from stdin
==================

To load a program from stdin, use `-` as the file path.

.. code-block:: bash

    $ cat hamiltonian.lp | viasp -


************
Optimization
************

The viASP command line passes on any optimization settings to the clingo backend, so that the optimization can be performed as usual.

To specify the optimization mode, use the ``--opt-mode`` option. The optimization mode can be one of ``opt``, ``enum``, ``optN``, or ``ignore``.

.. code-block:: bash

    $ viasp encoding.lp --opt-mode=optN



*********
Clingraph
*********

viASP can include clingraph visualizations in the frontend. To do so, pass the path to a separte visualization program as an argument.

.. code-block:: bash

    $ viasp encoding.lp --viz-encoding viz_encoding.lp

To pass additional arguments to clingraph, use the ``--engine`` and ``--graphviz-type`` options.

.. code-block:: bash

    $ viasp encoding.lp --viz-encoding viz_encoding.lp --engine clingraph --graphviz-type dot


*******
Relaxer
*******

By default, viASP supports the visualization of unsatisfiable programs using the relaxer. viASP transforms the integrity constraints of unsatisfiable programs into weak constraints and visualizes the resulting program. The resulting graph can be used to inspect the reason for unsatisfiability.

By default, variables in the body of integrity constraints are collected in the heads of constraints. To turn off this behavior, use the ``--no-collect-variables`` option.

To specify the head name of the weak constraint, use the ``--head-name`` option. By default, the head name is ``unsat``, but a different name should be specified, if the program already contains the predicate.

.. code-block:: bash

    $ viasp encoding.lp --head-name _unsat


To turn off the relaxer, use the ``--no-relaxer`` or ``-r`` option.

*************
Other options
*************

To specify the port of the backend, use the ``--port`` or ``-p`` option.

To specify the port of the frontend, use the ``--frontend-port`` or ``-f`` option.

To specify the host of both frontend and backend, use the ``--host`` option.
