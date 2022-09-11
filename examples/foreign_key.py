"""
Test creating a Model with a foreignkey and generating the SQL to create its table.
"""

from postDB import Model, Column, types


class User(Model):
    id = Column(types.Integer, primary_key=True)
    username = Column(types.String)
    email = Column(types.String, unique=True)


class Post(Model):
    id = Column(types.Integer, primary_key=True)
    title = Column(types.String, unique=True)
    content = Column(types.String)
    author_id = Column(types.ForeignKey("users", "id"))


if __name__ == "__main__":
    print(User.create_table_sql())
    print(Post.create_table_sql())

    user = User(id=5, username="frank", email="frank@doesnotexist")

    print(user.as_dict())
    print(user.as_dict("id", "username"))

    post = Post(id=1, title="Hello World", content="lorem ipsum", author_id=user.id)
    print(post.as_dict())
