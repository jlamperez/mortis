# Hybrid Execution System

## Overview

Mortis uses a **hybrid async execution system** that combines two different approaches for optimal performance:

1. **AsyncExecutor**: Simple threading for quick gestures
2. **LeRobotAsyncClient**: LeRobot async inference for complex manipulation

## Why Hybrid?

Different types of robot tasks have different requirements:

### Gestures (Simple & Fast)
- **Examples**: wave, point_left, point_right, idle, grab, drop
- **Duration**: 1-2 seconds
- **Complexity**: Predefined joint positions
- **Requirements**: Fast execution, low latency, no ML inference
- **Solution**: AsyncExecutor with simple threading

### Manipulation (Complex & Slow)
- **Examples**: "Pick up the skull and place it in the green cup"
- **Duration**: 30-60 seconds
- **Complexity**: Vision-language-action model, continuous inference
- **Requirements**: Real-time visual feedback, action chunking, GPU inference
- **Solution**: LeRobotAsyncClient with PolicyServer + RobotClient

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Gradio UI (Main Thread)                 │
│                                                              │
│  User Input → Gemini API → Intent Router                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ├─────────────────┬──────────────────────┐
                     ↓                 ↓                      ↓
              ┌──────────────┐  ┌──────────────┐   ┌──────────────┐
              │ Conversation │  │   Gesture    │   │ Manipulation │
              │   Response   │  │              │   │              │
              └──────────────┘  └──────┬───────┘   └──────┬───────┘
                                       ↓                   ↓
                              ┌─────────────────┐  ┌──────────────────┐
                              │ AsyncExecutor   │  │ LeRobotAsync     │
                              │                 │  │ Client           │
                              │ • Task Queue    │  │                  │
                              │ • Worker Thread │  │ • PolicyServer   │
                              │ • Status Queue  │  │ • RobotClient    │
                              └────────┬────────┘  │ • Action Receiver│
                                       ↓           │ • Control Loop   │
                              ┌─────────────────┐  └────────┬─────────┘
                              │  mortis_arm     │           ↓
                              │  .move_arm()    │  ┌──────────────────┐
                              └────────┬────────┘  │ SmolVLA Model    │
                                       ↓           │ + Cameras        │
                              ┌─────────────────┐  └────────┬─────────┘
                              │  SO101 Robot    │           ↓
                              │  (Gestures)     │  ┌──────────────────┐
                              └─────────────────┘  │  SO101 Robot     │
                                                   │  (Manipulation)  │
                                                   └──────────────────┘
```

## Component Details

### AsyncExecutor

**File**: `src/mortis/async_executor.py`

**Components**:
- `Task`: Dataclass representing a gesture task
- `TaskStatus`: Enum (QUEUED, RUNNING, COMPLETE, FAILED)
- `StatusUpdate`: Status messages from worker to UI
- `AsyncExecutor`: Main executor class

**Usage**:
```python
from mortis.async_executor import AsyncExecutor

def execute_gesture(task):
    mortis_arm.move_arm(task.gesture)

executor = AsyncExecutor(task_executor=execute_gesture)
executor.start()

# Submit gesture
task_id = executor.submit_gesture("wave")

# Check status
update = executor.get_status()
print(update.message)

executor.stop()
```

**Performance**:
- Latency: ~50ms
- Throughput: 20+ gestures/second
- Memory: ~1MB
- CPU: Single thread, low usage

### LeRobotAsyncClient

**File**: `src/mortis/lerobot_async_client.py`

**Components**:
- `ManipulationTask`: Dataclass representing a manipulation task
- `ManipulationStatus`: Enum (IDLE, STARTING, RUNNING, COMPLETE, FAILED, STOPPED)
- `LeRobotAsyncClient`: Wrapper over LeRobot async inference

**Usage**:
```python
from mortis.lerobot_async_client import LeRobotAsyncClient

client = LeRobotAsyncClient(
    robot_port="/dev/ttyACM1",
    robot_id="my_follower_robot_arm",  # Must match your calibration file
    model_path="jlamperez/kiroween-potion-smolvla",
    policy_device="cuda"
)

client.start()

# Execute manipulation
client.execute_task("Pick up the skull and place it in the green cup")

# Check status
while client.is_busy():
    status = client.get_status()
    print(f"Status: {status.value}")
    time.sleep(1.0)

client.stop()
```

**Performance**:
- Latency: ~100-200ms per action
- Throughput: 5-10 actions/second
- Memory: ~4-8GB GPU VRAM
- CPU: Multiple threads (server, client, receiver, control)

## Integration in Mortis

### app.py Structure

```python
from mortis.async_executor import AsyncExecutor
from mortis.lerobot_async_client import LeRobotAsyncClient
from mortis.gemini_client import GeminiClient
from mortis.intent_router import IntentRouter

# Initialize systems
gemini_client = GeminiClient(api_key=os.getenv("GEMINI_API_KEY"))
intent_router = IntentRouter()

# Gesture executor
def execute_gesture(task):
    mortis_arm.move_arm(task.gesture)

gesture_executor = AsyncExecutor(task_executor=execute_gesture)

# Manipulation client
manipulation_client = LeRobotAsyncClient(
    robot_id="my_follower_robot_arm",  # Must match your calibration file
    model_path="jlamperez/kiroween-potion-smolvla"
)

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
    
    return intent.message, status_msg

def check_status():
    """Check status of both systems."""
    # Check gesture executor
    gesture_update = gesture_executor.get_status(block=False)
    if gesture_update:
        return f"✋ {gesture_update.message}"
    
    # Check manipulation client
    if manipulation_client.is_busy():
        task = manipulation_client.get_current_task()
        return f"🤖 {task.status.value}: {task.task}"
    
    return "💀 Mortis is idle..."

# Gradio app
with gr.Blocks() as demo:
    status_display = gr.Textbox(label="Robot Status")
    
    # Update status every 500ms
    demo.load(fn=check_status, outputs=[status_display], every=0.5)

# Lifecycle management
demo.load(lambda: [gesture_executor.start(), manipulation_client.start()])
demo.unload(lambda: [gesture_executor.stop(), manipulation_client.stop()])
```

## Decision Matrix

Use this matrix to decide which system to use:

| Criteria | AsyncExecutor | LeRobotAsyncClient |
|----------|---------------|-------------------|
| Task is predefined gesture | ✅ | ❌ |
| Task requires ML inference | ❌ | ✅ |
| Task needs visual feedback | ❌ | ✅ |
| Task duration < 5 seconds | ✅ | ❌ |
| Task involves object manipulation | ❌ | ✅ |
| Need low latency | ✅ | ❌ |
| Need continuous inference | ❌ | ✅ |
| Simple joint movements | ✅ | ❌ |
| Complex multi-step actions | ❌ | ✅ |

## Testing

### Test AsyncExecutor
```bash
python -m pytest test/test_async_executor.py -v
```

### Test LeRobotAsyncClient
```bash
# TODO: Add tests
python -m pytest test/test_lerobot_async_client.py -v
```

### Run Demos
```bash
# AsyncExecutor demo
python examples/demo_async_executor.py

# LeRobotAsyncClient demo
python examples/demo_lerobot_async.py

# Hybrid system demo
python examples/demo_hybrid_execution.py
```

## Troubleshooting

### AsyncExecutor Issues

**Problem**: Tasks not executing
```
Solution: Ensure executor.start() was called before submitting tasks
```

**Problem**: Status updates not appearing
```
Solution: Call get_status() or get_all_status_updates() regularly
```

### LeRobotAsyncClient Issues

**Problem**: PolicyServer fails to start
```
Solution: 
1. Check port 8080 is available: lsof -i :8080
2. Change server_port if needed
3. Check LeRobot is installed: pip install -e ".[async]"
```

**Problem**: RobotClient can't connect
```
Solution:
1. Check robot connection: ls /dev/ttyACM*
2. Verify robot_port in configuration
3. Ensure robot is calibrated: make calibrate
4. Verify robot_id matches calibration file: .cache/calibration/so101/<robot_id>.json
```

**Problem**: GPU out of memory
```
Solution:
1. Reduce actions_per_chunk (default: 50)
2. Use CPU: policy_device="cpu"
3. Close other GPU processes
```

## Performance Optimization

### For Gestures (AsyncExecutor)
1. Keep gestures short (< 2 seconds)
2. Avoid blocking operations in task executor
3. Monitor queue size to prevent buildup
4. Use context manager for automatic cleanup

### For Manipulation (LeRobotAsyncClient)
1. Keep PolicyServer running (don't restart between tasks)
2. Tune `actions_per_chunk` for your GPU
3. Adjust `chunk_size_threshold` for smoother execution
4. Use GPU for inference (much faster than CPU)
5. Optimize camera resolution if needed

## Future Enhancements

1. **Task Prioritization**: Add priority queue for urgent gestures
2. **Task Cancellation**: Allow canceling running manipulation tasks
3. **Progress Reporting**: Add fine-grained progress updates from SmolVLA
4. **Multi-Robot Support**: Extend to control multiple robots
5. **Task Composition**: Chain gestures and manipulations
6. **Adaptive Execution**: Switch between systems based on load

## References

- [AsyncExecutor Guide](./ASYNC_EXECUTOR_GUIDE.md)
- [LeRobot Async Inference Docs](https://github.com/huggingface/lerobot/blob/main/lerobot/async_inference/README.md)
- [Design Document](../.kiro/specs/gemini-multimodal-refactor/design.md)
- [Implementation Tasks](../.kiro/specs/gemini-multimodal-refactor/tasks.md)
