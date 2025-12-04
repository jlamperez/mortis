# Implementation Plan

This implementation plan breaks down the Gemini multi-modal refactor into discrete, actionable coding tasks. Each task builds incrementally on previous work, following the 8-phase migration strategy outlined in the design document.

## Phase 1: Gemini API Integration

- [x] 1. Set up Gemini API client infrastructure
  - Create `src/mortis/gemini_client.py` module
  - Implement `GeminiClient` class with configuration management
  - Add environment variable handling for `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_TEMPERATURE`
  - Implement basic `send_message()` method using `google.generativeai` SDK
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Implement structured response parsing
  - Create `src/mortis/models.py` for data models
  - Implement `GeminiResponse`, `ResponseType`, `Mood`, `Gesture` enums and dataclasses
  - Add `from_json()` method for parsing Gemini JSON responses
  - Implement response validation logic
  - _Requirements: 1.1, 3.5_

- [x] 3. Design and implement Gemini system prompt
  - Create system prompt with Mortis character definition
  - Add manipulation task definitions (6 tasks) to prompt
  - Implement JSON response format specification in prompt
  - Configure Gemini to use JSON mode (`response_mime_type: application/json`)
  - _Requirements: 3.1, 3.2, 9.2_

- [x] 4. Implement error handling and retry logic
  - Add exponential backoff retry for rate limiting
  - Handle `BlockedPromptException` with fallback responses
  - Implement timeout handling for API calls
  - Add error logging and user-friendly error messages
  - _Requirements: 1.4, 11.1_

- [x] 5. Replace existing LLM API in tools.py
  - Refactor `ask_mortis()` function to use `GeminiClient`
  - Update response parsing to use new data models
  - Maintain backward compatibility with gesture execution
  - Update environment configuration documentation
  - _Requirements: 1.1, 9.1, 9.4_

- [ ]* 5.1 Write integration tests for Gemini client
  - Test successful API calls and response parsing
  - Test retry logic with mocked rate limit errors
  - Test fallback responses on API failures
  - Verify character personality maintained in responses
  - _Requirements: 1.1, 1.4_


## Phase 2: Voice Input and Output

- [x] 6. Implement Speech-to-Text service
  - Create `src/mortis/stt_service.py` module
  - Implement `STTService` class with Gemini native audio support
  - Add fallback to Google Cloud Speech-to-Text API
  - Implement audio file format validation and conversion
  - Add configuration for STT service selection (Gemini vs Google STT)
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 7. Implement Text-to-Speech service
  - Create `src/mortis/tts_service.py` module
  - Implement `TTSService` class using Google Cloud TTS
  - Configure voice parameters (pitch, speed) for Mortis character
  - Implement audio file generation (MP3 format)
  - Add local TTS fallback (gTTS) for offline scenarios
  - _Requirements: 8.1, 8.2, 8.4, 8.5_

- [x] 8. Update Gradio UI for audio input
  - Add `gr.Audio` component for microphone input to `app.py`
  - Implement audio input handler function
  - Connect audio input to STT service
  - Display transcribed text to user for confirmation
  - Handle audio processing errors gracefully
  - _Requirements: 2.1, 2.5, 11.2_

- [x] 9. Update Gradio UI for audio output
  - Add `gr.Audio` component for audio playback
  - Implement audio response generation in `mortis_reply()`
  - Configure autoplay for audio responses
  - Create `outputs/` directory for temporary audio files
  - Implement audio file cleanup mechanism
  - _Requirements: 8.3, 8.4_

- [x] 10. Integrate voice flow with Gemini
  - Update `ask_mortis()` to accept audio input
  - Implement voice-to-text-to-Gemini-to-TTS pipeline
  - Maintain text input compatibility
  - Add latency monitoring for voice processing
  - _Requirements: 2.4, 9.3_

- [ ]* 10.1 Write tests for audio processing
  - Test STT with sample audio files
  - Test TTS output quality and format
  - Test audio input/output in Gradio UI
  - Verify fallback mechanisms work correctly
  - _Requirements: 2.2, 8.2, 11.2, 11.4_


## Phase 3: Dataset Collection Infrastructure

- [x] 11. Set up LeRobot dataset infrastructure
  - Create `src/mortis/data_collector.py` module
  - Implement `DataCollector` class with LeRobot dataset integration
  - Configure dataset directory structure (`data/mortis_manipulation/`)
  - Implement dataset metadata management (task descriptions, episode counts)
  - _Requirements: 4.3, 5.2_

- [ ]* 12. Implement camera integration for data collection
  - Add camera initialization in `DataCollector`
  - Implement synchronized image capture with robot state
  - Configure camera parameters (resolution, FPS)
  - Add camera calibration utilities
  - _Requirements: 4.2_

- [ ]* 13. Implement episode recording functionality
  - Create `record_episode()` method for capturing demonstrations
  - Implement real-time data capture loop (30 FPS)
  - Add keyboard controls for start/stop recording
  - Implement episode data validation
  - Save episodes in LeRobot-compatible format
  - _Requirements: 4.1, 4.2, 4.5_

- [ ]* 14. Implement task labeling system
  - Add task description input for each episode
  - Create task label validation against predefined task set
  - Implement episode metadata storage
  - Add episode review and re-recording capability
  - _Requirements: 4.4_

- [ ]* 15. Create data collection CLI script
  - Create `src/mortis/collect_data.py` entry point
  - Implement interactive data collection workflow
  - Add progress tracking (episodes per task)
  - Implement dataset statistics display
  - Add Hugging Face Hub upload functionality
  - _Requirements: 4.1, 4.3, 5.1_

- [ ]* 15.1 Write data validation tests
  - Test episode data format compliance
  - Verify synchronized timestamps
  - Check image quality and dimensions
  - Validate action sequences
  - _Requirements: 4.5_


## Phase 4: SmolVLA Training Pipeline

- [ ]* 16. Create training configuration
  - Create `config/train_smolvla.yaml` with Hydra configuration
  - Configure SmolVLA policy parameters (vision backbone, chunk size)
  - Set training hyperparameters (batch size, learning rate, steps)
  - Configure evaluation settings
  - Add Weights & Biases integration configuration
  - _Requirements: 5.3, 5.5_

- [x] 17. Implement training script
  - Create `src/mortis/train.py` module
  - Implement dataset loading from local or Hugging Face
  - Configure LeRobot training pipeline
  - Add checkpoint saving logic
  - Implement training progress logging
  - _Requirements: 5.1, 5.2, 5.4, 5.5_

- [ ]* 18. Set up training monitoring
  - Integrate Weights & Biases for metric tracking
  - Log training loss, validation loss, learning rate
  - Add sample prediction visualization
  - Implement early stopping based on validation performance
  - _Requirements: 5.5_

- [ ]* 19. Create training execution commands
  - Add `train-smolvla` target to Makefile
  - Document training command with all parameters
  - Add GPU memory optimization flags
  - Create training resume functionality for interrupted runs
  - _Requirements: 5.3, 5.4_

- [ ]* 19.1 Write training validation tests
  - Test dataset loading and batching
  - Verify model architecture initialization
  - Test checkpoint saving and loading
  - Validate training loop executes without errors
  - _Requirements: 5.2, 5.4_


## Phase 5: SmolVLA Inference Integration

- [x] 20. Implement SmolVLA executor
  - Create `src/mortis/smolvla_executor.py` module
  - Implement `SmolVLAExecutor` class with model loading
  - Add checkpoint loading from configurable path
  - Implement GPU device management
  - Add model initialization and warmup
  - _Requirements: 6.1, 8.2_

- [x] 21. Implement observation capture
  - Add camera integration for visual observations
  - Implement robot state capture from SO101
  - Create observation dictionary formatting for SmolVLA
  - Add tensor conversion and device placement
  - _Requirements: 6.2, 6.4_

- [x] 22. Implement action execution loop
  - Create `execute()` method for task execution
  - Implement inference loop with visual feedback
  - Add action tensor to SO101 command conversion
  - Implement step-by-step action execution
  - Add task completion detection logic
  - _Requirements: 6.2, 6.3_

- [x] 23. Implement safety and error handling
  - Add command validation against trained task set
  - Implement workspace safety checks
  - Add emergency stop functionality
  - Implement timeout handling for long-running tasks
  - Add GPU out-of-memory recovery
  - _Requirements: 6.5, 11.3_

- [ ]* 23.1 Write SmolVLA inference tests
  - Test model loading from checkpoint
  - Test observation capture and formatting
  - Test action prediction and execution
  - Verify emergency stop functionality
  - _Requirements: 6.1, 6.3, 6.5_


## Phase 6: Intent Detection and Routing

- [ ] 24. Implement intent router
  - Create `src/mortis/intent_router.py` module
  - Implement `IntentRouter` class with task definitions
  - Add `parse_gemini_response()` method for JSON parsing
  - Implement command validation logic
  - Create `Intent` dataclass for structured intent representation
  - _Requirements: 3.2, 3.3, 3.4, 3.5_

- [ ] 25. Update Gemini prompt for intent detection
  - Enhance system prompt with all 6 manipulation task definitions
  - Add clear response format specification for manipulation vs conversation
  - Implement intent type detection in prompt
  - Add examples of manipulation and conversational inputs
  - _Requirements: 3.1, 3.2_

- [ ] 26. Integrate intent routing in main flow
  - Update `ask_mortis()` to use `IntentRouter`
  - Implement routing logic for manipulation vs gesture execution
  - Add command validation before SmolVLA execution
  - Implement fallback to gestures for invalid commands
  - _Requirements: 3.3, 3.4, 3.5_

- [ ]* 26.1 Write intent detection tests
  - Test parsing of manipulation responses
  - Test parsing of conversational responses
  - Test command validation logic
  - Verify fallback behavior for invalid commands
  - Test edge cases and malformed responses
  - _Requirements: 3.2, 3.3, 3.4_


## Phase 7: Asynchronous Execution System

- [ ] 27. Implement async executor infrastructure
  - Create `src/mortis/async_executor.py` module
  - Implement `AsyncExecutor` class with task queue
  - Add background worker thread for task processing
  - Implement status queue for progress updates
  - Add start/stop methods for executor lifecycle
  - _Requirements: 7.1, 7.2_

- [ ] 28. Implement task models and queue management
  - Create `Task` dataclass in `models.py`
  - Implement task creation methods for gestures and manipulation
  - Add task status tracking (queued, running, complete, failed)
  - Implement task submission and retrieval methods
  - _Requirements: 7.1, 7.5_

- [ ] 29. Integrate async execution with SmolVLA
  - Update SmolVLA executor to work with async system
  - Implement task execution in worker thread
  - Add status updates during SmolVLA inference
  - Handle errors and update task status accordingly
  - _Requirements: 7.1, 7.2, 7.5_

- [ ] 30. Add status display to Gradio UI
  - Add status textbox component to UI
  - Implement `check_status()` function for periodic updates
  - Configure Gradio to poll status every 500ms
  - Display task progress, completion, and errors
  - Add visual indicators for different task states
  - _Requirements: 7.3, 7.4, 7.5_

- [ ] 31. Update main flow for async execution
  - Modify `mortis_reply()` to submit tasks asynchronously
  - Return immediate response while task executes in background
  - Implement task queuing for multiple requests
  - Add concurrent request handling
  - _Requirements: 7.1, 7.2, 7.5_

- [ ]* 31.1 Write async execution tests
  - Test task queue operations
  - Test background worker thread
  - Test status updates and retrieval
  - Verify UI remains responsive during long tasks
  - Test concurrent task submission
  - _Requirements: 7.1, 7.2, 7.3, 7.5_


## Phase 8: Integration, Testing, and Deployment

- [ ] 32. Update project dependencies
  - Update `pyproject.toml` with new dependencies (google-generativeai, google-cloud-speech, google-cloud-texttospeech)
  - Add optional dependencies for training (wandb, hydra-core)
  - Update Makefile with new commands (collect-data, train-smolvla)
  - Run `make install` to sync dependencies
  - _Requirements: 8.4, 9.5_

- [ ] 33. Update environment configuration
  - Create `.env.example` with all required variables
  - Document Gemini API key setup
  - Document Google Cloud credentials setup
  - Add SmolVLA checkpoint path configuration
  - Update README with new environment variables
  - _Requirements: 1.3, 8.4_

- [ ] 34. Implement logging and monitoring
  - Add structured logging throughout application
  - Log Gemini API calls and response times
  - Log SmolVLA inference times and success rates
  - Add error logging with stack traces
  - Create log rotation and cleanup
  - _Requirements: 11.5_

- [ ] 35. Create comprehensive documentation
  - Update README with new features and setup instructions
  - Document data collection workflow
  - Document training process
  - Create user guide for voice interaction
  - Add troubleshooting section
  - _Requirements: 8.4, 9.5_

- [ ] 36. Perform end-to-end integration testing
  - Test complete voice input → Gemini → SmolVLA → audio output flow
  - Test text input → intent detection → gesture execution flow
  - Test error handling and recovery across all components
  - Verify UI responsiveness during long operations
  - Test with all 6 manipulation tasks
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [ ]* 36.1 Write system-level tests
  - Test multi-modal interaction flows
  - Test concurrent user requests
  - Test resource usage (GPU memory, CPU)
  - Benchmark performance metrics
  - _Requirements: 1.5, 2.4, 7.3_

- [ ] 37. Optimize performance
  - Profile Gemini API response times
  - Optimize SmolVLA inference speed
  - Reduce audio processing latency
  - Implement caching where appropriate
  - Optimize GPU memory usage
  - _Requirements: 1.5, 2.4_

- [ ] 38. Final deployment preparation
  - Create deployment checklist
  - Set up monitoring and alerting
  - Prepare rollback procedures
  - Create backup of current system
  - Document deployment process
  - _Requirements: 8.1, 8.2, 8.3_

