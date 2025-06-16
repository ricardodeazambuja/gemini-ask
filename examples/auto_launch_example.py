#!/usr/bin/env python3
"""
Auto-launch example for gemini-ask

This example demonstrates the automatic Chrome launching capability.
No need to manually start Chrome - the package will do it for you!
"""

from gemini_ask import GeminiAutomation, GeminiAutomationError, ChromeLauncher


def basic_auto_launch_example():
    """Simple example with auto-launch enabled (default)"""
    
    print("🚀 gemini-ask - Auto-Launch Example")
    print("=" * 60)
    print("This example will automatically:")
    print("1. Find Chrome on your system")
    print("2. Launch Chrome with debugging enabled") 
    print("3. Open Gemini in a new tab")
    print("4. Ask a question")
    print("5. Clean up when done")
    print()
    
    try:
        # Auto-launch is enabled by default
        with GeminiAutomation() as gemini:
            print("🔌 Connecting (auto-launch enabled)...")
            gemini.connect()
            
            # Check status
            status = gemini.get_chrome_status()
            print(f"📊 Chrome status: {status['chrome_running']}")
            print(f"📋 Tabs open: {status['tabs_count']}")
            print(f"🎯 Gemini tab available: {status['gemini_tab_available']}")
            
            # Ask a question
            question = "What is the largest planet in our solar system?"
            print(f"\n❓ Asking: '{question}'")
            
            response = gemini.ask_question(question, timeout=45)
            
            print("\n✨ Response received:")
            print("=" * 40)
            print(response)
            print("=" * 40)
            
            # Note: Chrome will be left running by default
            # Use gemini.close(cleanup_chrome=True) to close Chrome too
    
    except GeminiAutomationError as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("- Make sure Chrome/Chromium is installed")
        print("- Check internet connection for Gemini access")


def headless_example():
    """Example using headless Chrome (no GUI)"""
    
    print("\n🔍 Headless Chrome Example")
    print("=" * 40)
    
    try:
        # Launch in headless mode (no visible browser window)
        with GeminiAutomation(headless=True) as gemini:
            print("🤖 Connecting in headless mode...")
            gemini.connect()
            
            # Headless mode is great for servers/automation
            question = "What is artificial intelligence?"
            response = gemini.ask_question(question, timeout=30)
            
            print(f"Q: {question}")
            print(f"A: {response[:100]}{'...' if len(response) > 100 else ''}")
            
    except GeminiAutomationError as e:
        print(f"❌ Headless error: {e}")


def custom_chrome_location_example():
    """Example with custom Chrome configuration"""
    
    print("\n🔧 Custom Configuration Example")
    print("=" * 40)
    
    try:
        # Custom configuration
        gemini = GeminiAutomation(
            devtools_port=9223,  # Custom port
            auto_launch=True,
            headless=False,
            user_data_dir="/tmp/my-chrome-profile"  # Custom profile
        )
        
        with gemini:
            print(f"🔌 Connecting on custom port {gemini.devtools_port}...")
            gemini.connect()
            
            # Show status
            status = gemini.get_chrome_status()
            print(f"🏠 Chrome path: {status.get('chrome_path', 'Unknown')}")
            print(f"📁 User data dir: {status.get('user_data_dir', 'Unknown')}")
            
            # Quick question
            response = gemini.ask_question("What is 5 + 5?", timeout=20)
            print(f"🧮 Math answer: {response}")
            
    except GeminiAutomationError as e:
        print(f"❌ Custom config error: {e}")


def chrome_launcher_standalone_example():
    """Example using ChromeLauncher directly"""
    
    print("\n⚙️ ChromeLauncher Standalone Example")
    print("=" * 40)
    
    try:
        # Use ChromeLauncher directly for more control
        with ChromeLauncher(devtools_port=9224) as launcher:
            
            # Check Chrome status
            print("🔍 Chrome executable search...")
            chrome_path = launcher.find_chrome_executable()
            print(f"🌐 Found Chrome: {chrome_path}")
            
            # Launch Chrome
            print("🚀 Launching Chrome...")
            success = launcher.launch_chrome(open_gemini=True, headless=False)
            
            if success:
                print("✅ Chrome launched successfully!")
                
                # Get detailed status
                status = launcher.get_status()
                print(f"📊 Status: {status}")
                
                # Now use regular GeminiAutomation (without auto-launch)
                with GeminiAutomation(devtools_port=9224, auto_launch=False) as gemini:
                    gemini.connect()
                    response = gemini.ask_question("What is Python?", timeout=30)
                    print(f"🐍 Python answer: {response[:80]}...")
            
            # ChromeLauncher will cleanup automatically
                
    except Exception as e:
        print(f"❌ Launcher error: {e}")


def no_auto_launch_example():
    """Example with auto-launch disabled (traditional mode)"""
    
    print("\n🔧 Manual Chrome Mode (Traditional)")
    print("=" * 40)
    print("This example requires manually starting Chrome first:")
    print("chrome --remote-debugging-port=9222")
    
    try:
        # Disable auto-launch (traditional mode)
        with GeminiAutomation(auto_launch=False) as gemini:
            print("🔌 Connecting to existing Chrome...")
            gemini.connect()
            
            response = gemini.ask_question("What is machine learning?", timeout=30)
            print(f"🤖 ML answer: {response[:80]}...")
            
    except GeminiAutomationError as e:
        print(f"❌ Manual mode error: {e}")
        print("💡 Try running: chrome --remote-debugging-port=9222")


def main():
    """Run all examples"""
    
    examples = [
        ("Basic Auto-Launch", basic_auto_launch_example),
        ("Headless Mode", headless_example), 
        ("Custom Configuration", custom_chrome_location_example),
        ("ChromeLauncher Standalone", chrome_launcher_standalone_example),
        ("Manual Chrome Mode", no_auto_launch_example)
    ]
    
    for name, example_func in examples:
        try:
            example_func()
        except KeyboardInterrupt:
            print(f"\n🛑 {name} interrupted by user")
            break
        except Exception as e:
            print(f"\n💥 {name} failed: {e}")
        
        print("\n" + "="*60 + "\n")
    
    print("🎉 Auto-launch examples completed!")
    print("\n💡 Tips:")
    print("- Auto-launch is enabled by default")
    print("- Use headless=True for server environments") 
    print("- Use cleanup_chrome=True to close Chrome when done")
    print("- Custom ports avoid conflicts with existing Chrome")


if __name__ == "__main__":
    main()