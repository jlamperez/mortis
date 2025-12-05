# Manipulation Task Timeout Guide

## Understanding Task Limits

The main limit that controls manipulation task execution is:

**`MANIPULATION_TIMEOUT`** - Maximum time in seconds (default: 60.0)

Note: `MANIPULATION_MAX_STEPS` is kept for future use but currently not enforced by LeRobot's control loop.

## The Problem: Tasks Never Complete

VLA (Vision-Language-Action) models like SmolVLA don't have a built-in "task complete" signal. They will keep generating actions indefinitely unless stopped by:
- Reaching max_steps limit
- Reaching timeout limit  
- Manual stop button

If your tasks never complete on their own, this is **expected behavior** - you need to tune the limits.

## Typical Task Duration

Most manipulation tasks take **30-60 seconds** to complete:
- Simple pick-and-place: 30-45 seconds (900-1350 steps at 30fps)
- Complex multi-step tasks: 45-90 seconds (1350-2700 steps)
- Tasks with precise positioning: 60+ seconds (1800+ steps)

### What Happens on Timeout

1. Task is marked as STOPPED immediately
2. UI shows the timeout message
3. **The robot continues its current actions** (control loop finishes naturally)
4. After a few seconds, the robot stops and is ready for new tasks

### Recommended Settings

```bash
# For most tasks (recommended default)
MANIPULATION_TIMEOUT=60.0

# For simple, quick tasks (20-30 seconds)
MANIPULATION_TIMEOUT=30.0

# For complex, multi-step tasks (60-90 seconds)
MANIPULATION_TIMEOUT=90.0

# For testing/debugging (stop quickly to see behavior)
MANIPULATION_TIMEOUT=20.0
```

## How to Adjust

Edit your `.env` file:

```bash
MANIPULATION_TIMEOUT=60.0
```

Changes take effect on the next task execution (no restart needed).

## Tuning for Your Tasks

1. **Start with default** (60s timeout)
2. **Observe when tasks naturally "finish"** - When does the robot stop making useful progress?
3. **Set timeout slightly after that point** - Give it a bit of buffer
4. **Test and adjust** - If tasks are cut off too early, increase timeout

Example: If your pick-and-place tasks typically finish around 40 seconds:
```bash
MANIPULATION_TIMEOUT=50.0      # 10s buffer
```

## When to Use Manual Stop

The "🛑 Stop Manipulation Task" button is for:
- Tasks that are clearly stuck or repeating
- Tasks that are doing the wrong thing
- Emergency stops

**Don't use it** if the robot is making progress - just wait for completion or increase the timeout.

## Monitoring Task Progress

Watch the status display:
- `🤖 Manipulation: Pick up the skull... (15.3s)` - Task is running, elapsed time shown
- `⏹️ Stopped (finishing actions...)` - Timeout occurred, robot finishing current actions
- `✅ Manipulation complete (42.5s)` - Task completed successfully

If tasks consistently timeout but were making progress, increase `MANIPULATION_TIMEOUT`.
