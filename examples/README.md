# Examples

This directory contains example scripts demonstrating how to use the gemini-ask package.

## Prerequisites

Before running any examples:

1. **Start Chrome with remote debugging**:
   ```bash
   chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug
   ```

2. **Open Gemini**: Navigate to `https://gemini.google.com` in a Chrome tab

3. **Install the package**:
   ```bash
   cd .. && pip install -e .
   ```

## Available Examples

### 1. Basic Example (`basic_example.py`)

The simplest way to use the automation package.

**What it does:**
- Connects to Chrome
- Asks one question
- Displays the response

**Run it:**
```bash
python basic_example.py
```

**Expected output:**
```
gemini-ask - Basic Example
==================================================
1. Connecting to Chrome DevTools...
✅ Connected successfully!

2. Asking question: 'What is the capital of France?'

3. Response received:
==============================
Q: What is the capital of France?
A: The capital of France is Paris.
==============================

4. Cleaning up...
✅ Done!
```

### 2. Advanced Example (`advanced_example.py`)

Demonstrates multiple features and error handling.

**What it does:**
- Asks multiple questions
- Takes screenshots
- Handles errors gracefully
- Saves conversation log
- Uses context manager

**Run it:**
```bash
python advanced_example.py
```

**Features demonstrated:**
- Multiple questions in sequence
- Screenshot capture
- Error handling for timeouts
- Conversation logging
- Progress indicators

### 3. Step-by-Step Example (`step_by_step_example.py`)

Shows manual control over each automation step.

**What it does:**
- Manually controls each step
- Shows typing progress
- Takes screenshots at each stage
- Provides detailed feedback

**Run it:**
```bash
python step_by_step_example.py
```

**Steps demonstrated:**
1. Connection
2. Initial screenshot
3. Clicking input field
4. Typing with progress
5. Screenshot of typed question
6. Pressing Enter
7. Waiting for response
8. Displaying response
9. Final screenshot
10. Page statistics

## Output Files

The examples create several output files:

- `*.png` - Screenshots of the automation process
- `conversation_log.txt` - Complete conversation log (advanced example)
- `screenshots/` - Directory with timestamped screenshots

## Troubleshooting Examples

### Common Issues

1. **"No Gemini tab found"**
   ```bash
   # Make sure Gemini is open
   open https://gemini.google.com
   ```

2. **Connection refused**
   ```bash
   # Check if Chrome is running with debugging
   ps aux | grep chrome | grep remote-debugging
   ```

3. **Examples fail to import**
   ```bash
   # Install package in development mode
   pip install -e ..
   ```

### Debug Mode

Run examples with debug output:

```bash
export PYTHONPATH=..
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
exec(open('basic_example.py').read())
"
```

## Customizing Examples

### Modify Questions

Edit the questions in any example:

```python
# In advanced_example.py
questions = [
    "Your custom question here",
    "Another question",
    # Add more questions...
]
```

### Change Timeouts

Adjust timeout values:

```python
# Longer timeout for complex questions
response = gemini.ask_question(question, timeout=60)
```

### Custom Screenshots

Change screenshot behavior:

```python
# Take screenshots at custom intervals
if gemini.take_screenshot(f"custom_{timestamp}.png"):
    print("Screenshot saved!")
```

## Creating Your Own Examples

Use this template for new examples:

```python
#!/usr/bin/env python3
"""
Your custom example description
"""

from chrome_gemini_automation import GeminiAutomation, GeminiAutomationError

def main():
    with GeminiAutomation() as gemini:
        try:
            gemini.connect()
            
            # Your automation code here
            response = gemini.ask_question("Your question")
            print(response)
            
        except GeminiAutomationError as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
```

## Performance Tips

1. **Use delays between questions** to avoid overwhelming Gemini
2. **Implement retry logic** for flaky connections
3. **Take screenshots sparingly** to avoid performance issues
4. **Use context managers** for proper cleanup
5. **Handle timeouts gracefully** for long responses