from postDB import Model, Column, types


class User(Model):
    id = Column(types.Integer(big=True), primary_key=True)
    username = Column(types.String)
    email = Column(types.String, unique=True)


if __name__ == "__main__":
    print(User.create_table_sql())
