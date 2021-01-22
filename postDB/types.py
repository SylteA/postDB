from typing import Optional, Union, Type
import datetime
import inspect
import decimal
import pydoc

from postDB.exceptions import SchemaError


class SQLType:
    """Base class for all the other types."""

    python = None

    def to_dict(self) -> dict:
        """Returns a dict of the class attributes."""
        o = self.__dict__.copy()
        cls = self.__class__
        o["__meta__"] = cls.__module__ + "." + cls.__qualname__
        return o

    @classmethod
    def from_dict(cls, data: dict) -> "SQLType":
        """Create a type instance from a dict."""
        meta = data.pop("__meta__")
        given = cls.__module__ + "." + cls.__qualname__
        if given != meta:
            cls = pydoc.locate(meta)
            if cls is None:
                raise RuntimeError('Could not locate "%s".' % meta)

        self = cls.__new__(cls)
        self.__dict__.update(data)
        return self

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)

    def to_sql(self) -> str:
        """Returns the SQL of the type."""
        raise NotImplementedError()

    def is_real_type(self) -> bool:
        """Returns a bool stating if the type is a real PostgreSQL type
        or if it has been defined as a type for ease of use"""
        return True


class Binary(SQLType):
    """Type for python :class:`bytes`. ``BYTEA`` in PostgreSQL."""

    python = bytes

    def to_sql(self):
        return "BYTEA"


class Boolean(SQLType):
    """Type for python :class:`bool`. ``BOOLEAN`` in PostgreSQL."""

    python = bool

    def to_sql(self):
        return "BOOLEAN"


class Date(SQLType):
    """Type for python :class:`datetime.date`. ``DATE`` in PostgreSQL."""

    python = datetime.date

    def to_sql(self):
        return "DATE"


class DateTime(SQLType):
    """Type for python :class:`datetime.datetime`. ``TIMESTAMP WITH TIME ZONE``
    or ``TIMESTAMP WITHOUT TIME ZONE`` in PostgreSQL.

    Optional timezone with the :attr:`timezone` attribute."""

    python = datetime.datetime

    def __init__(self, *, timezone: bool = False):
        self.timezone = timezone

    def to_sql(self):
        if self.timezone:
            return "TIMESTAMP WITH TIME ZONE"
        return "TIMESTAMP WITHOUT TIME ZONE"


class Real(SQLType):
    """Type for python :class:`float`. ``REAL`` in PostgreSQL."""

    python = float

    def to_sql(self):
        return "REAL"


class Float(SQLType):
    """Type for python :class:`float`. ``FLOAT`` in PostgreSQL."""

    python = float

    def to_sql(self):
        return "FLOAT"


class Integer(SQLType):
    """Type for python :class:`int`. ``INTEGER``
    or ``BIG INT`` or ``SMALL INT`` in PostgreSQL.

    Optional big or small integer with :attr:`big` and :attr:`small`"""

    python = int

    def __init__(self, *, big: bool = False, small: bool = False):
        if big and small:
            raise SchemaError("Integer column type cannot be both big and small")

        self.big = big
        self.small = small

    def to_sql(self):
        if self.big or self.small:
            return ("BIG" if self.big else "SMALL") + "INT"

        return "INTEGER"


class Serial(Integer):
    """Type for python :class:`int` that autoincrements. ``SERIAL``
    or ``BIG SERIAL`` or ``SMALL SERIAL`` in PostgreSQL.

    Optional big or small integer with :attr:`big` and :attr:`small`"""

    def to_sql(self):
        if self.big or self.small:
            return ("BIG" if self.big else "SMALL") + "SERIAL"

        return "SERIAL"

    def is_real_type(self):
        return False


class Interval(SQLType):
    """Type for python :class:`datetime.timedelta`. ``INTERVAL``
    or ``INTERVAL {field}`` in PostgreSQL.

    Optional field argument for setting the interval type with the :attr:`field`.
    field argument needs to be in this list:

    - ``"YEAR"``
    - ``"MONTH"``
    - ``"DAY"``
    - ``"HOUR"``
    - ``"MINUTE"``
    - ``"SECOND"``
    - ``"YEAR TO MONTH"``
    - ``"DAY TO HOUR"``
    - ``"DAY TO MINUTE"``
    - ``"DAY TO SECOND"``
    - ``"HOUR TO MINUTE"``
    - ``"HOUR TO SECOND"``
    - ``"MINUTE TO SECOND"``
    """

    python = datetime.timedelta

    def __init__(self, field: str = None):
        if field:
            field = field.upper()
            if field not in (
                "YEAR",
                "MONTH",
                "DAY",
                "HOUR",
                "MINUTE",
                "SECOND",
                "YEAR TO MONTH",
                "DAY TO HOUR",
                "DAY TO MINUTE",
                "DAY TO SECOND",
                "HOUR TO MINUTE",
                "HOUR TO SECOND",
                "MINUTE TO SECOND",
            ):
                raise SchemaError("Invalid interval specified")
            self.field = field
        else:
            self.field = None

    def to_sql(self):
        if self.field:
            return "INTERVAL " + self.field
        return "INTERVAL"


class Numeric(SQLType):
    """Type for python :class:`decimal.Decimal`. ``NUMERIC``
    or ``NUMERIC({precision}, {scale})`` in PostgreSQL.

    Optional precision and scale with :attr:`precision` and :attr:`scale`"""

    python = decimal.Decimal

    def __init__(self, *, precision: int = None, scale: int = None):
        if precision is not None:
            if precision < 0 or precision > 1000:
                raise SchemaError("precision must be greater than 0 and below 1000")
            if scale is None:
                scale = 0

        self.precision = precision
        self.scale = scale

    def to_sql(self):
        if self.precision is not None:
            return "NUMERIC({0.precision}, {0.scale})".format(self)
        return "NUMERIC"


class String(SQLType):
    """Type for python :class:`str`. ``TEXT``
    or ``CHAR({length})`` or ``VARCHAR({length})`` in PostgreSQL.

    Optional length and fixed with :attr:`length` and :attr:`fixed`"""

    python = str

    def __init__(self, *, length: int = None, fixed: bool = False):
        if fixed and length is None:
            raise SchemaError("Cannot have fixed string with no length")

        self.length = length
        self.fixed = fixed

    def to_sql(self):
        if self.length is None:
            return "TEXT"

        if self.fixed:
            return "CHAR(%s)" % self.length

        return "VARCHAR(%s)" % self.length


class Time(SQLType):
    """Type for python :class:`datetime.time`. ``TIME WITH TIME ZONE``
    or ``TIME WITHOUT TIME ZONE`` in PostgreSQL.

    Optional timezone with the :attr:`timezone` attribute."""

    python = datetime.time

    def __init__(self, *, timezone: bool = False):
        self.timezone = timezone

    def to_sql(self):
        if self.timezone:
            return "TIME WITH TIME ZONE"
        return "TIME WITHOUT TIME ZONE"


class JSON(SQLType):
    """Type for python :class:`dict`. ``JSON`` in PostgreSQL."""

    python = dict

    def to_sql(self):
        return "JSON"


class ForeignKey(SQLType):
    """Reference to another column in another model."""

    def __init__(
        self,
        model: str,
        column: str,
        *,
        sql_type: Optional[Union[Type[SQLType], SQLType]] = None,
        on_delete: str = "CASCADE",
        on_update: str = "NO ACTION"
    ):
        if not model or not isinstance(model, str):
            raise SchemaError("missing model to reference (must be string)")

        valid_actions = (
            "NO ACTION",
            "RESTRICT",
            "CASCADE",
            "SET NULL",
            "SET DEFAULT",
        )

        on_delete = on_delete.upper()
        on_update = on_update.upper()

        if on_delete not in valid_actions:
            raise TypeError("on_delete must be one of %s." % str(valid_actions))

        if on_update not in valid_actions:
            raise TypeError("on_update must be one of %s." % str(valid_actions))

        self.model = model
        self.column = column
        self.on_update = on_update
        self.on_delete = on_delete

        if sql_type is None:
            sql_type = Integer

        if inspect.isclass(sql_type):
            sql_type = sql_type()

        if not isinstance(sql_type, SQLType):
            raise TypeError("Cannot have non-SQLType derived sql_type")

        if not sql_type.is_real_type():
            raise SchemaError('sql_type must be a "real" type')

        self.sql_type = sql_type.to_sql()

    def is_real_type(self):
        return False

    def to_sql(self):
        fmt = (
            "{0.sql_type} REFERENCES {0.model}({0.column})"
            " ON DELETE {0.on_delete} ON UPDATE {0.on_update}"
        )
        return fmt.format(self)


class Array(SQLType):
    """Type for python :class:`list`. ``{type} ARRAY`` in PostgreSQL."""

    python = list

    def __init__(self, sql_type: Union[Type[SQLType], SQLType]):
        if inspect.isclass(sql_type):
            sql_type = sql_type()

        if not isinstance(sql_type, SQLType):
            raise TypeError("Cannot have non-SQLType derived sql_type")

        if not sql_type.is_real_type():
            raise SchemaError('sql_type must be a "real" type')

        self.sql_type = sql_type.to_sql()

    def to_sql(self):
        return "{0.sql_type} ARRAY".format(self)

    def is_real_type(self):
        # technically, it is a real type
        # however, it doesn't play very well with migrations
        # so we're going to pretend that it isn't
        return False
