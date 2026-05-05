class BaseController:
    """Base controller providing Flask-compatible __name__ attribute."""

    def __init__(self):
        self.__name__ = self.__class__.__name__
