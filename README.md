# gemini-ask

**An unofficial Python CLI for interacting directly with the gemini.google.com web interface.**

Get instant AI answers without opening a browser, creating accounts, or managing API keys. Just install and ask!

## Quick Start

### Install
```bash
pip install git+https://github.com/ricardodeazambuja/gemini-ask.git
```

### Ask Questions
```bash
gemini-ask "What is the capital of France?"
# → The capital of France is Paris.

gemini-ask "Write a Python function to add two numbers"
# → def add_numbers(a, b): return a + b

gemini-ask "What's 15% of 240?"
# → 15% of 240 is 36.
```

**That's it!** No accounts, no API keys, no browser setup required.

## Why gemini-ask?

✅ **Zero setup** - Works instantly after install  
✅ **No sign-ups** - Uses your existing Google account through Chrome  
✅ **Works offline** - No external API dependencies  
✅ **Shell friendly** - Perfect for scripts and automation  
✅ **Free** - Uses Google Gemini directly, no middleman costs

## Common Use Cases

### Quick Answers
```bash
gemini-ask "How do I convert Celsius to Fahrenheit?"
gemini-ask "What are the NATO phonetic alphabet letters?"
gemini-ask "Explain quantum computing in simple terms"
```

### Code Help
```bash
gemini-ask "How do I reverse a string in Python?"
gemini-ask "Write a bash script to backup files"
gemini-ask "Debug this SQL query: SELECT * FROM users WHERE age > 25"
```

### Research & Writing
```bash
gemini-ask "Summarize the benefits of renewable energy"
gemini-ask "Write a professional email declining a meeting"
gemini-ask "What are the main causes of inflation?"
```

### Shell Integration
```bash
# Get word count of answer
gemini-ask "Explain photosynthesis" | wc -w

# Search for specific terms
gemini-ask "Python data structures" | grep -i "list"

# Save answer to file
gemini-ask "Linux commands cheat sheet" > cheatsheet.txt

# Process multiple questions
echo "What is Docker?" | gemini-ask --pipe --quiet
```

## Custom Prompts

Control how gemini-ask responds:

```bash
# Brief answers
gemini-ask "Explain AI" --system-prompt "Answer in one sentence"

# Specific format
gemini-ask "List programming languages" --system-prompt "Return as numbered list"

# Custom style
gemini-ask "Explain databases" --system-prompt "Explain like I'm 5 years old"
```

### Environment Variables
```bash
export GEMINI_SYSTEM_PROMPT="Always be concise and technical"
gemini-ask "What is machine learning?"
```

### Config Files
```bash
echo "Answer in a friendly, conversational tone" > .gemini_prompt
gemini-ask "How does WiFi work?"
```

## Installation Options

### Method 1: pip (Recommended)
```bash
pip install git+https://github.com/ricardodeazambuja/gemini-ask.git
```

### Method 2: From Source
```bash
git clone https://github.com/ricardodeazambuja/gemini-ask
cd gemini-ask
pip install .
```

## System Requirements

- **Python 3.7+**
- **Google Chrome or Chromium** (auto-installed on most systems)
- **Internet connection** (for accessing Gemini)

**That's it!** gemini-ask automatically:
- Finds and launches Chrome
- Opens Gemini
- Handles all the technical details

*Tested on Google Chrome 137.0.7151.103 / Ubuntu 22.04.5 LTS*

## Advanced Usage

### Quiet Mode for Scripts
```bash
# Only output the answer (perfect for scripts)
echo "What is 2+2?" | gemini-ask --pipe --quiet
# → 4

# Use in shell scripts
answer=$(echo "Best practices for password security" | gemini-ask --pipe --quiet)
echo "Security tip: $answer"
```

### Batch Processing
```bash
# Process multiple questions from a file
cat questions.txt | gemini-ask --pipe --quiet > answers.txt

# Process questions in a loop
for topic in "AI" "Blockchain" "IoT"; do
  echo "Explain $topic in one paragraph" | gemini-ask --pipe --quiet
done
```

### Performance & Interface Options
```bash
# Fast typing for quick questions
gemini-ask --typing-speed 0.01 "What is 2+2?"

# Slower typing for complex questions (more human-like)
gemini-ask --typing-speed 0.5 "Write detailed analysis of..."

# Background operation with minimized window
gemini-ask --minimized "Question"

# Silent background mode
gemini-ask --minimized --quiet "Question" > output.txt
```

### Command Options
```bash
gemini-ask --help                           # Show all options
gemini-ask --show-prompt                    # Show current system prompt
gemini-ask --timeout 60 "Complex question"  # Custom timeout
gemini-ask --headless "Question"            # Run without GUI
gemini-ask --verbose "Question"             # Show detailed info
gemini-ask --typing-speed 0.2 "Question"   # Custom typing speed
gemini-ask --minimized "Question"           # Start minimized
```

## Using with Gemini Pro Subscription

By default, **gemini-ask is completely secure** - it creates a temporary, isolated Chrome profile that contains no personal data, cookies, or login sessions from your main browser. This temporary profile is deleted when Chrome closes.

However, if you have a **Gemini Pro subscription** and want to access Pro features via gemini-ask, you'll need to use a Chrome instance that's logged into your Google account. This requires special security considerations.

### 🔒 Security Warning

⚠️ **CRITICAL SECURITY NOTICE**  
When Chrome runs with `--remote-debugging-port`, **ANY application on your computer gets FULL ACCESS to:**
- All open browser tabs and their content
- Cookies, passwords, and active login sessions  
- Ability to navigate to any website as you
- Read and modify any webpage content
- Access to all browser data and history

**NEVER enable remote debugging on browsers with:**
- Banking or financial accounts
- Work or corporate accounts  
- Personal email or social media
- Any sensitive personal data

### 🎯 Recommended Secure Setup

The safest way to use Gemini Pro with gemini-ask:

#### Step 1: Create a Dedicated Google Account
```bash
# Create a new Google account specifically for gemini-ask
# Use an email like: your-name-gemini@gmail.com
```

#### Step 2: Share Gemini Pro Access
1. Add the new account to your **Google One family plan**
2. This gives the dedicated account Gemini Pro access
3. No access to your personal emails, files, or data

#### Step 3: Set Up Chrome with Dedicated Profile
```bash
# Create a new Chrome user data directory
mkdir -p ~/chrome-gemini-profile

# Launch Chrome with debugging enabled (ONLY for the dedicated account)
# Linux/macOS:
google-chrome --remote-debugging-port=9222 --user-data-dir="$HOME/chrome-gemini-profile" --no-first-run

# Windows:
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\chrome-gemini-profile" --no-first-run
```

#### Step 4: Login Once
1. Chrome will open with a clean profile
2. Navigate to [gemini.google.com](https://gemini.google.com)
3. Login with your **dedicated account only**
4. Verify Gemini Pro features are available

#### Step 5: Use gemini-ask with Existing Session
```bash
# Connect to your existing Chrome session (don't auto-launch new Chrome)
gemini-ask --no-auto-launch "What are the advanced features of Gemini Pro?"

# The Chrome window will stay open with your session intact
# No need to login again for future gemini-ask commands
```

### Alternative: Profile Copying (Higher Risk)

If you prefer to copy an existing Chrome profile, follow these steps **at your own risk**:

#### Chrome Profile Locations:
```bash
# Windows
%LOCALAPPDATA%\Google\Chrome\User Data\Default

# macOS  
~/Library/Application Support/Google/Chrome/Default

# Linux
~/.config/google-chrome/Default
```

#### Copying Process:
```bash
# 1. COMPLETELY CLOSE Chrome first
pkill chrome  # Linux/macOS
# or Task Manager on Windows

# 2. Copy profile to new location
# Linux/macOS:
cp -r ~/.config/google-chrome/Default ~/chrome-gemini-profile/Default

# Windows (PowerShell):
Copy-Item "$env:LOCALAPPDATA\Google\Chrome\User Data\Default" -Destination "$env:USERPROFILE\chrome-gemini-profile\Default" -Recurse

# 3. Launch with debugging
google-chrome --remote-debugging-port=9222 --user-data-dir="$HOME/chrome-gemini-profile"
```

⚠️ **This method exposes ALL your browser data to remote debugging access.**

### Using Pro Features

Once connected to a Gemini Pro session:

```bash
# Access Pro features through gemini-ask
gemini-ask --no-auto-launch "Generate a detailed market analysis report"
gemini-ask --no-auto-launch "Create a comprehensive business plan outline"
gemini-ask --no-auto-launch "Analyze this data and provide insights: [your data]"

# Your Pro subscription features like longer responses, 
# advanced reasoning, and priority access will be available
```

### Command Options for Pro Usage

```bash
gemini-ask --no-auto-launch "Question"          # Connect to existing Chrome
gemini-ask --cleanup-chrome "Question"          # Close Chrome when done
gemini-ask --port 9223 --no-auto-launch "Q"    # Use different port
gemini-ask --timeout 120 "Complex question"    # Longer timeout for Pro features
```

### Best Practices

✅ **DO:**
- Use a dedicated Google account for gemini-ask
- Share Pro access via Google One family plan
- Keep the Chrome window minimized during use
- Close Chrome when finished with sensitive work

❌ **DON'T:**
- Use your main Google account with remote debugging
- Enable debugging on browsers with personal data
- Leave debugging enabled permanently
- Share or expose the debugging port externally

## Troubleshooting

### Chrome not found
**Problem:** "Chrome not found" error  
**Solution:** Install Google Chrome:
```bash
# Ubuntu/Debian
sudo apt install google-chrome-stable

# macOS
brew install --cask google-chrome

# Windows: Download from https://chrome.google.com
```

### Connection issues
**Problem:** "Failed to connect" error  
**Solution:** 
1. Close all Chrome windows
2. Run the command again (gemini-ask will auto-launch Chrome)
3. Make sure you're logged into Google in Chrome

### Slow responses
**Problem:** gemini-ask takes a long time  
**Solution:**
```bash
# Increase timeout for complex questions
gemini-ask --timeout 120 "Write a detailed analysis of..."

# Use headless mode (faster)
gemini-ask --headless "Quick question"
```

## API / Programming

For developers who want to integrate gemini-ask into Python applications:

### Basic Python Usage
```python
from gemini_ask import GeminiAutomation

# Simple usage
with GeminiAutomation() as gemini:
    gemini.connect()
    response = gemini.ask_question("What is machine learning?")
    print(response)
```

### Advanced Python Usage
```python
from gemini_ask import GeminiAutomation, GeminiAutomationError

# Custom configuration
gemini = GeminiAutomation(
    devtools_port=9222,
    headless=False,
    auto_launch=True
)

try:
    if gemini.connect():
        # Ask multiple questions
        questions = [
            "What is Python?",
            "Explain data structures",
            "How does machine learning work?"
        ]
        
        for question in questions:
            response = gemini.ask_question(question, timeout=60)
            print(f"Q: {question}")
            print(f"A: {response}\n")
            
except GeminiAutomationError as e:
    print(f"Error: {e}")
finally:
    gemini.close()
```

### Class Reference

#### GeminiAutomation Parameters
- `devtools_port`: Chrome DevTools port (default: 9222)
- `host`: Host address (default: "localhost")
- `auto_launch`: Automatically launch Chrome if not running (default: True)
- `headless`: Run Chrome in headless mode (default: False)
- `user_data_dir`: Custom Chrome user data directory (default: temp dir)
- `quiet`: Suppress all output (default: False)
- `typing_speed`: Typing speed in seconds per character (default: 0.05)
- `minimized`: Start browser window minimized (default: False)

#### Key Methods
- `connect() -> bool`: Connect to Chrome DevTools and find Gemini tab
- `ask_question(question: str, timeout: int = 30) -> str`: Ask a question and wait for response
- `close()`: Close WebSocket connection and cleanup

#### Exception Handling
```python
from gemini_ask import (
    GeminiAutomationError,  # Base exception
    ConnectionError,        # Connection issues
    InteractionError,       # UI interaction issues
    TimeoutError,          # Response timeout
    ElementNotFoundError   # UI elements not found
)

try:
    with GeminiAutomation() as gemini:
        gemini.connect()
        response = gemini.ask_question("Hello")
        print(response)
except ConnectionError:
    print("Could not connect to Chrome")
except ElementNotFoundError:
    print("Gemini interface not found")
except TimeoutError:
    print("Gemini took too long to respond")
except InteractionError as e:
    print(f"Failed to interact with Gemini: {e}")
```

## How It Works

gemini-ask uses Chrome DevTools Protocol to automate a real Chrome browser:

1. **Auto-launches Chrome** with debugging enabled
2. **Opens Gemini** (gemini.google.com) automatically
3. **Types your question** using realistic keyboard simulation
4. **Waits for response** using advanced DOM analysis
5. **Extracts the answer** and returns clean text

This approach means:
- ✅ **No API limits** - Uses Gemini's web interface directly
- ✅ **Always up-to-date** - Works with latest Gemini features
- ✅ **No authentication** - Uses your existing Google login
- ✅ **Realistic interaction** - Behaves like a human user

### Canvas Prevention
gemini-ask automatically prevents Gemini from using "Canvas mode" (visual/drawing interface) by adding special instructions to questions. This ensures you always get text responses suitable for command-line use.

## Contributing

Found a bug or want to contribute? 

- **Bug Reports**: [GitHub Issues](https://github.com/ricardodeazambuja/gemini-ask/issues)
- **Source Code**: [GitHub Repository](https://github.com/ricardodeazambuja/gemini-ask)

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

**gemini-ask** - Get AI answers instantly from your command line 🚀
