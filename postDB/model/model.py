import json
from asyncio import BaseEventLoop
from typing import Optional, List, Type

from asyncpg import create_pool
from asyncpg.connection import Connection
from asyncpg.pool import Pool

from postDB.model.meta import ModelMeta
from postDB.types import Serial


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
    """Base class for all the models."""

    pool: Optional[Pool] = None

    def __init__(self, **attrs):
        missing = []

        for col in self.columns:
            try:
                column_name = attrs[col.name]
            except KeyError:
                if (
                    col.default is None
                    and not col.nullable
                    and not isinstance(col.column_type, Serial)
                ):
                    missing.append(col)
                    continue

                column_name = col.default

            setattr(self, col.name, column_name)

        if missing:
            raise TypeError(
                "__init__() missing {0} required positional arguments: {1}".format(
                    len(missing), format_missing(missing)
                )
            )

    @classmethod
    def create_table_sql(cls, *, exists_ok: bool = True) -> str:
        """Generates the ``CREATE TABLE`` SQL statement."""
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
                + ("," if col != cls.columns[-1] or any(pks) else "")
            )

        if pks:
            columns.append("PRIMARY KEY (%s)" % ", ".join(pks))

        builder.append("(\n    %s\n)" % "\n    ".join(columns))
        statements.append(" ".join(builder) + ";")

        if any(col.index for col in cls.columns):
            statements.append("")

        for col in cls.columns:
            if col.index:
                fmt = col.index.generate_create_table_sql()
                statements.append(fmt)

        return "\n".join(statements)

    @classmethod
    def drop_table_sql(cls, *, exists_ok: bool = True, cascade: bool = False) -> str:
        """Generates the ``DROP TABLE`` SQL statement."""
        builder = ["DROP TABLE"]

        if exists_ok:
            builder.append("IF EXISTS")

        to_cascade = "CASCADE" if cascade else "RESTRICT"
        builder.append("%s %s;" % (cls.__tablename__, to_cascade))
        return " ".join(builder)

    @classmethod
    async def create_pool(
        cls,
        uri: str,
        *,
        min_con: int = 1,
        max_con: int = 10,
        timeout: float = 10.0,
        loop: BaseEventLoop = None,
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
            loop=loop,
            timeout=timeout,
            min_size=min_con,
            max_size=max_con,
            **pool_kwargs,
        )

    @classmethod
    async def create_table(
        cls,
        *,
        verbose: bool = False,
        exists_ok: bool = True,
    ):
        """Create the PostgreSQL Table for this Model."""
        if cls.pool is None:
            raise TypeError(
                "Unable to get Connection, please call `Model.create_pool` before using the coroutine."
            )

        sql = cls.create_table_sql(exists_ok=exists_ok)

        if verbose:
            print(sql)

        return await cls.pool.execute(sql)

    @classmethod
    async def drop_table(
        cls,
        *,
        verbose: bool = False,
        cascade: bool = True,
        exists_ok: bool = True,
    ):
        """Drop the PostgreSQL Table for this Model."""
        if cls.pool is None:
            raise TypeError(
                "Unable to get Connection, please call `Model.create_pool` before using the coroutine."
            )

        sql = cls.drop_table_sql(exists_ok=exists_ok, cascade=cascade)

        if verbose:
            print(sql)

        return await cls.pool.execute(sql)

    @classmethod
    def all_models(cls) -> List[Type["Model"]]:
        """Returns a list of all :class:`Model` subclasses."""
        return cls.__subclasses__()

    def as_dict(self, *columns) -> dict:
        """Returns a dict of attribute:value, only containing the columns specified."""
        all_column_names = [col.name for col in self.columns]
        if not columns:
            columns = all_column_names
        else:
            for col in columns:
                if col not in all_column_names:
                    raise ValueError(
                        "%s is not a attribute of the %s Model."
                        % (col, type(self).__name__)
                    )

        return {key: getattr(self, key, None) for key in columns}
