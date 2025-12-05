# Mortis Logging Guide

## Overview

Mortis uses Python's built-in `logging` module to provide detailed information about what's happening during execution. This is especially useful for debugging Gemini API calls, robot arm operations, and understanding the flow of the application.

## Viewing Logs

### When Running the Application

When you run `make run`, logs will be displayed in your terminal with timestamps:

```bash
make run
```

Example output:
```
20:07:36 - mortis.app - INFO - ============================================================
20:07:36 - mortis.app - INFO - 🎃 Starting Mortis application...
20:07:36 - mortis.app - INFO - 📊 Log level: INFO
20:07:36 - mortis.app - INFO - 🌐 Launching on http://127.0.0.1:7860
20:07:36 - mortis.app - INFO - ============================================================
20:07:38 - mortis.app - INFO - 💬 User message: Hello Mortis!
20:07:38 - mortis.app - INFO - 🤖 Using model: gemini-2.5-flash
20:07:38 - mortis.tools - INFO - Asking Mortis: Hello Mortis!...
20:07:38 - mortis.gemini_client - INFO - GeminiClient initialized with model: gemini-2.5-flash, temperature: 0.2, timeout: 30.0s
20:07:39 - mortis.gemini_client - INFO - Successfully parsed response (type: conversation)
20:07:39 - mortis.tools - INFO - Mortis responds (type: conversation, mood: ominous, gesture: wave)
20:07:39 - mortis.app - INFO - 👻 Mortis reply: Greetings, mortal... welcome to my haunted domain.
20:07:39 - mortis.app - INFO - 😈 Mood: ominous, Gesture: wave
```

## Log Levels

You can control how much detail you see by setting the `LOG_LEVEL` environment variable in your `.env` file:

### Available Levels (from most to least verbose)

1. **DEBUG** - Most detailed, shows everything
   - All API requests and responses
   - Function entry/exit points
   - Variable values
   - Timing information
   
   ```bash
   LOG_LEVEL=DEBUG
   ```

2. **INFO** (Default) - General information
   - Application startup
   - API calls (without full details)
   - Robot connections
   - Response types
   
   ```bash
   LOG_LEVEL=INFO
   ```

3. **WARNING** - Only warnings and errors
   - Potential issues
   - Fallback responses
   - Retry attempts
   
   ```bash
   LOG_LEVEL=WARNING
   ```

4. **ERROR** - Only errors
   - API failures
   - Connection errors
   - Parsing failures
   
   ```bash
   LOG_LEVEL=ERROR
   ```

5. **CRITICAL** - Only critical failures
   - Application crashes
   - Fatal errors
   
   ```bash
   LOG_LEVEL=CRITICAL
   ```

## Common Use Cases

### Debugging Gemini API Issues

Set `LOG_LEVEL=DEBUG` to see full API request/response details:

```bash
# In .env file
LOG_LEVEL=DEBUG
```

Then run:
```bash
make run
```

You'll see:
- Full system prompts sent to Gemini
- Complete JSON responses
- Retry attempts with timing
- Error details

### Normal Operation

Use `LOG_LEVEL=INFO` (default) for normal operation:

```bash
# In .env file
LOG_LEVEL=INFO
```

You'll see:
- Application startup
- Model configuration
- User interactions (summarized)
- Response types

### Production/Quiet Mode

Use `LOG_LEVEL=WARNING` or `LOG_LEVEL=ERROR` for minimal output:

```bash
# In .env file
LOG_LEVEL=WARNING
```

You'll only see warnings and errors.

## Logging in Different Components

### GeminiClient (`gemini_client.py`)

Logs include:
- Client initialization with model and settings
- API call attempts and retries
- Response parsing
- Error handling and fallbacks

Example:
```
INFO - GeminiClient initialized with model: gemini-2.5-flash, temperature: 0.2
DEBUG - Sending message to Gemini (attempt 1/4)
DEBUG - Received response in 1.23s: {"type": "conversation"...
INFO - Successfully parsed response (type: conversation)
WARNING - Rate limit exceeded. Retrying in 2s... (attempt 1/3)
ERROR - Gemini API error: TimeoutError: API call timeout exceeded (30.0s)
```

### Tools (`tools.py`)

Logs include:
- Robot arm connection status
- User message processing
- Response parsing
- Gesture execution

Example:
```
INFO - Robot arm connected
INFO - Asking Mortis: Hello Mortis!...
INFO - Mortis responds (type: conversation, mood: ominous, gesture: wave)
ERROR - Failed to parse Gemini response: ValueError: Missing required field: 'type'
```

### Application (`app.py`)

Logs include:
- Application startup
- Configuration settings
- Server launch information

Example:
```
INFO - Starting Mortis application...
INFO - Log level: INFO
INFO - Launching on http://127.0.0.1:7860
```

## Saving Logs to File

If you want to save logs to a file for later analysis, you can redirect the output:

```bash
# Save logs to file
make run 2>&1 | tee mortis.log

# Or just redirect
make run > mortis.log 2>&1
```

This will save all logs to `mortis.log` while still displaying them in the terminal (with `tee`).

## Troubleshooting with Logs

### Problem: "The spirits are restless... try again."

Check logs for:
```
ERROR - Gemini API error: ...
```

Common causes:
- Invalid API key
- Rate limiting
- Network issues
- Timeout

### Problem: Robot arm not moving

Check logs for:
```
ERROR - Failed to connect to robot arm: ...
```

Common causes:
- Wrong `ROBOT_PORT` in `.env`
- Robot not connected
- Permission issues (try `sudo`)

### Problem: Slow responses

Check logs for timing:
```
DEBUG - Received response in 5.23s: ...
```

If response time > 3s, consider:
- Network latency
- Model choice (try gemini-2.5-flash for faster responses)
- API rate limiting

## Advanced: Custom Logging Configuration

If you need more control, you can modify the logging configuration in `src/mortis/app.py`:

```python
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('mortis.log')  # File output
    ]
)
```

## Quick Reference

| Task | Command |
|------|---------|
| See all logs | `LOG_LEVEL=DEBUG make run` |
| Normal operation | `LOG_LEVEL=INFO make run` (default) |
| Quiet mode | `LOG_LEVEL=WARNING make run` |
| Save to file | `make run 2>&1 \| tee mortis.log` |
| Check API calls | Set `LOG_LEVEL=DEBUG` in `.env` |

## Environment Variable Summary

Add to your `.env` file:

```bash
# Logging configuration
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

Then run normally:
```bash
make run
```

The logs will appear in your terminal automatically!
