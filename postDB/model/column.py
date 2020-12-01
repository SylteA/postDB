import inspect


from postDB.exceptions import SchemaError
from postDB.types import SQLType, String


class Column:
    __slots__ = (
        "column_type",
        "index",
        "primary_key",
        "nullable",
        "default",
        "unique",
        "name",
        "index_name",
    )

    def __init__(
        self,
        column_type,
        *,
        index=False,
        primary_key=False,
        nullable=False,
        unique=False,
        default=None,
        name=None
    ):
        if inspect.isclass(column_type):
            column_type = column_type()

        if not isinstance(column_type, SQLType):
            raise TypeError("Cannot have a non-SQLType derived column_type")

        if default is not None:
            if not nullable:
                # If provided default is not of same type as column_type raise an error.
                if not isinstance(default, column_type.python):
                    try:
                        default = column_type.python(default)
                    except TypeError:
                        raise TypeError("Column default cannot be of different type than column_type")

        self.column_type = column_type
        self.index = index
        self.unique = unique
        self.primary_key = primary_key
        self.nullable = nullable
        self.default = default
        self.name = name
        self.index_name = None  # to be filled later

        if sum(map(bool, (unique, primary_key, default is not None))) > 1:
            raise SchemaError(
                "'unique', 'primary_key', and 'default' are mutually exclusive."
            )

    @classmethod
    def from_dict(cls, data: dict) -> "Column":
        index_name = data.pop("index_name", None)
        column_type = data.pop("column_type")
        column_type = SQLType.from_dict(column_type)
        self = cls(column_type=column_type, **data)
        self.index_name = index_name
        return self

    def to_dict(self) -> dict:
        d = {attr: getattr(self, attr) for attr in self.__slots__}
        d["column_type"] = self.column_type.to_dict()
        return d

    @property
    def _comparable_id(self) -> str:
        return "-".join(
            "%s:%s" % (attr, getattr(self, attr)) for attr in self.__slots__
        )

    def _qualifiers_dict(self):
        return {attr: getattr(self, attr) for attr in ("nullable", "default")}

    def _is_rename(self, other):
        if self.name == other.name:
            return False

        return self.unique == other.unique and self.primary_key == other.primary_key

    def generate_create_table_sql(self):
        builder = [self.name, self.column_type.to_sql()]

        default = self.default
        if default is not None:
            builder.append("DEFAULT")
            if isinstance(default, str) and isinstance(self.column_type, String):
                builder.append("'%s'" % default)
            elif isinstance(default, bool):
                builder.append(str(default).upper())
            else:
                builder.append("(%s)" % default)

        elif self.unique:
            builder.append("UNIQUE")
        if not self.nullable:
            builder.append("NOT NULL")

        return " ".join(builder)
