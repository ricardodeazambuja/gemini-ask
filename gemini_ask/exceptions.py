"""
Custom exceptions for gemini-ask
"""


class GeminiAutomationError(Exception):
    """Base exception for Gemini automation errors"""
    pass


class ConnectionError(GeminiAutomationError):
    """Raised when connection to Chrome DevTools fails"""
    pass


class InteractionError(GeminiAutomationError):
    """Raised when interaction with Gemini interface fails"""
    pass


class TimeoutError(GeminiAutomationError):
    """Raised when operation times out"""
    pass


class ElementNotFoundError(GeminiAutomationError):
    """Raised when expected UI elements are not found"""
    pass