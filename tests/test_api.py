"""
API contract tests for gemini-ask - Tests public API methods with minimal mocking
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import base64

from gemini_ask import GeminiAutomation
from gemini_ask.exceptions import ConnectionError, InteractionError, TimeoutError


class TestGeminiAutomationAPI(unittest.TestCase):
    """Test public API methods with controlled mocking"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.gemini = GeminiAutomation(auto_launch=False)  # Disable auto-launch for tests
    
    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self.gemini, 'ws') and self.gemini.ws:
            self.gemini.close()
    
    @patch('gemini_ask.gemini_automation.websocket.create_connection')
    @patch('gemini_ask.gemini_automation.requests.get')
    @patch('gemini_ask.gemini_automation.time.sleep')
    def test_connect_success(self, mock_sleep, mock_requests, mock_websocket):
        """Test successful connection to Chrome DevTools"""
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
        mock_ws.recv.side_effect = [
            '{"id": 1, "result": {}}',  # Runtime.enable
            '{"id": 2, "result": {}}'   # DOM.enable
        ]
        mock_websocket.return_value = mock_ws
        
        # Test connection
        result = self.gemini.connect()
        
        self.assertTrue(result)
        self.assertEqual(self.gemini.gemini_tab_id, "test-tab-id")
        self.assertIsNotNone(self.gemini.ws)
        
        # Verify essential setup calls
        mock_requests.assert_called_once()
        mock_websocket.assert_called_once()
        mock_sleep.assert_called_with(3)  # Page load delay
    
    @patch('gemini_ask.gemini_automation.requests.get')
    def test_connect_no_chrome(self, mock_requests):
        """Test connection failure when Chrome is not running"""
        mock_requests.side_effect = Exception("Connection refused")
        
        with self.assertRaises(ConnectionError) as cm:
            self.gemini.connect()
        
        self.assertIn("Connection error", str(cm.exception))
    
    @patch('gemini_ask.gemini_automation.requests.get')
    def test_connect_no_gemini_tab(self, mock_requests):
        """Test connection when no Gemini tab is open"""
        # Mock response with no Gemini tabs
        mock_response = Mock()
        mock_response.json.return_value = [
            {"id": "tab1", "url": "https://google.com"},
            {"id": "tab2", "url": "https://youtube.com"}
        ]
        mock_response.raise_for_status.return_value = None
        mock_requests.return_value = mock_response
        
        with self.assertRaises(Exception):  # Should raise ElementNotFoundError
            self.gemini.connect()
    
    def test_ask_question_not_connected(self):
        """Test ask_question when not connected"""
        with self.assertRaises(ConnectionError) as cm:
            self.gemini.ask_question("What is 2+2?")
        
        self.assertIn("Not connected", str(cm.exception))
    
    @patch.object(GeminiAutomation, 'wait_for_response_smart')
    @patch.object(GeminiAutomation, 'wait_for_element')
    @patch.object(GeminiAutomation, '_send_command')
    def test_ask_question_success(self, mock_send_command, mock_wait_element, mock_wait_response):
        """Test successful question asking"""
        # Set up connected state
        self.gemini.ws = Mock()
        
        # Mock finding input field
        mock_wait_element.return_value = 123  # Mock node ID
        
        # Mock successful response
        mock_wait_response.return_value = "The answer is 4."
        
        # Mock send_command responses
        mock_send_command.return_value = {"id": 1, "result": {}}
        
        # Test asking question
        response = self.gemini.ask_question("What is 2+2?", timeout=30)
        
        self.assertEqual(response, "The answer is 4.")
        
        # Verify the flow
        mock_wait_element.assert_called()  # Input field search
        mock_wait_response.assert_called_once()  # Response waiting
        
        # Verify typing and submission commands were sent
        self.assertGreater(mock_send_command.call_count, 5)  # Focus + typing + enter
    
    @patch.object(GeminiAutomation, 'wait_for_response_smart')
    @patch.object(GeminiAutomation, 'wait_for_element')
    def test_ask_question_no_input_field(self, mock_wait_element, mock_wait_response):
        """Test ask_question when input field not found"""
        # Set up connected state
        self.gemini.ws = Mock()
        
        # Mock input field not found
        mock_wait_element.return_value = None
        
        with self.assertRaises(InteractionError) as cm:
            self.gemini.ask_question("What is 2+2?")
        
        self.assertIn("Could not find input field", str(cm.exception))
    
    @patch.object(GeminiAutomation, 'wait_for_response_smart')
    @patch.object(GeminiAutomation, 'wait_for_element')
    @patch.object(GeminiAutomation, '_send_command')
    def test_ask_question_timeout(self, mock_send_command, mock_wait_element, mock_wait_response):
        """Test ask_question timeout"""
        # Set up connected state
        self.gemini.ws = Mock()
        mock_wait_element.return_value = 123  # Mock node ID
        mock_send_command.return_value = {"id": 1, "result": {}}
        
        # Mock timeout - no response
        mock_wait_response.return_value = None
        
        with self.assertRaises(TimeoutError) as cm:
            self.gemini.ask_question("What is 2+2?", timeout=5)
        
        self.assertIn("No response received within 5 seconds", str(cm.exception))
    
    def test_take_screenshot_not_connected(self):
        """Test take_screenshot when not connected"""
        result = self.gemini.take_screenshot("/tmp/test.png")
        self.assertFalse(result)
    
    @patch.object(GeminiAutomation, '_send_command')
    @patch('builtins.open', create=True)
    def test_take_screenshot_success(self, mock_open, mock_send_command):
        """Test successful screenshot capture"""
        # Set up connected state
        self.gemini.ws = Mock()
        
        # Mock screenshot response
        screenshot_data = base64.b64encode(b"fake-png-data").decode()
        mock_send_command.return_value = {
            "result": {"data": screenshot_data}
        }
        
        # Mock file operations
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        result = self.gemini.take_screenshot("/tmp/test.png")
        
        self.assertTrue(result)
        mock_send_command.assert_called_once_with({
            "method": "Page.captureScreenshot",
            "params": {"format": "png"}
        })
        mock_file.write.assert_called_once_with(b"fake-png-data")
    
    @patch.object(GeminiAutomation, '_send_command')
    def test_take_screenshot_failure(self, mock_send_command):
        """Test screenshot capture failure"""
        # Set up connected state
        self.gemini.ws = Mock()
        
        # Mock failed response
        mock_send_command.return_value = {"result": {}}  # No data field
        
        result = self.gemini.take_screenshot("/tmp/test.png")
        self.assertFalse(result)
    
    def test_get_page_text_not_connected(self):
        """Test get_page_text when not connected"""
        with self.assertRaises(ConnectionError):
            self.gemini.get_page_text()
    
    @patch.object(GeminiAutomation, '_send_command')
    def test_get_page_text_success(self, mock_send_command):
        """Test successful page text retrieval"""
        # Set up connected state
        self.gemini.ws = Mock()
        
        # Mock page text response
        mock_send_command.return_value = {
            "result": {"result": {"value": "Hello, this is the page text."}}
        }
        
        result = self.gemini.get_page_text()
        
        self.assertEqual(result, "Hello, this is the page text.")
        mock_send_command.assert_called_once_with({
            "method": "Runtime.evaluate",
            "params": {
                "expression": "document.body.innerText",
                "returnByValue": True
            }
        })
    
    @patch.object(GeminiAutomation, '_send_command')
    def test_get_page_text_empty(self, mock_send_command):
        """Test page text retrieval with empty result"""
        # Set up connected state
        self.gemini.ws = Mock()
        
        # Mock empty response
        mock_send_command.return_value = {"result": {}}
        
        result = self.gemini.get_page_text()
        self.assertEqual(result, "")
    
    @patch('gemini_ask.gemini_automation.requests.get')
    def test_get_chrome_status_no_launcher(self, mock_requests):
        """Test Chrome status without launcher"""
        # Disable auto-launch
        self.gemini.chrome_launcher = None
        
        # Mock successful Chrome connection
        mock_response = Mock()
        mock_response.json.return_value = [
            {"url": "https://gemini.google.com/app"},
            {"url": "https://google.com"}
        ]
        mock_requests.return_value = mock_response
        
        status = self.gemini.get_chrome_status()
        
        self.assertTrue(status["chrome_running"])
        self.assertEqual(status["devtools_port"], 9222)
        self.assertEqual(status["tabs_count"], 2)
        self.assertTrue(status["gemini_tab_available"])
        self.assertFalse(status["auto_launch_enabled"])
    
    @patch('gemini_ask.gemini_automation.requests.get')
    def test_get_chrome_status_not_running(self, mock_requests):
        """Test Chrome status when Chrome is not running"""
        # Disable auto-launch
        self.gemini.chrome_launcher = None
        
        # Mock connection failure
        mock_requests.side_effect = Exception("Connection refused")
        
        status = self.gemini.get_chrome_status()
        
        self.assertFalse(status["chrome_running"])
        self.assertEqual(status["devtools_port"], 9222)
        self.assertFalse(status["auto_launch_enabled"])
    
    def test_close_with_screenshot(self):
        """Test close method with screenshot path"""
        # Set up state
        self.gemini.screenshot_path = "/tmp/final.png"
        self.gemini.ws = Mock()
        
        with patch.object(self.gemini, 'take_screenshot', return_value=True) as mock_screenshot:
            self.gemini.close()
            
            mock_screenshot.assert_called_once_with("/tmp/final.png")
            self.assertIsNone(self.gemini.ws)
    
    def test_close_cleanup_chrome(self):
        """Test close method with Chrome cleanup"""
        # Set up state
        mock_launcher = Mock()
        self.gemini.chrome_launcher = mock_launcher
        self.gemini.ws = Mock()
        
        self.gemini.close(cleanup_chrome=True)
        
        mock_launcher.cleanup.assert_called_once()
        self.assertIsNone(self.gemini.ws)


if __name__ == '__main__':
    unittest.main(verbosity=2)