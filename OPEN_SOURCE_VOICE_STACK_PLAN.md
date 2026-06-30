# Open-Source Voice Stack Plan

## Product Direction

Ram is the user-facing assistant. Sham is the backend/tool intelligence layer.

The open-source voice stack should keep that split:

- Ram owns microphone input, speech-to-text, user session, UI, and spoken responses.
- Sham owns backend skills, tool reasoning, weather intelligence, RAG, and future capabilities.

## Why Replace VAPI Gradually

VAPI currently gives us several things at once:

1. Microphone capture
2. Speech-to-text
3. LLM conversation
4. Tool calling
5. Text-to-speech
6. Session/call state

To learn and control the system, we will replace these pieces step by step instead of all at once.

## Target Architecture

First open-source flow:

```text
Browser microphone
-> Ram STT endpoint
-> Whisper transcription
-> Ram command/action routing
-> existing Ram/Sham backend endpoints
-> response text
-> browser text-to-speech
```

Later flow:

```text
Browser microphone
-> Ram STT endpoint
-> fine-tuned Whisper
-> local/open-source LLM planner
-> Sham skills/tools
-> open-source TTS model
```

## Phase 1: Replace STT First

Goal:

Use Whisper to transcribe user speech and display the transcript in the assistant UI.

Tasks:

- Add browser audio recording with `MediaRecorder`.
- Add Ram endpoint: `POST /stt/transcribe`.
- Run Whisper transcription on uploaded audio.
- Show transcript in the UI.
- Keep existing VAPI flow available until the new flow works.

## Phase 2: Route Text To Existing Actions

Goal:

Use transcribed text to call existing backend actions.

Initial command:

- "What are my meetings today?"

Backend path:

- Call existing `/meetings-weather-summary`.
- Return summary text.

## Phase 3: Add Simple TTS

Goal:

Speak the backend response back to the user.

First version:

- Use browser `speechSynthesis`.

Later version:

- Replace browser TTS with an open-source TTS model such as Piper or Coqui.

## Phase 4: Replace VAPI Tool Planning

Goal:

Move from fixed command routing to an assistant planner.

Possible approaches:

- simple rules first
- structured LLM output later
- local/open-source LLM after the STT path is stable

## Current Next Step

Create a feature branch in Ram:

```bash
git checkout -b feature/open-source-voice-stack
```

Then start with Phase 1: browser recording and `/stt/transcribe`.

