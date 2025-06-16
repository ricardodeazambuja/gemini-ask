#!/usr/bin/env python3
"""
Advanced example of using gemini-ask

This example demonstrates:
- Multiple questions
- Error handling
- Screenshots
- Custom settings
- Context manager usage
"""

import time
from gemini_ask import (
    GeminiAutomation, 
    GeminiAutomationError,
    ConnectionError,
    TimeoutError,
    InteractionError
)


def main():
    """Advanced example with multiple features"""
    
    print("gemini-ask - Advanced Example")
    print("=" * 60)
    
    # Questions to ask
    questions = [
        "What is machine learning?",
        "How do neural networks work?",
        "What are the main applications of AI?",
        "Explain quantum computing in simple terms"
    ]
    
    # Use context manager for automatic cleanup
    try:
        with GeminiAutomation(devtools_port=9222) as gemini:
            
            print("1. Connecting to Chrome DevTools...")
            gemini.connect()
            print("✅ Connected successfully!")
            
            print("2. Taking initial screenshot...")
            gemini.take_screenshot("screenshots/initial_state.png")
            
            print(f"3. Asking {len(questions)} questions...")
            responses = []
            
            for i, question in enumerate(questions, 1):
                print(f"\n--- Question {i}/{len(questions)} ---")
                print(f"Q: {question}")
                
                try:
                    # Ask question with custom timeout
                    response = gemini.ask_question(question, timeout=45)
                    responses.append((question, response))
                    
                    print(f"A: {response[:100]}{'...' if len(response) > 100 else ''}")
                    
                    # Take screenshot after each response
                    screenshot_name = f"screenshots/response_{i}.png"
                    if gemini.take_screenshot(screenshot_name):
                        print(f"📸 Screenshot saved: {screenshot_name}")
                    
                    # Wait between questions to be polite
                    if i < len(questions):
                        print("⏳ Waiting 3 seconds before next question...")
                        time.sleep(3)
                        
                except TimeoutError:
                    print("⏰ Question timed out - Gemini took too long to respond")
                    responses.append((question, "TIMEOUT"))
                    
                except InteractionError as e:
                    print(f"🔧 Interaction failed: {e}")
                    responses.append((question, f"ERROR: {e}"))
                    
                except Exception as e:
                    print(f"❌ Unexpected error: {e}")
                    responses.append((question, f"UNEXPECTED_ERROR: {e}"))
            
            # Print summary
            print("\n" + "=" * 60)
            print("CONVERSATION SUMMARY")
            print("=" * 60)
            
            for i, (question, response) in enumerate(responses, 1):
                print(f"\n{i}. Q: {question}")
                if response.startswith(("TIMEOUT", "ERROR", "UNEXPECTED_ERROR")):
                    print(f"   A: ❌ {response}")
                else:
                    print(f"   A: {response}")
            
            # Get final page content
            print("\n4. Getting final page content...")
            page_text = gemini.get_page_text()
            print(f"📄 Page contains {len(page_text)} characters")
            
            # Save page content to file
            with open("conversation_log.txt", "w", encoding="utf-8") as f:
                f.write("=== GEMINI-ASK LOG ===\n\n")
                for i, (question, response) in enumerate(responses, 1):
                    f.write(f"Question {i}: {question}\n")
                    f.write(f"Response {i}: {response}\n\n")
                f.write("\n=== FULL PAGE CONTENT ===\n")
                f.write(page_text)
            
            print("💾 Conversation saved to: conversation_log.txt")
            
    except ConnectionError:
        print("❌ Could not connect to Chrome DevTools")
        print("\nSetup instructions:")
        print("1. Close all Chrome instances")
        print("2. Start Chrome with: chrome --remote-debugging-port=9222")
        print("3. Open gemini.google.com in a tab")
        print("4. Run this script again")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
    
    print("\n✅ Advanced example completed!")


def setup_directories():
    """Create necessary directories"""
    import os
    os.makedirs("screenshots", exist_ok=True)


if __name__ == "__main__":
    setup_directories()
    main()