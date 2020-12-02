from postDB.model.meta import ModelMeta
from postDB.types import Serial

from asyncpg.connection import Connection
from asyncpg import create_pool
from asyncpg.pool import Pool

from typing import Optional
import json


def format_missing(missing):
    def fmt_single(name) -> str:
        return "'%s'" % name

    if len(missing) == 1:
        return fmt_single(missing[0].name)

    if len(missing) == 2:
        return " and ".join(fmt_single(col.name) for col in missing)

    return ", ".join(
        fmt_single(col.name) for col in missing[:-1]
    ) + " and %s" % fmt_single(missing[-1].name)


class Model(metaclass=ModelMeta):
    pool: Optional[Pool] = None

    def __init__(self, **attrs):
        missing = []

        for col in self.columns:
            try:
                val = attrs[col.name]
            except KeyError:
                if (
                    col.default is None
                    and not col.nullable
                    and not isinstance(col.column_type, Serial)
                ):
                    missing.append(col)
                    continue

                val = col.default

            setattr(self, col.name, val)

        if missing:
            raise TypeError(
                "__init__() missing {0} required positional arguments: {1}".format(
                    len(missing), format_missing(missing)
                )
            )

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
                col.generate_create_table_sql() + ","
                if col != cls.columns[-1] or any(pks)
                else ""
            )

        if pks:
            columns.append("PRIMARY KEY (%s)" % ", ".join(pks))

        builder.append("(\n    %s\n)" % "\n    ".join(columns))
        statements.append(" ".join(builder) + ";")

        if any(col.index for col in cls.columns):
            statements.append("")

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

    @classmethod
    async def create_pool(
        cls,
        uri: str,
        *,
        min_con: int = 1,
        max_con: int = 10,
        timeout: float = 10.0,
        **pool_kwargs,
    ) -> None:
        """Populate the internal pool keyword."""

        if isinstance(cls.pool, Pool):
            await cls.pool.close()

        async def init(con: Connection) -> None:
            await con.set_type_codec(
                "json", schema="pg_catalog", encoder=json.dumps, decoder=json.loads
            )

        cls.pool = await create_pool(
            dsn=uri,
            init=init,
            timeout=timeout,
            min_size=min_con,
            max_size=max_con,
            **pool_kwargs,
        )

    @classmethod
    async def ensure_con(cls, con: Optional[Connection] = None) -> Connection:
        if isinstance(con, Connection):
            return con

        if isinstance(cls.pool, Pool):
            return await cls.pool.acquire()

        raise RuntimeWarning(
            f"Unable to get Connection, either call `Model.create_pool` or provide a `con` arg."
        )

    @classmethod
    async def create_table(
        cls,
        con: Optional[Connection] = None,
        *,
        verbose: bool = False,
        exists_ok: bool = True,
    ):
        """Create the PostgreSQL Table for this Model."""
        con = await cls.ensure_con(con=con)

        sql = cls.create_table_sql(exists_ok=exists_ok)

        if verbose:
            print(sql)

        return await con.execute(sql)

    @classmethod
    async def drop_table(
        cls,
        con: Optional[Connection] = None,
        *,
        verbose: bool = False,
        exists_ok: bool = True,
    ):
        """Drop the PostgreSQL Table for this Model."""
        con = await cls.ensure_con(con=con)

        sql = cls.drop_table_sql(exists_ok=exists_ok)

        if verbose:
            print(sql)

        return await con.execute(sql)
