class AppException(Exception):
    """Base application exception."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class UserNotFoundException(AppException):
    """Raised when a user is not found."""
    pass

class UserAlreadyExistsException(AppException):
    """Raised when a user already exists."""
    pass

class AnalysisGatewayError(AppException):
    """Raised when the analysis gateway fails."""
    pass
