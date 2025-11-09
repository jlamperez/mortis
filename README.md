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

## 🤖 Robot Arm Calibration

Before using the robotic arm for the first time, it needs to be calibrated.
This process sets the initial positions and limits for each motor.

To start the calibration, connect the arm and run:

```bash
make calibrate
```

This command executes the `src/mortis/calibrate.py` script, which will guide you through the calibration process.
Follow the on-screen instructions. The calibration data will be saved in the `.cache/calibration/so101/` directory.

## �🧪 Useful Commands

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
| `make check-env`      | Verifies `.env` exists and required env vars (e.g., `COMPACTIFAI_API_KEY`).  |
| `make add-<pkg>`      | Adds a dependency via `uv add` (e.g., `make add-python-dotenv`).             |
| `make export`         | Exports pinned deps to `requirements.txt` from `uv.lock`.                    |
| `make clean`          | Removes build/test caches and artifacts.

## 🧛 Credits

Created by Jorge Lamperez
Part of the CompactifAI Halloween Challenge 2025 🎃

## 📜 License

MIT License © 2025 Jorge Lamperez