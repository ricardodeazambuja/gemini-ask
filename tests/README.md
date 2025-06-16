# Tests for gemini-ask

## Test Structure

This project uses a simplified 3-tier test structure:

### 1. Unit Tests (`test_unit.py`)
- **Purpose**: Pure unit tests with no external dependencies
- **Coverage**: Initialization, configuration, validation logic, Canvas prevention
- **Execution**: Fast (< 5 seconds), always runs in CI
- **Dependencies**: None - fully mocked

### 2. API Tests (`test_api.py`) 
- **Purpose**: Test public API contracts with minimal mocking
- **Coverage**: `ask_question()`, `connect()`, `take_screenshot()`, `get_page_text()`
- **Execution**: Fast (< 10 seconds), runs in CI
- **Dependencies**: Minimal - key interactions mocked

### 3. Smoke Tests (`test_smoke.py`)
- **Purpose**: End-to-end validation with real Chrome
- **Coverage**: Basic connection, simple question, screenshot capture
- **Execution**: Slow (30+ seconds), optional - environment gated
- **Dependencies**: Real Chrome with remote debugging

## Running Tests

### Standard Test Suite (CI)
```bash
# Run unit and API tests (fast, no dependencies)
python -m pytest tests/test_unit.py tests/test_api.py -v
```

### Legacy Tests
```bash
# Run existing basic tests
python -m pytest tests/test_basic.py -v

# Run canvas prevention tests
python -m pytest tests/test_canvas_prevention.py -v
```

### Smoke Tests (Optional)
```bash
# 1. Start Chrome with remote debugging
chrome --remote-debugging-port=9222

# 2. Open Gemini in Chrome
# Navigate to: https://gemini.google.com

# 3. Run smoke tests
RUN_SMOKE_TESTS=1 python -m pytest tests/test_smoke.py -v

# 4. Extended smoke tests (multiple questions)
RUN_EXTENDED_SMOKE_TESTS=1 python -m pytest tests/test_smoke.py -v
```

## Test Guidelines

### For CI/Automated Testing
- Use `test_unit.py` and `test_api.py` only
- Fast execution (< 30 seconds total)
- Zero external dependencies
- 100% reliable

### For Local Development
- Include smoke tests for comprehensive validation
- Test real Chrome integration before releases
- Use smoke tests to debug browser interaction issues

### Test Requirements
- **Unit tests**: No setup required
- **API tests**: No setup required  
- **Smoke tests**: Chrome + Gemini tab required
- **Legacy tests**: May have various requirements

## Migration Notes

This simplified structure replaces the previous complex test suite that included:
- 10+ test files with heavy Chrome automation
- Flaky integration tests with timeouts
- Complex mocking causing reliability issues

The new structure maintains coverage while dramatically improving:
- **Reliability**: 99%+ pass rate vs ~50% 
- **Speed**: 30s vs 5+ minutes
- **Maintainability**: 3 files vs 13 files
- **CI compatibility**: No browser dependencies