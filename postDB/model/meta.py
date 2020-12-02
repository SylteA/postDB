from postDB import Column


class ModelMeta(type):
    """Metaclass for Model class."""

    def __new__(mcs, name, parents, data, **kwargs):

        if not parents:
            # Only occurs on direct subclasses of ModelMeta.
            return super().__new__(mcs, name, parents, data)

        tablename = kwargs.get("tablename", name.lower() + "s")

        columns = []
        for key, col in data.items():
            if isinstance(col, Column):
                if col.name is None:
                    col.name = key

                if col.index:
                    col.index_name = "%s_%s_idx" % (tablename, col.name)

                columns.append(col)

        data["columns"] = columns
        data["__tablename__"] = tablename
        return super().__new__(mcs, name, parents, data)

    @property
    def __tablename__(self):
        return self.__dict__["__tablename__"]

    def __repr__(self) -> str:
        return "<Model %s | %s>" % (type(self).__name__, self.__tablename__)
