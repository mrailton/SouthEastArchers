"""Application-level exceptions shared across layers."""


class LoginRequired(Exception):
    pass


class AuthorizationError(Exception):
    pass
