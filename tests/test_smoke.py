"""
Smoke tests for gemini-ask - Optional tests that use real Chrome
Run with: RUN_SMOKE_TESTS=1 python -m pytest tests/test_smoke.py
"""

import unittest
import os
import requests
import time

from gemini_ask import GeminiAutomation
from gemini_ask.exceptions import ConnectionError


@unittest.skipUnless(
    os.environ.get('RUN_SMOKE_TESTS') == '1',
    "Smoke tests require RUN_SMOKE_TESTS=1 environment variable"
)
class TestSmokeTests(unittest.TestCase):
    """
    Basic smoke tests using real Chrome instance
    
    Prerequisites:
    1. Chrome running with: chrome --remote-debugging-port=9222
    2. Open https://gemini.google.com in a tab
    3. Set environment: export RUN_SMOKE_TESTS=1
    4. Run: python -m pytest tests/test_smoke.py -v
    """
    
    @classmethod
    def setUpClass(cls):
        """Check if Chrome DevTools is available"""
        try:
            response = requests.get("http://localhost:9222/json", timeout=3)
            response.raise_for_status()
            tabs = response.json()
            
            # Check if Gemini tab exists
            gemini_tab_found = any(
                "gemini.google.com" in tab.get("url", "") 
                for tab in tabs
            )
            
            if not gemini_tab_found:
                raise unittest.SkipTest(
                    "No Gemini tab found. Please open https://gemini.google.com in Chrome"
                )
                
            cls.chrome_available = True
            
        except Exception as e:
            raise unittest.SkipTest(
                f"Chrome with remote debugging not available: {e}\n"
                f"Start Chrome with: chrome --remote-debugging-port=9222"
            )
    
    def setUp(self):
        """Set up for each test"""
        self.gemini = GeminiAutomation(auto_launch=False)  # Don't auto-launch for smoke tests
    
    def tearDown(self):
        """Clean up after each test"""
        if hasattr(self, 'gemini') and self.gemini:
            self.gemini.close()
    
    def test_basic_connection(self):
        """Test basic connection to Chrome and Gemini"""
        success = self.gemini.connect()
        self.assertTrue(success, "Should successfully connect to Chrome DevTools")
        self.assertIsNotNone(self.gemini.ws, "WebSocket should be established")
        self.assertIsNotNone(self.gemini.gemini_tab_id, "Gemini tab should be found")
    
    def test_page_text_retrieval(self):
        """Test retrieving page text from Gemini"""
        self.gemini.connect()
        
        page_text = self.gemini.get_page_text()
        self.assertIsInstance(page_text, str)
        self.assertGreater(len(page_text), 0, "Page should have content")
        
        # Should contain some Gemini-related content
        page_lower = page_text.lower()
        has_gemini_content = any(
            keyword in page_lower 
            for keyword in ['gemini', 'google', 'ai', 'chat', 'conversation']
        )
        self.assertTrue(has_gemini_content, "Page should contain Gemini-related content")
    
    def test_screenshot_capture(self):
        """Test taking a screenshot"""
        self.gemini.connect()
        
        screenshot_path = "/tmp/smoke_test_screenshot.png"
        
        # Clean up any existing file
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
        
        success = self.gemini.take_screenshot(screenshot_path)
        self.assertTrue(success, "Screenshot should be captured successfully")
        self.assertTrue(os.path.exists(screenshot_path), "Screenshot file should exist")
        
        # Check file is reasonable size
        file_size = os.path.getsize(screenshot_path)
        self.assertGreater(file_size, 1000, "Screenshot should be larger than 1KB")
        self.assertLess(file_size, 10 * 1024 * 1024, "Screenshot should be smaller than 10MB")
        
        # Clean up
        os.remove(screenshot_path)
    
    def test_chrome_status(self):
        """Test getting Chrome status information"""
        status = self.gemini.get_chrome_status()
        
        self.assertIsInstance(status, dict)
        self.assertIn("chrome_running", status)
        self.assertIn("devtools_port", status)
        self.assertIn("tabs_count", status)
        self.assertIn("gemini_tab_available", status)
        
        # These should be true for a working setup
        self.assertTrue(status["chrome_running"])
        self.assertEqual(status["devtools_port"], 9222)
        self.assertGreater(status["tabs_count"], 0)
        self.assertTrue(status["gemini_tab_available"])
    
    def test_simple_math_question(self):
        """Test asking a simple math question (LIVE TEST - sends real request)"""
        self.gemini.connect()
        
        question = "What is 2+2?"
        
        start_time = time.time()
        response = self.gemini.ask_question(question, timeout=30)  # Short timeout
        elapsed = time.time() - start_time
        
        # Validate response
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0, "Should get a non-empty response")
        
        # Response should contain the answer (4 or "four")
        response_lower = response.lower()
        has_answer = any(
            answer in response_lower 
            for answer in ['4', 'four', 'equals 4', '= 4', 'is 4']
        )
        self.assertTrue(has_answer, f"Response should contain answer: {response}")
        
        # Should complete reasonably quickly
        self.assertLess(elapsed, 30, f"Response took too long: {elapsed:.1f}s")
        
        print(f"\n✅ Math question answered in {elapsed:.1f}s: '{response}'")


@unittest.skipUnless(
    os.environ.get('RUN_EXTENDED_SMOKE_TESTS') == '1',
    "Extended smoke tests require RUN_EXTENDED_SMOKE_TESTS=1"
)
class TestExtendedSmokeTests(unittest.TestCase):
    """
    Extended smoke tests - more comprehensive but slower
    Only run when specifically requested
    """
    
    def setUp(self):
        """Set up for extended tests"""
        # Check Chrome availability
        try:
            response = requests.get("http://localhost:9222/json", timeout=3)
            response.raise_for_status()
        except:
            self.skipTest("Chrome not available for extended tests")
        
        self.gemini = GeminiAutomation(auto_launch=False)
    
    def tearDown(self):
        """Clean up after extended tests"""
        if hasattr(self, 'gemini'):
            self.gemini.close()
    
    def test_multiple_questions(self):
        """Test asking multiple questions in sequence"""
        self.gemini.connect()
        
        questions_and_keywords = [
            ("What is the capital of France?", ["paris"]),
            ("What color is the sky?", ["blue"]),
            ("How many days in a week?", ["7", "seven"]),
        ]
        
        for question, expected_keywords in questions_and_keywords:
            with self.subTest(question=question):
                response = self.gemini.ask_question(question, timeout=30)
                
                self.assertIsInstance(response, str)
                self.assertGreater(len(response), 0)
                
                response_lower = response.lower()
                has_expected = any(keyword in response_lower for keyword in expected_keywords)
                self.assertTrue(has_expected, f"Response should contain expected keywords: {response}")
                
                # Brief pause between questions
                time.sleep(1)


if __name__ == '__main__':
    # Print setup instructions
    print("=" * 60)
    print("SMOKE TEST SETUP INSTRUCTIONS")
    print("=" * 60)
    print("1. Start Chrome with remote debugging:")
    print("   chrome --remote-debugging-port=9222")
    print()
    print("2. Open Gemini in a Chrome tab:")
    print("   https://gemini.google.com")
    print()
    print("3. Run basic smoke tests:")
    print("   RUN_SMOKE_TESTS=1 python tests/test_smoke.py")
    print()
    print("4. Run extended smoke tests:")
    print("   RUN_EXTENDED_SMOKE_TESTS=1 python tests/test_smoke.py")
    print("=" * 60)
    print()
    
    unittest.main(verbosity=2)