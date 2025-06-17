"""
Main automation module for interacting with Google Gemini through Chrome DevTools Protocol

This implementation uses smart DOM navigation to reliably find responses:
1. Detects page changes after submission
2. Finds the question element in the conversation
3. Navigates to the response element that follows
4. Extracts clean response text

Based on the insight that Gemini shows question-answer pairs in sequence.
"""

import websocket
import json
import time
import requests
import re
from typing import Dict, List, Optional, Tuple
from .exceptions import ConnectionError, InteractionError, TimeoutError, ElementNotFoundError
from .chrome_launcher import ChromeLauncher


class GeminiAutomation:
    """
    Automate interactions with Google Gemini through Chrome DevTools Protocol
    
    This class provides methods to connect to a Chrome browser instance running with
    remote debugging enabled, find the Gemini tab, and interact with it using
    realistic keyboard and mouse simulation.
    
    Uses smart DOM navigation to reliably find responses:
    - Detects page changes after submission
    - Finds the question element in the conversation  
    - Navigates to the response element that follows
    - Extracts clean response text
    
    Can automatically launch Chrome if not already running.
    """
    
    def __init__(self, devtools_port: int = 9222, host: str = "localhost", 
                 auto_launch: bool = True, headless: bool = False, 
                 user_data_dir: Optional[str] = None, screenshot_path: Optional[str] = None,
                 quiet: bool = False, typing_speed: float = 0.05, minimized: bool = False):
        """
        Initialize the Gemini automation client
        
        Args:
            devtools_port: Port number where Chrome DevTools is running (default: 9222)
            host: Host address for Chrome DevTools (default: localhost)
            auto_launch: Whether to automatically launch Chrome if not running (default: True)
            headless: Whether to run Chrome in headless mode (default: False)
            user_data_dir: Custom user data directory for Chrome (default: temp dir)
            screenshot_path: Optional path to save screenshot before closing (default: None)
            quiet: Whether to suppress all output (default: False)
        """
        self.devtools_port = devtools_port
        self.host = host
        self.devtools_url = f"http://{host}:{devtools_port}"
        self.auto_launch = auto_launch
        self.headless = headless
        self.screenshot_path = screenshot_path
        self.quiet = quiet
        self.typing_speed = max(0.001, min(5.0, typing_speed))
        self.minimized = minimized
        self.ws = None
        self.gemini_tab_id = None
        self.gemini_ws_url = None
        
        # Sequential message ID management
        self.message_id = 1
        
        # Chrome launcher for auto-launch functionality
        self.chrome_launcher = ChromeLauncher(
            devtools_port=devtools_port,
            user_data_dir=user_data_dir,
            quiet=quiet
        ) if auto_launch else None
    
    def _print(self, *args, **kwargs):
        """Print message only if not in quiet mode"""
        if not self.quiet:
            print(*args, **kwargs)
        
    def connect(self) -> bool:
        """Connect to Chrome DevTools and find the Gemini tab"""
        try:
            # Try to connect to existing Chrome instance
            try:
                response = requests.get(f"{self.devtools_url}/json", timeout=2)
                response.raise_for_status()
                tabs = response.json()
                chrome_available = True
            except (requests.RequestException, requests.Timeout):
                chrome_available = False
            
            # Auto-launch Chrome if not available
            if not chrome_available and self.auto_launch and self.chrome_launcher:
                self._print("Chrome not found, auto-launching...")
                launch_success = self.chrome_launcher.launch_chrome(
                    open_gemini=True, 
                    headless=self.headless
                )
                
                if not launch_success:
                    raise ConnectionError("Failed to auto-launch Chrome")
                
                # Get tabs after launch
                response = requests.get(f"{self.devtools_url}/json")
                response.raise_for_status()
                tabs = response.json()
            
            elif not chrome_available:
                raise ConnectionError(
                    f"Chrome DevTools not accessible on port {self.devtools_port}. "
                    f"Please start Chrome with: chrome --remote-debugging-port={self.devtools_port} "
                    f"or enable auto_launch=True"
                )
            
            # Find Gemini tab
            gemini_tab = None
            for tab in tabs:
                if "gemini.google.com" in tab.get("url", ""):
                    gemini_tab = tab
                    break
            
            # If no Gemini tab found, try to open one
            if not gemini_tab:
                if self.auto_launch and self.chrome_launcher:
                    print("No Gemini tab found, opening new tab...")
                    if self.chrome_launcher.open_gemini_tab():
                        # Refresh tabs list
                        response = requests.get(f"{self.devtools_url}/json")
                        response.raise_for_status()
                        tabs = response.json()
                        
                        # Find the newly opened Gemini tab
                        for tab in tabs:
                            if "gemini.google.com" in tab.get("url", ""):
                                gemini_tab = tab
                                break
                
                if not gemini_tab:
                    raise ElementNotFoundError(
                        "No Gemini tab found. Please open gemini.google.com in Chrome "
                        "or enable auto_launch=True"
                    )
            
            self.gemini_tab_id = gemini_tab["id"]
            self.gemini_ws_url = gemini_tab["webSocketDebuggerUrl"]
            
            # Connect to the tab via WebSocket
            self.ws = websocket.create_connection(self.gemini_ws_url)
            
            # Enable essential domains
            self._send_command({"method": "Runtime.enable"})
            self._send_command({"method": "DOM.enable"})
            
            # Minimize window if requested
            if self.minimized:
                self._minimize_window()
            
            # Simple wait for page readiness
            self._print("⏳ Giving page time to load...")
            time.sleep(3)
            
            self._print("✅ Connected to Gemini tab successfully!")
            return True
            
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to connect to Chrome DevTools: {e}")
        except Exception as e:
            raise ConnectionError(f"Connection error: {e}")
    
    def _send_command(self, command: Dict) -> Dict:
        """Send command to Chrome DevTools with sequential message IDs"""
        if not self.ws:
            raise ConnectionError("Not connected to Chrome DevTools")
        
        # Use sequential message ID
        if 'id' not in command:
            command['id'] = self.message_id
            self.message_id += 1
        
        command_id = command['id']
        self.ws.send(json.dumps(command))
        
        # Keep reading until we get our command response
        while True:
            response_str = self.ws.recv()
            response = json.loads(response_str)
            
            # Check if this is our command response
            if 'id' in response and response['id'] == command_id:
                return response
            
            # Otherwise it's an event, continue reading
    
    def _minimize_window(self):
        """Minimize the browser window using Chrome DevTools Protocol"""
        try:
            # Enable Browser domain
            self._send_command({"method": "Browser.enable"})
            
            # Get window ID for current target
            window_response = self._send_command({
                "method": "Browser.getWindowForTarget",
                "params": {}
            })
            
            # Extract window ID and minimize
            window_id = window_response['result']['windowId']
            self._send_command({
                "method": "Browser.setWindowBounds",
                "params": {
                    "windowId": window_id,
                    "bounds": {
                        "windowState": "minimized"
                    }
                }
            })
        except Exception:
            # Don't fail if minimization fails
            pass
    
    def wait_for_element(self, selector: str, timeout: int = 10) -> Optional[int]:
        """Wait for element to appear using DOM polling"""
        print(f"Waiting up to {timeout}s for element: '{selector}'")
        try:
            # Get document root
            doc_result = self._send_command({"method": "DOM.getDocument", "params": {"depth": -1}})
            root_node_id = doc_result.get('result', {}).get('root', {}).get('nodeId')
            
            if not root_node_id:
                print("Could not get document root")
                return None
            
            # Poll for element  
            for _ in range(timeout * 5):  # 5 checks per second
                query_result = self._send_command({
                    "method": "DOM.querySelector",
                    "params": {
                        "nodeId": root_node_id,
                        "selector": selector
                    }
                })
                node_id = query_result.get('result', {}).get('nodeId')
                
                if node_id:
                    print("Element found!")
                    return node_id
                
                time.sleep(0.2)
            
            print("Timed out waiting for element")
            return None
            
        except Exception as e:
            print(f"Error waiting for element: {e}")
            return None
    
    def _detect_page_change(self, timeout: int = 30) -> bool:
        """
        Phase 1: Wait for DOM changes after question submission.
        Simplified approach that doesn't depend on specific element detection.
        """
        print("🔍 Waiting for DOM changes after question submission...")
        
        # Simple approach: wait for any significant DOM changes and text content growth
        page_change_detector_js = f"""
new Promise((resolve) => {{
    let timeoutId = setTimeout(() => {{
        console.log('Timeout waiting for page change');
        resolve(false);
    }}, {timeout * 1000});
    
    let initialTextLength = document.body.textContent.length;
    let changeDetected = false;
    let checkCount = 0;
    
    function checkForChanges() {{
        checkCount++;
        const currentTextLength = document.body.textContent.length;
        const textGrowth = currentTextLength - initialTextLength;
        
        console.log(`Check ${{checkCount}}: text length ${{currentTextLength}} (growth: ${{textGrowth}})`);
        
        // Look for substantial text growth (indicating new content like a response)
        if (textGrowth > 10 && !changeDetected) {{
            console.log('Significant text growth detected, waiting for stabilization...');
            changeDetected = true;
            
            // Wait a bit more for content to stabilize
            setTimeout(() => {{
                console.log('Content stabilization period complete');
                clearTimeout(timeoutId);
                resolve(true);
            }}, 3000);
        }}
        
        // Also check for conversation elements as backup
        const userQuery = document.querySelector('user-query');
        const hasConversation = userQuery && userQuery.textContent.length > 0;
        
        if (hasConversation && !changeDetected) {{
            console.log('Conversation elements detected');
            changeDetected = true;
            setTimeout(() => {{
                clearTimeout(timeoutId);
                resolve(true);
            }}, 2000);
        }}
    }}
    
    // Check immediately
    checkForChanges();
    
    // Then check periodically
    const interval = setInterval(() => {{
        if (!changeDetected) {{
            checkForChanges();
        }} else {{
            clearInterval(interval);
        }}
    }}, 1000);
    
    // Also set up mutation observer for immediate detection
    const observer = new MutationObserver(() => {{
        if (!changeDetected) {{
            checkForChanges();
        }}
    }});
    
    observer.observe(document.body, {{
        childList: true,
        subtree: true
    }});
}})
        """
        
        try:
            response = self._send_command({
                "method": "Runtime.evaluate",
                "params": {
                    "expression": page_change_detector_js,
                    "awaitPromise": True,
                    "timeout": timeout * 1000
                }
            })
            
            if "result" in response and "result" in response["result"]:
                result = response["result"]["result"]["value"]
                if result:
                    print("✅ Complete conversation detected!")
                    return True
                else:
                    print("❌ Complete conversation not detected within timeout")
                    return False
            else:
                print("❌ Response detection failed")
                return False
                
        except Exception as e:
            print(f"❌ Response detection error: {e}")
            return False
    
    def _find_question_element(self, question: str) -> Optional[int]:
        """
        Phase 2: Find the DOM element containing our specific question
        This gives us a reliable anchor point in the conversation
        """
        print(f"🔍 Searching for question element: '{question[:50]}...'")
        
        find_question_js = f"""
(() => {{
    const questionText = {json.dumps(question)};
    
    // Search through all text-containing elements
    const allElements = document.querySelectorAll('*');
    let candidates = [];
    
    for (const element of allElements) {{
        const text = element.textContent || element.innerText || '';
        
        // Check if this element contains our exact question
        if (text.trim() === questionText.trim()) {{
            console.log('Found exact question match:', element);
            return element;
        }}
        
        // Collect elements that contain the question
        if (text.includes(questionText)) {{
            candidates.push({{
                element: element,
                textLength: text.length,
                tag: element.tagName
            }});
        }}
    }}
    
    if (candidates.length > 0) {{
        // Sort by text length (prefer shorter elements - more specific)
        candidates.sort((a, b) => a.textLength - b.textLength);
        
        // Find the smallest element that's still reasonable
        for (const candidate of candidates) {{
            if (candidate.textLength < questionText.length * 10) {{ // Not too big
                console.log('Selected question container:', candidate.tag, 'with', candidate.textLength, 'chars');
                return candidate.element;
            }}
        }}
        
        // If all candidates are huge, take the smallest one anyway
        console.log('All candidates are large, using smallest:', candidates[0].tag, 'with', candidates[0].textLength, 'chars');
        return candidates[0].element;
    }}
    
    console.log('Question element not found');
    return null;
}})()
        """
        
        try:
            response = self._send_command({
                "method": "Runtime.evaluate",
                "params": {
                    "expression": find_question_js,
                    "returnByValue": False  # Return object reference
                }
            })
            
            if "result" in response and "result" in response["result"]:
                # Get object ID of the element
                object_id = response["result"]["result"].get("objectId")
                if object_id:
                    # Convert object to node ID
                    node_response = self._send_command({
                        "method": "DOM.requestNode",
                        "params": {"objectId": object_id}
                    })
                    
                    node_id = node_response.get("result", {}).get("nodeId")
                    if node_id:
                        print(f"✅ Found question element with node ID: {node_id}")
                        return node_id
            
            print("❌ Question element not found")
            return None
                
        except Exception as e:
            print(f"❌ Error finding question element: {e}")
            return None
    
    
    def wait_for_response_smart(self, question: str, timeout: int = 180) -> Optional[str]:
        """
        Smart response detection using DOM structure navigation with dynamic completion detection
        
        Phase 1: Detect page change after submission
        Phase 2: Find question element in DOM  
        Phase 3: Find response element location
        Phase 4: Monitor response completion dynamically
        Phase 5: Extract clean response text
        """
        print("🧠 Using smart response detection with dynamic completion...")
        
        # Phase 1: Wait for page to change after submission
        if not self._detect_page_change(30):  # Keep shorter timeout for initial detection
            print("❌ No page change detected - response may not have appeared")
            return None
        
        # Give a moment for content to start rendering
        time.sleep(2)
        
        # Phase 2: Find the question element
        question_node_id = self._find_question_element(question)
        if not question_node_id:
            print("❌ Could not find question element in conversation")
            return None
        
        # Phase 3: Find response element location (but don't extract yet)
        response_node_id = self._find_response_element(question_node_id)
        if not response_node_id:
            print("❌ Could not find response element after question")
            return None
        
        # Debug: Analyze what we actually found
        print(f"🔍 Debug: Question node {question_node_id} vs Response node {response_node_id}")
        question_text_debug = self._get_element_text(question_node_id)
        response_text_debug = self._get_element_text(response_node_id)
        print(f"🔍 Debug: Question node text: '{question_text_debug[:100]}...'")
        print(f"🔍 Debug: Response node text: '{response_text_debug[:100]}...'")
        
        if response_node_id == question_node_id:
            print("❌ Critical error: Response node ID same as question node ID")
            return None
        
        # Phase 4: Monitor response completion dynamically
        final_response = self._monitor_response_completion(response_node_id, question, timeout)
        if not final_response:
            print("❌ Could not get complete response")
            return None
        
        # Phase 5: Clean and validate final response
        cleaned_response = self._clean_response_text(final_response, question)
        print(f"🔍 Debug: Raw response length: {len(final_response)}")
        print(f"🔍 Debug: Raw response: '{final_response[:200]}{'...' if len(final_response) > 200 else ''}'")
        print(f"🔍 Debug: Cleaned response: '{cleaned_response[:200]}{'...' if len(cleaned_response) > 200 else ''}'")
        
        if self._validate_response(cleaned_response, question):
            return cleaned_response
        else:
            print("❌ Response validation failed")
            return None
    
    def _clean_response_text(self, raw_text: str, question: str = "") -> str:
        """Extract response from conversation container by removing question part"""
        if not raw_text:
            return ""
        
        # Clean up the raw text
        cleaned = re.sub(r'\s+', ' ', raw_text.strip())
        
        # Remove the question part if provided
        if question:
            question_clean = re.sub(r'\s+', ' ', question.strip())
            # Try to find and remove the question from the beginning
            if cleaned.startswith(question_clean):
                cleaned = cleaned[len(question_clean):].strip()
            else:
                # Try to find question anywhere and remove it
                cleaned = cleaned.replace(question_clean, "", 1).strip()
        
        # Remove common UI elements that might appear
        ui_elements = [
            "Show thinking",
            "Copy code",
            "Copy",
            "Gemini can make mistakes, so double-check it"
        ]
        
        for element in ui_elements:
            cleaned = cleaned.replace(element, "").strip()
        
        return cleaned
    
    def _walk_up_dom_tree(self, start_node_id: int, question_length: int) -> Optional[int]:
        """
        Walk up the DOM tree from question element to find common parent based on text length.
        
        The algorithm:
        1. Start from question element (should contain only question text)
        2. Walk up parent chain, checking text length at each level
        3. First element with text significantly longer than question = common parent
        4. This common parent should contain both question and answer
        
        Args:
            start_node_id: Node ID of the question element
            question_length: Length of the question text for comparison
            
        Returns:
            Node ID of common parent, or None if not found
        """
        print(f"🌲 Walking up DOM tree from node {start_node_id}, question length: {question_length}")
        
        current_node_id = start_node_id
        level = 0
        max_levels = 10  # Safety limit
        
        while current_node_id and level < max_levels:
            try:
                # Get text content of current element
                text_content = self._get_element_text(current_node_id)
                text_length = len(text_content) if text_content else 0
                
                # Get element info for debugging
                element_info = self._get_element_info(current_node_id)
                tag_name = element_info.get('tag', 'unknown')
                classes = element_info.get('classes', [])
                
                print(f"  Level {level}: <{tag_name}> classes={classes} text_length={text_length}")
                
                # Special case: Check if this is already a conversation container
                class_names = ' '.join(classes).lower()
                if any(keyword in class_names for keyword in ['chat-history', 'conversation', 'chat-container']):
                    print(f"  🎯 Found conversation container at level {level}: <{tag_name}> with classes {classes}")
                    
                    # Verify this element contains both question and answer
                    if self._verify_common_parent(current_node_id, question_length):
                        print(f"  ✅ Confirmed conversation container as common parent")
                        return current_node_id
                    else:
                        print(f"  ⚠️  Conversation container found but verification failed")
                
                # Check if this could be the common parent based on text length
                if text_length > question_length * 1.2:  # At least 20% more text
                    print(f"  ✅ Found potential common parent at level {level}: {text_length} chars > {question_length} chars")
                    
                    # Verify this element contains both question and answer by checking for response elements
                    if self._verify_common_parent(current_node_id, question_length):
                        print(f"  🎯 Confirmed common parent: <{tag_name}> with {text_length} chars")
                        return current_node_id
                    else:
                        print(f"  ⚠️  Element has more text but doesn't appear to contain answer, continuing...")
                
                # Try to get parent using alternative method since parentId may not be available
                parent_node_id = self._get_parent_node_id_alternative(current_node_id)
                if not parent_node_id:
                    print(f"  🏁 No parent found at level {level}")
                    break
                
                current_node_id = parent_node_id
                level += 1
                
            except Exception as e:
                print(f"  ❌ Error at level {level}: {e}")
                break
        
        print(f"❌ Could not find common parent after walking {level} levels")
        return None
    
    def _get_element_info(self, node_id: int) -> dict:
        """Get basic information about a DOM element"""
        try:
            # Get element description
            desc_response = self._send_command({
                "method": "DOM.describeNode",
                "params": {"nodeId": node_id}
            })
            
            if "result" in desc_response and "node" in desc_response["result"]:
                node_info = desc_response["result"]["node"]
                return {
                    "tag": node_info.get("localName", "unknown"),
                    "classes": [attr["value"] for attr in node_info.get("attributes", []) 
                               if attr.get("name") == "class"],
                    "node_type": node_info.get("nodeType", 0)
                }
            
            return {"tag": "unknown", "classes": [], "node_type": 0}
            
        except Exception:
            return {"tag": "unknown", "classes": [], "node_type": 0}
    
    def _get_parent_node_id(self, node_id: int) -> Optional[int]:
        """Get the parent node ID of a given node"""
        try:
            # Get node description which includes parent info
            desc_response = self._send_command({
                "method": "DOM.describeNode", 
                "params": {"nodeId": node_id}
            })
            
            if "result" in desc_response and "node" in desc_response["result"]:
                node_info = desc_response["result"]["node"]
                parent_id = node_info.get("parentId")
                return parent_id if parent_id and parent_id != 0 else None
            
            return None
            
        except Exception as e:
            return None
    
    def _get_parent_node_id_alternative(self, node_id: int) -> Optional[int]:
        """Alternative method to get parent node using JavaScript DOM traversal"""
        try:
            # Resolve the node to get JavaScript object
            resolve_response = self._send_command({
                "method": "DOM.resolveNode",
                "params": {"nodeId": node_id}
            })
            
            object_id = resolve_response.get("result", {}).get("object", {}).get("objectId")
            if not object_id:
                return None
            
            # Use JavaScript to get parent element
            parent_js = """
            function() {
                return this.parentElement;
            }
            """
            
            parent_response = self._send_command({
                "method": "Runtime.callFunctionOn",
                "params": {
                    "objectId": object_id,
                    "functionDeclaration": parent_js,
                    "returnByValue": False
                }
            })
            
            if "result" in parent_response and "result" in parent_response["result"]:
                parent_object_id = parent_response["result"]["result"].get("objectId")
                if parent_object_id:
                    # Convert back to node ID
                    node_response = self._send_command({
                        "method": "DOM.requestNode",
                        "params": {"objectId": parent_object_id}
                    })
                    
                    return node_response.get("result", {}).get("nodeId")
            
            return None
            
        except Exception as e:
            print(f"    ❌ Alternative parent method failed: {e}")
            return None
    
    def _verify_common_parent(self, parent_node_id: int, question_length: int) -> bool:
        """
        Verify that this element is indeed the common parent by checking:
        1. It contains response-related elements (model-response, etc.)
        2. Total text length suggests it contains both question and answer
        """
        try:
            # Look for response elements within this parent
            verify_js = """
            function() {
                // Look for Gemini's response element patterns
                const responseElements = this.querySelectorAll(
                    'model-response, [class*="model-response"], [class*="response"], message-content'
                );
                
                const hasResponseElements = responseElements.length > 0;
                let responseTextLength = 0;
                
                if (hasResponseElements) {
                    for (const el of responseElements) {
                        const text = el.textContent || '';
                        responseTextLength += text.length;
                    }
                }
                
                return {
                    hasResponseElements: hasResponseElements,
                    responseCount: responseElements.length,
                    responseTextLength: responseTextLength,
                    totalTextLength: (this.textContent || '').length
                };
            }
            """
            
            # Get parent element object
            resolve_response = self._send_command({
                "method": "DOM.resolveNode",
                "params": {"nodeId": parent_node_id}
            })
            
            parent_object_id = resolve_response.get("result", {}).get("object", {}).get("objectId")
            if not parent_object_id:
                return False
            
            # Run verification
            verify_response = self._send_command({
                "method": "Runtime.callFunctionOn",
                "params": {
                    "objectId": parent_object_id,
                    "functionDeclaration": verify_js,
                    "returnByValue": True
                }
            })
            
            if "result" in verify_response and "result" in verify_response["result"]:
                result = verify_response["result"]["result"]["value"]
                
                has_response = result.get("hasResponseElements", False)
                response_count = result.get("responseCount", 0)
                response_text_length = result.get("responseTextLength", 0)
                total_length = result.get("totalTextLength", 0)
                
                print(f"    🔍 Verification: response_elements={has_response}, count={response_count}")
                print(f"    🔍 Text lengths: response={response_text_length}, total={total_length}, question={question_length}")
                
                # Good indicators of a common parent:
                # 1. Contains response elements
                # 2. Total text length is roughly question + response
                if has_response and response_count > 0:
                    return True
                
                # Alternative: text length suggests combined content
                if total_length > question_length and total_length < question_length * 3:
                    print(f"    💡 No response elements found but text length suggests common parent")
                    return True
            
            return False
            
        except Exception as e:
            print(f"    ❌ Verification error: {e}")
            return False

    def _find_response_element(self, question_node_id: int) -> Optional[int]:
        """
        Phase 3: Find response element using DOM tree walking approach
        
        New algorithm based on hypothesis:
        1. Walk up DOM tree from question element
        2. Find common parent based on text length analysis  
        3. Within common parent, locate the response element
        
        Returns the node ID of the response container for monitoring
        """
        print(f"🔍 Finding response element using tree-walking approach from question {question_node_id}...")
        
        # First, get the question text length for comparison
        question_text = self._get_element_text(question_node_id)
        question_length = len(question_text) if question_text else 0
        
        if question_length == 0:
            print("❌ Question element has no text content")
            return None
        
        print(f"📏 Question text length: {question_length} chars")
        
        # Walk up DOM tree to find common parent
        common_parent_id = self._walk_up_dom_tree(question_node_id, question_length)
        if not common_parent_id:
            print("❌ Could not find common parent using tree walking")
            return None
        
        # Find response element within the common parent
        response_node_id = self._find_response_within_parent(common_parent_id)
        if not response_node_id:
            print("❌ Could not find response element within common parent")
            return None
        
        print(f"✅ Found response element: {response_node_id}")
        return response_node_id
    
    def _find_response_within_parent(self, parent_node_id: int) -> Optional[int]:
        """Find the response element within the common parent container"""
        print(f"🔍 Searching for response element within parent {parent_node_id}...")
        
        find_response_js = """
        function() {
            // Look for various response element patterns
            const selectors = [
                'model-response',
                'message-content', 
                'response-container',
                '[class*="model-response"]',
                '[class*="response-text"]',
                '[class*="message-content"]'
            ];
            
            for (const selector of selectors) {
                const elements = this.querySelectorAll(selector);
                for (const element of elements) {
                    const text = (element.textContent || '').trim();
                    // Look for elements with meaningful content (not just question)
                    if (text.length > 0 && !text.includes('What is 2+2?')) {
                        console.log('Found response element:', selector, 'with text:', text.substring(0, 50));
                        return element;
                    }
                }
            }
            
            console.log('No response element found with standard selectors');
            return null;
        }
        """
        
        try:
            # Get the parent element object from the node ID
            element_response = self._send_command({
                "method": "DOM.resolveNode",
                "params": {"nodeId": parent_node_id}
            })
            
            element_object_id = element_response.get("result", {}).get("object", {}).get("objectId")
            if not element_object_id:
                print("❌ Could not resolve parent element")
                return None
            
            # Find response element within parent
            response = self._send_command({
                "method": "Runtime.callFunctionOn",
                "params": {
                    "objectId": element_object_id,
                    "functionDeclaration": find_response_js,
                    "returnByValue": False  # Return object reference
                }
            })
            
            if "result" in response and "result" in response["result"]:
                # Get object ID of response element
                response_object_id = response["result"]["result"].get("objectId")
                if response_object_id:
                    # Convert object to node ID
                    node_response = self._send_command({
                        "method": "DOM.requestNode",
                        "params": {"objectId": response_object_id}
                    })
                    
                    response_node_id = node_response.get("result", {}).get("nodeId")
                    if response_node_id:
                        print(f"✅ Found response element with node ID: {response_node_id}")
                        return response_node_id
            
            print("❌ Response element not found within parent")
            return None
                
        except Exception as e:
            print(f"❌ Error finding response element within parent: {e}")
            return None
    
    def _monitor_response_completion(self, response_node_id: int, question: str, max_timeout: int = 180) -> Optional[str]:
        """
        Phase 4: Monitor response element for content growth and completion
        Uses adaptive waiting based on content changes rather than fixed timeouts
        """
        print(f"📊 Monitoring response completion (max {max_timeout}s)...")
        
        start_time = time.time()
        last_length = 0
        last_text = ""
        stable_count = 0
        check_interval = 0.5  # Check every 500ms
        
        while time.time() - start_time < max_timeout:
            try:
                # Get current response text
                current_text = self._get_element_text(response_node_id)
                current_length = len(current_text) if current_text else 0
                
                if current_length > last_length:
                    # Content is growing - reset stability counter
                    stable_count = 0
                    last_length = current_length
                    last_text = current_text
                    print(f"📝 Response growing... ({current_length} chars)")
                    
                elif current_length == last_length and current_length > 0:
                    # Content stable - check if it looks complete
                    if current_text == last_text:
                        stable_count += 1
                        
                        # If stable for 6 checks (3 seconds) and content looks complete
                        if stable_count >= 6:
                            if self._is_response_complete(current_text, question):
                                elapsed = time.time() - start_time
                                print(f"✅ Response completed after {elapsed:.1f}s ({current_length} chars)")
                                return current_text
                            else:
                                # Content stable but doesn't look complete - keep waiting
                                print(f"⏳ Content stable but may be incomplete, continuing...")
                                stable_count = 0  # Reset to continue monitoring
                    else:
                        # Text changed slightly - reset counter
                        stable_count = 0
                        last_text = current_text
                
                time.sleep(check_interval)
                
            except Exception as e:
                print(f"⚠️ Error monitoring response: {e}")
                time.sleep(check_interval)
        
        # Timeout reached - return what we have if it's substantial
        elapsed = time.time() - start_time
        print(f"⏰ Monitoring timeout after {elapsed:.1f}s")
        
        if last_text and len(last_text) > 50:
            print(f"📋 Returning partial response ({len(last_text)} chars)")
            return last_text
        
        return None
    
    def _get_element_text(self, node_id: int) -> Optional[str]:
        """Get text content from a DOM element by node ID"""
        try:
            # Get element text content
            response = self._send_command({
                "method": "DOM.resolveNode",
                "params": {"nodeId": node_id}
            })
            
            object_id = response.get("result", {}).get("object", {}).get("objectId")
            if not object_id:
                return None
            
            # Get text content
            text_response = self._send_command({
                "method": "Runtime.callFunctionOn",
                "params": {
                    "objectId": object_id,
                    "functionDeclaration": "function() { return this.textContent || this.innerText || ''; }",
                    "returnByValue": True
                }
            })
            
            if "result" in text_response and "result" in text_response["result"]:
                return text_response["result"]["result"].get("value", "")
            
            return None
            
        except Exception as e:
            return None
    
    def _is_response_complete(self, text: str, question: str) -> bool:
        """
        Check if response appears to be complete based on content analysis
        """
        if not text or len(text) < 1:
            return False
        
        text_lower = text.lower()
        question_lower = question.lower()
        
        # Don't accept if it's just the question
        if text.strip().lower() == question.strip().lower():
            return False
        
        # For math questions - short answers are often complete
        if any(word in question_lower for word in ['what is', '+', '-', '*', '/', 'calculate', 'solve']):
            # Math answers can be very short (e.g., "4", "2 + 2 = 4")
            if len(text.strip()) >= 1 and any(char.isdigit() for char in text):
                print(f"    💡 Math answer detected: '{text}' - accepting as complete")
                return True
        
        # For code-related questions
        if any(word in question_lower for word in ['code', 'python', 'function', 'script', 'program']):
            # Check for code block completion
            if '```' in text:
                code_blocks = text.count('```')
                if code_blocks % 2 != 0:  # Unclosed code block
                    return False
            
            # Check for typical code structure
            if any(pattern in text for pattern in ['import ', 'def ', 'class ', 'if __name__']):
                return True
            
            # Code answers need reasonable length
            return len(text) > 20
        
        # For general questions - check for natural completion
        text_stripped = text.strip()
        if text_stripped.endswith(('.', '!', '?', '```', '"', "'")):
            return len(text) > 10  # Reduced from 100 to allow shorter complete answers
        
        # Short definitive answers (e.g., "Paris", "Yes", "No")
        if len(text.strip()) > 2 and len(text.strip()) < 50:
            # Check if it looks like a simple factual answer
            words = text.strip().split()
            if len(words) <= 5 and not any(word in text_lower for word in ['loading', 'wait', 'processing']):
                print(f"    💡 Short factual answer detected: '{text}' - accepting as complete")
                return True
        
        # If response is getting long, it's probably complete enough
        if len(text) > 500:
            return True
        
        # Medium length answers are likely complete
        if len(text) > 50:
            return True
        
        return False
    
    def _validate_response(self, response: str, question: str) -> bool:
        """Validate that the response looks reasonable"""
        # Must have reasonable length (at least 1 character)
        if len(response) < 1 or len(response) > 10000:
            return False
        
        # Should not be identical to the question
        if response.strip().lower() == question.strip().lower():
            return False
        
        # Should not contain the full question (unless it's a long response)
        if question.lower() in response.lower() and len(response) < len(question) * 2:
            return False
        
        # Basic validation - response should be meaningful
        response_lower = response.lower().strip()
        
        # Special handling for math questions - allow very short answers
        question_lower = question.lower()
        if any(word in question_lower for word in ['what is', '+', '-', '*', '/', 'calculate', 'solve']):
            if any(char.isdigit() for char in response) and len(response.strip()) >= 1:
                print(f"✅ Math response accepted: '{response}'")
                return True
        
        # Only reject if it's clearly just UI text and very short
        if len(response) < 3:
            print(f"❌ Response too short: '{response}'")
            return False
        
        # Reject common UI placeholder text
        ui_text = ['loading', 'wait', 'processing', '...', 'error']
        if any(ui in response_lower for ui in ui_text) and len(response) < 20:
            print(f"❌ Response appears to be UI text: '{response}'")
            return False
        
        return True
    
    def _detect_and_handle_canvas(self) -> bool:
        """
        Detect if Gemini is trying to use Canvas and handle it
        Canvas requires sign-in and will cause failures
        """
        print("🎨 Checking for Canvas usage...")
        
        canvas_detection_js = """
        (() => {
            // Look for Canvas-related elements or text
            const canvasIndicators = [
                'canvas',
                'Try again without Canvas',
                'sign in to use Canvas',
                'Canvas requires sign-in',
                'Use Canvas',
                'Open in Canvas'
            ];
            
            const bodyText = document.body.textContent.toLowerCase();
            const foundIndicators = canvasIndicators.filter(indicator => 
                bodyText.includes(indicator.toLowerCase())
            );
            
            // Also check for Canvas buttons or links
            const canvasButtons = document.querySelectorAll(
                'button[title*="Canvas"], button[aria-label*="Canvas"], a[href*="canvas"]'
            );
            
            return {
                hasCanvasText: foundIndicators.length > 0,
                foundIndicators: foundIndicators,
                canvasButtonCount: canvasButtons.length,
                bodyTextSample: bodyText.substring(0, 200)
            };
        })()
        """
        
        try:
            response = self._send_command({
                "method": "Runtime.evaluate",
                "params": {
                    "expression": canvas_detection_js,
                    "returnByValue": True
                }
            })
            
            if "result" in response and "result" in response["result"]:
                result = response["result"]["result"]["value"]
                
                has_canvas = result.get("hasCanvasText", False)
                indicators = result.get("foundIndicators", [])
                button_count = result.get("canvasButtonCount", 0)
                
                if has_canvas or button_count > 0:
                    print(f"⚠️  Canvas detected! Indicators: {indicators}, Buttons: {button_count}")
                    return True
                else:
                    print("✅ No Canvas usage detected")
                    return False
            
            return False
            
        except Exception as e:
            print(f"❌ Canvas detection error: {e}")
            return False
    
    def _get_system_prompt(self) -> str:
        """
        Get system prompt from various sources in order of precedence:
        1. Environment variable GEMINI_SYSTEM_PROMPT
        2. Config file .gemini_prompt in current directory
        3. Config file .gemini_prompt in home directory
        4. Default Canvas prevention prompt
        """
        import os
        
        # 1. Check environment variable first (highest precedence)
        env_prompt = os.getenv('GEMINI_SYSTEM_PROMPT')
        if env_prompt:
            return env_prompt.strip()
        
        # 2. Check for .gemini_prompt in current directory
        current_dir_prompt = os.path.join(os.getcwd(), '.gemini_prompt')
        if os.path.exists(current_dir_prompt):
            try:
                with open(current_dir_prompt, 'r', encoding='utf-8') as f:
                    prompt = f.read().strip()
                    if prompt:
                        return prompt
            except Exception:
                pass  # Fall back to next option
        
        # 3. Check for .gemini_prompt in home directory
        home_prompt = os.path.expanduser('~/.gemini_prompt')
        if os.path.exists(home_prompt):
            try:
                with open(home_prompt, 'r', encoding='utf-8') as f:
                    prompt = f.read().strip()
                    if prompt:
                        return prompt
            except Exception:
                pass  # Fall back to default
        
        # 4. Default Canvas prevention prompt
        return "<ATTENTION> never start the canvas mode! write everything always as normal text </ATTENTION>"
    
    def _add_canvas_prevention_prompt(self, original_question: str) -> str:
        """Add system prompt (Canvas prevention or custom) to the question"""
        system_prompt = self._get_system_prompt()
        return original_question + " " + system_prompt

    def ask_question(self, question: str, timeout: int = 30) -> str:
        """
        Ask a question to Gemini using smart DOM navigation
        
        Args:
            question: Question to ask
            timeout: Maximum time to wait for response
            
        Returns:
            str: Gemini's response
            
        Raises:
            InteractionError: If interaction fails
            TimeoutError: If no response within timeout
        """
        if not self.ws:
            raise ConnectionError("Not connected. Call connect() first.")
        
        print(f"🎯 Asking question: '{question}'")
        
        # Always add Canvas prevention to be safe
        print("🛡️  Adding Canvas prevention to question")
        modified_question = self._add_canvas_prevention_prompt(question)
        
        try:
            # Step 1: Find and focus input field
            print("1️⃣ Finding input field...")
            input_selectors = [
                'rich-textarea',
                '[contenteditable="true"]',
                'textarea',
                '[role="textbox"]',
                'input[type="text"]'
            ]
            
            input_node_id = None
            for selector in input_selectors:
                input_node_id = self.wait_for_element(selector, timeout=5)
                if input_node_id:
                    print(f"  Found input with selector: {selector}")
                    break
            
            if not input_node_id:
                raise InteractionError("Could not find input field")
            
            # Step 2: Focus the input field
            print("2️⃣ Focusing input field...")
            self._send_command({
                "method": "DOM.focus",
                "params": {"nodeId": input_node_id}
            })
            time.sleep(0.3)  # Wait for focus
            
            # Step 3: Type the question (use modified version if needed)
            print("3️⃣ Typing question...")
            for char in modified_question:
                self._send_command({
                    "method": "Input.dispatchKeyEvent",
                    "params": {
                        "type": "char",
                        "text": char
                    }
                })
                time.sleep(self.typing_speed)  # Configurable typing speed
            
            # Step 4: Submit the question
            print("4️⃣ Submitting question...")
            self._send_command({
                "method": "Input.dispatchKeyEvent",
                "params": {
                    "type": "keyDown",
                    "windowsVirtualKeyCode": 13,
                    "key": "Enter"
                }
            })
            self._send_command({
                "method": "Input.dispatchKeyEvent",
                "params": {
                    "type": "keyUp",
                    "windowsVirtualKeyCode": 13,
                    "key": "Enter"
                }
            })
            
            # Brief wait for submission to process
            time.sleep(1)
            
            # Step 5: Use smart response detection (use original question for searching)
            print("5️⃣ Using smart response detection...")
            response = self.wait_for_response_smart(question, timeout)
            
            if not response:
                raise TimeoutError(f"No response received within {timeout} seconds")
            
            print(f"✅ Got response: '{response[:100]}{'...' if len(response) > 100 else ''}'")
            return response
            
        except Exception as e:
            print(f"❌ Question failed: {e}")
            raise
    
    def close(self, cleanup_chrome: bool = False):
        """Close WebSocket connection and optionally cleanup Chrome"""
        # Take screenshot before closing if requested
        if self.screenshot_path and self.ws:
            print(f"📸 Taking screenshot before closing: {self.screenshot_path}")
            success = self.take_screenshot(self.screenshot_path)
            if not success:
                print(f"⚠️  Failed to save screenshot: {self.screenshot_path}")
        
        if self.ws:
            self.ws.close()
            self.ws = None
        
        # Cleanup Chrome if it was auto-launched and cleanup is requested
        if cleanup_chrome and self.chrome_launcher:
            self.chrome_launcher.cleanup()
    
    def take_screenshot(self, filepath: str) -> bool:
        """Take a screenshot of the current page"""
        try:
            import base64
            
            response = self._send_command({
                "method": "Page.captureScreenshot",
                "params": {"format": "png"}
            })
            
            if "result" in response and "data" in response["result"]:
                with open(filepath, 'wb') as f:
                    f.write(base64.b64decode(response["result"]["data"]))
                return True
            
            return False
            
        except Exception:
            return False
    
    def get_page_text(self) -> str:
        """Get all visible text from the current page"""
        if not self.ws:
            raise ConnectionError("Not connected")
            
        response = self._send_command({
            "method": "Runtime.evaluate",
            "params": {
                "expression": "document.body.innerText",
                "returnByValue": True
            }
        })
        
        if "result" in response and "result" in response["result"]:
            return response["result"]["result"]["value"]
        
        return ""
    
    def get_chrome_status(self) -> dict:
        """Get status information about Chrome and Gemini"""
        if self.chrome_launcher:
            return self.chrome_launcher.get_status()
        else:
            # Basic status without launcher
            try:
                response = requests.get(f"{self.devtools_url}/json", timeout=2)
                tabs = response.json()
                return {
                    "chrome_running": True,
                    "devtools_port": self.devtools_port,
                    "tabs_count": len(tabs),
                    "gemini_tab_available": any(
                        "gemini.google.com" in tab.get("url", "") for tab in tabs
                    ),
                    "auto_launch_enabled": False
                }
            except:
                return {
                    "chrome_running": False,
                    "devtools_port": self.devtools_port,
                    "auto_launch_enabled": False
                }
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()