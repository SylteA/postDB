from postDB.model.meta import ModelMeta

from asyncpg.connection import Connection
from asyncpg import UniqueViolationError
from typing import List


def format_missing(missing):
    def fmt_single(name) -> str:
        return "'%s'" % name

    if len(missing) == 1:
        return fmt_single(missing[0].name)

    if len(missing) == 2:
        return " and ".join(fmt_single(col.name) for col in missing)

    return ", ".join(fmt_single(col.name) for col in missing[:-1]) \
           + " and %s" % fmt_single(missing[-1].name)


class Model(metaclass=ModelMeta):

    def __init__(self, **attrs):
        missing = self.columns.copy()

        for col in missing:
            try:
                val = attrs[col.name]
            except KeyError:
                if col.default is None and not col.nullable:
                    continue

                val = col.default

            setattr(self, col.name, val)
            missing.remove(col)

        if missing:
            raise TypeError("__init__() missing {0} required positional arguments: {1}".format(
                len(missing), format_missing(missing)
            ))

    @classmethod
    def create_table_sql(cls, *, exists_ok: bool = True):
        """Generates the CREATE TABLE statement."""
        statements = []
        builder = ["CREATE TABLE"]

        if exists_ok:
            builder.append("IF NOT EXISTS")

        builder.append(cls.__tablename__)

        columns = []
        pks = [col.name for col in cls.columns if col.primary_key]

        for col in cls.columns:
            columns.append(
                col.generate_create_table_sql()
                + "," if col != cls.columns[-1] or any(pks) else ""
            )

        if pks:
            columns.append("PRIMARY KEY (%s)" % ", ".join(pks))

        builder.append("(\n    %s)" % "\n    ".join(columns))
        statements.append(" ".join(builder) + ";")

        if any(col.index for col in cls.columns):
            statements.append('')

        for col in cls.columns:
            if col.index:
                fmt = "CREATE INDEX IF NOT EXISTS {1.index_name} ON {0} ({1.name});".format(
                    cls.__tablename__, col
                )
                statements.append(fmt)

        return "\n".join(statements)

    @classmethod
    def drop_table_sql(cls, exists_ok: bool = True):
        builder = ["DROP TABLE"]

        if exists_ok:
            builder.append("IF EXISTS")

        builder.append("%s CASCADE;" % cls.__tablename__)
        return " ".join(builder)

