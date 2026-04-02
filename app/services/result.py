"""Standardised return type for service-layer methods."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ServiceResult[T]:
    """Standardised return value for service methods.

    Replaces raw ``tuple[bool, str]`` / ``tuple[Entity | None, str | None]``
    patterns with a single, self-documenting type that supports IDE
    autocomplete and explicit attribute access.

    Attributes:
        success: Whether the operation succeeded.
        data: The entity produced by the operation (e.g. a created model
            instance), or ``None`` for mutation-only operations.
        message: Human-readable feedback — a success description **or** an
            error description, depending on *success*.
        warnings: Non-fatal messages (e.g. negative-credit-balance alerts
            from shoot creation).
    """

    success: bool
    data: T | None = None
    message: str | None = None
    warnings: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Convenience constructors
    # ------------------------------------------------------------------

    @staticmethod
    def ok(data=None, message: str | None = None, warnings: list[str] | None = None) -> ServiceResult:
        """Create a successful result."""
        return ServiceResult(success=True, data=data, message=message, warnings=warnings or [])

    @staticmethod
    def fail(message: str | None = None, warnings: list[str] | None = None) -> ServiceResult:
        """Create a failed result."""
        return ServiceResult(success=False, message=message, warnings=warnings or [])
