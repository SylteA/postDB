from postDB.exceptions import SchemaError
from postDB.types import SQLType, String
from postDB.model.index import Index

from typing import Optional, Union, Type, Any
import inspect


class Column:
    """Class to define a column in a :class:`Model`."""

    __slots__ = (
        "column_type",
        "index",
        "primary_key",
        "nullable",
        "default",
        "unique",
        "model",
        "name",
    )

    def __init__(
        self,
        column_type: Union[Type[SQLType], SQLType],
        *,
        index: Optional[Union[Index, bool]] = None,
        default: Optional[Any] = None,
        name: Optional[str] = None,
        primary_key: bool = False,
        nullable: bool = False,
        unique: bool = False
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
                        raise TypeError(
                            "Column default cannot be of different type than column_type"
                        )

        if index and not isinstance(index, Index):
            index = Index()

        if isinstance(index, Index):
            index.column = self

        self.column_type = column_type
        self.index = index
        self.unique = unique
        self.primary_key = primary_key
        self.nullable = nullable
        self.default = default
        self.name = name

        self.model = None  # set later.

        if sum(map(bool, (unique, primary_key, default is not None))) > 1:
            raise SchemaError(
                "'unique', 'primary_key', and 'default' are mutually exclusive."
            )

    def generate_create_table_sql(self) -> str:
        """Generates the SQL for this column for the ``CREATE TABLE`` statement."""
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
