# Custom exceptions

class BaseAppException(Exception):
    """Base exception for application-specific errors"""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class AuthenticationError(BaseAppException):
    """Raised when authentication fails"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_FAILED")


class AuthorizationError(BaseAppException):
    """Raised when user doesn't have permission to access resource"""
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, "ACCESS_DENIED")


class ValidationError(BaseAppException):
    """Raised when input validation fails"""
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, "VALIDATION_ERROR")


class NotFoundError(BaseAppException):
    """Raised when requested resource is not found"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, "NOT_FOUND")


class ConflictError(BaseAppException):
    """Raised when there's a conflict with current state"""
    def __init__(self, message: str = "Conflict detected"):
        super().__init__(message, "CONFLICT")


class ServiceUnavailableError(BaseAppException):
    """Raised when external service is unavailable"""
    def __init__(self, message: str = "Service unavailable"):
        super().__init__(message, "SERVICE_UNAVAILABLE")


class RateLimitError(BaseAppException):
    """Raised when rate limit is exceeded"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, "RATE_LIMIT_EXCEEDED")
