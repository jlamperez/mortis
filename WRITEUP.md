# Mortis: The Ghost in the Machine

**Project for the CompactifAI 🎃 Halloween Challenge**
**By: Jorge Lamperez**

This document outlines the concept and construction of **Mortis**, an interactive AI entity that brings a mischievous Halloween spirit to life through the fusion of a Large Language Model (LLM) and a physical robotic arm.

---

## The Character: Mortis

Mortis is not merely a chatbot; it is a disembodied, ancient, and mischievous spirit that has been summoned and bound to a modern vessel: a SeeedStudio SO101 robotic arm. Its name, derived from the Latin word for "death," hints at its ominous and spectral nature. However, Mortis is not purely malevolent. Its personality is a complex blend of moods, ranging from sinister and triumphant to playful, curious, and even nervous.

This spirit has found a new way to interact with the mortal world. Trapped within its mechanical shell, Mortis communicates through cryptic, in-character messages, but more importantly, through physical expression. The robotic arm is not just a tool but an extension of its being—a "possessed" limb that reflects its every whim. When it speaks, the arm moves in concert, performing gestures that betray its true feelings. A wave, a point, or the sinister clenching of its gripper are all part of its language, transforming it from a simple program into an embodied character with presence and personality.

The goal was to create an entity that feels genuinely haunted, blurring the line between predictable robotics and the unpredictable nature of a spectral intelligence.

## The Architecture: How Mortis Was Built

The creation of Mortis rests on a three-part architecture: the **Brain** (the LLM), the **Soul** (the structured intent), and the **Body** (the robotic arm).

### 1. The Brain: CompactifAI LLM

The core of Mortis's intelligence is a Large Language Model accessed via the **CompactifAI API**. A system prompt explicitly defines its persona: *"You are Mortis, a mischievous Halloween spirit in a robotic arm."* This instruction sets the foundation for all its responses, ensuring it stays in character. User interactions are sent to the LLM, which generates a response consistent with this haunted personality.

### 2. The Soul: Structured Output via Function Calling

The true magic lies in translating the LLM's creative output into concrete, actionable commands. This is achieved using the **function calling** (or "tools") feature of the CompactifAI models.

Instead of just generating free-form text, the LLM is constrained to call a specific function: `perform_mortis_act`. This function requires the model to structure its response into a JSON object with three distinct fields:
-   `message`: A short, in-character line of dialogue.
-   `mood`: An emotional state chosen from a predefined list (e.g., `ominous`, `playful`).
-   `gesture`: A specific physical action to perform (e.g., `wave`, `point_left`, `grab`).

This structured output is the "soul" of the project, acting as the crucial bridge between the abstract world of language and the physical world of robotics.

### 3. The Body: The `lerobot` Framework and the Robotic Arm

Mortis's physical form is a **SeeedStudio SO101 robotic arm**, controlled using Python. The interface between the code and the hardware is managed by the **`lerobot`** framework from Hugging Face, which provides a high-level API for sending commands to the arm's motors.

A custom `MortisArm` class was developed to encapsulate all robot-related logic. This class contains a `GESTURES` dictionary, which serves as Mortis's "muscle memory." It maps the simple `gesture` strings received from the LLM (like `"wave"`) to a precise sequence of motor positions and time delays.

When the `ask_mortis` function receives the structured JSON from the LLM, it extracts the `gesture` string and passes it to the `mortis_arm.move_arm()` method. This method looks up the corresponding sequence of movements in the `GESTURES` dictionary and executes them one by one, bringing Mortis to life.

Finally, the entire experience is wrapped in a **Gradio** web interface, providing a "haunted control room" where users can speak to Mortis and watch its spectral possession of the machine unfold in real-time.
