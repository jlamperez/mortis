---
inclusion: always
---

# Tech Stack

## Core Technologies

- **Python**: 3.12+ (required)
- **Package Manager**: `uv` (modern Python dependency manager)
- **Web Framework**: Gradio 5.49.1+
- **Robotics**: LeRobot 0.4.0+ with Feetech servo support
- **API Client**: requests library for LLM API
- **Environment**: python-dotenv for configuration

## Build System

The project uses a **Makefile** for all common operations. Always prefer `make` commands over direct CLI invocations.

### Common Commands

```bash
# Setup and dependencies
make install          # Install/sync dependencies
make sync            # Alias for install
make upgrade         # Upgrade all dependencies

# Running the application
make run             # Run via CLI entrypoint (mortis)
make run-m           # Run as Python module
make demo            # Run example script

# Robot operations
make calibrate       # Calibrate the SO101 arm (required first-time setup)
make test-gesture    # Test individual gestures

# Development
make check-env       # Verify .env configuration
make add-<package>   # Add new dependency (e.g., make add-numpy)
make export          # Export requirements.txt from uv.lock
make clean           # Remove build artifacts
```

## Environment Configuration

Required `.env` file in project root:
```
API_KEY=your_api_key
API_BASE_URL=https://api.example.com/v1/chat/completions
ROBOT_PORT=/dev/ttyACM1  # Optional, defaults to /dev/ttyACM1
PORT=7860                # Optional, defaults to 7860
```

## API Integration

- Uses LLM chat completions API
- Supports multiple models
- Implements structured tool calling for coordinated responses
- Tool: `perform_mortis_act` returns {message, mood, gesture}

## Robot Hardware

- **Device**: SeeedStudio SO101 robotic arm
- **Connection**: USB serial (typically /dev/ttyACM1)
- **Calibration**: Stored in `.cache/calibration/so101/`
- **Control**: LeRobot framework with SO101Follower driver
- **Modes**: 
  - `physical` - Connects to real robot hardware (default)
  - `simulation` - Simulates robot without hardware (for development/testing)
