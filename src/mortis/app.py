import base64
import json
import os
import logging
import time

from pathlib import Path
import gradio as gr

from .tools import ask_mortis, mortis_arm
from .stt_service import STTService, AudioProcessingError
from .tts_service import get_tts_service
from .async_executor import AsyncExecutor, Task, TaskType, TaskStatus
from .lerobot_async_client import LeRobotAsyncClient, ManipulationStatus
from .intent_router import IntentRouter, Intent
from .models import ResponseType


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

# Initialize async execution systems (global instances)
async_executor = None
lerobot_client = None
intent_router = None

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


def execute_async_task(task: Task):
    """
    Execute a task asynchronously (called by AsyncExecutor worker thread).
    
    This function is called by the AsyncExecutor's worker thread to execute
    tasks. It handles both gesture and manipulation tasks.
    
    Args:
        task: Task to execute
    """
    logger = logging.getLogger(__name__)
    
    try:
        if task.type == TaskType.GESTURE:
            # Execute gesture using mortis_arm
            gesture = task.gesture
            logger.info(f"Executing gesture: {gesture}")
            
            if mortis_arm.connected:
                mortis_arm.move_arm(gesture)
            else:
                logger.warning("Robot arm not connected, skipping gesture")
        
        elif task.type == TaskType.MANIPULATION:
            # This shouldn't happen - manipulation goes through LeRobotAsyncClient
            logger.warning(f"Manipulation task in AsyncExecutor: {task.command}")
            logger.warning("Manipulation tasks should use LeRobotAsyncClient")
        
        else:
            logger.error(f"Unknown task type: {task.type}")
    
    except Exception as e:
        logger.error(f"Error executing task {task.id}: {e}", exc_info=True)
        raise


def get_async_executor():
    """Lazy initialization of AsyncExecutor."""
    global async_executor
    if async_executor is None:
        try:
            # Create executor with gesture execution function
            async_executor = AsyncExecutor(task_executor=execute_async_task)
            logging.getLogger(__name__).info("✅ AsyncExecutor initialized")
        except Exception as e:
            logging.getLogger(__name__).error(f"❌ Failed to initialize AsyncExecutor: {e}")
            raise
    return async_executor


def get_lerobot_client():
    """Lazy initialization of LeRobotAsyncClient."""
    global lerobot_client
    
    # Use a sentinel value to indicate we've already checked and manipulation is disabled
    if lerobot_client is None:
        # Check if we're in simulation mode
        robot_mode = os.getenv("ROBOT_MODE", "physical").lower()
        if robot_mode == "simulation":
            # Set to False to indicate manipulation is not available in simulation
            lerobot_client = False
            logging.getLogger(__name__).info("ℹ️ Manipulation disabled in simulation mode")
            return None
        
        # Check if manipulation is enabled
        enable_manipulation = os.getenv("ENABLE_MANIPULATION", "false").lower() == "true"
        
        if not enable_manipulation:
            # Set to False (not None) to indicate we've checked and it's disabled
            # This prevents logging the message repeatedly
            lerobot_client = False
            logging.getLogger(__name__).info("ℹ️ Manipulation disabled (ENABLE_MANIPULATION=false)")
            return None
        
        try:
            robot_port = os.getenv("ROBOT_PORT", "/dev/ttyACM1")
            model_path = os.getenv("SMOLVLA_MODEL_PATH", "jlamperez/kiroween-potion-smolvla")
            
            lerobot_client = LeRobotAsyncClient(
                robot_port=robot_port,
                model_path=model_path
            )
            
            # Configure idle callback to move robot to safe position on timeout
            lerobot_client.set_idle_callback(lambda: mortis_arm.move_arm("idle") if mortis_arm.connected else None)
            
            logging.getLogger(__name__).info("✅ LeRobotAsyncClient initialized")
        except Exception as e:
            logging.getLogger(__name__).error(f"❌ Failed to initialize LeRobotAsyncClient: {e}")
            # Don't raise - manipulation is optional
            return None
    
    # Return None if manipulation is disabled (lerobot_client == False)
    return lerobot_client if lerobot_client is not False else None


def get_intent_router_instance():
    """Lazy initialization of IntentRouter."""
    global intent_router
    if intent_router is None:
        try:
            intent_router = IntentRouter()
            logging.getLogger(__name__).info("✅ IntentRouter initialized")
        except Exception as e:
            logging.getLogger(__name__).error(f"❌ Failed to initialize IntentRouter: {e}")
            raise
    return intent_router


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


def mortis_reply_with_audio(message, history, model_name, audio_input_path=None):
    """
    Generate Mortis reply with both text and audio output using hybrid execution.
    
    This function integrates the hybrid async execution system:
    - Gestures are routed to AsyncExecutor (simple threading)
    - Manipulation tasks are routed to LeRobotAsyncClient (LeRobot async inference)
    
    Supports both text and voice input through the unified voice pipeline.
    
    Args:
        message: User message text (optional if audio_input_path provided)
        history: Chat history
        model_name: Gemini model to use
        audio_input_path: Optional path to audio input file
        
    Returns:
        Tuple of (text_response, audio_path)
    """
    logger = logging.getLogger(__name__)
    
    # Import necessary components
    from .gemini_client import GeminiClient
    
    # Log input type
    if audio_input_path:
        logger.info(f"🎤 Voice input: {audio_input_path}")
        
        # Transcribe audio to text
        try:
            stt = get_stt_service()
            message = stt.transcribe(audio_input_path)
            logger.info(f"📝 Transcribed: '{message[:50]}...'")
            
            if not message or not message.strip():
                logger.warning("⚠️ STT returned empty transcription")
                return "I couldn't hear you... speak again.", None
        except Exception as e:
            logger.error(f"❌ Voice input processing failed: {e}")
            return "The spirits couldn't understand... try again.", None
    else:
        logger.info(f"💬 Text input: {message[:50]}{'...' if len(message) > 50 else ''}")
    
    logger.info(f"🤖 Using model: {model_name}")
    
    try:
        # Get Gemini client and send message
        gemini_client = GeminiClient()
        if model_name:
            gemini_client.configure_model(model_name=model_name)
        
        response_json = gemini_client.send_message(message)
        
        # Parse response using IntentRouter
        router = get_intent_router_instance()
        intent = router.parse_gemini_response(response_json)
        
        # Extract response components
        msg = intent.message
        mood = intent.mood
        
        logger.info(f"👻 Mortis reply: {msg[:50]}{'...' if len(msg) > 50 else ''}")
        logger.info(f"😈 Mood: {mood}")
        
        # Route execution based on intent type
        execution_path = router.route_intent(intent)
        
        if execution_path == "manipulation" and intent.is_valid:
            # Route to LeRobotAsyncClient for manipulation
            logger.info(f"🤖 Routing manipulation to LeRobotAsyncClient: {intent.command}")
            
            client = get_lerobot_client()
            if client and client.is_running():
                try:
                    # Get timeout from environment or use default (60s)
                    timeout = float(os.getenv("MANIPULATION_TIMEOUT", "60.0"))
                    
                    # Submit manipulation task asynchronously with timeout
                    client.execute_task(
                        intent.command, 
                        blocking=False, 
                        timeout=timeout
                    )
                    logger.info(f"✅ Manipulation task submitted: {intent.command} (timeout: {timeout}s)")
                except Exception as e:
                    logger.error(f"❌ Failed to submit manipulation task: {e}")
                    logger.info("Falling back to gesture execution")
                    
                    # Fallback to gesture
                    executor = get_async_executor()
                    if executor.running:
                        task = Task.create_gesture_task("idle")
                        executor.submit_task(task)
            else:
                logger.warning("LeRobotAsyncClient not available, falling back to gesture")
                
                # Fallback to gesture
                executor = get_async_executor()
                if executor.running:
                    task = Task.create_gesture_task("idle")
                    executor.submit_task(task)
        
        elif execution_path == "gesture":
            # Route to AsyncExecutor for gesture
            gesture = intent.gesture if intent.gesture else "idle"
            logger.info(f"👋 Routing gesture to AsyncExecutor: {gesture}")
            
            executor = get_async_executor()
            if executor.running:
                try:
                    # Submit gesture task asynchronously
                    task = Task.create_gesture_task(gesture)
                    executor.submit_task(task)
                    logger.info(f"✅ Gesture task submitted: {gesture}")
                except Exception as e:
                    logger.error(f"❌ Failed to submit gesture task: {e}")
            else:
                logger.warning("AsyncExecutor not running, executing gesture synchronously")
                if mortis_arm.connected:
                    mortis_arm.move_arm(gesture)
        
        else:
            # Invalid intent - fallback to idle gesture
            logger.warning(f"⚠️ Invalid intent, falling back to idle gesture")
            
            executor = get_async_executor()
            if executor.running:
                task = Task.create_gesture_task("idle")
                executor.submit_task(task)
            elif mortis_arm.connected:
                mortis_arm.move_arm("idle")
        
        # Generate audio response
        audio_path = None
        try:
            tts = get_tts_service_instance()
            audio_path = tts.synthesize(msg)
            
            if audio_path:
                logger.info(f"🔊 Audio output: {audio_path}")
        except Exception as e:
            logger.error(f"❌ TTS generation failed: {e}")
            # Continue without audio
        
        return msg, audio_path
    
    except Exception as e:
        logger.error(f"❌ Error in mortis_reply_with_audio: {e}", exc_info=True)
        return "The spirits are confused... try again.", None


def start_async_systems():
    """
    Start the async execution systems on app load.
    
    This function initializes and starts:
    1. Robot arm connection
    2. AsyncExecutor for gesture execution
    3. LeRobotAsyncClient for manipulation tasks (if enabled)
    """
    logger = logging.getLogger(__name__)
    logger.info("🚀 Starting async execution systems...")
    
    # Connect to robot arm
    try:
        if not mortis_arm.connected:
            mortis_arm.connect()
            if mortis_arm.mode == "simulation":
                logger.info("🎭 Robot arm in SIMULATION mode")
            else:
                logger.info("✅ Robot arm connected")
        else:
            logger.info("ℹ️ Robot arm already connected")
    except Exception as e:
        logger.error(f"❌ Failed to connect robot arm: {e}", exc_info=True)
        logger.info("ℹ️ Gestures will be skipped until robot is connected")
    
    # Start AsyncExecutor
    try:
        executor = get_async_executor()
        if not executor.running:
            executor.start()
            logger.info("✅ AsyncExecutor started")
        else:
            logger.info("ℹ️ AsyncExecutor already running")
    except Exception as e:
        logger.error(f"❌ Failed to start AsyncExecutor: {e}", exc_info=True)
    
    # Start LeRobotAsyncClient (if enabled)
    try:
        client = get_lerobot_client()
        if client and not client.is_running():
            success = client.start()
            if success:
                logger.info("✅ LeRobotAsyncClient started")
            else:
                logger.warning("⚠️ LeRobotAsyncClient failed to start")
    except Exception as e:
        logger.error(f"❌ Failed to start LeRobotAsyncClient: {e}", exc_info=True)
        logger.info("ℹ️ Manipulation tasks will fall back to gestures")


def check_status():
    """
    Check status of both async execution systems and return formatted status message.
    
    This function monitors:
    1. AsyncExecutor for gesture status updates
    2. LeRobotAsyncClient for manipulation status
    
    Returns:
        Formatted status string with icons and messages
    """
    logger = logging.getLogger(__name__)
    
    status_parts = []
    
    # Add robot mode indicator
    if mortis_arm.mode == "simulation":
        status_parts.append("🎭 SIMULATION MODE")
    
    # Check AsyncExecutor status
    try:
        executor = get_async_executor()
        if executor and executor.running:
            # Check if executor is busy
            current_task = executor.get_current_task()
            if current_task:
                # Task is running
                if current_task.type == TaskType.GESTURE:
                    status_parts.append(f"👋 Gesture: {current_task.gesture} (running)")
                else:
                    status_parts.append(f"🤖 Task: {current_task.command[:30]}... (running)")
            else:
                # Check for recent status updates
                updates = executor.get_all_status_updates()
                if updates:
                    latest = updates[-1]
                    if latest.status == TaskStatus.COMPLETE:
                        status_parts.append(f"✅ Gesture complete")
                    elif latest.status == TaskStatus.FAILED:
                        status_parts.append(f"❌ Gesture failed: {latest.error}")
                    elif latest.status == TaskStatus.QUEUED:
                        status_parts.append(f"⏳ Gesture queued")
    except Exception as e:
        logger.error(f"Error checking AsyncExecutor status: {e}")
    
    # Check LeRobotAsyncClient status
    try:
        client = get_lerobot_client()
        if client and client.is_running():
            manipulation_status = client.get_status()
            current_task = client.get_current_task()
            
            if manipulation_status == ManipulationStatus.RUNNING and current_task:
                # Manipulation task is running
                elapsed = time.time() - current_task.started_at if current_task.started_at else 0
                status_parts.append(f"🤖 Manipulation: {current_task.task[:40]}... ({elapsed:.1f}s)")
            elif manipulation_status == ManipulationStatus.COMPLETE and current_task:
                # Task just completed
                duration = current_task.duration or 0
                status_parts.append(f"✅ Manipulation complete ({duration:.1f}s)")
            elif manipulation_status == ManipulationStatus.FAILED and current_task:
                # Task failed
                error = current_task.error or "Unknown error"
                status_parts.append(f"❌ Manipulation failed: {error[:50]}")
            elif manipulation_status == ManipulationStatus.STARTING:
                status_parts.append(f"⏳ Starting manipulation...")
            elif manipulation_status == ManipulationStatus.STOPPED and current_task:
                # Task was stopped (timeout or manual stop)
                duration = current_task.duration or 0
                error_msg = current_task.error or "Stopped"
                
                # Check if control thread is still finishing
                if client.control_thread and client.control_thread.is_alive():
                    status_parts.append(f"⏹️ Stopped (finishing actions...): {error_msg[:30]}")
                else:
                    status_parts.append(f"⏹️ Stopped: {error_msg[:40]} ({duration:.1f}s)")
    except Exception as e:
        logger.error(f"Error checking LeRobotAsyncClient status: {e}")
    
    # Return formatted status or idle message
    if status_parts:
        return " | ".join(status_parts)
    else:
        return "💤 Idle - Ready for commands"


def stop_async_systems():
    """
    Stop the async execution systems on app unload.
    
    This function gracefully shuts down:
    1. AsyncExecutor
    2. LeRobotAsyncClient
    3. Robot arm connection
    """
    logger = logging.getLogger(__name__)
    logger.info("🛑 Stopping async execution systems...")
    
    # Stop AsyncExecutor
    try:
        if async_executor and async_executor.running:
            async_executor.stop()
            logger.info("✅ AsyncExecutor stopped")
    except Exception as e:
        logger.error(f"❌ Error stopping AsyncExecutor: {e}")
    
    # Stop LeRobotAsyncClient
    try:
        if lerobot_client and lerobot_client.is_running():
            lerobot_client.stop()
            logger.info("✅ LeRobotAsyncClient stopped")
    except Exception as e:
        logger.error(f"❌ Error stopping LeRobotAsyncClient: {e}")
    
    # Disconnect robot arm
    try:
        mortis_arm.disconnect()
        logger.info("✅ Robot arm disconnected")
    except Exception as e:
        logger.error(f"❌ Error disconnecting robot arm: {e}")


def ui() -> gr.Blocks:
    css=build_css(BG_IMAGE)
    with gr.Blocks(fill_height=True, theme="soft", css=css) as demo:
        # Dynamic title based on robot mode
        mode_indicator = " (Simulation Mode 🎭)" if mortis_arm.mode == "simulation" else ""
        gr.Markdown(
            f"# Kiroween Hackathon 🎃\n"
            f"## Mortis: Haunted Control Room 👻🤖{mode_indicator}",
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
                
                # State to store the latest audio path
                audio_state = gr.State(value=None)
                
                # Custom wrapper to add audio output to chat responses
                def mortis_reply_wrapper(message, history, model_name, audio_state_value):
                    """Wrapper that generates both text and audio."""
                    text_response, audio_path = mortis_reply_with_audio(message, history, model_name)
                    # Return text for chat and audio path for state
                    return text_response, audio_path
                
                # Chat interface
                chat_interface = gr.ChatInterface(
                    fn=mortis_reply_wrapper,
                    additional_inputs=[model_dd, audio_state],
                    additional_outputs=[audio_state],
                    chatbot=gr.Chatbot(height=380, label="Mortis chat", type="messages"),
                    textbox=gr.Textbox(placeholder="Write your message here or use voice input above…"),
                    submit_btn="Send",
                )
                
                # Connect audio input to transcription display and chat
                def handle_audio_and_submit(audio_path, history, model_name):
                    """Handle audio input: transcribe and submit to chat with audio response."""
                    if audio_path is None:
                        return "", history, None
                    
                    logger = logging.getLogger(__name__)
                    logger.info(f"🎤 Handling audio input: {audio_path}")
                    
                    # First, get the transcription for display
                    transcript = process_audio_input(audio_path)
                    
                    # If transcription failed, return error
                    if not transcript or transcript.startswith("[Error:"):
                        return transcript, history, None
                    
                    # Now use the transcribed text to get Mortis response with audio
                    # We pass the transcript as text, not the audio file, to avoid double transcription
                    response_text, response_audio = mortis_reply_with_audio(
                        message=transcript,  # Use the transcribed text
                        history=history,
                        model_name=model_name,
                        audio_input_path=None  # Don't pass audio since we already transcribed
                    )
                    
                    # Update chat history
                    history.append({"role": "user", "content": transcript})
                    history.append({"role": "assistant", "content": response_text})
                    
                    return transcript, history, response_audio
                
                # Wire up audio input to trigger transcription and chat submission
                audio_input.stop_recording(
                    fn=handle_audio_and_submit,
                    inputs=[audio_input, chat_interface.chatbot, model_dd],
                    outputs=[transcription_display, chat_interface.chatbot, audio_output],
                )
                
                # Connect audio state changes to audio output
                # This ensures audio plays whenever the state is updated by ChatInterface
                audio_state.change(
                    fn=lambda x: x,  # Pass through the audio path
                    inputs=[audio_state],
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
                
                # Robot status display
                status_display = gr.Textbox(
                    label="🤖 Robot Status",
                    value="💤 Idle - Ready for commands",
                    interactive=False,
                    lines=2,
                    max_lines=3,
                )
                
                # Stop button for manipulation tasks
                def stop_manipulation_task():
                    """Stop the currently running manipulation task."""
                    logger = logging.getLogger(__name__)
                    client = get_lerobot_client()
                    
                    if client and client.is_running():
                        if client.is_busy():
                            logger.info("🛑 User requested task stop")
                            success = client.stop_current_task()
                            if success:
                                return "⏹️ Task stopped by user"
                            else:
                                return "❌ Failed to stop task"
                        else:
                            return "ℹ️ No task running"
                    else:
                        return "ℹ️ Manipulation not enabled"
                
                stop_button = gr.Button(
                    "🛑 Stop Manipulation Task",
                    variant="stop",
                    size="sm",
                )
                
                stop_button.click(
                    fn=stop_manipulation_task,
                    outputs=[status_display]
                )
                
                # Status polling timer (must be inside Blocks context)
                status_timer = gr.Timer(value=0.5, active=True)

        # Lifecycle management: start async systems on load, stop on unload
        demo.load(fn=start_async_systems)
        demo.unload(fn=stop_async_systems)
        
        # Status polling: update status display every 500ms using a timer
        status_timer.tick(
            fn=check_status,
            outputs=[status_display]
        )

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
    
    # Start async systems before launching UI
    start_async_systems()
    
    port = int(os.getenv("PORT", "7860"))
    logger.info(f"🌐 Launching on http://127.0.0.1:{port}")
    logger.info("=" * 60)
    
    try:
        ui().launch(server_name="127.0.0.1", server_port=port, show_error=True)
    finally:
        # Ensure cleanup on exit
        stop_async_systems()
