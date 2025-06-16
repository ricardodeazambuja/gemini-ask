"""
Chrome launcher module for automatically starting Chrome with remote debugging
"""

import os
import platform
import subprocess
import time
import shutil
import tempfile
import requests
from pathlib import Path
from typing import Optional, List, Tuple
import signal
import atexit

from .exceptions import ConnectionError, ElementNotFoundError


class ChromeLauncher:
    """
    Automatically launch and manage Chrome instances with remote debugging enabled
    """
    
    def __init__(self, devtools_port: int = 9222, user_data_dir: Optional[str] = None, quiet: bool = False):
        """
        Initialize Chrome launcher
        
        Args:
            devtools_port: Port for Chrome DevTools (default: 9222)
            user_data_dir: Custom user data directory (default: temp directory)
            quiet: Whether to suppress all output (default: False)
        """
        self.devtools_port = devtools_port
        self.user_data_dir = user_data_dir or os.path.join(tempfile.gettempdir(), f"chrome-debug-{devtools_port}")
        self.quiet = quiet
        self.chrome_process = None
        self.chrome_path = None
        
        # Register cleanup on exit
        atexit.register(self.cleanup)
    
    def _print(self, *args, **kwargs):
        """Print message only if not in quiet mode"""
        if not self.quiet:
            print(*args, **kwargs)
    
    def find_chrome_executable(self) -> Optional[str]:
        """
        Find Chrome executable on the system
        
        Returns:
            str: Path to Chrome executable, or None if not found
        """
        system = platform.system().lower()
        
        if system == "linux":
            # Common Chrome locations on Linux
            chrome_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable", 
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser",
                "/snap/bin/chromium",
                "/usr/local/bin/google-chrome",
                shutil.which("google-chrome"),
                shutil.which("google-chrome-stable"),
                shutil.which("chromium"),
                shutil.which("chromium-browser")
            ]
        
        elif system == "darwin":  # macOS
            chrome_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium",
                "/usr/local/bin/google-chrome",
                shutil.which("google-chrome"),
                shutil.which("chromium")
            ]
        
        elif system == "windows":
            chrome_paths = [
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"),
                shutil.which("chrome.exe"),
                shutil.which("google-chrome.exe")
            ]
        
        else:
            # Unknown system, try common executables
            chrome_paths = [
                shutil.which("google-chrome"),
                shutil.which("chrome"),
                shutil.which("chromium")
            ]
        
        # Find first existing executable
        for path in chrome_paths:
            if path and os.path.isfile(path) and os.access(path, os.X_OK):
                return path
        
        return None
    
    def get_chrome_launch_args(self, open_gemini: bool = True, headless: bool = False) -> List[str]:
        """
        Get Chrome launch arguments
        
        Args:
            open_gemini: Whether to automatically open Gemini tab
            headless: Whether to run in headless mode
            
        Returns:
            List of command line arguments
        """
        # Essential debugging args
        args = [
            f"--remote-debugging-port={self.devtools_port}",
            f"--user-data-dir={self.user_data_dir}",
            "--remote-allow-origins=*",
        ]
        
        # Safe compatibility flags
        safe_args = [
            "--no-first-run",  # Skip first run setup
            "--disable-default-apps",  # Don't load default apps
            "--disable-popup-blocking",  # Allow popups if needed
            "--disable-background-timer-throttling",  # Prevent throttling
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
        ]
        args.extend(safe_args)
        
        # Conditional flags based on environment
        system = platform.system().lower()
        
        # Only add sandbox flags if we're in a container, CI, or truly needed
        # Avoid --no-sandbox in normal desktop environments as it causes warnings
        if (headless and (os.getenv('DOCKER_CONTAINER') or os.getenv('CI'))) or \
           (os.getenv('CHROME_NO_SANDBOX') == 'true'):
            args.extend([
                "--no-sandbox", 
                "--disable-dev-shm-usage"
            ])
        
        # GPU flags for stability
        if headless:
            args.extend([
                "--headless",
                "--disable-gpu",
                "--disable-software-rasterizer"
            ])
        # Note: --disable-gpu-sandbox removed as it's unsupported and causes warnings
        
        # Web security for automation (optional)
        # Note: Only disable if really needed for automation
        # args.append("--disable-web-security")
        
        if open_gemini:
            args.append("https://gemini.google.com")
        
        return args
    
    def is_chrome_running(self) -> bool:
        """
        Check if Chrome with remote debugging is already running
        
        Returns:
            bool: True if Chrome DevTools is accessible
        """
        try:
            response = requests.get(f"http://localhost:{self.devtools_port}/json", timeout=2)
            response.raise_for_status()
            return True
        except:
            return False
    
    def wait_for_chrome_ready(self, timeout: int = 30) -> bool:
        """
        Wait for Chrome to be ready and DevTools accessible
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if Chrome is ready, False if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.is_chrome_running():
                # Additional check: make sure we can get tabs list
                try:
                    response = requests.get(f"http://localhost:{self.devtools_port}/json", timeout=2)
                    tabs = response.json()
                    if isinstance(tabs, list):
                        return True
                except:
                    pass
            
            time.sleep(1)
        
        return False
    
    def launch_chrome(self, open_gemini: bool = True, headless: bool = False) -> bool:
        """
        Launch Chrome with remote debugging
        
        Args:
            open_gemini: Whether to automatically open Gemini 
            headless: Whether to run Chrome in headless mode
            
        Returns:
            bool: True if Chrome launched successfully
            
        Raises:
            ConnectionError: If Chrome cannot be found or launched
        """
        # Check if Chrome is already running
        if self.is_chrome_running():
            self._print(f"Chrome already running on port {self.devtools_port}")
            return True
        
        # Find Chrome executable
        self.chrome_path = self.find_chrome_executable()
        if not self.chrome_path:
            raise ConnectionError(
                "Chrome not found. Please install Google Chrome or Chromium.\n"
                "On Ubuntu: sudo apt install google-chrome-stable\n"
                "On macOS: brew install --cask google-chrome\n"
                "On Windows: Download from https://chrome.google.com"
            )
        
        self._print(f"Found Chrome at: {self.chrome_path}")
        
        # Prepare launch arguments
        args = self.get_chrome_launch_args(open_gemini=open_gemini, headless=headless)
        
        # Create user data directory
        os.makedirs(self.user_data_dir, exist_ok=True)
        
        # Launch Chrome
        cmd = [self.chrome_path] + args
        
        try:
            self._print(f"Launching Chrome on port {self.devtools_port}...")
            self._print(f"Command: {' '.join(cmd)}")
            
            # Launch Chrome process
            self.chrome_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=None if platform.system() == "Windows" else os.setsid
            )
            
            # Wait for Chrome DevTools to be ready
            if self.wait_for_chrome_ready(timeout=30):
                self._print("✅ Chrome launched and DevTools ready!")
                
                if open_gemini:
                    # Wait for Gemini tab to be fully loaded and ready
                    if self.wait_for_gemini_tab_ready(timeout=60):
                        return True
                    else:
                        self._print("❌ Chrome launched but Gemini tab failed to load properly")
                        self._print("💡 This might be due to:")
                        self._print("   - Not being logged into Google account")
                        self._print("   - Network connectivity issues")
                        self._print("   - Gemini service being unavailable")
                        return False
                
                return True
            else:
                self._print("❌ Chrome launched but DevTools not accessible")
                self.cleanup()
                return False
                
        except Exception as e:
            raise ConnectionError(f"Failed to launch Chrome: {e}")
    
    def check_gemini_tab(self) -> bool:
        """
        Check if Gemini tab is open and accessible
        
        Returns:
            bool: True if Gemini tab found
        """
        try:
            response = requests.get(f"http://localhost:{self.devtools_port}/json", timeout=5)
            tabs = response.json()
            
            for tab in tabs:
                if "gemini.google.com" in tab.get("url", ""):
                    return True
            
            return False
        except:
            return False
    
    def wait_for_gemini_tab_ready(self, timeout: int = 60, check_interval: float = 2.0) -> bool:
        """
        Wait for Gemini tab to be not just present, but actually loaded and ready
        
        Args:
            timeout: Maximum time to wait in seconds
            check_interval: How often to check in seconds
            
        Returns:
            bool: True if Gemini tab is ready, False if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # First check if tab exists
                response = requests.get(f"http://localhost:{self.devtools_port}/json", timeout=5)
                tabs = response.json()
                
                gemini_tab = None
                for tab in tabs:
                    if "gemini.google.com" in tab.get("url", ""):
                        gemini_tab = tab
                        break
                
                if not gemini_tab:
                    self._print("⏳ Waiting for Gemini tab to open...")
                    time.sleep(check_interval)
                    continue
                
                # Just check if tab exists and is accessible - simplify for now
                try:
                    # Basic check that we can connect to the tab
                    import json
                    ws_url = gemini_tab["webSocketDebuggerUrl"]
                    import websocket
                    temp_ws = websocket.create_connection(ws_url, timeout=3)
                    temp_ws.close()
                    
                    self._print("✅ Gemini tab loaded and accessible!")
                    return True
                    
                except Exception as ws_error:
                    self._print(f"⏳ Gemini tab not yet accessible... ({ws_error})")
                
                time.sleep(check_interval)
                
            except Exception as e:
                self._print(f"⏳ Waiting for Gemini tab... ({e})")
                time.sleep(check_interval)
        
        self._print("❌ Timeout waiting for Gemini tab to be ready")
        return False
    
    def open_gemini_tab(self) -> bool:
        """
        Open a new Gemini tab in existing Chrome instance
        
        Returns:
            bool: True if tab opened successfully
        """
        try:
            # Use Chrome DevTools API to open new tab
            response = requests.put(
                f"http://localhost:{self.devtools_port}/json/new?https://gemini.google.com",
                timeout=5
            )
            response.raise_for_status()
            
            # Wait for tab to load
            time.sleep(3)
            return self.check_gemini_tab()
            
        except Exception as e:
            print(f"Failed to open Gemini tab: {e}")
            return False
    
    def get_status(self) -> dict:
        """
        Get status information about Chrome and Gemini
        
        Returns:
            dict: Status information
        """
        status = {
            "chrome_running": self.is_chrome_running(),
            "chrome_path": self.chrome_path,
            "devtools_port": self.devtools_port,
            "user_data_dir": self.user_data_dir,
            "process_id": self.chrome_process.pid if self.chrome_process else None,
            "gemini_tab_available": False,
            "tabs_count": 0
        }
        
        if status["chrome_running"]:
            try:
                response = requests.get(f"http://localhost:{self.devtools_port}/json", timeout=2)
                tabs = response.json()
                status["tabs_count"] = len(tabs)
                status["gemini_tab_available"] = any(
                    "gemini.google.com" in tab.get("url", "") for tab in tabs
                )
            except:
                pass
        
        return status
    
    def cleanup(self):
        """Clean up Chrome process and temporary files"""
        if self.chrome_process:
            try:
                # Try graceful shutdown first
                if platform.system() != "Windows":
                    os.killpg(os.getpgid(self.chrome_process.pid), signal.SIGTERM)
                else:
                    self.chrome_process.terminate()
                
                # Wait for process to end
                try:
                    self.chrome_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if needed
                    if platform.system() != "Windows":
                        os.killpg(os.getpgid(self.chrome_process.pid), signal.SIGKILL)
                    else:
                        self.chrome_process.kill()
                    
                self._print("🧹 Chrome process cleaned up")
                
            except (ProcessLookupError, OSError):
                # Process already gone
                pass
            
            self.chrome_process = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()