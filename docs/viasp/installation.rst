============
Installation
============

Installing with pip 
===================

The python viasp package can be found `here <https://pypi.org/project/viasp/>`_.

.. warning:: 
    The latest version is currently not available on PyPI. Please install from source.

.. code-block:: bash

    $ pip install viasp

.. warning:: 
    To support the usage of clingraph in viASP, the user must first install `graphviz <https://www.graphviz.org/download/>`_  (version 2.50 or greater) manually.

Installing from source
======================

The project can currently only be installed from source. To do so, clone the repository at https://github.com/stephanzwicknagl/viasp and run the following commands in the root directory of the project:

1. create a virtual environment

.. code-block:: bash
    
    $ conda create -n viasp_env
    $ conda activate viasp_env

2. install pip

.. code-block:: bash

    $ conda install pip

3. install `graphviz <https://www.graphviz.org/download/>`_
4. use pip to install the project

.. code-block:: bash

    $ pip install -q viasp viasp/backend viasp/frontend
