# Requirements Document

## Introduction

This document specifies the requirements for refactoring the Mortis interactive AI Halloween experience to use Google Gemini API with multi-modal (voice and text) interaction capabilities. The refactor replaces the existing LLM API integration and adds SmolVLA-based robotic control for specific manipulation tasks. The system must maintain the character-driven conversational experience while enabling precise robotic manipulation through voice or text commands.

## Glossary

- **Mortis System**: The complete interactive AI Halloween experience including web UI, conversational AI, and robotic arm control
- **Gemini API**: Google's large language model API service used for conversational AI and intent detection
- **SmolVLA Model**: A vision-language-action model trained using LeRobot for specific robotic manipulation tasks
- **Gradio Interface**: The web-based user interface framework for the Mortis System
- **SO101 Arm**: The SeeedStudio SO101 robotic arm hardware controlled by the Mortis System
- **STT Service**: Speech-to-Text service that converts audio input to text
- **TTS Service**: Text-to-Speech service that converts text responses to audio output
- **Task String**: A specific command format recognized by the SmolVLA Model (e.g., "Pick up the skull and place it in the green cup")
- **LeRobot Framework**: The robotics framework used for dataset management, model training, and inference
- **Message Queue**: An asynchronous communication mechanism for decoupling robotic execution from the web interface
- **Cloud-Agnostic Architecture**: A system design that does not depend on vendor-specific cloud platform services (like AWS Lambda, Azure Functions, or GCP Cloud Run), allowing deployment on any infrastructure including local hardware

## Requirements

### Requirement 1: Gemini API Integration

**User Story:** As a developer, I want to replace the existing LLM API with Google Gemini API, so that the system uses Google's language model for all conversational interactions.

#### Acceptance Criteria

1. THE Mortis System SHALL use the Google Gemini API for all language model interactions
2. THE Mortis System SHALL support multiple Gemini model variants through configuration
3. THE Mortis System SHALL authenticate with the Gemini API using API keys stored in environment variables
4. THE Mortis System SHALL handle Gemini API errors gracefully and provide user feedback when API calls fail
5. THE Mortis System SHALL maintain response times under 5 seconds for typical conversational interactions

### Requirement 2: Multi-Modal Voice Input

**User Story:** As a user, I want to speak to Mortis through my microphone, so that I can interact naturally without typing.

#### Acceptance Criteria

1. THE Gradio Interface SHALL provide an audio input component for capturing user voice
2. WHEN a user provides voice input, THE Mortis System SHALL convert the audio to text using a Speech-to-Text service
3. THE Mortis System SHALL support both cloud-based STT services and local STT models as configurable options
4. THE Mortis System SHALL process voice input with latency under 3 seconds for utterances under 10 seconds
5. THE Mortis System SHALL display the transcribed text to the user for confirmation

### Requirement 3: Intent Detection and Command Routing

**User Story:** As a system, I want to detect when user input matches a specific robotic task command, so that I can route the request to the appropriate control mechanism.

#### Acceptance Criteria

1. THE Gemini API SHALL receive a system prompt that defines all valid SmolVLA Task Strings
2. WHEN the Gemini API processes user input, THE Mortis System SHALL determine if the input matches a valid Task String
3. IF the user input matches a valid Task String, THEN THE Mortis System SHALL extract the exact command string for robotic execution
4. IF the user input does not match a valid Task String, THEN THE Mortis System SHALL generate a standard conversational response with gesture control
5. THE Mortis System SHALL return both a conversational response and a command indicator in a structured format

### Requirement 4: Dataset Creation and Collection

**User Story:** As a developer, I want to create and collect demonstration data for robotic manipulation tasks, so that I have training data for the SmolVLA model.

#### Acceptance Criteria

1. THE Mortis System SHALL provide a data collection script for recording SO101 Arm demonstrations
2. THE Mortis System SHALL capture synchronized camera observations and robot actions during demonstrations
3. THE Mortis System SHALL save collected demonstrations in LeRobot-compatible format
4. THE Mortis System SHALL support labeling demonstrations with corresponding Task String commands
5. THE Mortis System SHALL validate collected data for completeness before adding to the training dataset

### Requirement 5: SmolVLA Model Training Infrastructure

**User Story:** As a developer, I want to train a SmolVLA model using LeRobot with collected demonstration data, so that the robot can perform precise manipulation tasks.

#### Acceptance Criteria

1. THE Mortis System SHALL provide a training script that loads datasets from local LeRobot databases or Hugging Face
2. THE Mortis System SHALL create and manage LeRobot dataset databases for training data
3. THE Mortis System SHALL configure SmolVLA training using lerobot-train with appropriate hyperparameters
4. THE Mortis System SHALL save trained model checkpoints to a configurable directory
5. THE Mortis System SHALL log training metrics including loss, accuracy, and validation performance

### Requirement 6: SmolVLA Inference Execution

**User Story:** As a system, I want to execute SmolVLA model inference when a valid task command is detected, so that the robot performs the requested manipulation.

#### Acceptance Criteria

1. THE Mortis System SHALL load the trained SmolVLA Model from saved checkpoints
2. WHEN a valid Task String is received, THE Mortis System SHALL execute SmolVLA inference with the command as input
3. THE Mortis System SHALL control the SO101 Arm through the SmolVLA Model output actions
4. THE Mortis System SHALL provide visual feedback during robotic execution through the webcam view
5. THE Mortis System SHALL handle inference errors and return the robot to a safe idle state

### Requirement 7: Asynchronous Robotic Execution

**User Story:** As a user, I want the web interface to remain responsive while the robot executes tasks, so that I can monitor progress without the UI freezing.

#### Acceptance Criteria

1. THE Mortis System SHALL execute SmolVLA inference asynchronously without blocking the Gradio Interface
2. THE Mortis System SHALL use a message queue or background processing mechanism to decouple inference from the web interface
3. WHILE SmolVLA inference is executing, THE Gradio Interface SHALL display a status indicator showing task progress
4. THE Mortis System SHALL allow users to view the robot's actions through the webcam during execution
5. WHEN robotic execution completes, THE Mortis System SHALL update the interface with completion status

### Requirement 8: Voice Output Integration

**User Story:** As a user, I want to hear Mortis speak responses aloud, so that I can experience a fully voice-based interaction.

#### Acceptance Criteria

1. THE Mortis System SHALL convert Gemini API text responses to audio using a Text-to-Speech service
2. THE Mortis System SHALL support Google TTS or equivalent widely-available TTS services
3. THE Gradio Interface SHALL play generated audio responses automatically after receiving them
4. THE Mortis System SHALL generate audio in a format compatible with web browsers (MP3 or WAV)
5. THE Mortis System SHALL maintain character voice consistency across all audio responses

### Requirement 9: Architecture and Deployment

**User Story:** As a developer, I want a system that can run on local hardware without vendor-specific cloud dependencies, so that I can deploy it flexibly while using Google APIs for LLM services.

#### Acceptance Criteria

1. THE Mortis System SHALL not depend on vendor-specific cloud platform services such as AWS Lambda, Azure Functions, or GCP Cloud Run
2. THE Mortis System SHALL support deployment on local hardware with GPU access for SmolVLA inference
3. THE Mortis System SHALL use standard Python libraries and open-source frameworks for all non-Google API components
4. THE Mortis System SHALL document all external service dependencies in the environment configuration
5. THE Mortis System SHALL provide configuration options for switching between cloud-based and local STT and TTS processing

### Requirement 10: Backward Compatibility and Migration

**User Story:** As a developer, I want to migrate from the existing LLM API to Gemini without losing existing functionality, so that users experience a seamless transition.

#### Acceptance Criteria

1. THE Mortis System SHALL maintain all existing gesture capabilities during the refactor
2. THE Mortis System SHALL preserve the Halloween character theme and response style
3. THE Mortis System SHALL continue to support text-only interaction for users without microphones
4. THE Mortis System SHALL maintain the existing Gradio Interface layout and visual design
5. THE Mortis System SHALL provide a migration guide documenting configuration changes

### Requirement 11: Error Handling and Robustness

**User Story:** As a user, I want the system to handle errors gracefully, so that temporary failures don't break my interaction experience.

#### Acceptance Criteria

1. IF the Gemini API is unavailable, THEN THE Mortis System SHALL display an error message and allow retry
2. IF STT conversion fails, THEN THE Mortis System SHALL prompt the user to try again or use text input
3. IF SmolVLA inference fails, THEN THE Mortis System SHALL return the SO101 Arm to idle position safely
4. IF TTS generation fails, THEN THE Mortis System SHALL display the text response without audio
5. THE Mortis System SHALL log all errors with sufficient detail for debugging
