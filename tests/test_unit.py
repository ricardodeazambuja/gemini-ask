"""
Unit tests for gemini-ask - Pure unit tests with no external dependencies
"""

import unittest
from unittest.mock import Mock, patch
import os

from gemini_ask import GeminiAutomation
from gemini_ask.exceptions import ConnectionError, InteractionError


class TestGeminiAutomationUnit(unittest.TestCase):
    """Pure unit tests for GeminiAutomation class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.gemini = GeminiAutomation()
    
    def test_init_default_values(self):
        """Test initialization with default values"""
        self.assertEqual(self.gemini.devtools_port, 9222)
        self.assertEqual(self.gemini.host, "localhost")
        self.assertEqual(self.gemini.devtools_url, "http://localhost:9222")
        self.assertTrue(self.gemini.auto_launch)
        self.assertFalse(self.gemini.headless)
        self.assertFalse(self.gemini.quiet)
        self.assertIsNone(self.gemini.ws)
        self.assertIsNone(self.gemini.gemini_tab_id)
    
    def test_init_custom_values(self):
        """Test initialization with custom values"""
        gemini = GeminiAutomation(
            devtools_port=9223,
            host="127.0.0.1",
            auto_launch=False,
            headless=True,
            quiet=True,
            screenshot_path="/tmp/test.png"
        )
        
        self.assertEqual(gemini.devtools_port, 9223)
        self.assertEqual(gemini.host, "127.0.0.1")
        self.assertEqual(gemini.devtools_url, "http://127.0.0.1:9223")
        self.assertFalse(gemini.auto_launch)
        self.assertTrue(gemini.headless)
        self.assertTrue(gemini.quiet)
        self.assertEqual(gemini.screenshot_path, "/tmp/test.png")
    
    def test_print_quiet_mode(self):
        """Test _print method in quiet mode"""
        gemini = GeminiAutomation(quiet=True)
        
        # Should not raise exception
        gemini._print("test message")
        gemini._print("test", "multiple", "args")
    
    def test_print_normal_mode(self):
        """Test _print method in normal mode"""
        with patch('builtins.print') as mock_print:
            self.gemini._print("test message")
            mock_print.assert_called_once_with("test message")
    
    def test_send_command_not_connected(self):
        """Test _send_command when not connected"""
        with self.assertRaises(ConnectionError) as cm:
            self.gemini._send_command({"method": "test"})
        
        self.assertIn("Not connected", str(cm.exception))
    
    def test_message_id_increment(self):
        """Test message ID incrementing"""
        self.assertEqual(self.gemini.message_id, 1)
        
        # Mock WebSocket for command sending
        mock_ws = Mock()
        mock_ws.recv.return_value = '{"id": 1, "result": {}}'
        self.gemini.ws = mock_ws
        
        # Send command
        command = {"method": "test"}
        self.gemini._send_command(command)
        
        # Message ID should increment
        self.assertEqual(self.gemini.message_id, 2)
    
    def test_canvas_prevention_system_prompt(self):
        """Test Canvas prevention system prompt generation"""
        default_prompt = self.gemini._get_system_prompt()
        self.assertIn("never start the canvas mode", default_prompt.lower())
        self.assertIn("normal text", default_prompt.lower())
    
    @patch.dict(os.environ, {'GEMINI_SYSTEM_PROMPT': 'Custom prompt from env'})
    def test_system_prompt_from_environment(self):
        """Test system prompt from environment variable"""
        prompt = self.gemini._get_system_prompt()
        self.assertEqual(prompt, "Custom prompt from env")
    
    def test_add_canvas_prevention_prompt(self):
        """Test adding Canvas prevention to question"""
        original_question = "What is 2+2?"
        modified_question = self.gemini._add_canvas_prevention_prompt(original_question)
        
        self.assertIn(original_question, modified_question)
        self.assertIn("never start the canvas mode", modified_question.lower())
    
    def test_validate_response_basic(self):
        """Test response validation with valid responses"""
        question = "What is 2+2?"
        
        # Valid responses
        self.assertTrue(self.gemini._validate_response("4", question))
        self.assertTrue(self.gemini._validate_response("The answer is 4", question))
        self.assertTrue(self.gemini._validate_response("2 + 2 equals 4", question))
    
    def test_validate_response_invalid(self):
        """Test response validation with invalid responses"""
        question = "What is 2+2?"
        
        # Invalid responses
        self.assertFalse(self.gemini._validate_response("", question))  # Empty
        self.assertFalse(self.gemini._validate_response("What is 2+2?", question))  # Same as question
        self.assertFalse(self.gemini._validate_response("loading", question))  # UI text
        self.assertFalse(self.gemini._validate_response("...", question))  # UI text
    
    def test_is_response_complete_math(self):
        """Test response completion detection for math questions"""
        question = "What is 2+2?"
        
        # Complete math responses
        self.assertTrue(self.gemini._is_response_complete("4", question))
        self.assertTrue(self.gemini._is_response_complete("The answer is 4.", question))
        self.assertTrue(self.gemini._is_response_complete("2 + 2 = 4", question))
        
        # Incomplete responses
        self.assertFalse(self.gemini._is_response_complete("", question))
        self.assertFalse(self.gemini._is_response_complete("What is 2+2?", question))
    
    def test_is_response_complete_general(self):
        """Test response completion detection for general questions"""
        question = "What is the capital of France?"
        
        # Complete responses
        self.assertTrue(self.gemini._is_response_complete("Paris", question))
        self.assertTrue(self.gemini._is_response_complete("The capital of France is Paris.", question))
        
        # Short factual answers should be accepted
        self.assertTrue(self.gemini._is_response_complete("Tokyo", "What is the capital of Japan?"))
    
    def test_clean_response_text(self):
        """Test response text cleaning"""
        question = "What is 2+2?"
        raw_response = "What is 2+2?  The answer is 4.  Copy code  Show thinking"
        
        cleaned = self.gemini._clean_response_text(raw_response, question)
        
        self.assertEqual(cleaned, "The answer is 4.")
        self.assertNotIn("Copy code", cleaned)
        self.assertNotIn("Show thinking", cleaned)
    
    def test_context_manager(self):
        """Test context manager functionality"""
        with patch.object(self.gemini, 'close') as mock_close:
            with self.gemini as gemini_instance:
                self.assertIs(gemini_instance, self.gemini)
            mock_close.assert_called_once()
    
    def test_close_with_websocket(self):
        """Test close method with active WebSocket"""
        mock_ws = Mock()
        self.gemini.ws = mock_ws
        
        self.gemini.close()
        
        mock_ws.close.assert_called_once()
        self.assertIsNone(self.gemini.ws)
    
    def test_close_without_websocket(self):
        """Test close method without WebSocket"""
        # Should not raise exception
        self.gemini.close()
        self.assertIsNone(self.gemini.ws)


class TestExceptions(unittest.TestCase):
    """Test custom exception classes"""
    
    def test_exception_inheritance(self):
        """Test exception class hierarchy"""
        from gemini_ask.exceptions import (
            GeminiAutomationError, ConnectionError, InteractionError, 
            TimeoutError, ElementNotFoundError
        )
        
        # Test inheritance
        self.assertTrue(issubclass(ConnectionError, GeminiAutomationError))
        self.assertTrue(issubclass(InteractionError, GeminiAutomationError))
        self.assertTrue(issubclass(TimeoutError, GeminiAutomationError))
        self.assertTrue(issubclass(ElementNotFoundError, GeminiAutomationError))
    
    def test_exception_messages(self):
        """Test exception message handling"""
        from gemini_ask.exceptions import ConnectionError, InteractionError
        
        conn_error = ConnectionError("Connection failed")
        interact_error = InteractionError("Interaction failed")
        
        self.assertEqual(str(conn_error), "Connection failed")
        self.assertEqual(str(interact_error), "Interaction failed")


if __name__ == '__main__':
    unittest.main(verbosity=2)