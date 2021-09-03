from typing import Literal, Optional


class Index:
    """Class to define a index in a :class:`Model`."""

    __slots__ = ("order", "method", "unique", "column", "__name")

    def __init__(
        self,
        *,
        method: Literal["btree", "hash", "gist", "gin"] = "btree",
        order: Literal["ASC", "DESC"] = "ASC",
        name: Optional[str] = None,
        unique: bool = True,
    ):

        methods = ("btree", "hash", "gist", "gin")
        assert method in methods, "Invalid index method, must be one of: " + ", ".join(
            methods
        )

        orders = ("ASC", "DESC")
        assert order in orders, "Invalid index order, must be one of: " + ", ".join(
            orders
        )

        self.column = None
        self.__name = None

        self.name: str = name
        self.order: str = order
        self.method: str = method
        self.unique: bool = unique

    @property
    def name(self) -> str:
        """Default name impl."""
        if self.__name is None:
            default = "%s_%s_idx" % (self.column.model.__tablename__, self.column.name)
            self.name = default

        return self.__name

    @name.setter
    def name(self, value: str):
        self.__name = value

    def generate_create_table_sql(self) -> str:
        """Generates the SQL for this index."""
        builder = ["CREATE"]

        if self.unique:
            builder.append("UNIQUE")

        builder.extend(
            [
                "INDEX",
                self.name,
                "ON",
                self.column.model.__tablename__,
                "USING",
                self.method,
                f"({self.column.name} {self.order})",
            ]
        )

        return " ".join(builder) + ";"
