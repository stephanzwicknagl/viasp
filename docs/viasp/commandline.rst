##########################
Command line functionality
##########################

viASP provides command line functionality to create visualizations. It acts as a proxy to the clingo command meaning that it is usually sufficient to replace `clingo` with `viasp`:

.. code-block:: bash

    $ clingo encoding.lp -n0

.. code-block:: bash

    $ viasp encoding.lp -n0

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

Programs can be loaded from stdin

.. code-block:: bash

    $ cat hamiltonian.lp | viasp

Run clingo to obtain answer sets formatted as json with option `--outf=2`.

.. code-block:: bash

    $ clingo hamiltonian.lp --outf=2 | viasp hamiltonian.lp

Note that the program is passed as an argument to viasp. It is not possible to pipe the program and answer sets at the same time.

Load a json file in the style of clingo's output directly in viASP. This avoids recalculating the answer sets using clingo. Optionally, select one or multiple answer sets from the file using the answer set's index starting with index 0.

.. code-block:: bash

    $ viasp hamiltonian.json hamiltonian.lp --select-model=1

************
Optimization
************

The viASP command line passes on any optimization settings to the clingo backend, so that the optimization can be performed as usual.

To specify the optimization mode, use the ``--opt-mode`` option. The optimization mode can be one of ``opt``, ``enum``, ``optN``, or ``ignore``.

.. code-block:: bash

    $ viasp encoding.lp --opt-mode=optN

When using optimization, not all models listed by clingo are visualized. Depending on the optimization mode, different models are marked marked for visualization: 

- ``opt``: Only the last (optimal) model is marked
- ``optN``: All optimal models are marked
- ``enum``: All models are marked
- ``ignore``: All models are marked

*********
Clingraph
*********

viASP can integrate clingraph visualizations. To do so, pass the path to a separte visualization program as an argument.

.. code-block:: bash

    $ viasp encoding.lp --viz-encoding viz_encoding.lp

To pass additional arguments to clingraph, use the ``--engine`` and ``--graphviz-type`` options.

.. code-block:: bash

    $ viasp encoding.lp --viz-encoding viz_encoding.lp --engine clingraph --graphviz-type dot


**********
Relaxation
**********

Unsatisfiable programs can not be visualized by viASP. When such a program is encountered, viASP suggests using the relaxation mode through the ``--print-relax`` or ``--relax`` options. 

The relaxation mode transforms all integrity constraints of the input program into a relaxed version. Answer sets of the transformed program can point to which of the integrity constraints is violated.

.. admonition:: Example

    An unsatisfiable program

    .. code-block:: bash
    
        a(1..3). 
        b(X) :- a(X+1).
        :- a(X), b(X).
        :- c(1).

    is passed to viASP.

    .. code-block:: bash

        $ viasp unsat-example.lp
        viasp version 2.1.1
        Reading from unsat-example.lp

        Starting backend at http://localhost:5050
        UNSAT
        [INFO] The input program is unsatisfiable. To visualize the relaxed program 
        use --print-relax or --relax.

    Using the ``--print-relax`` option outputs the transformed program

    .. code-block:: bash

        $ viasp unsat-example.lp --print-relax
        #program base.
        a((1..3)).
        b(X) :- a((X+1)).
        unsat(r1,(X,)) :- a(X); b(X).
        unsat(r2) :- c(1).
        :~ unsat(R,T). [1@0,R,T]

When solving the relaxed program, the atom ``unsat(r1, (X,))`` will be derived, if the constraint ``r1`` is violated for the variable ``X``. Answer sets with a minimal number of violated constraints is considered optimal.

.. admonition:: Example


    This relaxed program can be piped into viasp for a visualization

    .. code-block:: bash

        $ viasp unsat-example.lp --print-relax | viasp

    Alternatively, the relaxation and visualization can be executed at once with the ``--relax`` option.

    .. code-block:: bash

        $ viasp unsat-example.lp --relax
        viasp version 2.1.1
        Reading from unsat-example.lp
        UNSAT
        [INFO] Set models.
        [INFO] Reconstructing in progress.
        [INFO] No answer sets found. Switching to transformed visualization.
        [INFO] Successfully transformed program constraints.
        [INFO] Set models.
        [INFO] Reconstructing in progress.
        [INFO] Drawing in progress.
        Dash is running on http://localhost:8050/

    .. image:: ../img/relaxer-program.png


    The visualized answer set to this transformed program shows that the original program is unsatisfiable due to the first integrity constraint. It is violated for the variables ``X=1`` or ``X=2``.
    

By default, variables in the body of integrity constraints are collected in the heads of constraints. To turn off this behavior, use the ``--no-collect-variables`` option.

To specify the head name of the weak constraint, use the ``--head-name`` option. By default, the head name is ``unsat``, but a different name has to be specified, if the program already contains the predicate.

.. code-block:: bash

    $ viasp encoding.lp --head-name _unsat

The relaxer mode only shows one of the optimal answer sets of the transformed program. To change the optimization mode, use the ``--relaxer-opt-mode`` option. The optimization mode is one of clingo's opt mode options. 

.. code-block:: bash

    $ viasp encoding.lp --relaxer-opt-mode=optN


*************
Other options
*************

To specify the port of the backend, use the ``--port`` or ``-p`` option.

To specify the port of the frontend, use the ``--frontend-port`` or ``-f`` option.

To specify the host of both frontend and backend, use the ``--host`` option.
