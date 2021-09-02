from postDB import Column

from typing import List


class ModelMeta(type):
    """Metaclass for Model class."""

    def __new__(mcs, name, parents, data, **kwargs):

        if not parents:
            # Only occurs on direct subclasses of ModelMeta.
            return super().__new__(mcs, name, parents, data)

        tablename = kwargs.get("tablename", name.lower() + "s")

        columns: List[Column] = []
        for key, col in data.items():
            if isinstance(col, Column):
                if col.name is None:
                    col.name = key

                columns.append(col)

        data["columns"] = columns
        data["__tablename__"] = tablename

        model = super().__new__(mcs, name, parents, data)

        for col in columns:
            col.model = model

        return model

    @property
    def __tablename__(self):
        return self.__dict__["__tablename__"]

    def __repr__(self) -> str:
        return "<Model %s | %s>" % (type(self).__name__, self.__tablename__)
