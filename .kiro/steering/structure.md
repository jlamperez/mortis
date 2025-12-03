---
inclusion: always
---

# Project Structure

## Directory Layout

```
mortis/
├── src/mortis/          # Main application package
│   ├── app.py          # Gradio UI and main entry point
│   ├── tools.py        # LLM API integration and tool calling
│   ├── robot.py        # Robot arm control and gesture definitions
│   └── calibrate.py    # Robot calibration script
├── examples/           # Example/demo scripts
│   └── demo.py        # Simple demo runner
├── assets/            # Static assets (images, backgrounds)
│   └── image.png      # Halloween background image
├── .cache/            # Runtime cache (calibration data)
├── .env               # Environment variables (not committed)
├── pyproject.toml     # Project metadata and dependencies
├── uv.lock            # Locked dependency versions
├── Makefile           # Build and run commands
└── README.md          # User documentation
```

## Module Organization

### `src/mortis/app.py`
- Gradio UI construction
- Chat interface setup
- Model selection dropdown
- CSS styling with base64-encoded background
- Main entry point (`main()` function)

### `src/mortis/tools.py`
- LLM API client
- Tool definition for structured outputs
- `ask_mortis()` function: sends user message, receives structured response
- Coordinates LLM response with robot gesture execution
- Manages global `mortis_arm` instance

### `src/mortis/robot.py`
- `MortisArm` class: robot connection and control
- `GESTURES` dictionary: predefined gesture sequences
- Each gesture is a list of (pose_dict, delay) tuples
- Available gestures: idle, wave, point_left, point_right, grab, drop
- Pose dictionaries specify joint positions in degrees

### `src/mortis/calibrate.py`
- Standalone calibration script
- Configures SO101Follower with calibration directory
- Interactive calibration process

## Code Conventions

### Import Style
- Standard library imports first
- Third-party imports second
- Local imports last
- Use `from .module import` for intra-package imports

### Path Handling
- Use `pathlib.Path` for all file paths
- `REPO_ROOT` defined as `Path(__file__).resolve().parents[2]`
- Relative paths from repo root for assets and config

### Robot Control Pattern
- Always check `mortis_arm.connected` before operations
- Connect once, reuse connection
- Disconnect on app unload (Gradio `demo.unload()`)
- Gestures execute synchronously with blocking delays

### API Response Handling
- Structured tool calling enforced via `tool_choice`
- Parse `tool_calls[0].function.arguments` as JSON
- Extract: message (str), mood (enum), gesture (enum)
- Execute gesture immediately after parsing response

## Entry Points

Defined in `pyproject.toml`:
- `mortis` → `mortis.app:main` (run the Gradio app)
- `calibrate` → `mortis.calibrate:main` (calibrate robot)
