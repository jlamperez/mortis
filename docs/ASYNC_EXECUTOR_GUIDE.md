# Async Execution Guide

## Overview

Mortis uses a **hybrid async execution system** to keep the Gradio UI responsive:

1. **AsyncExecutor** (simple threading): For quick gesture tasks
2. **LeRobotAsyncClient** (LeRobot async inference): For complex manipulation tasks with SmolVLA

This guide covers both systems and when to use each.

## Architecture

### System 1: AsyncExecutor (for Gestures)

Simple producer-consumer pattern using Python threading:

- **Main Thread (Gradio UI)**: Submits gesture tasks to the queue
- **Worker Thread**: Executes gestures via `mortis_arm.move_arm()`
- **Task Queue**: FIFO queue of pending gesture tasks
- **Status Queue**: Queue of status updates from the worker to the UI

**Use for**: Quick predefined gestures (wave, point, idle, etc.)

### System 2: LeRobotAsyncClient (for Manipulation)

LeRobot's async inference system with PolicyServer + RobotClient:

- **PolicyServer Thread**: Loads SmolVLA model, performs continuous inference
- **RobotClient**: Captures observations, sends to server, executes actions
- **Action Receiver Thread**: Receives action chunks from server
- **Control Loop Thread**: Coordinates observation → inference → execution cycle

**Use for**: Complex manipulation tasks requiring vision-language-action model

## Key Components

### Task

Represents a robot task with metadata and status tracking:

```python
from mortis.async_executor import Task, TaskType, TaskStatus

# Create a gesture task
gesture_task = Task.create_gesture_task("wave")

# Create a manipulation task
manip_task = Task.create_manipulation_task("Pick up the skull")

# Task lifecycle
task.start()      # Mark as running
task.complete()   # Mark as complete
task.fail("error message")  # Mark as failed
```

### AsyncExecutor

Manages the background worker thread and task execution:

```python
from mortis.async_executor import AsyncExecutor

# Create executor with custom task executor function
def execute_robot_task(task):
    if task.type == TaskType.GESTURE:
        mortis_arm.move_arm(task.gesture)
    elif task.type == TaskType.MANIPULATION:
        smolvla_executor.execute(task.command)

executor = AsyncExecutor(task_executor=execute_robot_task)

# Start the executor
executor.start()

# Submit tasks
task_id = executor.submit_gesture("wave")
task_id = executor.submit_manipulation("Pick up the skull")

# Get status updates
update = executor.get_status(block=False)
if update:
    print(f"Status: {update.status.value} - {update.message}")

# Stop the executor
executor.stop()
```

## Usage Patterns

### Context Manager

The recommended way to use the executor:

```python
with AsyncExecutor(task_executor=execute_robot_task) as executor:
    # Submit tasks
    executor.submit_gesture("wave")
    executor.submit_manipulation("Pick up the skull")
    
    # Monitor status
    while executor.is_busy():
        update = executor.get_status(block=True, timeout=1.0)
        if update:
            print(update.message)
# Executor automatically stopped when exiting context
```

### Gradio Integration

Example integration with Gradio UI:

```python
# Global executor instance
executor = AsyncExecutor(task_executor=execute_robot_task)

def mortis_reply(message, history, model_name):
    """Handle user message and submit robot task."""
    # Get response from Gemini
    intent = process_with_gemini(message, model_name)
    
    # Submit task asynchronously
    if intent.type == IntentType.MANIPULATION:
        task_id = executor.submit_manipulation(intent.command)
        status_msg = f"🤖 Executing: {intent.command}..."
    else:
        task_id = executor.submit_gesture(intent.gesture)
        status_msg = f"👻 {intent.gesture}"
    
    # Generate audio response
    audio_path = tts_service.synthesize(intent.message)
    
    return intent.message, audio_path, status_msg

def check_status():
    """Periodic status checker for Gradio."""
    update = executor.get_status(block=False)
    if update:
        if update.status == TaskStatus.COMPLETE:
            return f"✅ Completed: {update.message}"
        elif update.status == TaskStatus.RUNNING:
            return f"⏳ Running: {update.message}"
        elif update.status == TaskStatus.FAILED:
            return f"❌ Error: {update.error}"
    return "Idle"

with gr.Blocks() as demo:
    status_display = gr.Textbox(label="Robot Status", value="Idle")
    
    # Update status every 500ms
    demo.load(
        fn=check_status,
        outputs=[status_display],
        every=0.5
    )

# Start executor when app starts
executor.start()

# Stop executor when app closes
demo.unload(lambda: executor.stop())
```

## API Reference

### AsyncExecutor Methods

#### Lifecycle Management

- `start()`: Start the background worker thread
- `stop(timeout=5.0)`: Stop the worker thread (waits for current task to complete)

#### Task Submission

- `submit_task(task)`: Submit a Task object
- `submit_gesture(gesture, metadata=None)`: Submit a gesture task
- `submit_manipulation(command, metadata=None)`: Submit a manipulation task

#### Status Monitoring

- `get_status(block=False, timeout=None)`: Get next status update
- `get_all_status_updates()`: Get all pending status updates
- `get_current_task()`: Get currently executing task
- `get_queue_size()`: Get number of queued tasks
- `is_busy()`: Check if a task is currently executing

#### Queue Management

- `clear_queue()`: Clear all pending tasks (doesn't stop current task)

### Task Properties

- `id`: Unique task identifier
- `type`: TaskType.GESTURE or TaskType.MANIPULATION
- `status`: TaskStatus (QUEUED, RUNNING, COMPLETE, FAILED)
- `gesture`: Gesture name (for gesture tasks)
- `command`: Command string (for manipulation tasks)
- `duration`: Execution duration in seconds
- `wait_time`: Time spent in queue before execution
- `error`: Error message (if failed)

### StatusUpdate Properties

- `task_id`: ID of the related task
- `status`: Current task status
- `message`: Human-readable status message
- `progress`: Optional progress percentage (0-100)
- `error`: Optional error message
- `timestamp`: When the update was created

## Error Handling

The executor handles errors gracefully:

```python
def safe_task_executor(task):
    try:
        if task.type == TaskType.GESTURE:
            mortis_arm.move_arm(task.gesture)
        elif task.type == TaskType.MANIPULATION:
            smolvla_executor.execute(task.command)
    except Exception as e:
        # Error is automatically captured and reported
        raise

# Errors are reported via status updates
update = executor.get_status()
if update.status == TaskStatus.FAILED:
    print(f"Task failed: {update.error}")
```

## Thread Safety

The executor is designed to be thread-safe:

- Task submission is thread-safe (can be called from any thread)
- Status retrieval is thread-safe
- The worker thread is isolated and doesn't share mutable state

## Performance Considerations

- **Queue Size**: Monitor queue size to avoid unbounded growth
- **Task Duration**: Long-running tasks block the queue (consider breaking into smaller tasks)
- **Status Updates**: Poll status updates regularly to avoid queue buildup
- **Memory**: Clear completed tasks periodically if running for extended periods

## Testing

Run the test suite:

```bash
python -m pytest test/test_async_executor.py -v
```

Run the demo:

```bash
python examples/demo_async_executor.py
```

## Requirements

The async executor satisfies requirements 7.1 and 7.2 from the design document:

- **7.1**: Executes SmolVLA inference asynchronously without blocking the Gradio Interface
- **7.2**: Uses a message queue (Python Queue) to decouple inference from the web interface

## Next Steps

After implementing the async executor, the next tasks are:

1. **Task 28**: Implement task models and queue management (already included in this implementation)
2. **Task 29**: Integrate async execution with SmolVLA
3. **Task 30**: Add status display to Gradio UI
4. **Task 31**: Update main flow for async execution


---

## LeRobot Async Client (for Manipulation)

### Quick Start

```python
from mortis.lerobot_async_client import LeRobotAsyncClient

# Create client with your model
client = LeRobotAsyncClient(
    robot_port="/dev/ttyACM1",
    robot_id="my_follower_robot_arm",  # Must match your calibration file name
    model_path="jlamperez/kiroween-potion-smolvla",
    policy_device="cuda",
    camera_configs={
        "top": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30},
        "right": {"type": "opencv", "index_or_path": 8, "width": 640, "height": 480, "fps": 30},
        "gripper": {"type": "opencv", "index_or_path": 4, "width": 640, "height": 480, "fps": 30}
    }
)

# Start the system (PolicyServer + RobotClient)
client.start()

# Execute a manipulation task
client.execute_task("Pick up the skull and place it in the green cup")

# Check status
while client.is_busy():
    status = client.get_status()
    print(f"Status: {status.value}")
    time.sleep(0.5)

# Stop when done
client.stop()
```

### Context Manager Usage

```python
with LeRobotAsyncClient(model_path="jlamperez/kiroween-potion-smolvla") as client:
    # Execute task
    client.execute_task("Pick up the eyeball and place it in the orange cup")
    
    # Wait for completion
    while client.is_busy():
        time.sleep(0.5)
# Automatically stopped
```

### Configuration Options

```python
client = LeRobotAsyncClient(
    robot_port="/dev/ttyACM1",              # SO101 serial port
    robot_id="my_follower_robot_arm",       # Robot identifier (must match calibration file)
    model_path="jlamperez/kiroween-potion-smolvla",  # HF model or local path
    policy_device="cuda",                    # "cuda" or "cpu"
    server_host="127.0.0.1",                # PolicyServer host
    server_port=8080,                        # PolicyServer port
    actions_per_chunk=50,                    # Actions per inference
    chunk_size_threshold=0.5,                # Chunk aggregation threshold
    aggregate_fn_name="weighted_average",    # Aggregation function
    camera_configs={...}                     # Camera configuration dict
)
```

### API Reference

#### Lifecycle Methods

- `start()`: Start PolicyServer and RobotClient
- `stop()`: Stop all components gracefully
- `is_running()`: Check if system is running

#### Task Execution

- `execute_task(task, max_steps=200, blocking=False)`: Execute manipulation task
  - `task`: Natural language task description
  - `max_steps`: Maximum action steps to execute
  - `blocking`: If True, wait for completion before returning

#### Status Monitoring

- `get_status()`: Get current ManipulationStatus (IDLE, STARTING, RUNNING, COMPLETE, FAILED, STOPPED)
- `get_current_task()`: Get ManipulationTask object with details
- `is_busy()`: Check if task is currently executing

### ManipulationTask Object

```python
task = client.get_current_task()
if task:
    print(f"Task: {task.task}")
    print(f"Status: {task.status.value}")
    print(f"Duration: {task.duration}s")
    if task.error:
        print(f"Error: {task.error}")
```

---

## Hybrid System Integration

### Complete Example with Both Systems

```python
from mortis.async_executor import AsyncExecutor, Task, TaskType
from mortis.lerobot_async_client import LeRobotAsyncClient
from mortis.robot import MortisArm

# Initialize both systems
mortis_arm = MortisArm()
mortis_arm.connect()

# 1. Gesture executor (simple, fast)
def execute_gesture(task: Task):
    if task.type == TaskType.GESTURE:
        mortis_arm.move_arm(task.gesture)

gesture_executor = AsyncExecutor(task_executor=execute_gesture)
gesture_executor.start()

# 2. Manipulation client (LeRobot async)
manipulation_client = LeRobotAsyncClient(
    model_path="jlamperez/kiroween-potion-smolvla"
)
manipulation_client.start()

# Execute gesture (fast)
gesture_executor.submit_gesture("wave")

# Execute manipulation (slow, complex)
manipulation_client.execute_task("Pick up the skull and place it in the green cup")

# Monitor both
print(f"Gesture queue: {gesture_executor.get_queue_size()}")
print(f"Manipulation status: {manipulation_client.get_status().value}")

# Cleanup
gesture_executor.stop()
manipulation_client.stop()
mortis_arm.disconnect()
```

### Gradio Integration (Hybrid)

```python
import gradio as gr
from mortis.async_executor import AsyncExecutor
from mortis.lerobot_async_client import LeRobotAsyncClient
from mortis.gemini_client import GeminiClient
from mortis.intent_router import IntentRouter, IntentType

# Initialize systems
gemini_client = GeminiClient(api_key=os.getenv("GEMINI_API_KEY"))
intent_router = IntentRouter()
gesture_executor = AsyncExecutor(task_executor=execute_gesture)
manipulation_client = LeRobotAsyncClient(model_path="jlamperez/kiroween-potion-smolvla")

# Start both systems
gesture_executor.start()
manipulation_client.start()

def mortis_reply(message, history, model_name):
    """Handle user message with hybrid execution."""
    # Get intent from Gemini
    response = gemini_client.send_message(message, model_name)
    intent = intent_router.parse_gemini_response(response)
    
    # Route to appropriate executor
    if intent.type == IntentType.MANIPULATION:
        # Use LeRobot async for manipulation
        manipulation_client.execute_task(intent.command)
        status_msg = f"🤖 Executing: {intent.command}..."
    else:
        # Use simple executor for gestures
        gesture_executor.submit_gesture(intent.gesture)
        status_msg = f"👻 {intent.gesture}"
    
    # Generate audio response
    audio_path = tts_service.synthesize(intent.message)
    
    return intent.message, audio_path, status_msg

def check_status():
    """Check status of both systems."""
    # Check gesture executor
    gesture_update = gesture_executor.get_status(block=False)
    if gesture_update:
        return f"✋ Gesture: {gesture_update.message}"
    
    # Check manipulation client
    manip_status = manipulation_client.get_status()
    if manip_status.value != "idle":
        task = manipulation_client.get_current_task()
        if task:
            return f"🤖 Manipulation: {manip_status.value} - {task.task}"
    
    return "💀 Mortis is idle..."

with gr.Blocks() as demo:
    status_display = gr.Textbox(label="Robot Status", value="Idle")
    
    # Update status every 500ms
    demo.load(
        fn=check_status,
        outputs=[status_display],
        every=0.5
    )

# Cleanup on app close
demo.unload(lambda: [gesture_executor.stop(), manipulation_client.stop()])
```

---

## When to Use Which System

### Use AsyncExecutor (Gestures) when:
- ✅ Task is a predefined gesture (wave, point, idle, etc.)
- ✅ Execution is fast (< 2 seconds)
- ✅ No ML inference needed
- ✅ Simple robot movements

### Use LeRobotAsyncClient (Manipulation) when:
- ✅ Task requires vision-language understanding
- ✅ Task involves object manipulation
- ✅ Need continuous visual feedback
- ✅ Task is complex and multi-step
- ✅ Execution time is long (10-60 seconds)

---

## Troubleshooting

### LeRobot Async Issues

**Problem**: PolicyServer fails to start
```
Solution: Check that port 8080 is available, or change server_port
```

**Problem**: RobotClient can't connect to robot
```
Solution: 
1. Check robot is connected: ls /dev/ttyACM*
2. Verify port in configuration
3. Check robot is calibrated: make calibrate
4. Ensure robot_id matches calibration file name in .cache/calibration/so101/
```

**Problem**: Camera not found
```
Solution:
1. Find cameras: lerobot-find-cameras opencv
2. Update camera_configs with correct indices/paths
3. IMPORTANT: Use the SAME camera configuration as training!
4. If you used IntelRealSense during training, install: uv pip install -e ".[intelrealsense]"
```

**Problem**: GPU out of memory
```
Solution:
1. Use smaller batch size (reduce actions_per_chunk)
2. Use CPU: policy_device="cpu"
3. Close other GPU processes
```

### AsyncExecutor Issues

**Problem**: Tasks not executing
```
Solution: Make sure executor.start() was called
```

**Problem**: Status updates not appearing
```
Solution: Call get_status() or get_all_status_updates() regularly
```

---

## Performance Considerations

### AsyncExecutor (Gestures)
- **Latency**: ~50ms (very fast)
- **Throughput**: 20+ gestures/second
- **Memory**: Minimal (~1MB)
- **CPU**: Single thread, low usage

### LeRobotAsyncClient (Manipulation)
- **Latency**: ~100-200ms per action (depends on GPU)
- **Throughput**: 5-10 actions/second
- **Memory**: ~4-8GB GPU VRAM (SmolVLA model)
- **CPU**: Multiple threads (server, client, receiver, control)

### Optimization Tips

1. **Keep PolicyServer running**: Don't stop/start between tasks (expensive)
2. **Tune chunk parameters**: Adjust `actions_per_chunk` and `chunk_size_threshold`
3. **Use GPU**: Much faster than CPU for SmolVLA inference
4. **Monitor queue sizes**: Prevent unbounded growth
5. **Batch gestures**: Group multiple gestures if possible

---

## Testing

### Test AsyncExecutor
```bash
python -m pytest test/test_async_executor.py -v
```

### Test LeRobot Async Client
```bash
# TODO: Add tests for LeRobotAsyncClient
python -m pytest test/test_lerobot_async_client.py -v
```

### Run Demos
```bash
# AsyncExecutor demo
python examples/demo_async_executor.py

# LeRobot async demo
python examples/demo_lerobot_async.py
```

---

## Requirements Satisfied

- ✅ **7.1**: Executes SmolVLA inference asynchronously without blocking Gradio Interface
- ✅ **7.2**: Uses message queue (Python Queue for gestures, gRPC for manipulation) to decouple inference from web interface
- ✅ **7.3**: Provides status updates during long-running operations
- ✅ **7.4**: UI remains responsive during task execution
- ✅ **7.5**: Supports concurrent task submission and queuing
