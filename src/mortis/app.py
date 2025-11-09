import base64
import json
import os

from pathlib import Path
import gradio as gr

from .tools import ask_mortis


REPO_ROOT = Path(__file__).resolve().parents[2]
BG_IMAGE = REPO_ROOT / "assets" / "image.png"

MODEL_CHOICES = [
    "cai-llama-3-1-8b-slim",
    "cai-llama-3-1-8b-slim-r",
    "cai-llama-3-3-70b-slim",
    "cai-llama-4-scout-slim",
    # "gpt-oss-20b", # No Tools
    # "gpt-oss-120b" # No Tools
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
    msg, mood, gesture = ask_mortis(message, model_name=model_name)

    body = {
        "mood": mood,
        "gesture": gesture
    }

    # Opcional: aquí podrías llamar a move_arm(gesture)
    print(json.dumps(body, ensure_ascii=False))

    # return "=== Mortis says ===\n" + msg + "\n" + json.dumps(body, ensure_ascii=False)
    return msg


def ui() -> gr.Blocks:
    css=build_css(BG_IMAGE)
    with gr.Blocks(fill_height=True, theme="soft", css=css) as demo:
        gr.Markdown(
            "# CompactifAI 🎃 Halloween 🎃 Challenge\n"
            "## Mortis: Haunted Control Room 👻🤖",
            elem_id="app-title"
        )

        with gr.Row(equal_height=True):
            with gr.Column():
                model_dd = gr.Dropdown(
                    choices=MODEL_CHOICES,
                    value=MODEL_CHOICES[0],
                    label="LLM model",
                    info="Select Mortis LLM model",
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
                    sources=["webcam"],   # usa la cámara del navegador
                    label="Camera view",
                    height=480,
                    include_audio=False,  # sin audio
                )
                gr.Markdown("**Webcam (local, no data upload)**\nThe video is only processed in your browser.")
    return demo


def main():
    port = int(os.getenv("PORT", "7860"))
    ui().launch(server_name="127.0.0.1", server_port=port, show_error=True,)
