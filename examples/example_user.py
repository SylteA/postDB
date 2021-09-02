"""
Test creating a Model and generating the SQL to create its table.
"""

from postDB import Model, Column, types


class User(Model):
    id = Column(types.Integer, primary_key=True)
    username = Column(types.String)
    email = Column(types.String, unique=True)


if __name__ == "__main__":
    print(User.create_table_sql())

    user = User(id=5, username="frank", email="frank@doesnotexist")

    print(user.as_dict())
    print(user.as_dict("id", "username"))
