# Camera Troubleshooting Guide

## Problem: Gradio Webcam Frozen When ENABLE_MANIPULATION=false

### Symptoms
- Gradio webcam shows frozen/black screen
- Cannot access webcam in browser
- LeRobot cameras (indices 0 and 8) are blocked

### Root Cause
When LeRobot async inference is enabled, it initializes and locks cameras with indices 0 and 8. Even when `ENABLE_MANIPULATION=false`, if the cameras were previously initialized, they may remain locked until the process is fully terminated.

### Solutions

#### Solution 1: Enable Automatic Camera Release (RECOMMENDED)

The best solution is to configure LeRobot to automatically release cameras when idle. This allows Gradio to access the webcam between manipulation tasks.

**Add to your `.env` file:**
```bash
LEROBOT_RELEASE_CAMERAS_WHEN_IDLE=true
```

**How it works:**
- When a manipulation task completes, LeRobot disconnects the cameras
- Gradio can now access the webcam
- When a new manipulation task starts, LeRobot reconnects the cameras automatically
- Small delay (~1-2 seconds) when starting tasks due to camera reconnection

**Pros:**
- ✅ Allows concurrent use of Gradio webcam and LeRobot manipulation
- ✅ Automatic - no manual intervention needed
- ✅ Works with all 3 cameras

**Cons:**
- ⚠️ Slight delay when starting manipulation tasks (camera reconnection)
- ⚠️ Not suitable if you need continuous camera streaming

#### Solution 2: Restart the Application
The simplest solution is to fully restart the Mortis application:

```bash
# Stop the current process (Ctrl+C)
# Then restart
make run
```

This ensures all camera resources are released.

#### Solution 2: Identify Available Cameras
Find which cameras are available on your system:

```bash
# List all video devices
ls -la /dev/video*

# Or use v4l2-ctl (if installed)
v4l2-ctl --list-devices
```

You should see something like:
```
/dev/video0  <- Used by LeRobot (OpenCV camera)
/dev/video2  <- RealSense camera (multiple indices)
/dev/video4
/dev/video6
/dev/video8  <- Used by LeRobot (OpenCV camera)
/dev/video10 <- Available for Gradio
```

#### Solution 3: Configure Browser to Use Specific Camera
In your browser (Chrome/Firefox):

1. Click the camera icon in the address bar when Gradio asks for camera permission
2. Select "Camera settings" or "Manage camera permissions"
3. Choose a different camera from the dropdown (not camera 0 or 8)
4. Refresh the Gradio page

#### Solution 4: Disable LeRobot Cameras Completely
If you don't need LeRobot manipulation at all, you can prevent camera initialization by keeping `ENABLE_MANIPULATION=false` in your `.env` file:

```bash
# .env
ENABLE_MANIPULATION=false
```

Then make sure to restart the application completely.

#### Solution 5: Use a Different Camera for Gradio
If you have 3 cameras and want to dedicate one for Gradio:

1. Identify your third camera index (e.g., `/dev/video2`, `/dev/video10`)
2. Configure your browser to use that specific camera (see Solution 3)
3. Keep LeRobot cameras (0 and 8) for manipulation tasks

### Camera Configuration Reference

**LeRobot Default Configuration:**
- Camera 1: RealSense (serial: 030522070314) - typically `/dev/video0-6`
- Camera 2: OpenCV (index: 8) - `/dev/video8`

**Gradio Webcam:**
- Uses browser's default camera (usually `/dev/video0`)
- Can be changed in browser settings

### Prevention

To avoid camera conflicts:

1. **Always restart the application** after changing `ENABLE_MANIPULATION` setting
2. **Use different cameras** for LeRobot and Gradio
3. **Check camera availability** before starting the application
4. **Close other applications** that might be using cameras (Zoom, Skype, etc.)

### Advanced: Release Cameras Manually

If cameras remain locked after stopping the application:

```bash
# Find processes using video devices
sudo lsof /dev/video* 2>/dev/null

# Kill the process if needed (replace PID with actual process ID)
kill -9 <PID>
```

### Testing Camera Access

Test if a camera is available:

```bash
# Test camera 0
ffmpeg -f v4l2 -i /dev/video0 -frames:v 1 test0.jpg

# Test camera 2
ffmpeg -f v4l2 -i /dev/video2 -frames:v 1 test2.jpg

# Test camera 8
ffmpeg -f v4l2 -i /dev/video8 -frames:v 1 test8.jpg
```

If a camera is locked, you'll see an error like:
```
/dev/video0: Device or resource busy
```

### Quick Fix Checklist

- [ ] Stop the Mortis application completely (Ctrl+C)
- [ ] Verify `ENABLE_MANIPULATION=false` in `.env`
- [ ] Check no other processes are using cameras: `lsof /dev/video*`
- [ ] Restart the application: `make run`
- [ ] In browser, select a different camera in Gradio webcam settings
- [ ] Refresh the Gradio page

### Still Having Issues?

If the problem persists:

1. Check system logs: `dmesg | grep video`
2. Verify camera permissions: `ls -la /dev/video*`
3. Test cameras individually with `ffmpeg` (see above)
4. Restart your computer to fully release all camera resources
