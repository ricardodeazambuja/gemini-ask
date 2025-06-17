# gemini-ask

**Ask questions to Google Gemini from your command line**

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