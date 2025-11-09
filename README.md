# 👻 Mortis: Haunted Control Room

**Mortis** is an interactive AI experience built with [Gradio](https://www.gradio.app/) for the **CompactifAI 🎃 Halloween Challenge** by **Multiverse**.
At its core, Mortis connects to a powerful **Large Language Model (LLM)** through the **CompactifAI API**, giving life to a ghostly digital entity that speaks, feels, and acts.

As you converse with Mortis, its responses are not limited to text — the spirit manifests itself through a **SeeedStudio SO101 robotic arm**, whose gestures are controlled via the **[LeRobot](https://huggingface.co/lerobot)** framework from Hugging Face.
Each motion of the arm reflects Mortis’s emotions and mood, as if the mechanical limb were **possessed** — transforming AI intent into tangible, spectral movement.

This project explores the haunting intersection of **language, embodiment, and robotics**, blending cutting-edge AI with creative storytelling to build a truly haunted control room 👻🤖.


![Mortis Demo](assets/image.png)


## 🚀 Features

- Web UI with a custom Halloween background 🎃
- Chat with CompactifAI models
- Secure `.env` environment variable loading
- Dependency management with [`uv`](https://github.com/astral-sh/uv)
- Developer-friendly `Makefile` shortcuts


## 🧰 Requirements

- **Python 3.12+**
- **uv** installed
  ```bash
  pip install uv
  ```


## ⚙️ Installation

Clone the repository and sync dependencies with uv:

```bash
git clone https://github.com/jlamperez/mortis.git
cd mortis
uv sync
```

## 🔑 Environment Setup

Create a .env file in the project root:

```bash
COMPACTIFAI_API_KEY=your_api_key_here
API_BASE_URL=https://api.compactif.ai/v1/chat/completions
```

(Do not commit .env; it’s already ignored in .gitignore)

## 🕹️ Run Mortis

Run via CLI

```bash
make run
```

Or directly as a Python module

```bash
make run-m
# or without make:
uv run python -m mortis.app
```

Mortis will be available at dark mode in http://127.0.0.1:7860/?__theme=dark

## 💬 Talking to Mortis

Once Mortis is running, you can interact with it using natural language. Here are a few examples to get you started and see the arm in action:

- Hi Mortis, introduce yourself with a sinister bow.
- Mortis, someone is entering the lab from right side… act!
- No, they are in the left side.
- Grab the cursed vial and then release it.
- Drop the artifact, Mortis. Let the shadows claim it.
- Mortis, the lights are flickering… check the power core.
- Raise your claw, Mortis, and point at the source of the whisper.
- Mortis, something moves behind you — react swiftly.
- Place the relic on the altar, then retreat into the shadows.
- Mortis, drop to one knee before the entity and await command.
- Mortis, raise the cursed vial… and let one drop spill.
- Step back, Mortis. The experiment has begun without you.


## 🤖 Robot Arm Calibration

Before using the robotic arm for the first time, it needs to be calibrated.
This process sets the initial positions and limits for each motor.

To start the calibration, connect the arm and run:

```bash
make calibrate
```

This command executes the `src/mortis/calibrate.py` script, which will guide you through the calibration process.
Follow the on-screen instructions. The calibration data will be saved in the `.cache/calibration/so101/` directory.

## 🦾 Testing Gestures

To test a specific gesture without running the full application, you can use the `test-gesture` command:

```bash
make test-gesture
```

This command executes the main block of `src/mortis/robot.py`, which connects to the arm, performs a pre-defined gesture, and then disconnects. This is very useful for fine-tuning the movements of each gesture.

By default, it performs the `"drop"` gesture. To test a different one (e.g., `"wave"`), you can edit the `if __name__ == "__main__"` block at the end of `src/mortis/robot.py`:

```python
# In src/mortis/robot.py

if __name__ == "__main__":
    # ... (connection logic is handled here) ...

    # Change "drop" to any other gesture name from the GESTURES dictionary
    mortis_arm.move_arm("wave") # <-- EDIT THIS LINE

    mortis_arm.disconnect()
```

## 🧪 Useful Commands

| Command               | What it does                                                                 |
|-----------------------|------------------------------------------------------------------------------|
| `make help`           | Prints all available targets and what they do.                               |
| `make install`        | Installs dependencies with `uv` (creates `.venv/` if missing).               |
| `make sync`           | Alias of `install` (re-sync deps from `pyproject.toml` / `uv.lock`).         |
| `make lock`           | Creates/updates `uv.lock` with resolved versions.                            |
| `make upgrade`        | Upgrades dependencies and regenerates `uv.lock`, then syncs.                 |
| `make run`            | Runs the CLI entrypoint `$(APP)` (requires `[project.scripts]`).             |
| `make run-m`          | Runs the app as a module: `python -m $(MODULE)`.                             |
| `make calibrate`      | Runs the robot arm calibration script.                                       |
| `make demo`           | Runs the example script at `$(DEMO)`.                                        |
| `make test-gesture`   | Executes a test gesture with the robotic arm (`mortis.robot`).               |
| `make check-env`      | Verifies `.env` exists and required env vars (e.g., `COMPACTIFAI_API_KEY`).  |
| `make add-<pkg>`      | Adds a dependency via `uv add` (e.g., `make add-python-dotenv`).             |
| `make export`         | Exports pinned deps to `requirements.txt` from `uv.lock`.                    |
| `make clean`          | Removes build/test caches and artifacts.

## 🧛 Credits

Created by Jorge Lamperez
Part of the CompactifAI Halloween Challenge 2025 🎃

## 📜 License

MIT License © 2025 Jorge Lamperez