Class Documentation
===================

the Data class
--------------
This class handles hierarchical data and is specifically made for handling XNAT experiment data but could potentially have other use cases

.. autoclass:: xnatio.Data
    :members:

the SubjectData class
---------------------
This class, which inherits from xnatio.Data, manages the data of subjects (specifically ones from an XNAT database--but any subject with an ID should work),
and provides methods for selecting certain subjects to collect their experiment data, both by grouping subjects based on qualitative parameters or by selecting subject ID.

.. autoclass:: xnatio.SubjectData
    :members:

the XnatUI class
----------------

This class uses the Data and SubjectData classes to interface with an XNAT instance (so far, it has been tested using CNDA).
However, it's methods are not just simple wrappers: they are designed to add new functionality, in addition to exposing access to the API

.. autoclass:: xnatio.XnatUI
    :members:

