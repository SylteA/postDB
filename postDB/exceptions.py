class SchemaError(Exception):
    """Base error for the module."""

    pass


class UniqueViolationError(SchemaError):
    """Raised when a unique constraint is violated."""

    pass
