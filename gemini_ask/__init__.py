"""
gemini-ask Package

A Python package for asking questions to Google Gemini from the command line.
Provides both CLI interface and Python API for automating interactions with Gemini.
"""

from .gemini_automation import GeminiAutomation
from .chrome_launcher import ChromeLauncher
from .exceptions import GeminiAutomationError, ConnectionError, InteractionError, TimeoutError

__version__ = "3.0.0"
__author__ = "Ricardo de Azambuja"

__all__ = [
    "GeminiAutomation",
    "ChromeLauncher",
    "GeminiAutomationError", 
    "ConnectionError",
    "InteractionError",
    "TimeoutError"
]