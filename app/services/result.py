from dataclasses import dataclass, field


class ErrorCode:
    NOT_FOUND = "not_found"
    INVALID_STATE = "invalid_state"
    CONFLICT = "conflict"
    VALIDATION = "validation"
    FORBIDDEN = "forbidden"


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
            error description, depending on *success*.  Always a ``str``
            (empty when no message is relevant).
        error_code: Machine-readable error identifier for route handling.
        warnings: Non-fatal messages (e.g. negative-credit-balance alerts
            from shoot creation).
    """

    success: bool
    data: T | None = None
    message: str = ""
    error_code: str | None = None
    warnings: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Convenience constructors
    # ------------------------------------------------------------------

    @staticmethod
    def ok(data: T | None = None, message: str = "", warnings: list[str] | None = None) -> ServiceResult:
        """Create a successful result."""
        return ServiceResult(success=True, data=data, message=message, warnings=warnings or [])

    @staticmethod
    def fail(
        message: str = "",
        *,
        error_code: str | None = None,
        warnings: list[str] | None = None,
    ) -> ServiceResult:
        """Create a failed result."""
        return ServiceResult(success=False, message=message, error_code=error_code, warnings=warnings or [])
