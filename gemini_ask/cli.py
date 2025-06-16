#!/usr/bin/env python3
"""
Command-line interface for gemini-ask
"""

import argparse
import sys
import time
import os
import warnings
import contextlib
from pathlib import Path
from .gemini_automation import GeminiAutomation
from .exceptions import GeminiAutomationError, ConnectionError, TimeoutError

# Suppress warnings to keep output clean when using --quiet
warnings.filterwarnings("ignore")


def eprint(*args, **kwargs):
    """Print to stderr instead of stdout"""
    print(*args, file=sys.stderr, **kwargs)


class StderrRedirector:
    """Context manager to redirect stdout to stderr while preserving our own stdout"""
    
    def __init__(self, quiet=False):
        self.quiet = quiet
        self.original_stdout = sys.stdout
        
    def __enter__(self):
        if self.quiet:
            # Redirect to null if quiet mode
            self.devnull = open(os.devnull, 'w')
            sys.stdout = self.devnull
        else:
            # Redirect to stderr
            sys.stdout = sys.stderr
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(sys.stdout, 'close') and sys.stdout != sys.stderr:
            sys.stdout.close()
        sys.stdout = self.original_stdout



def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Ask questions to Google Gemini through Chrome automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Basic Usage:
  gemini-ask "What is the capital of France?"
  gemini-ask "What is 2+2?"
  gemini-ask "Explain quantum computing"

Pipe Mode:
  echo "What is 2+2?" | gemini-ask --pipe
  echo "Write Python code" | gemini-ask --pipe --quiet | grep "def"
  cat questions.txt | gemini-ask --pipe

Custom System Prompts (Canvas prevention enabled by default):
  gemini-ask "Question" --system-prompt "Answer briefly"
  export GEMINI_SYSTEM_PROMPT="Be concise"; gemini-ask "Question"
  echo "Custom prompt" > .gemini_prompt; gemini-ask "Question"
  gemini-ask --show-prompt                           # Show current prompt
  gemini-ask "Question" --no-system-prompt           # Disable entirely

Advanced Options:
  gemini-ask --timeout 60 "Complex question..."     # Longer timeout
  gemini-ask --headless "How does AI work?"         # No GUI
  gemini-ask --screenshot result.png "Question"     # Save screenshot
  gemini-ask --verbose "Question"                   # Detailed output
  gemini-ask --quiet "Question"                     # Minimal output
  gemini-ask --no-auto-launch "Question"            # Manual Chrome setup

Chrome Management:
  gemini-ask --cleanup-chrome "Question"            # Close Chrome when done

Features:
  ✅ Canvas prevention enabled by default (avoids sign-in loops)
  ✅ Custom system prompts (env var, config file, or command line)
  ✅ Pipe mode for shell scripting integration
  ✅ Reliable response detection via DOM structure
  ✅ Smart DOM navigation with no false positives

Debugging:
  --verbose            Show detailed execution steps
        """
    )
    
    parser.add_argument(
        "question",
        nargs="?",
        help="Question to ask Gemini (optional if using --pipe mode)"
    )
    
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=9222,
        help="Chrome DevTools port (default: 9222)"
    )
    
    parser.add_argument(
        "--host",
        default="localhost",
        help="Chrome DevTools host (default: localhost)"
    )
    
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=30,
        help="Response timeout in seconds (default: 30)"
    )
    
    parser.add_argument(
        "--screenshot", "-s",
        help="Save screenshot to file after response"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--typing-speed",
        type=float,
        default=0.1,
        help="Typing speed in seconds per character (default: 0.1)"
    )
    
    parser.add_argument(
        "--no-auto-launch",
        action="store_true",
        help="Disable automatic Chrome launching (default: auto-launch enabled)"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true", 
        help="Run Chrome in headless mode (no GUI)"
    )
    
    parser.add_argument(
        "--cleanup-chrome",
        action="store_true",
        help="Close Chrome when done (if auto-launched)"
    )
    
    # Piping mode options
    parser.add_argument(
        "--pipe",
        action="store_true",
        help="Enable pipe mode - read question from stdin"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress all stderr output except errors (useful for piping)"
    )
    
    # Custom prompt options
    parser.add_argument(
        "--system-prompt", "-sp",
        type=str,
        help="Custom system prompt (overrides env var and config files)"
    )
    
    parser.add_argument(
        "--no-system-prompt",
        action="store_true",
        help="Disable system prompt entirely (send question as-is, without Canvas prevention)"
    )
    
    parser.add_argument(
        "--show-prompt",
        action="store_true",
        help="Show the system prompt that would be used and exit"
    )
    
    args = parser.parse_args()
    
    # Handle --show-prompt option early
    if args.show_prompt:
        # Create a temporary automation instance to get the system prompt
        original_env = os.environ.get('GEMINI_SYSTEM_PROMPT')
        if args.system_prompt:
            os.environ['GEMINI_SYSTEM_PROMPT'] = args.system_prompt
        
        try:
            temp_gemini = GeminiAutomation()
            if args.no_system_prompt:
                print("No system prompt (disabled)")
            else:
                system_prompt = temp_gemini._get_system_prompt()
                print(f"System prompt: {system_prompt}")
        finally:
            # Restore original environment
            if original_env is not None:
                os.environ['GEMINI_SYSTEM_PROMPT'] = original_env
            elif 'GEMINI_SYSTEM_PROMPT' in os.environ:
                del os.environ['GEMINI_SYSTEM_PROMPT']
        
        sys.exit(0)
    
    # Handle input: either from argument or stdin
    question = None
    if args.pipe or (not args.question and not sys.stdin.isatty()):
        # Pipe mode: read from stdin
        if sys.stdin.isatty() and args.pipe:
            eprint("Error: --pipe specified but no input provided via stdin")
            eprint("Example: echo 'What is 2+2?' | gemini-ask --pipe")
            sys.exit(1)
        
        question = sys.stdin.read().strip()
        if not question:
            eprint("Error: Empty question provided via stdin")
            sys.exit(1)
            
        # Auto-enable quiet mode in pipe mode unless verbose is explicitly set
        if args.pipe and not args.verbose:
            args.quiet = True
            
    elif args.question:
        # Interactive mode: use provided question
        question = args.question
    else:
        # No question provided and not in pipe mode
        eprint("Error: No question provided")
        eprint("Usage: gemini-ask 'Your question' or echo 'Your question' | gemini-ask --pipe")
        sys.exit(1)
    
    # Handle custom system prompt options - system prompts are ALWAYS enabled by default
    # Users can customize via env var, config file, or command line
    # Only --no-system-prompt disables them entirely
    original_env = os.environ.get('GEMINI_SYSTEM_PROMPT')
    if args.system_prompt:
        os.environ['GEMINI_SYSTEM_PROMPT'] = args.system_prompt
    
    # Set up output functions based on quiet mode
    def output_info(*args_out, **kwargs):
        if not args.quiet and not args.verbose:
            eprint(*args_out, **kwargs)
    
    def output_verbose(*args_out, **kwargs):
        if args.verbose:
            eprint(*args_out, **kwargs)
    
    if args.verbose:
        print(f"Chrome Gemini CLI v2.0 - Smart DOM Navigation", file=sys.stderr)
        print(f"Question: '{question[:50]}{'...' if len(question) > 50 else ''}'", file=sys.stderr)
        print(f"Connecting to {args.host}:{args.port}", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
    elif not args.quiet:
        eprint(f"🎯 Processing question: '{question[:50]}{'...' if len(question) > 50 else ''}'")
    
    
    # Use smart implementation (only version available)
    GeminiClass = GeminiAutomation
    
    try:
        gemini = None
        try:
            # Use context manager to redirect all automation output if in quiet mode
            with StderrRedirector(quiet=args.quiet):
                # Create automation instance
                gemini = GeminiClass(
                    devtools_port=args.port, 
                    host=args.host,
                    auto_launch=not args.no_auto_launch,
                    headless=args.headless,
                    screenshot_path=args.screenshot,
                    quiet=args.quiet
                )
                
                # System prompt is enabled by default with Canvas prevention
                # Only disable if user explicitly requests --no-system-prompt
                if args.no_system_prompt:
                    # Monkey-patch to disable system prompt entirely
                    gemini._add_canvas_prevention_prompt = lambda q: q
            
            output_verbose("🔌 Connecting to Chrome DevTools...")
            output_info("🔌 Connecting to Gemini...")
            
            # Connect to Chrome
            success = gemini.connect()
            if not success:
                eprint("❌ Failed to connect to Chrome DevTools")
                if not args.quiet:
                    eprint("\nTroubleshooting:")
                    eprint("1. Start Chrome: chrome --remote-debugging-port=9222")
                    eprint("2. Open https://gemini.google.com")
                    eprint("3. Try again")
                sys.exit(1)
            
            output_verbose("✅ Connected successfully!")
            output_verbose(f"❓ Asking question (timeout: {args.timeout}s)...")
            output_info("✅ Connected successfully")
            output_info("🤔 Asking question...")
            
            # Ask the question with potential output redirection
            start_time = time.time()
            with StderrRedirector(quiet=args.quiet):
                response = gemini.ask_question(question, timeout=args.timeout)
            elapsed_time = time.time() - start_time
            
            # Output the response - this is the only stdout output in quiet mode
            if args.verbose:
                eprint(f"⏱️  Response received in {elapsed_time:.1f} seconds")
                eprint("=" * 60)
                eprint(f"Q: {question}")
                print(response)  # This goes to stdout
                eprint("=" * 60)
            else:
                print(response)  # This goes to stdout for piping
                
                if not args.quiet:
                    eprint("✅ Response delivered")
            
            # Cleanup Chrome if requested
            if args.cleanup_chrome:
                output_verbose("🧹 Cleaning up Chrome...")
                with StderrRedirector(quiet=args.quiet):
                    gemini.close(cleanup_chrome=True)
    
        except GeminiAutomationError as e:
            eprint(f"❌ Gemini automation error: {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            eprint("\n⚠️ Interrupted by user")
            sys.exit(1)
        except Exception as e:
            eprint(f"❌ Unexpected error: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc(file=sys.stderr)
            sys.exit(1)
    finally:
        # Final cleanup in case something failed
        if gemini:
            try:
                with StderrRedirector(quiet=True):  # Always suppress final cleanup
                    gemini.close()
            except:
                pass  # Ignore cleanup errors
        
        # Restore original environment variable
        if 'original_env' in locals():
            if original_env is not None:
                os.environ['GEMINI_SYSTEM_PROMPT'] = original_env
            elif 'GEMINI_SYSTEM_PROMPT' in os.environ:
                del os.environ['GEMINI_SYSTEM_PROMPT']


if __name__ == "__main__":
    main()