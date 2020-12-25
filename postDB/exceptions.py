class SchemaError(Exception):
    """Base error for the module."""
    pass


class UniqueViolationError(SchemaError):
    """Raised when a Unique constraint is violated."""
    pass
