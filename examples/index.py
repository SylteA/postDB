"""
Test creating a Model with a foreignkey and an index.
"""

from postDB import Model, Column, Index, types


class User(Model):
    id = Column(types.Integer, primary_key=True)
    username = Column(types.String)
    email = Column(types.String, unique=True)


class Post(Model):
    id = Column(types.Integer, primary_key=True)
    title = Column(types.String, unique=True)
    content = Column(types.String)
    author_id = Column(types.ForeignKey("users", "id"), index=Index(method="btree"))


async def main():
    await Model.create_pool(uri="postgres://TEST:TEST@localhost:5432/TEST")

    try:
        await User.create_table()
        await Post.create_table()
    except Exception as e:
        print(e)
    finally:
        await User.drop_table()
        await Post.drop_table()
        ...


if __name__ == "__main__":
    print(User.create_table_sql())
    print(Post.create_table_sql())

    user = User(id=5, username="frank", email="frank@doesnotexist")

    print(user.as_dict())
    print(user.as_dict("id", "username"))

    post = Post(id=1, title="Hello World", content="lorem ipsum", author_id=user.id)
    print(post.as_dict())

    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
