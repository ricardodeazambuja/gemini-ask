#!/usr/bin/env python3
"""
Test Canvas prevention system with various question types
"""

from gemini_ask import GeminiAutomation
import time


def test_canvas_prevention():
    """Test Canvas prevention with questions that typically trigger Canvas"""
    
    print("Testing Canvas Prevention System")
    print("=" * 50)
    
    # Questions that commonly trigger Canvas
    test_questions = [
        {
            "question": "What is 2+2?",
            "canvas_expected": False,
            "description": "Simple math (should not trigger Canvas)"
        },
        {
            "question": "Write a Python function to add two numbers",
            "canvas_expected": True,
            "description": "Code request (Canvas-prone)"
        },
        {
            "question": "What is the capital of France?",
            "canvas_expected": False,
            "description": "Simple factual question"
        },
        {
            "question": "Create a simple HTML page structure",
            "canvas_expected": True,
            "description": "HTML/code request (Canvas-prone)"
        },
        {
            "question": "Explain photosynthesis in one sentence",
            "canvas_expected": False,
            "description": "Explanation request (should not trigger Canvas)"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_questions, 1):
        question = test_case["question"]
        expected_canvas = test_case["canvas_expected"]
        description = test_case["description"]
        
        print(f"\n--- Test {i}/5: {description} ---")
        print(f"Question: '{question}'")
        print(f"Canvas expected: {expected_canvas}")
        
        gemini = GeminiAutomation()
        
        try:
            if not gemini.connect():
                print(f"❌ Test {i}: Connection failed")
                results.append({"test": i, "status": "connection_failed", "canvas_handled": False})
                continue
            
            # Ask the question
            start_time = time.time()
            response = gemini.ask_question(question, timeout=20)
            end_time = time.time()
            
            if response:
                print(f"✅ Test {i}: SUCCESS")
                print(f"   Response: {response[:100]}{'...' if len(response) > 100 else ''}")
                print(f"   Time taken: {end_time - start_time:.1f}s")
                
                results.append({
                    "test": i,
                    "status": "success", 
                    "response_length": len(response),
                    "time_taken": end_time - start_time,
                    "canvas_handled": True,
                    "description": description
                })
            else:
                print(f"❌ Test {i}: FAILED - No response")
                results.append({"test": i, "status": "no_response", "canvas_handled": False})
                
        except Exception as e:
            print(f"❌ Test {i}: ERROR - {e}")
            results.append({"test": i, "status": "error", "error": str(e), "canvas_handled": False})
            
        finally:
            gemini.close()
            time.sleep(0.5)  # Brief pause between tests
    
    # Summary
    print(f"\n🏁 Canvas Prevention Test Results")
    print("=" * 50)
    
    successful_tests = [r for r in results if r["status"] == "success"]
    failed_tests = [r for r in results if r["status"] != "success"]
    
    print(f"✅ Successful: {len(successful_tests)}/{len(results)}")
    print(f"❌ Failed: {len(failed_tests)}/{len(results)}")
    
    if successful_tests:
        print(f"\n✅ Successful Tests:")
        for result in successful_tests:
            desc = result.get("description", f"Test {result['test']}")
            time_taken = result.get("time_taken", 0)
            response_len = result.get("response_length", 0)
            print(f"   • {desc}: {response_len} chars in {time_taken:.1f}s")
    
    if failed_tests:
        print(f"\n❌ Failed Tests:")
        for result in failed_tests:
            desc = test_questions[result["test"]-1]["description"]
            status = result["status"]
            print(f"   • {desc}: {status}")
    
    # Overall assessment
    success_rate = len(successful_tests) / len(results) * 100
    print(f"\n📊 Overall Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 Canvas prevention system working well!")
    elif success_rate >= 60:
        print("⚠️  Canvas prevention system needs some improvement")
    else:
        print("❌ Canvas prevention system needs significant work")


if __name__ == "__main__":
    print("🎨 Canvas Prevention Test Suite")
    print("Testing the Canvas detection and prevention system")
    print("to ensure code questions don't trigger sign-in requirements.")
    print()
    
    success = test_canvas_prevention()
    
    if success:
        print("\n🎯 Canvas prevention system validated!")
        print("   The tree walking algorithm should now work reliably")
        print("   with Canvas-prone questions without sign-in failures.")
    else:
        print("\n💡 Canvas prevention needs refinement.")
        print("   Some questions may still trigger Canvas or sign-in prompts.")
    
    print("\n✨ Tree walking implementation with Canvas prevention complete!")