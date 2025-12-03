import base64
import json
import os
import logging

from pathlib import Path
import gradio as gr

from .tools import ask_mortis, mortis_arm


REPO_ROOT = Path(__file__).resolve().parents[2]
BG_IMAGE = REPO_ROOT / "assets" / "kiroween.png"

MODEL_CHOICES = [
    "gemini-2.5-flash",
    "gemini-2.0-flash-exp",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
]


def build_css(image_path: str) -> str:
    """Background with custom image."""
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    return f"""
    .gradio-container {{
    background-image: url("data:image/png;base64,{b64}");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
    }}

    footer::after{{
    content: "by: Jorge Lamperez 🤖";
    margin-left: 8px;
    opacity: .85;
    }}
    """


def mortis_reply(message, history, model_name):
    logger = logging.getLogger(__name__)
    logger.info(f"💬 User message: {message[:50]}{'...' if len(message) > 50 else ''}")
    logger.info(f"🤖 Using model: {model_name}")
    
    msg, mood, gesture = ask_mortis(message, model_name=model_name)
    
    logger.info(f"👻 Mortis reply: {msg[:50]}{'...' if len(msg) > 50 else ''}")
    logger.info(f"😈 Mood: {mood}, Gesture: {gesture}")
    
    return msg


def ui() -> gr.Blocks:
    css=build_css(BG_IMAGE)
    with gr.Blocks(fill_height=True, theme="soft", css=css) as demo:
        gr.Markdown(
            "# Kiroween Hackathon 🎃\n"
            "## Mortis: Haunted Control Room 👻🤖",
            elem_id="app-title"
        )

        with gr.Row(equal_height=True):
            with gr.Column():
                model_dd = gr.Dropdown(
                    choices=MODEL_CHOICES,
                    value=MODEL_CHOICES[0],
                    label="Gemini Model",
                    info="Select Gemini model for Mortis",
                    interactive=True,
                )
                gr.ChatInterface(
                    fn=mortis_reply,
                    additional_inputs=[model_dd],
                    chatbot=gr.Chatbot(height=480, label="Mortis chat", type="messages"),
                    textbox=gr.Textbox(placeholder="Write your message here…"),
                    submit_btn="Send",
                )

            with gr.Column():
                gr.Video(
                    sources=["webcam"],
                    label="Camera view",
                    height=480,
                    include_audio=False,
                )
                gr.Markdown("**Webcam (local, no data upload)**\nThe video is only processed in your browser.")

        demo.unload(mortis_arm.disconnect)

    return demo


def main():
    # Configure logging - force configuration even if already set
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Remove existing handlers and reconfigure
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set up new handler with our format
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    ))
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level))
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("🎃 Starting Mortis application...")
    logger.info(f"📊 Log level: {log_level}")
    
    port = int(os.getenv("PORT", "7860"))
    logger.info(f"🌐 Launching on http://127.0.0.1:{port}")
    logger.info("=" * 60)
    
    ui().launch(server_name="127.0.0.1", server_port=port, show_error=True,)
