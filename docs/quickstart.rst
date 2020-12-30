.. _quickstart:

.. currentmodule:: postDB

Quickstart
==========

This page gives a brief introduction to the module. It assumes you have the module installed,
if you don't check the :ref:`installing` portion.
You can find examples `here <https://github.com/SylteA/postDB/tree/main/examples>`_.

Create a basic User model
-------------------------

Let's create a basic User model without adding it to the database

The code will be something like this:

.. code-block:: python3

    from postDB import Model, Column, types

    class User(Model):
        id = Column(types.Integer(big=True), primary_key=True)
        username = Column(types.String)
        email = Column(types.String, unique=True)

    if __name__ == "__main__":
        print(User.create_table_sql())

        user = User(id=5, username="frank", email="frank@doesnotexist")

        print(user.as_dict())
        print(user.as_dict("id", "username"))

Let's understand this example:

- We import :class:`Model`, :class:`Column` and :py:mod:`postDB.types`.
- We create a User class that is subclassed from :class:`Model`.
- We define the columns by using :class:`Column`. We provide the
  type and we can also use keyword arguments like ``primary_key`` or
  ``unique`` to customize the column.

- Then, we print the SQL query for creating the table in the database.
- We create a User with data given for each column.
- We print the dictionary for the user with every column.
- We print the dictionary for the user with only the ``id`` and ``username`` columns.
