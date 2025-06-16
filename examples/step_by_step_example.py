#!/usr/bin/env python3
"""
Step-by-step example of using gemini-ask

This example demonstrates the complete automation workflow with detailed progress tracking.
"""

import time
from gemini_ask import GeminiAutomation, GeminiAutomationError


def main():
    """Step-by-step interaction example"""
    
    print("gemini-ask - Step by Step Example")
    print("=" * 60)
    
    gemini = GeminiAutomation()
    
    try:
        # Step 1: Connect
        print("Step 1: Connecting to Chrome DevTools...")
        success = gemini.connect()
        if not success:
            print("❌ Connection failed")
            return
        print("✅ Connected!")
        
        # Step 2: Take initial screenshot
        print("\nStep 2: Taking initial screenshot...")
        gemini.take_screenshot("step_by_step_initial.png")
        print("📸 Screenshot saved")
        
        # Step 3: Check Chrome status
        print("\nStep 3: Checking Chrome status...")
        status = gemini.get_chrome_status()
        print(f"📊 Chrome running: {status.get('chrome_running', False)}")
        print(f"📊 Gemini tab available: {status.get('gemini_tab_available', False)}")
        print(f"📊 Total tabs: {status.get('tabs_count', 0)}")
        
        # Step 4: Ask simple math question
        math_question = "What is 2+2?"
        print(f"\nStep 4: Asking math question: '{math_question}'")
        print("⏳ Processing...", end="", flush=True)
        
        start_time = time.time()
        math_response = gemini.ask_question(math_question, timeout=20)
        elapsed = time.time() - start_time
        
        print(f"\n✅ Math response received in {elapsed:.1f}s: '{math_response}'")
        
        # Step 5: Take screenshot after first question
        print("\nStep 5: Taking screenshot after math question...")
        gemini.take_screenshot("step_by_step_math.png")
        print("📸 Screenshot saved")
        
        # Step 6: Ask factual question
        fact_question = "What is the capital of France?"
        print(f"\nStep 6: Asking factual question: '{fact_question}'")
        print("⏳ Processing...", end="", flush=True)
        
        start_time = time.time()
        fact_response = gemini.ask_question(fact_question, timeout=20)
        elapsed = time.time() - start_time
        
        print(f"\n✅ Factual response received in {elapsed:.1f}s: '{fact_response}'")
        
        # Step 7: Ask more complex question
        complex_question = "Explain artificial intelligence in one sentence."
        print(f"\nStep 7: Asking complex question: '{complex_question}'")
        print("⏳ Processing (may take longer)...", end="", flush=True)
        
        start_time = time.time()
        complex_response = gemini.ask_question(complex_question, timeout=30)
        elapsed = time.time() - start_time
        
        print(f"\n✅ Complex response received in {elapsed:.1f}s")
        print(f"📝 Response: {complex_response}")
        
        # Step 8: Take final screenshot
        print("\nStep 8: Taking final screenshot...")
        gemini.take_screenshot("step_by_step_final.png")
        print("📸 Final screenshot saved")
        
        # Step 9: Get page statistics
        print("\nStep 9: Getting page statistics...")
        page_text = gemini.get_page_text()
        word_count = len(page_text.split()) if page_text else 0
        char_count = len(page_text) if page_text else 0
        
        print(f"📊 Page statistics:")
        print(f"   - Total characters: {char_count:,}")
        print(f"   - Total words: {word_count:,}")
        
        # Step 10: Display summary
        print("\nStep 10: Summary of all interactions...")
        print("=" * 50)
        print(f"Math Q: {math_question}")
        print(f"Math A: {math_response}")
        print()
        print(f"Fact Q: {fact_question}")
        print(f"Fact A: {fact_response}")
        print()
        print(f"Complex Q: {complex_question}")
        print(f"Complex A: {complex_response[:100]}{'...' if len(complex_response) > 100 else ''}")
        print("=" * 50)
        
        print("\n🎯 Step-by-step automation completed successfully!")
        print("📁 Screenshots saved:")
        print("   - step_by_step_initial.png")
        print("   - step_by_step_math.png") 
        print("   - step_by_step_final.png")
        
    except GeminiAutomationError as e:
        print(f"\n❌ Automation error during step-by-step process: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        print("\nCleaning up...")
        gemini.close()
        print("✅ Cleanup complete")


if __name__ == "__main__":
    main()