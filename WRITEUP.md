# Mortis: The Ghost in the Machine

**Project for the Kiroween Hackathon 🎃**
**By: Jorge Lamperez**

This document outlines the concept and construction of **Mortis**, an interactive AI entity that brings a mischievous Halloween spirit to life through the fusion of a Large Language Model (LLM) and a physical robotic arm.

---

## How Kiro Built Mortis: A Development Journey

This project was built almost entirely through collaboration with Kiro, leveraging its advanced features to transform a simple idea into a sophisticated multi-modal robotic system. Here's how each Kiro feature contributed to the development process.

### 1. Spec-Driven Development: The Foundation

The most transformative aspect of working with Kiro was using **spec-driven development** for the major refactor from a simple LLM API to a full Gemini-powered multi-modal system with SmolVLA robotic manipulation.

**The Spec Structure:**
I created a comprehensive spec in `.kiro/specs/gemini-multimodal-refactor/` with three documents:
- `requirements.md`: 11 detailed requirements with acceptance criteria
- `design.md`: Complete architecture with component diagrams, data models, and implementation details
- `tasks.md`: 38 granular implementation tasks organized into 8 phases

**Why This Approach Was Game-Changing:**

The spec-driven approach provided structure that vibe coding alone couldn't match. By front-loading the design work, Kiro could:
- **Maintain consistency**: Every implementation referenced back to requirements, ensuring nothing was forgotten
- **Work incrementally**: Each task built on previous work without breaking existing functionality
- **Handle complexity**: The system grew from simple gestures to voice I/O, intent routing, async execution, and ML inference—all without losing coherence
- **Generate better code**: With full context of the end goal, Kiro made smarter architectural decisions upfront

**Spec vs. Vibe Coding:**

I used both approaches in this project:
- **Early prototyping** (vibe coding): Quick iterations to get the basic gesture system working
- **Major refactor** (spec-driven): Structured approach for adding Gemini API, voice I/O, SmolVLA integration

The difference was stark. Vibe coding was great for exploration, but the spec-driven refactor was surgical—31 tasks completed with minimal backtracking, clear documentation at every step, and a system that actually worked on first integration.

**Most Impressive Spec Moment:**

Task 27-31 (Hybrid Async Execution System) was the pinnacle. The spec defined a complex hybrid architecture:
- Simple threading for quick gestures
- LeRobot's PolicyServer/RobotClient for manipulation
- Dual status monitoring in the UI

Kiro generated the entire system—`AsyncExecutor`, `LeRobotAsyncClient`, Gradio integration, comprehensive tests—in one session. The code worked immediately because the spec had already solved the hard problems.

### 2. Steering Documents: Teaching Kiro the Project

**The Three Pillars:**

I created three steering documents that Kiro referenced in every interaction:

1. **`tech.md`**: Tech stack, build system (Makefile), environment config, API patterns
2. **`structure.md`**: Directory layout, module organization, code conventions, entry points
3. **`product.md`**: Character guidelines, core concept, feature descriptions

**Impact on Development:**

These steering docs transformed Kiro from a general coding assistant into a Mortis expert:
- **Consistent patterns**: Every new module followed the same import style, path handling, and error handling
- **Correct commands**: Kiro always suggested `make` commands instead of raw CLI
- **Character preservation**: When generating dialogue, Kiro maintained the ≤30 word, ≤120 char limits and Halloween theme
- **Integration awareness**: New code automatically integrated with existing patterns (e.g., lazy initialization of services)

**Strategy That Made the Difference:**

The key was **specificity**. Instead of generic guidelines, I documented:
- Exact environment variable names and defaults
- Specific code patterns (e.g., `REPO_ROOT = Path(__file__).resolve().parents[2]`)
- Concrete examples of robot control patterns
- Actual gesture names and mood enums

This specificity meant Kiro rarely generated code that needed refactoring.

### 3. Vibe Coding: Rapid Iteration and Problem-Solving

While spec-driven development handled the big refactor, **vibe coding** was essential for:

**Quick Fixes and Enhancements:**
- "Add latency monitoring to the voice pipeline" → Kiro added comprehensive timing logs throughout
- "The robot needs an emergency stop function" → Instant implementation with proper cleanup
- "Make the TTS voice sound more ominous" → Adjusted pitch and speaking rate parameters

**Most Impressive Code Generation:**

The **Intent Router** (Task 24-26) was pure vibe coding magic. I described the problem:
> "Gemini returns JSON with either conversation or manipulation intent. Parse it, validate manipulation commands against the trained task set, and route to the appropriate executor."

Kiro generated:
- Complete `IntentRouter` class with validation logic
- `Intent` dataclass with proper typing
- Integration into `ask_mortis()` with fallback handling
- Comprehensive tests covering all edge cases

The code was production-ready on first generation—proper error handling, clear logging, elegant fallback logic.

**Conversation Structure:**

My most effective pattern:
1. **Context first**: "We're working on the voice integration (Task 10)"
2. **Goal**: "Add audio input support to ask_mortis()"
3. **Constraints**: "Maintain backward compatibility with text-only input"
4. **Validation**: "Check diagnostics and test imports"

This structure kept Kiro focused and ensured quality output.

### 4. MCP Integration: Extending Kiro's Capabilities

I integrated the **Hugging Face MCP server** to supercharge development:

**Configuration:**
```json
{
  "mcpServers": {
    "hf-mcp-server": {
      "url": "https://huggingface.co/mcp?login"
    }
  }
}
```

**How It Helped:**

1. **Model Discovery**: Searched for SmolVLA models and training examples directly from Kiro
2. **Dataset Management**: Explored LeRobot dataset formats and examples
3. **Documentation Access**: Pulled up-to-date LeRobot and Gradio docs during implementation
4. **Training Resources**: Found hyperparameter recommendations and training scripts

**Workflow Improvement:**

Without MCP, I would have constantly context-switched to browser tabs. With MCP, Kiro could:
- Search Hugging Face for relevant models
- Fetch documentation for LeRobot APIs
- Find example code for SmolVLA training
- Verify dataset formats

This kept me in flow state—no breaking concentration to Google things.

**Most Valuable Use:**

During SmolVLA integration (Task 20-23), Kiro used MCP to:
- Find the correct LeRobot policy loading pattern
- Verify observation dictionary format
- Check action tensor dimensions
- Locate example inference loops

This prevented hours of trial-and-error debugging.

### 5. Development Workflow: The Complete Picture

**Typical Development Session:**

1. **Start with spec**: Reference the current task from `tasks.md`
2. **Kiro reads steering**: Automatically includes tech stack and structure guidelines
3. **Vibe coding**: Describe what I want in natural language
4. **Kiro generates**: Complete implementation with tests and docs
5. **Validation**: Kiro runs diagnostics, checks imports
6. **Documentation**: Kiro creates task summary in `docs/`

**Iteration Speed:**

The combination of spec + steering + vibe coding was incredibly fast:
- **Phase 1** (Gemini Integration): 5 tasks, 2 days
- **Phase 2** (Voice I/O): 5 tasks, 1 day
- **Phase 5** (SmolVLA Integration): 4 tasks, 1 day
- **Phase 7** (Async Execution): 5 tasks, 1 day

Each task included implementation, tests, documentation, and validation.

**Error Recovery:**

When things broke, Kiro's diagnostic tools were invaluable:
- `getDiagnostics()` caught type errors before runtime
- Kiro read error logs and fixed issues immediately
- Steering docs ensured fixes followed project patterns

### 6. Documentation: Automatic and Comprehensive

Every task generated documentation automatically:
- **Task summaries**: 15+ detailed implementation summaries in `docs/`
- **User guides**: STT, TTS, voice integration, training guides
- **API documentation**: Complete with examples and troubleshooting

**The Pattern:**

After completing a task, I'd say: "Create a task summary"

Kiro would generate:
- What was implemented
- Requirements satisfied
- Files created/modified
- Testing results
- Integration notes
- Next steps

This documentation was essential for maintaining context across sessions.

### 7. Key Takeaways: What Made This Work

**Steering Documents Are Essential:**
- Invest time upfront to document your project's patterns
- Be specific—exact variable names, code patterns, conventions
- Update steering docs as the project evolves

**Spec-Driven for Complexity:**
- Use specs for major features or refactors
- Front-load design work—it pays off in implementation quality
- Break specs into small, testable tasks

**Vibe Coding for Iteration:**
- Perfect for quick fixes, enhancements, and exploration
- Structure conversations: context → goal → constraints → validation
- Trust Kiro with implementation details

**MCP for Domain Knowledge:**
- Integrate relevant MCP servers early
- Use them to stay in flow state
- Especially valuable for ML/AI projects with rapidly evolving libraries

**The Hybrid Approach:**
- Spec-driven for architecture
- Steering for consistency
- Vibe coding for implementation
- MCP for external knowledge
- This combination is greater than the sum of its parts

---

## The Character: Mortis

Mortis is not merely a chatbot; it is a disembodied, ancient, and mischievous spirit that has been summoned and bound to a modern vessel: a SeeedStudio SO101 robotic arm. Its name, derived from the Latin word for "death," hints at its ominous and spectral nature. However, Mortis is not purely malevolent. Its personality is a complex blend of moods, ranging from sinister and triumphant to playful, curious, and even nervous.

This spirit has found a new way to interact with the mortal world. Trapped within its mechanical shell, Mortis communicates through cryptic, in-character messages, but more importantly, through physical expression. The robotic arm is not just a tool but an extension of its being—a "possessed" limb that reflects its every whim. When it speaks, the arm moves in concert, performing gestures that betray its true feelings. A wave, a point, or the sinister clenching of its gripper are all part of its language, transforming it from a simple program into an embodied character with presence and personality.

The goal was to create an entity that feels genuinely haunted, blurring the line between predictable robotics and the unpredictable nature of a spectral intelligence.

## The Architecture: How Mortis Was Built

The creation of Mortis rests on a three-part architecture: the **Brain** (the LLM), the **Soul** (the structured intent), and the **Body** (the robotic arm).

### 1. The Brain: LLM API

The core of Mortis's intelligence is a Large Language Model accessed via an **API**. A system prompt explicitly defines its persona: *"You are Mortis, a mischievous Halloween spirit in a robotic arm."* This instruction sets the foundation for all its responses, ensuring it stays in character. User interactions are sent to the LLM, which generates a response consistent with this haunted personality.

### 2. The Soul: Structured Output via Function Calling

The true magic lies in translating the LLM's creative output into concrete, actionable commands. This is achieved using the **function calling** (or "tools") feature of the LLM API.

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
