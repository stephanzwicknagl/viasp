==========================
Command line functionality
==========================

viASP provides command line functionality to generate graphs from files. The graphs can then be inspected in the browser.


To use viASP from the command line, simply run

.. code-block:: bash

    $ viasp encoding.lp

You can now inspect the visualization at http://localhost:8050/. To stop the server, press ``CTRL+C``.


The command line usage is described below. Additionally, all options can be found by running

.. code-block:: bash

    $ viasp --help


Loading Programs
================

To load a program, pass the path to the program file as an argument. For programs split into multiple files, all of them can be loaded at once.

.. code-block:: bash

    $ viasp sprinkler.lp encoding2.lp

The output prints the stable models of the program and information about the viasp server and frontend url

.. code-block:: bash
    
    Starting backend at http://localhost:5050
    Answer:
    rain wet    
    Answer:
    sprinkler wet
    SAT
    [INFO] (2023-12-01 12:38:44) Set models.
    [INFO] (2023-12-01 12:38:44) Reconstructing in progress.
    [INFO] (2023-12-01 12:38:44) Drawing in progress.
    Dash is running on http://localhost:8050/

    Press CTRL+C to quit


To define how many models should be included at most, use the ``--models`` or ``-n`` option.

.. code-block:: bash

    $ viasp encoding.lp -n 3


Clingraph
=========

viASP can include clingraph visualizations in the frontend. To do so, pass the path to a separte visualization program as an argument.

.. code-block:: bash

    $ viasp encoding.lp --viz_encoding viz_encoding.lp

To pass additional arguments to clingraph, use the ``--engine`` and ``--graphviz_type`` options.

.. code-block:: bash

    $ viasp encoding.lp --viz_encoding viz_encoding.lp --engine clingraph --graphviz_type dot


Relaxer
=======

By default, viASP supports the visualization of unsatisfiable programs using the relaxer. viASP transforms the integrity constraints of unsatisfiable programs into weak constraints and visualizes the resulting program. The resulting graph can be used to inspect the reason for unsatisfiability.

By default, variables in the body of integrity constraints are collected in the heads of constraints. To turn off this behavior, use the ``--no-collect-variables`` option.

To specify the head name of the weak constraint, use the ``--head_name`` option. By default, the head name is ``unsat``, but a different name should be specified, if the program already contains the predicate.

.. code-block:: bash

    $ viasp encoding.lp --head_name _unsat


To turn off the relaxer, use the ``--no-relaxer`` or ``-r`` option.

Other options
=============

To specify the port of the backend, use the ``--port`` or ``-p`` option.

To specify the port of the frontend, use the ``--frontend-port`` or ``-f`` option.

To specify the host of both frontend and backend, use the ``--host`` option.