.. currentmodule:: postDB

===============
API Reference
===============

The following section outlines the API of postDB.

Version Related Info
----------------------

There are some ways to query version information about the library.

.. data:: version_info

    A named tuple that is similar to :obj:`py:sys.version_info`.

    Just like :obj:`py:sys.version_info` the valid values for ``releaselevel`` are
    ``'alpha'``, ``'beta'``, ``'candidate'`` and ``'final'``.

.. data:: __version__

    A string representation of the version. e.g. ``'1.3.0rc1'``. This is based
    off of :pep:`440`.

.. data:: VERSION

    A tuple representation of the version. e.g. ``(1, 3, 0, "candidate", 1)``.
    :data:`version_info` is made out of this tuple

.. autofunction:: get_version()

Model
-----

.. autoclass:: Model()
    :members:

Column
------

.. autoclass:: Column()
    :members:

Column types
------------

Base class
~~~~~~~~~~

.. autoclass:: postDB.types.SQLType()
    :members:

Types
~~~~~

.. automodule:: postDB.types
    :members:
    :exclude-members: SQLType, python, to_sql, is_real_type

Exceptions
------------

The following exceptions are thrown by the module.
Other exceptions might be raised by :py:mod:`asyncpg`.

.. autoexception:: postDB.exceptions.SchemaError

.. autoexception:: postDB.exceptions.UniqueViolationError

Exception Hierarchy
~~~~~~~~~~~~~~~~~~~~~

- :exc:`Exception`
    - :exc:`postDB.exceptions.SchemaError`
        - :exc:`postDB.exceptions.UniqueViolationError`
