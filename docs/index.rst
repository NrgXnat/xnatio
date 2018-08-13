.. xnatio documentation master file, created by
   sphinx-quickstart on Tue Jul 31 13:43:38 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to xnatio's documentation!
==================================

xnatio is a Python library, running in the Jupyter Notebook environment, that provides methods for easily accessing data from the XNAT_ database,
allowing quick access to various methods within experiments. xnatio will allow you to select which projects, subjects, and experiments to gather data from,
then, with a helpful UI, allow you to specify which paths within the experiments to gather. Then, it will generate data points (or lists, if you prefer) and
automatically group like variables (for example, if you select subject ID and a CDR score, then the data points will each contain an ID and CDR score from
the same subject)

What xnatio is good at
   - Generating easily plotted data of specific parts of experiment(s) (note: xnatio itself does not plot data; use something like matplotlib_)
   - Accessing specific data for specific subject(s)
   - Creating interactive demonstrations, using the functionality of the Jupyter Notebook

What xnatio isn't as good at
   - Getting large amounts of raw experiment data (including filtering through that data)
   - Uploading or editing any data (xnatio will not change make any changes to the data)

.. _XNAT: https://www.xnat.org
.. _matplotlib: https://matplotlib.org/

.. toctree::
   :maxdepth: 2
   :caption: Table of Contents

   installation
   docindex
   ui_example
   script_example


Index
=====
* :ref:`genindex`