"""Application-level exceptions shared across layers."""


class LoginRequired(Exception):
    pass


class AuthorizationError(Exception):
    pass


class CsrfError(Exception):
    pass


class AlreadyAuthenticated(Exception):
    pass
