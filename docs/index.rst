Static file serving with bareASGI
=================================

Static file support for `bareASGI <https://bareasgi.readthedocs.io/en/latest>`_.

Installation
------------

The package can be installed with pip.

.. code-block:: bash

    pip install bareasgi-static

This is a Python 3.7 and later package with dependencies on:

* bareASGI
* aiofiles

Usage
-----

A utility function is provided.

.. code-block:: python

    import os.path
    import uvicorn
    from bareasgi import Application
    from bareasgi_static import add_static_file_provider

    here = os.path.abspath(os.path.dirname(__file__))

    app = Application()
    add_static_file_provider(app, os.path.join(here, 'simple_www'), index_filename='index.html')

    uvicorn.run(app, port=9010)


.. toctree::
    :maxdepth: 2
    :caption: Contents:

    api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
