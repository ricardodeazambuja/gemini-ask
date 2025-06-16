"""
Basic tests for Chrome Gemini Automation
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json

from gemini_ask import GeminiAutomation
from gemini_ask.exceptions import ConnectionError, InteractionError


class TestGeminiAutomation(unittest.TestCase):
    """Test cases for GeminiAutomation class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.gemini = GeminiAutomation()
    
    def test_init(self):
        """Test initialization"""
        self.assertEqual(self.gemini.devtools_port, 9222)
        self.assertEqual(self.gemini.host, "localhost")
        self.assertIsNone(self.gemini.ws)
        self.assertIsNone(self.gemini.gemini_tab_id)
    
    def test_custom_init(self):
        """Test initialization with custom parameters"""
        gemini = GeminiAutomation(devtools_port=9223, host="127.0.0.1")
        self.assertEqual(gemini.devtools_port, 9223)
        self.assertEqual(gemini.host, "127.0.0.1")
    
    @patch.object(GeminiAutomation, '_send_command')  # Mock command sending
    @patch('gemini_ask.gemini_automation.time.sleep')  # Mock sleep to prevent delays
    @patch('gemini_ask.gemini_automation.requests.get')
    @patch('gemini_ask.gemini_automation.websocket.create_connection')
    def test_connect_success(self, mock_websocket, mock_requests, mock_sleep, mock_send_command):
        """Test successful connection"""
        # Mock HTTP response with Gemini tab
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "id": "test-tab-id",
                "url": "https://gemini.google.com/app",
                "webSocketDebuggerUrl": "ws://localhost:9222/devtools/page/test-tab-id"
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_requests.return_value = mock_response
        
        # Mock WebSocket connection
        mock_ws = Mock()
        mock_websocket.return_value = mock_ws
        
        # Mock _send_command to return success
        mock_send_command.return_value = {"id": 1, "result": {}}
        
        # Disable auto-launch to simplify test
        self.gemini.auto_launch = False
        
        # Test connection
        result = self.gemini.connect()
        
        self.assertTrue(result)
        self.assertEqual(self.gemini.gemini_tab_id, "test-tab-id")
        self.assertIsNotNone(self.gemini.ws)
        
        # Verify essential commands were sent
        self.assertEqual(mock_send_command.call_count, 2)  # Runtime.enable and DOM.enable
        
        # Verify sleep was called (page load delay)
        mock_sleep.assert_called_with(3)
    
    @patch('gemini_ask.gemini_automation.requests.get')
    def test_connect_no_gemini_tab(self, mock_requests):
        """Test connection when no Gemini tab is found"""
        # Mock HTTP response without Gemini tab
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "id": "other-tab",
                "url": "https://google.com",
                "webSocketDebuggerUrl": "ws://localhost:9222/devtools/page/other-tab"
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_requests.return_value = mock_response
        
        # Test connection should raise exception
        with self.assertRaises(Exception):
            self.gemini.connect()
    
    def test_send_command_not_connected(self):
        """Test sending command when not connected"""
        with self.assertRaises(ConnectionError):
            self.gemini._send_command({"test": "command"})
    
    def test_context_manager(self):
        """Test context manager functionality"""
        with patch.object(self.gemini, 'close') as mock_close:
            with self.gemini as gemini_instance:
                self.assertIs(gemini_instance, self.gemini)
            mock_close.assert_called_once()
    
    def test_close(self):
        """Test close method"""
        # Mock WebSocket
        mock_ws = Mock()
        self.gemini.ws = mock_ws
        
        self.gemini.close()
        
        mock_ws.close.assert_called_once()
        self.assertIsNone(self.gemini.ws)


class TestExceptions(unittest.TestCase):
    """Test custom exceptions"""
    
    def test_exception_hierarchy(self):
        """Test exception inheritance"""
        from gemini_ask.exceptions import (
            GeminiAutomationError, ConnectionError, InteractionError
        )
        
        # Test inheritance
        self.assertTrue(issubclass(ConnectionError, GeminiAutomationError))
        self.assertTrue(issubclass(InteractionError, GeminiAutomationError))
        
        # Test instantiation
        base_error = GeminiAutomationError("Base error")
        conn_error = ConnectionError("Connection error")
        interact_error = InteractionError("Interaction error")
        
        self.assertEqual(str(base_error), "Base error")
        self.assertEqual(str(conn_error), "Connection error")
        self.assertEqual(str(interact_error), "Interaction error")


if __name__ == '__main__':
    unittest.main()