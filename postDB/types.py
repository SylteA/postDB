from typing import Optional
import datetime
import inspect
import decimal
import pydoc

from postDB.exceptions import SchemaError


class SQLType:
    python = None

    def to_dict(self):
        o = self.__dict__.copy()
        cls = self.__class__
        o["__meta__"] = cls.__module__ + "." + cls.__qualname__
        return o

    @classmethod
    def from_dict(cls, data):
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

    def to_sql(self):
        raise NotImplementedError()

    def is_real_type(self):
        return True


class Binary(SQLType):
    python = bytes

    def to_sql(self):
        return "BYTEA"


class Boolean(SQLType):
    python = bool

    def to_sql(self):
        return "BOOLEAN"


class Date(SQLType):
    python = datetime.date

    def to_sql(self):
        return "DATE"


class DateTime(SQLType):
    python = datetime.datetime

    def __init__(self, *, timezone=False):
        self.timezone = timezone

    def to_sql(self):
        if self.timezone:
            return "TIMESTAMP WITH TIME ZONE"
        return "TIMESTAMP WITHOUT TIME ZONE"


class Real(SQLType):
    python = float

    def to_sql(self):
        return "REAL"


class Float(SQLType):
    python = float

    def to_sql(self):
        return "FLOAT"


class Integer(SQLType):
    python = int

    def __init__(self, *, big=False, small=False):
        if big and small:
            raise SchemaError("Integer column type cannot be both big and small")

        self.big = big
        self.small = small

    def to_sql(self):
        if self.big or self.small:
            return ("BIG" if self.big else "SMALL") + "INT"

        return "INTEGER"


class Serial(Integer):
    def to_sql(self):
        if self.big or self.small:
            return ("BIG" if self.big else "SMALL") + "SERIAL"

        return "SERIAL"

    def is_real_type(self):
        return False


class Interval(SQLType):
    python = datetime.timedelta

    def __init__(self, field=None):
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
                raise SchemaError("invalid interval specified")
            self.field = field
        else:
            self.field = None

    def to_sql(self):
        if self.field:
            return "INTERVAL " + self.field
        return "INTERVAL"


class Numeric(SQLType):
    python = decimal.Decimal

    def __init__(self, *, precision=None, scale=None):
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
    python = str

    def __init__(self, *, length=None, fixed=False):
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
    python = datetime.time

    def __init__(self, *, timezone=False):
        self.timezone = timezone

    def to_sql(self):
        if self.timezone:
            return "TIME WITH TIME ZONE"
        return "TIME WITHOUT TIME ZONE"


class JSON(SQLType):
    python = dict

    def to_sql(self):
        return "JSON"


class ForeignKey(SQLType):
    def __init__(
        self,
        model: str,
        column: str,
        *,
        sql_type: Optional[SQLType] = None,
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
    python = list

    def __init__(self, sql_type):
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
