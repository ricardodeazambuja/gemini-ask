#!/usr/bin/env python3
"""
Basic example of using gemini-ask

This example demonstrates the simplest way to ask a question to Gemini
and get a response.
"""

from gemini_ask import GeminiAutomation, GeminiAutomationError


def main():
    """Basic example of asking Gemini a question"""
    
    print("gemini-ask - Basic Example")
    print("=" * 50)
    print("🚀 Auto-launch enabled! No manual Chrome setup needed.")
    print()
    
    # Create automation instance (auto-launch enabled by default)
    gemini = GeminiAutomation()
    
    try:
        print("1. Connecting (auto-launching Chrome if needed)...")
        success = gemini.connect()
        
        if not success:
            print("❌ Failed to connect to Chrome DevTools")
            print("\nTroubleshooting:")
            print("- Make sure Chrome/Chromium is installed")
            print("- Check internet connection")
            print("- Try manual mode: GeminiAutomation(auto_launch=False)")
            return
        
        print("✅ Connected successfully!")
        
        # Show Chrome status
        status = gemini.get_chrome_status()
        print(f"📊 Chrome running: {status['chrome_running']}")
        print(f"📋 Tabs open: {status['tabs_count']}")
        
        # Ask a simple question
        question = "What is the capital of France?"
        print(f"\n2. Asking question: '{question}'")
        
        response = gemini.ask_question(question, timeout=30)
        
        print("\n3. Response received:")
        print("=" * 30)
        print(f"Q: {question}")
        print(f"A: {response}")
        print("=" * 30)
        
    except GeminiAutomationError as e:
        print(f"❌ Automation error: {e}")
        print("\nCommon solutions:")
        print("- Make sure Chrome/Chromium is installed")
        print("- Check internet connection for Gemini access") 
        print("- Try manual mode if auto-launch fails")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        
    finally:
        print("\n4. Cleaning up...")
        gemini.close()  # Leaves Chrome running
        print("✅ Done! (Chrome left running)")
        print("💡 Use gemini.close(cleanup_chrome=True) to close Chrome too")


if __name__ == "__main__":
    main()