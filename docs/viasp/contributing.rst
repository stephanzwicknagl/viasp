=================
Contributing
=================

Requirements
============

- `Git <https://git-scm.com>`_
- `Node.JS <https://nodejs.org>`_
- `Python <https://www.python.org>`_
- A suitable browser


Getting started
===============

1. Clone the repository using :code:`git clone https://github.com/stephanzwicknagl/viasp.git`
2. Create and activate a conda environment
3. Install pip :code:`conda install pip`
4. Install viASP in editable mode :code:`pip install -e viasp -e viasp/backend -e viasp/frontend`

Developing the backend
======================

1. Simply edit the code in the backend folder :code:`viasp/backend/src`
2. Run viASP with a clingo program :code:`viasp encoding.lp`

Developing the frontend
=======================

1. Move to frontend folder :code:`cd viasp/frontend`
2. Run :code:`npm i` to install all needed dependencies
3. Run :code:`npx webpack` to pack the javascript
4. Run viASP with a clingo program :code:`viasp encoding.lp`

.. Note::
    The JavaScript and CSS files are located at ``/frontend/src/lib``. The frontend code needs to be packed before changes become visible to the webpage.

Code your heart out!

