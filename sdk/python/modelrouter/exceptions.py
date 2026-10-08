from typing import Optional, Any


class ModelRouterError(Exception):
    """Base exception for all Model Router SDK errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_body = response_body

    def __str__(self):
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(ModelRouterError):
    """Raised when API key or Workspace authentication fails (HTTP 401/403)."""
    pass


class RateLimitError(ModelRouterError):
    """Raised when Workspace or Token rate limits are exceeded (HTTP 429)."""
    pass


class APIConnectionError(ModelRouterError):
    """Raised when unable to reach the Model Router gateway server."""
    pass


class APIStatusError(ModelRouterError):
    """Raised for general HTTP errors (4xx/5xx)."""
    pass


class RoutingError(ModelRouterError):
    """Raised when request routing cannot find an eligible model."""
    pass
