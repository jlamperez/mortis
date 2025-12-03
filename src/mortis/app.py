import base64
import json
import os
import logging

from pathlib import Path
import gradio as gr

from .tools import ask_mortis, mortis_arm
from .stt_service import STTService, AudioProcessingError
from .tts_service import get_tts_service


REPO_ROOT = Path(__file__).resolve().parents[2]
BG_IMAGE = REPO_ROOT / "assets" / "kiroween.png"

MODEL_CHOICES = [
    "gemini-2.5-flash",
    "gemini-2.0-flash-exp",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
]

# Initialize STT service (global instance)
stt_service = None

def get_stt_service():
    """Lazy initialization of STT service."""
    global stt_service
    if stt_service is None:
        try:
            stt_service = STTService()
            logging.getLogger(__name__).info("✅ STT service initialized")
        except Exception as e:
            logging.getLogger(__name__).error(f"❌ Failed to initialize STT service: {e}")
            raise
    return stt_service


# Initialize TTS service (global instance)
tts_service = None

def get_tts_service_instance():
    """Lazy initialization of TTS service."""
    global tts_service
    if tts_service is None:
        try:
            tts_service = get_tts_service()
            logging.getLogger(__name__).info("✅ TTS service initialized")
        except Exception as e:
            logging.getLogger(__name__).error(f"❌ Failed to initialize TTS service: {e}")
            raise
    return tts_service


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


def process_audio_input(audio_path):
    """
    Process audio input from microphone and return transcribed text.
    
    Args:
        audio_path: Path to recorded audio file from Gradio
        
    Returns:
        Transcribed text or error message
    """
    logger = logging.getLogger(__name__)
    
    if audio_path is None:
        return ""
    
    try:
        logger.info(f"🎤 Processing audio input: {audio_path}")
        
        # Get STT service
        stt = get_stt_service()
        
        # Transcribe audio
        transcript = stt.transcribe(audio_path)
        
        if not transcript:
            logger.warning("⚠️ Audio transcription returned empty result")
            return ""
        
        logger.info(f"✅ Transcription successful: '{transcript[:50]}...'")
        return transcript
        
    except FileNotFoundError as e:
        error_msg = f"Audio file not found: {e}"
        logger.error(f"❌ {error_msg}")
        return f"[Error: {error_msg}]"
    
    except AudioProcessingError as e:
        error_msg = f"Audio processing failed: {e}"
        logger.error(f"❌ {error_msg}")
        return f"[Error: {error_msg}]"
    
    except Exception as e:
        error_msg = f"Unexpected error during transcription: {type(e).__name__}: {e}"
        logger.error(f"❌ {error_msg}")
        return f"[Error: {error_msg}]"


def mortis_reply(message, history, model_name):
    logger = logging.getLogger(__name__)
    logger.info(f"💬 User message: {message[:50]}{'...' if len(message) > 50 else ''}")
    logger.info(f"🤖 Using model: {model_name}")
    
    msg, mood, gesture = ask_mortis(message, model_name=model_name)
    
    logger.info(f"👻 Mortis reply: {msg[:50]}{'...' if len(msg) > 50 else ''}")
    logger.info(f"😈 Mood: {mood}, Gesture: {gesture}")
    
    return msg


def mortis_reply_with_audio(message, history, model_name):
    """
    Generate Mortis reply with both text and audio output.
    
    Args:
        message: User message text
        history: Chat history
        model_name: Gemini model to use
        
    Returns:
        Tuple of (text_response, audio_path)
    """
    logger = logging.getLogger(__name__)
    logger.info(f"💬 User message: {message[:50]}{'...' if len(message) > 50 else ''}")
    logger.info(f"🤖 Using model: {model_name}")
    
    # Get text response from Gemini
    msg, mood, gesture = ask_mortis(message, model_name=model_name)
    
    logger.info(f"👻 Mortis reply: {msg[:50]}{'...' if len(msg) > 50 else ''}")
    logger.info(f"😈 Mood: {mood}, Gesture: {gesture}")
    
    # Generate audio response
    audio_path = None
    try:
        tts = get_tts_service_instance()
        audio_path = tts.synthesize(msg)
        
        if audio_path:
            logger.info(f"🔊 Audio generated: {audio_path}")
        else:
            logger.warning("⚠️ Audio generation returned None")
    except Exception as e:
        logger.error(f"❌ Failed to generate audio: {e}")
        # Continue without audio - text response is still valid
    
    return msg, audio_path


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
                
                # Audio input component for voice interaction
                with gr.Row():
                    audio_input = gr.Audio(
                        sources=["microphone"],
                        type="filepath",
                        label="🎤 Speak to Mortis",
                        show_label=True,
                        interactive=True,
                        waveform_options=gr.WaveformOptions(
                            show_controls=False,
                        ),
                    )
                
                # Transcription display for user confirmation
                transcription_display = gr.Textbox(
                    label="Transcribed Text",
                    placeholder="Your transcribed speech will appear here...",
                    interactive=False,
                    visible=True,
                    lines=2,
                )
                
                # Audio output component for Mortis voice responses
                audio_output = gr.Audio(
                    label="🔊 Mortis speaks",
                    autoplay=True,
                    type="filepath",
                    interactive=False,
                    show_label=True,
                )
                
                # Custom wrapper to add audio output to chat responses
                def mortis_reply_wrapper(message, history, model_name):
                    """Wrapper that generates both text and audio, but returns only text for ChatInterface."""
                    text_response, audio_path = mortis_reply_with_audio(message, history, model_name)
                    # Store audio path in a way that can be accessed by the audio output component
                    # ChatInterface expects only text return, so we'll handle audio separately
                    return text_response
                
                # Chat interface
                chat_interface = gr.ChatInterface(
                    fn=mortis_reply_wrapper,
                    additional_inputs=[model_dd],
                    chatbot=gr.Chatbot(height=380, label="Mortis chat", type="messages"),
                    textbox=gr.Textbox(placeholder="Write your message here or use voice input above…"),
                    submit_btn="Send",
                )
                
                # Connect audio input to transcription display and chat
                def handle_audio_and_submit(audio_path, history, model_name):
                    """Handle audio input: transcribe and submit to chat with audio response."""
                    if audio_path is None:
                        return "", history, None
                    
                    # Transcribe audio
                    transcript = process_audio_input(audio_path)
                    
                    # If transcription successful and not an error, submit to chat
                    if transcript and not transcript.startswith("[Error:"):
                        # Add user message to history
                        history.append({"role": "user", "content": transcript})
                        
                        # Get Mortis reply with audio
                        response_text, response_audio = mortis_reply_with_audio(transcript, history, model_name)
                        
                        # Add assistant response to history
                        history.append({"role": "assistant", "content": response_text})
                        
                        return transcript, history, response_audio
                    else:
                        # Show error in transcription display
                        return transcript, history, None
                
                # Wire up audio input to trigger transcription and chat submission
                audio_input.stop_recording(
                    fn=handle_audio_and_submit,
                    inputs=[audio_input, chat_interface.chatbot, model_dd],
                    outputs=[transcription_display, chat_interface.chatbot, audio_output],
                )
                
                # Wire up text chat submit to also generate audio
                def handle_text_submit_with_audio(message, history, model_name):
                    """Handle text input and generate audio response."""
                    if not message or not message.strip():
                        return None
                    
                    # Get audio response (text is already handled by ChatInterface)
                    _, audio_path = mortis_reply_with_audio(message, history, model_name)
                    
                    return audio_path
                
                # Connect text submission to audio output
                # Note: ChatInterface handles the submit internally, we just add audio output
                chat_interface.textbox.submit(
                    fn=handle_text_submit_with_audio,
                    inputs=[chat_interface.textbox, chat_interface.chatbot, model_dd],
                    outputs=[audio_output],
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


def cleanup_audio_files():
    """Periodic cleanup of old audio files."""
    try:
        tts = get_tts_service_instance()
        tts.cleanup_old_files(max_age_seconds=3600)  # Clean files older than 1 hour
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to cleanup audio files: {e}")


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
    
    # Ensure outputs directory exists
    from pathlib import Path
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Audio output directory: {outputs_dir.absolute()}")
    
    # Clean up old audio files on startup
    cleanup_audio_files()
    
    port = int(os.getenv("PORT", "7860"))
    logger.info(f"🌐 Launching on http://127.0.0.1:{port}")
    logger.info("=" * 60)
    
    ui().launch(server_name="127.0.0.1", server_port=port, show_error=True,)
